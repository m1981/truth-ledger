#!/usr/bin/env python3
"""arm-index -- which arm guards what? (A6)

META-REPO ONLY (ADR-003 rule 2, ADR-046 Tier C): it sweeps THIS
repository's instruments and is never shipped to a consumer.

--- WHY THIS EXISTS ------------------------------------------------------
The machinery has three structural levels. Two are pinned mechanically and
one is not:

    modules   8      TestStructureDocMatchesDisk (both sides derived)  pinned
    checks   13      gate-reachability.sh (closure from roots)         pinned
    arms   ~830      nothing

"Which arms guard ADR-051?" is answerable only by grep. When an ADR moves,
nothing says which arms move with it; when an arm stops guarding what its
name claims, nothing notices. Three defects of exactly that shape landed
in one session (2026-08-13/14): three ADR-011 arms asserted a HEADLESS
refusal without redirecting stdin and passed on a typed-text mismatch; a
hand-transcribed atlas drifted from the canary it describes; and two
seeded mutations missed silently, each looking exactly like an arm that
held.

--- THE FOUR SPECIES, KEPT APART -----------------------------------------
"Arm" names four different things, and conflating them is half the
cognitive load this index exists to reduce:

  seeded-fault   canary: plant a defect, assert the gate catches it
  unit-test      core + v04: pure functions over plain data
  meta-arm       test-*.sh: test that the CHECKERS work
  probe          fingerprint: asserts NOTHING; the whole file is compared

A probe cannot "fail" in isolation, so it is never subject-checked; it is
counted and indexed so the reverse lookup is complete.

--- THE SUBJECT RULE, AND WHERE IT IS ENFORCED ---------------------------
A family declares its subject in its own header:

    say "FAULT DG (ADR-025): doctor decides the commit gate via CI ..."
    say "FAULT B  (INV-C):   commit touching evidence paths ..."

ENFORCED for the canary, where the convention exists and is 89% followed
(108 of 122 families at the time of writing). A family there without a
subject FAILS.

REPORTED, NOT ENFORCED, everywhere else -- and this is a declared limit,
not an oversight. The meta-suites use `CASE n` / `ARM n` headers and only
2 of 28 cite a subject; core unit tests name a function, not an ADR.
Failing ~70 arms for a convention that was never adopted would be a gate
refusing legitimate work, which teaches its own bypass (ADR-014's
confused-deputy lesson, the reason ADR-037's lints are warnings). Adopt
the convention there first, then move the species into ENFORCED.

--- WHAT THIS CANNOT DO --------------------------------------------------
It maps DECLARED subjects. It cannot verify that an arm does what its
header says -- a family headed `(ADR-051)` whose body exercises something
else is indexed under ADR-051 and this instrument will never know. That
stays red-proof, by hand, per arm. What changes is that you can see WHERE
to run it.

It also parses rather than executes, deliberately: an index that costs ten
minutes will not be run. The consequence is that static arm counts differ
from runtime ones -- the canary's if/else pairs mean 280 `ok` call sites
produce 283 exercised arms -- so both numbers are reported and neither is
silently preferred.

Exit: 0 clean, 1 subject-less families in an enforced species, 8 zero arms
examined (ADR-042 rule 2 -- an index that indexed nothing has not passed).

Usage: python3 instruments/arm-index.py [--json] [--subject ADR-051]
Gate:  NONE yet -- wire it once the enforced backlog is closed, or this
       file becomes the thing it was built to detect.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPT_OUT_REL = ".truth/arm-subject-opt-out"
EXIT_SUBJECTLESS = 1
EXIT_EMPTY = 8

# A subject is an ADR, an invariant, a G-number, a roadmap/TL item, or a
# tracked issue. Deliberately broad: the point is traceability to SOME
# named decision, not to one register.
SUBJECT_RE = re.compile(
    r"\b(ADR-\d+|INV-[A-Z]\b|G\d+\b|FS-\d+|TL-\d+|SI-\d+|R\d+\b|issue #\d+)")

SOURCES = (
    # (path, species, enforced)
    ("template/scripts/truth-canary.sh", "seeded-fault", True),
    ("scripts/test-release-battery.sh", "meta-arm", False),
    ("scripts/test-fact-health.sh", "meta-arm", False),
    ("scripts/test-session-digest.sh", "meta-arm", False),
    ("scripts/test-whisper-hook.sh", "meta-arm", False),
    ("scripts/test-instruments.sh", "meta-arm", False),
    ("template/scripts/test-truth-core.py", "unit-test", False),
    ("template/scripts/test-truth-v04.py", "unit-test", False),
    ("instruments/fingerprint.sh", "probe", False),
)

FAMILY_RE = re.compile(r'^\s*(?:say|echo)\s+"((?:FAULT|ARM|CASE|LANE)[^"]*)"')
ASSERT_RE = re.compile(r'(?:^|\s)(ok|miss|bad)\s+"')
PROBE_RE = re.compile(r'^probe\s+"([^"]+)"')
CLASS_RE = re.compile(r"^class\s+(Test\w+)")
TESTDEF_RE = re.compile(r"^\s+def\s+(test_\w+)")


# The convention AS PRACTISED, which is wider than one register: a family
# header declares its subject in the parenthesis right after its id.
# `FAULT DG (ADR-025)` names an ADR; `FAULT S1 (spec-health)` names the
# script it guards; `FAULT RP (F1.1)` names a plan item. All three are
# traceable, which is the whole point -- "what does this arm guard?" is
# answered by any of them. Insisting on ADR-nnn alone reported 15 families
# as subject-less when 13 of them plainly declare a subject, and a rule
# that calls a followed convention a violation gets switched off.
PAREN_TAG_RE = re.compile(r"^(?:FAULT|ARM|CASE|LANE)\s+\S+\s*\(([^)]+)\)")


def _subject(text):
    """Canonical register first, then the parenthesised tag as practised."""
    m = SUBJECT_RE.search(text or "")
    if m:
        return m.group(1)
    t = PAREN_TAG_RE.match((text or "").strip())
    return t.group(1).strip() if t else None


def scan_shell(path, species, rel):
    """Shell suites: a family is a say/echo header; arms are the ok/miss
    calls that follow it until the next header."""
    arms, family, fam_line = [], None, 0
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            m = FAMILY_RE.match(line)
            if m:
                family, fam_line = m.group(1), n
                continue
            if species == "probe":
                p = PROBE_RE.match(line)
                if p:
                    label = p.group(1)
                    arms.append({"instrument": rel, "species": species,
                                 "family": label.split(":")[0],
                                 "label": label, "line": n,
                                 "subject": _subject(label)})
                continue
            if ASSERT_RE.search(line):
                arms.append({"instrument": rel, "species": species,
                             "family": family or "(no family header)",
                             "label": line.strip()[:70], "line": n,
                             "family_line": fam_line,
                             "subject": _subject(family)})
    return arms


def scan_python(path, species, rel):
    """Unit suites: the class is the family, each test_* is an arm; the
    subject may be in the class name or its docstring."""
    import ast
    src = open(path, encoding="utf-8").read()
    arms = []
    for node in ast.parse(src).body:
        if not isinstance(node, ast.ClassDef):
            continue
        subj = _subject(node.name + " " + (ast.get_docstring(node) or ""))
        for sub in node.body:
            if isinstance(sub, ast.FunctionDef) and sub.name.startswith("test_"):
                arms.append({"instrument": rel, "species": species,
                             "family": node.name, "label": sub.name,
                             "line": sub.lineno, "family_line": node.lineno,
                             "subject": subj or _subject(sub.name)})
    return arms


def load_opt_out():
    """SI-4 + ADR-053: absent -> loud warning; committed-empty -> conscious
    and dated; populated -> `<family> -- <reason>` per line."""
    path = os.path.join(ROOT, OPT_OUT_REL)
    if not os.path.exists(path):
        return "absent", {}
    entries = {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        k, _, why = line.partition("--")
        entries[k.strip()] = why.strip()
    return ("populated" if entries else "empty"), entries


def build():
    arms = []
    for rel, species, enforced in SOURCES:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        got = (scan_python(path, species, rel) if path.endswith(".py")
               else scan_shell(path, species, rel))
        for a in got:
            a["enforced"] = enforced
        arms += got
    return arms


def main(argv):
    arms = build()
    opt_state, opt_entries = load_opt_out()

    families, failures, warnings = {}, [], []
    for a in arms:
        key = (a["instrument"], a["family"])
        fam = families.setdefault(key, {"instrument": a["instrument"],
                                        "family": a["family"],
                                        "species": a["species"],
                                        "enforced": a["enforced"],
                                        "subject": a["subject"], "arms": 0})
        fam["arms"] += 1
        if a["subject"] and not fam["subject"]:
            fam["subject"] = a["subject"]

    for fam in families.values():
        if fam["subject"] or fam["family"] in opt_entries:
            continue
        if fam["enforced"]:
            failures.append(
                f"{fam['instrument']}: family {fam['family']!r} "
                f"({fam['arms']} arm(s)) declares no subject -- name the "
                f"ADR/INV/G it guards in its header, or record the exemption "
                f"in {OPT_OUT_REL} with a reason")
        else:
            warnings.append(f"{fam['instrument']}: {fam['family']!r}")

    for key in opt_entries:
        if not any(f["family"] == key for f in families.values()):
            failures.append(
                f"{key} is exempted in {OPT_OUT_REL} but no family by that "
                "name exists -- the exemption outlived its arm")

    if not arms:
        print("arm-index: indexed ZERO arms -- an index that indexed nothing "
              "has not passed (ADR-042 rule 2). Check the SOURCES table.",
              file=sys.stderr)
        return EXIT_EMPTY
    if opt_state == "absent":
        warnings.insert(0, f"no {OPT_OUT_REL} on record -- this sweep cannot "
                        "tell a deliberate exemption from an oversight, so it "
                        "excused NOTHING")

    reverse = {}
    for a in arms:
        if a["subject"]:
            reverse.setdefault(a["subject"], []).append(
                f"{a['instrument']}:{a['line']} {a['family']}")

    by_species = {}
    for a in arms:
        by_species[a["species"]] = by_species.get(a["species"], 0) + 1

    if "--subject" in argv:
        want = argv[argv.index("--subject") + 1]
        for row in sorted(reverse.get(want, [])):
            print(f"  {row}")
        print(f"{want}: {len(reverse.get(want, []))} arm(s)")
        return 0

    report = {"arms": len(arms), "families": len(families),
              "by_species": by_species,
              "subjects": len(reverse),
              "opt_out_state": opt_state,
              "failures": failures, "warnings": warnings,
              "reverse_index": {k: sorted(v) for k, v in sorted(reverse.items())},
              "family_rows": sorted(families.values(),
                                    key=lambda f: (f["instrument"], f["family"]))}
    if "--json" in argv:
        print(json.dumps(report, indent=2))
        return EXIT_SUBJECTLESS if failures else 0

    for sp, n in sorted(by_species.items()):
        print(f"  {sp:14} {n:5} arm(s)")
    print(f"  {'subjects':14} {len(reverse):5} distinct, "
          f"{len(families)} families")
    for w in warnings[:8]:
        print("WARN  " + w)
    if len(warnings) > 8:
        print(f"WARN  ... and {len(warnings) - 8} more family/families with "
              "no declared subject in a REPORTED (non-enforced) species")
    for f in failures:
        print("FAIL  " + f)
    print(f"arm-index: {len(arms)} arm(s) in {len(families)} families over "
          f"{len(SOURCES)} instruments -- {len(failures)} failure(s) "
          f"[{OPT_OUT_REL}: {opt_state}]")
    return EXIT_SUBJECTLESS if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
