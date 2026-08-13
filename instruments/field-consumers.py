#!/usr/bin/env python3
"""field-consumers -- does every payload field this ledger actually
carries have a READER? (F1.4)

META-REPO ONLY (ADR-003 rule 2), same posture as gate-reachability.sh:
this sweeps THIS repository's ledger against THIS repository's code.

--- WHY THIS EXISTS ------------------------------------------------------
ADR-046 states the envelope admission rule -- a payload field is admitted
only if the fold or a blocking gate reads it -- and then leaves the rule
as prose. Prose does not fail. A field with no reader is not harmless
decoration: it is a record that LOOKS like it is doing work. Every one of
them invites an auditor to trust a label nothing consumes, and the cost
compounds because the field is append-only and permanent.

Measured at the time of writing: `reaffirm_cleared` rides 1072 records in
this ledger, is written by cmd_reaffirm, and is read by nothing. It is
the label that says which watched-file change an anchor advance buried --
exactly the audit trail the burial was made auditable for -- and no code
has ever looked at it. That is what an unmeasured admission rule costs.

--- THE READER RULE ------------------------------------------------------
A payload key K has a reader when some file under the SEARCH ROOTS reads
the VALUE stored at K:

    x.get("K")           x.get("K", default)
    x["K"]               (Load context only)

A PRESENCE TEST IS NOT A READER, and this distinction is the sharpest
thing the sweep does:

    "K" in x                     asks whether the field exists
    x.get("K") is not None       ditto
    if x.get("K"): / not x[...]  ditto

A field whose only consumer asks whether it is there could be replaced by
a boolean, and everything it actually records still goes unread. That is
not a hypothetical: `reaffirm_cleared` rides 1072 records of this ledger,
its only consumer is `_staling_bucket`'s `is not None` test, and the
`prior_anchor` and `touched` it carries -- the entire audit trail of what
an anchor advance buried -- have never been looked at by anything. A
sweep that counted the presence test as a reader would have reported this
field healthy, which is how it stayed invisible.

Deliberately NOT readers either:

    x["K"] = v           a Store subscript -- that is the WRITER
    {"K": v}             a dict literal -- also the writer
    x.setdefault("K",..) writes on the read path
    def K(...)           a function that happens to share the name
                         (`blast_forecast` is a function in kernel.py AND
                         a legacy payload key; a grep cannot tell them
                         apart, an AST can)

The AST is the point. `grep -l reaffirm_cleared truthlib/` finds cli.py
and reports the field consumed -- by the very code that wrote it. This
sweep would be worthless as a grep.

KNOWN LIMIT, stated rather than implied: a Load subscript on a LOCAL dict
that happens to use a payload key's name counts as a reader. It can only
over-credit common names (`text`, `basis`, `commit`, `reason`), all of
which have real readers anyway, and never under-credits -- so the error
direction is confined to keys that were never at risk. Nested keys
(`evidence.command`, `reaffirm_cleared.touched`) are NOT swept; the gating
set is top-level payload keys, and the contents of `reaffirm_cleared` are
F3.5's subject, not this sweep's.

--- OPT-OUT POLICY (.truth/field-consumer-opt-out) -----------------------
Fail-mode semantics copied from .truth/generated-paths and
.truth/reachability-opt-out, deliberately (SI-4):

  ABSENT          -- no policy on record. The sweep cannot tell a
                     deliberate exemption from an oversight, so it
                     excuses NOTHING and says so loudly.
  COMMITTED EMPTY -- a conscious "every field here must have a reader".
                     Armed and silent; empty is a statement, not an
                     omission.
  POPULATED       -- armed. One entry per line: `<key> -- <reason>`.

A STALE ENTRY IS A FAILURE, in both directions: an exempted key that has
since acquired a reader, and an exempted key the ledger no longer carries.
An opt-out list nobody prunes becomes a list nobody reads, and then the
sweep is measuring the list instead of the code.

ZERO KEYS EXAMINED IS A FAILURE, never a pass (ADR-042 rule 2). A sweep
that measured nothing has not proven anything clean.

Usage: python3 instruments/field-consumers.py [--json]
Gate:  scripts/test-instruments.sh
"""
import ast
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, ".truth/claims.jsonl")
OPT_OUT_REL = ".truth/field-consumer-opt-out"
SEARCH_ROOTS = ("template/truthlib", "instruments")


