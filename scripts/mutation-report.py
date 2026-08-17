#!/usr/bin/env python3
"""mutation-report.py -- scores and survivors from .mutmut-cache.

`mutmut results` prints survivor IDs and nothing else: no killed count, no
score, no source line. This reads the same sqlite cache mutmut writes and
reports what a mutation run is actually for -- per file:

    killed / survived / timeout / suspicious, score, and every survivor with
    its line number and source text, so a survivor is a finding you can read
    rather than an id you have to `mutmut show` one at a time.

Score counts timeouts as killed (the mutant did change behaviour; the suite
just could not finish deciding how), and excludes skipped/untested mutants
from the denominator.

Run: python3 scripts/mutation-report.py [file-substring ...]
Stdlib only, like everything else here.
"""
import os
import sqlite3
import sys

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                     ".mutmut-cache")
KILLED = ("ok_killed", "bad_timeout")
COUNTED = KILLED + ("bad_survived", "bad_suspicious")


def rows(con, wanted):
    q = """SELECT sf.filename, l.line_number, l.line, m.status, m.id
             FROM Mutant m
             JOIN Line l ON m.line = l.id
             JOIN SourceFile sf ON l.sourcefile = sf.id"""
    for fn, lineno, text, status, mid in con.execute(q):
        if wanted and not any(w in fn for w in wanted):
            continue
        yield fn, lineno, text, status, mid


def main(argv):
    if not os.path.exists(CACHE):
        sys.exit("no .mutmut-cache -- run ./scripts/mutate.sh first")
    con = sqlite3.connect(CACHE)
    by_file = {}
    for fn, lineno, text, status, mid in rows(con, argv):
        f = by_file.setdefault(fn, {"counts": {}, "survivors": []})
        f["counts"][status] = f["counts"].get(status, 0) + 1
        if status == "bad_survived":
            f["survivors"].append((mid, lineno, (text or "").strip()))

    if not by_file:
        sys.exit("no mutants matched")

    for fn in sorted(by_file):
        c = by_file[fn]["counts"]
        killed = sum(c.get(s, 0) for s in KILLED)
        total = sum(c.get(s, 0) for s in COUNTED)
        score = (100.0 * killed / total) if total else 0.0
        print("=" * 72)
        print(f"{fn}")
        print(f"  killed {c.get('ok_killed', 0)}  "
              f"survived {c.get('bad_survived', 0)}  "
              f"timeout {c.get('bad_timeout', 0)} (counted as killed)  "
              f"suspicious {c.get('bad_suspicious', 0)}  "
              f"skipped {c.get('skipped', 0)}")
        print(f"  MUTATION SCORE: {score:.1f}%  ({killed}/{total})")
        survivors = sorted(by_file[fn]["survivors"], key=lambda r: r[1])
        if survivors:
            print(f"  --- {len(survivors)} survivors ---")
            for mid, lineno, text in survivors:
                print(f"  #{mid:<5} L{lineno:<5} {text[:96]}")


if __name__ == "__main__":
    main(sys.argv[1:])
