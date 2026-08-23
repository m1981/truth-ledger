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

# WINDOW IS IN CHARACTERS, NOT LINES, because matching is over
# whitespace-normalised text (see normalise below) where lines no longer
# exist. 600 chars is the old 8-line window at this repo's ~75-column
# prose -- same reach, expressed in the unit the matcher actually has.
WINDOW = 600

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

# A comment marker opening a continuation line, in the languages this
# repository actually sweeps: shell/python `#`, C/JS `//` and ` *`, SQL/Lua
# `--`. Kept deliberately short -- a marker earns its place when a wrapped
# phrase has actually hidden behind it here.
_LEADING_MARKER_RE = re.compile(r"(?m)^[ \t]*(?:#+|//+|\*|--)[ \t]?")


def normalise(text):
    """Collapse every whitespace run to one space, and return the mapping
    back to source line numbers so a hit can still be reported at a line.

    THIS IS THE WHOLE FIX. The first version of this sweep matched
    line-by-line, so a multi-token retracted literal broken across a line
    boundary was invisible to the tool built to catch stale figures --
    fail-open, in the safe-looking direction, exactly like a `grep` for a
    prose phrase wrapped at 76 columns. Two such misses were measured in
    one week elsewhere in this repo (AGENTS.md's "six arms"; a correction
    check that read 0 for a phrase that was present). Harmless here only
    because both entries then in .truth/retracted-figures were single
    tokens -- while that file's own header advised making a noisy literal
    LONGER, walking the reader straight into the gap."""
    # STRIP THE CONTINUATION MARKER FIRST, or the fix is half a fix.
    # Whitespace-normalising alone handles prose wrapped in Markdown, but
    # the commonest case here is prose wrapped inside a COMMENT BLOCK:
    #     # the battery has six
    #     # arms, historically
    # which normalises to "six # arms" and still does not match. Found by
    # testing the fix instead of assuming it -- the planted case was the
    # one the first version still missed. Only a marker at the START of a
    # line is removed, so inline text is never merged.
    text = _LEADING_MARKER_RE.sub("", text)
    out, line_of, line, prev_ws = [], [], 1, False
    for ch in text:
        if ch.isspace():
            if not prev_ws:
                out.append(" ")
                line_of.append(line)
            prev_ws = True
        else:
            out.append(ch)
            line_of.append(line)
            prev_ws = False
        if ch == "\n":
            line += 1
    return "".join(out), line_of


failures = 0
checked = 0
for retracted, replacement, where in entries:
    rx = re.compile(r"\b" + re.escape(retracted) + r"\b")
    rep = re.compile(r"\b" + re.escape(replacement) + r"\b")
    for path in files:
        try:
            raw = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        norm, line_of = normalise(raw)
        for m in rx.finditer(norm):
            checked += 1
            lo = max(0, m.start() - WINDOW)
            hi = min(len(norm), m.end() + WINDOW)
            if rep.search(norm[lo:hi]):
                continue
            failures += 1
            line = line_of[m.start()] if m.start() < len(line_of) else 0
            print(f"  FAIL  {path}:{line}  quotes retracted {retracted!r} with "
                  f"no {replacement!r} within {WINDOW} characters")
            print(f"        retracted in {where}; either cite the correction "
                  f"beside it or replace it with {replacement!r}")

print(f"retracted-figures: {len(entries)} figure(s), {checked} occurrence(s) "
      f"in code/policy -- {failures} failure(s)")
sys.exit(1 if failures else 0)
PYEOF