def payload_keys(path):
    """Every top-level payload key the ledger actually carries, with its
    record count. MECHANICAL, from the ledger -- never a hardcoded list,
    which is the one thing that would make this sweep lie the day a new
    field ships."""
    keys, records = {}, 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except ValueError:
                continue            # validate owns malformed lines
            records += 1
            for k in (ev.get("payload") or {}):
                keys[k] = keys.get(k, 0) + 1
    return keys, records


_TRUTHY_CONSTANTS = (None, True, False)


def _is_presence_context(node, parent):
    """Is this read's value discarded in favour of the mere fact that it
    is there? Judged from the IMMEDIATE parent only -- a deeper dataflow
    analysis would be more precise and far less auditable, and the
    shallow rule errs toward calling a read CONTENT (the safe direction:
    it under-reports presence-only fields rather than inventing them)."""
    if parent is None:
        return False
    if isinstance(parent, ast.UnaryOp) and isinstance(parent.op, ast.Not):
        return True
    if isinstance(parent, ast.Compare) and parent.left is node:
        return all(isinstance(c, ast.Constant) and c.value in _TRUTHY_CONSTANTS
                   for c in parent.comparators)
    if isinstance(parent, (ast.If, ast.While, ast.IfExp)) \
            and parent.test is node:
        return True
    if isinstance(parent, ast.BoolOp) and node in parent.values:
        # `a.get("K") or b` USES the value; only a boolean chain that is
        # itself a test discards it -- and that is decided one level up,
        # which this shallow rule cannot see. Treat as content.
        return False
    return False


def _reads_in(tree):
    """(content_keys, presence_keys) for one module. Writes never appear:
    a Store-context Subscript and a dict-literal key are not visited as
    reads at all."""
    content, presence = set(), set()
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            key = None
            if isinstance(child, ast.Subscript) \
                    and isinstance(child.ctx, ast.Load) \
                    and isinstance(child.slice, ast.Constant) \
                    and isinstance(child.slice.value, str):
                key = child.slice.value
            elif isinstance(child, ast.Call) \
                    and isinstance(child.func, ast.Attribute) \
                    and child.func.attr == "get" and child.args \
                    and isinstance(child.args[0], ast.Constant) \
                    and isinstance(child.args[0].value, str):
                key = child.args[0].value
            elif isinstance(child, ast.Compare) \
                    and isinstance(child.left, ast.Constant) \
                    and isinstance(child.left.value, str) \
                    and any(isinstance(op, ast.In) for op in child.ops):
                presence.add(child.left.value)
                continue
            if key is None:
                continue
            (presence if _is_presence_context(child, parent)
             else content).add(key)
    return content, presence


def readers(root, search_roots):
    """(content, presence): key -> sorted repo-relative files."""
    content, presence = {}, {}
    for rel in search_roots:
        base = os.path.join(root, rel)
        for dirpath, _dirs, files in os.walk(base):
            for name in sorted(files):
                if not name.endswith(".py"):
                    continue
                path = os.path.join(dirpath, name)
                try:
                    with open(path, encoding="utf-8") as f:
                        tree = ast.parse(f.read(), filename=path)
                except (OSError, SyntaxError):
                    continue
                c, p = _reads_in(tree)
                who = os.path.relpath(path, root)
                for k in c:
                    content.setdefault(k, set()).add(who)
                for k in p - c:
                    presence.setdefault(k, set()).add(who)
    return ({k: sorted(v) for k, v in content.items()},
            {k: sorted(v) for k, v in presence.items()})


