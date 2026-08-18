#!/usr/bin/env python3
"""label-coupling -- which modules share decisions without sharing code?

META-REPO ONLY (ADR-003 rule 2, ADR-046 Tier C): it sweeps THIS
repository's truthlib against THIS repository's ADR vocabulary and is
never shipped to a consumer.

--- WHY THIS EXISTS ------------------------------------------------------
Two taxonomies describe the same modules and are maintained by different
hands. The IMPORT graph says which module depends on which -- pinned by
TestStructureDocMatchesDisk, which derives both sides at run time. The
DECISION vocabulary (ADR-nnn cited in comments and docstrings) says which
module implements which ruling, and is pinned by nothing.

When the two disagree in one direction -- an import edge with no shared
decision -- that is ordinary layering. The other direction is the
finding: two modules carrying the same rulings with NO import between
them are two implementations of one contract, and this repository has
already named what happens next, twice in its own prose:

    "a second screen implementation is forbidden -- the F1/F5 drift
     lesson"                                     (evidence.py:192)
    "a second matcher implementation is forbidden (two copies of the
     matching contract will drift, the F1/F5 lesson)"  (advisory.py:600)

Nothing detects the third occurrence. Import linters cannot: there is no
edge to inspect. `make health`'s field-consumers sweep cannot: it reads
payload keys, not rulings. The gap is real and was measured -- on
2026-08-18, `policy` and `reports` shared ten ADRs with no import between
them, a pair that did not exist before `reports.py` was extracted from
`advisory.py` days earlier. The defect class is BORN AT DECOMPOSITION,
which is exactly when nobody is looking for it.

--- THE RULE -------------------------------------------------------------
For each unordered pair of modules under truthlib/, compute the Jaccard
similarity of their ADR sets. A pair FAILS when

    jaccard >= THRESHOLD  and  neither module imports the other

unless the pair is recorded in .truth/label-coupling-opt-out with a
reason. The opt-out carries today's four pairs as a baseline: the point
of this sweep is not to relitigate them but to refuse the FIFTH.

Jaccard, not raw overlap: two modules citing forty rulings each share
several by arithmetic. The ratio asks whether their decision sets are the
SAME set, which is what "one contract, two implementations" looks like.

Only the ADR family is counted. Short labels (G12, H5, F2) name test arms
and incidents, not rulings -- a 2026-08-18 measurement read 165 ADR->arm
citation edges as a dependency inversion and 40 hand-read sites showed
they were incident citations, meaning nothing. Arms are arm-index.py's
subject, not this sweep's.

--- WHAT THIS DOES NOT SEE ----------------------------------------------
Comments, so a module implementing a ruling silently is invisible to it,
and a stale citation counts as live. This is a heuristic over prose and
is disclosed as one: it is why the exit code is a refusal to admit NEW
pairs, never an assertion that the existing ones are correct.

Stdlib only; no truthlib import -- like every Tier C instrument, it
exercises the surfaces any external reader has.

Exit: 0 clean · 1 an unrecorded pair · 8 examined nothing (ADR-042 rule
2: an instrument that measured nothing has not passed, it has failed to
run) · 2 usage.
"""
import ast
import os
import re
import sys
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PKG_REL = os.path.join("template", "truthlib")
OPT_OUT_REL = ".truth/label-coupling-opt-out"
THRESHOLD = 0.25

ADR_RE = re.compile(r"\bADR-(\d{1,4})\b")


def canon(match):
    """ADR-9 and ADR-009 are one ruling, so the trailing run is padded."""
    return "ADR-%03d" % int(match)


def modules(pkg_dir):
    return sorted(f[:-3] for f in os.listdir(pkg_dir)
                  if f.endswith(".py") and f != "__init__.py")


def adr_set(path):
    """Every ADR cited anywhere in the file -- comments, docstrings, strings.

    A plain text scan on purpose: the citation may sit in a section banner
    that `ast` discards, which is where this repository puts most of them.
    """
    with open(path, encoding="utf-8", errors="replace") as f:
        return {canon(m) for m in ADR_RE.findall(f.read())}


def imports(path, known):
    """Intra-package imports only, resolved to bare module names."""
    out = set()
    with open(path, encoding="utf-8", errors="replace") as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            return out
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            name = node.module.split(".")[-1]
            if name in known:
                out.add(name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name.split(".")[-1]
                if name in known:
                    out.add(name)
    return out


def load_opt_out(path):
    """`module~module  reason` per line; '#' comments and blanks ignored."""
    recorded, state = {}, "absent"
    if not os.path.exists(path):
        return recorded, state
    state = "empty"
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            state = "populated"
            pair, _, reason = line.partition(" ")
            if "~" not in pair:
                continue
            a, b = pair.split("~", 1)
            recorded[frozenset((a.strip(), b.strip()))] = reason.strip()
    return recorded, state


def sweep(pkg_dir, opt_out):
    names = modules(pkg_dir)
    adrs = {m: adr_set(os.path.join(pkg_dir, m + ".py")) for m in names}
    imps = {m: imports(os.path.join(pkg_dir, m + ".py"), set(names))
            for m in names}
    rows, failures, examined = [], [], 0
    for a, b in combinations(names, 2):
        examined += 1
        union = adrs[a] | adrs[b]
        if not union:
            continue
        shared = adrs[a] & adrs[b]
        jaccard = len(shared) / len(union)
        linked = b in imps[a] or a in imps[b]
        if jaccard < THRESHOLD or linked:
            continue
        key = frozenset((a, b))
        reason = opt_out.get(key)
        row = {"pair": "%s~%s" % (a, b), "jaccard": jaccard,
               "shared": sorted(shared), "reason": reason}
        rows.append(row)
        if reason is None:
            failures.append(
                "%s~%s shares %d ruling(s) (jaccard %.2f) with no import "
                "between them: %s -- one contract in two implementations, or "
                "record the pair in %s with a reason"
                % (a, b, len(shared), jaccard, ", ".join(sorted(shared)),
                   OPT_OUT_REL))
    return {"rows": rows, "failures": failures, "examined": examined,
            "modules": len(names)}


def main(argv):
    if argv and argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    pkg_dir = os.path.join(ROOT, PKG_REL)
    if not os.path.isdir(pkg_dir):
        print("label-coupling: %s not found -- run from the meta-repo"
              % PKG_REL, file=sys.stderr)
        return 2
    opt_out, opt_state = load_opt_out(os.path.join(ROOT, OPT_OUT_REL))
    r = sweep(pkg_dir, opt_out)

    if not r["examined"]:
        print("label-coupling: examined ZERO module pairs over %s -- the "
              "sweep did not run (ADR-042 rule 2)" % PKG_REL, file=sys.stderr)
        return 8

    for row in sorted(r["rows"], key=lambda x: -x["jaccard"]):
        mark = "OK   " if row["reason"] else "FAIL "
        tail = row["reason"] or ("no import; shared: "
                                 + ", ".join(row["shared"]))
        print("%s %-22s %.2f  %s" % (mark, row["pair"], row["jaccard"], tail))
    for f in r["failures"]:
        print("FAIL  " + f)
    print("label-coupling: %d module pair(s) over %d module(s) -- %d "
          "unrecorded coupling(s) [%s: %s]"
          % (r["examined"], r["modules"], len(r["failures"]),
             OPT_OUT_REL, opt_state))
    return 1 if r["failures"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
