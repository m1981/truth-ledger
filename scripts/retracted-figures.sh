#!/usr/bin/env bash
# retracted-figures.sh -- has a WITHDRAWN number outlived its retraction?
#
# The complement of fact-health.sh, which sweeps *.md for ledger IDs. This
# sweeps CODE AND POLICY for figures listed in .truth/retracted-figures, and
# fails on any occurrence that does not carry its replacement within 8 lines.
# See that file's header for the measurement that motivated it.
#
# META-REPO ONLY (untemplated): the figures are this project's own.
set -uo pipefail
cd "$(dirname "$0")/.."
PY="$(if [ -x .venv/bin/python3 ]; then echo .venv/bin/python3; else echo python3; fi)"
exec "$PY" - <<'PYEOF'
import os, re, subprocess, sys

POLICY = ".truth/retracted-figures"
WINDOW = 8

if not os.path.exists(POLICY):
    print(f"retracted-figures: no {POLICY} -- nothing to sweep")
    sys.exit(0)

entries = []
for n, raw in enumerate(open(POLICY, encoding="utf-8"), 1):
    s = raw.strip()
    if not s or s.startswith("#"):
        continue
    parts = [p.strip() for p in s.split(" -- ")]
    if len(parts) < 2 or not parts[0] or not parts[1]:
        sys.exit(f"retracted-figures: {POLICY} line {n} is not "
                 "'<retracted> -- <replacement> -- <where>': " + repr(s))
    entries.append((parts[0], parts[1], parts[2] if len(parts) > 2 else "?"))

if not entries:
    print("retracted-figures: 0 figure(s) listed -- nothing to sweep")
    sys.exit(0)

tracked = subprocess.run(["git", "ls-files", "template", "scripts",
                          "instruments", ".truth"],
                         capture_output=True, text=True).stdout.split()
files = [f for f in tracked
         if f != ".truth/claims.jsonl" and f != POLICY
         and not f.endswith((".png", ".jpg", ".pyc"))]

failures = 0
checked = 0
for retracted, replacement, where in entries:
    rx = re.compile(r"\b" + re.escape(retracted) + r"\b")
    rep = re.compile(r"\b" + re.escape(replacement) + r"\b")
    for path in files:
        try:
            lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines):
            if not rx.search(line):
                continue
            checked += 1
            lo, hi = max(0, i - WINDOW), min(len(lines), i + WINDOW + 1)
            if any(rep.search(l) for l in lines[lo:hi]):
                continue
            failures += 1
            print(f"  FAIL  {path}:{i+1}  quotes retracted {retracted!r} with "
                  f"no {replacement!r} within {WINDOW} lines")
            print(f"        retracted in {where}; either cite the correction "
                  f"beside it or replace it with {replacement!r}")

print(f"retracted-figures: {len(entries)} figure(s), {checked} occurrence(s) "
      f"in code/policy -- {failures} failure(s)")
sys.exit(1 if failures else 0)
PYEOF