def load_opt_out(root):
    """Returns (state, {key: reason}) with state in
    absent | empty | populated -- the SI-4 three-way, never a bare dict
    (an absent file and an empty one mean opposite things and a caller
    that cannot tell them apart will pick the wrong one)."""
    path = os.path.join(root, OPT_OUT_REL)
    if not os.path.exists(path):
        return "absent", {}
    entries = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, _, reason = line.partition("--")
            entries[key.strip()] = reason.strip()
    return ("populated" if entries else "empty"), entries


def sweep(keys, content, presence, opt_state, opt_entries):
    """Pure: the whole decision, given gathered facts. Returns a report."""
    rows, failures, warnings = [], [], []
    for key in sorted(keys):
        who = content.get(key, [])
        seen = presence.get(key, [])
        exempt = key in opt_entries
        if who:
            status = "read"
            if exempt:
                status = "stale-exemption"
                failures.append(
                    f"{key} is exempted in {OPT_OUT_REL} but its value IS "
                    f"read ({', '.join(who)}) -- prune the entry; an "
                    "opt-out list nobody prunes is a list nobody reads")
        elif exempt:
            status = "exempt"
        elif seen:
            status = "presence-only"
            failures.append(
                f"{key} rides {keys[key]} record(s) and the only code that "
                f"touches it ({', '.join(seen)}) just tests whether it is "
                "THERE -- its contents have never been read. Either read "
                "them, replace the field with a boolean, or record the "
                f"exemption in {OPT_OUT_REL} with a reason (ADR-046 "
                "admission rule)")
        else:
            status = "unread"
            failures.append(
                f"{key} rides {keys[key]} record(s) and NOTHING under "
                f"{'/, '.join(SEARCH_ROOTS)}/ reads it -- give it a reader "
                f"or record the exemption in {OPT_OUT_REL} with a reason "
                "(ADR-046 admission rule)")
        rows.append({"key": key, "records": keys[key], "status": status,
                     "readers": who, "presence_only": seen,
                     "exemption": opt_entries.get(key)})
    for key in sorted(opt_entries):
        if key not in keys:
            failures.append(
                f"{key} is exempted in {OPT_OUT_REL} but no record in this "
                "ledger carries it -- the exemption outlived its field")
    if opt_state == "absent":
        warnings.append(
            f"no {OPT_OUT_REL} on record -- this sweep cannot tell a "
            "deliberate exemption from an oversight, so it excused "
            "NOTHING. Commit the file (empty is a statement: every field "
            "must have a reader).")
    if not keys:
        failures.append(
            "the sweep examined ZERO payload keys -- it measured nothing, "
            "which is a failure, not a pass (ADR-042 rule 2). Check the "
            "ledger path.")
    return {"keys": rows, "opt_out_state": opt_state,
            "failures": failures, "warnings": warnings,
            "examined": len(rows)}


def main(argv):
    keys, records = payload_keys(LEDGER)
    content, presence = readers(ROOT, SEARCH_ROOTS)
    opt_state, opt_entries = load_opt_out(ROOT)
    r = sweep(keys, content, presence, opt_state, opt_entries)
    r["records"] = records
    if "--json" in argv:
        print(json.dumps(r, indent=2))
        return 1 if r["failures"] else 0
    for row in r["keys"]:
        mark = {"read": "OK   ", "exempt": "EXEMPT", "unread": "FAIL ",
                "presence-only": "FAIL ",
                "stale-exemption": "FAIL "}[row["status"]]
        tail = (", ".join(row["readers"]) if row["readers"]
                else row["exemption"]
                or (("presence test only: " + ", ".join(row["presence_only"]))
                    if row["presence_only"] else "no reader"))
        print(f"{mark} {row['key']:<24} {row['records']:>5}  {tail}")
    for w in r["warnings"]:
        print("WARN  " + w)
    for f in r["failures"]:
        print("FAIL  " + f)
    print(f"field-consumers: {r['examined']} payload key(s) over {records} "
          f"record(s) -- {len(r['failures'])} failure(s) "
          f"[{OPT_OUT_REL}: {opt_state}]")
    return 1 if r["failures"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
