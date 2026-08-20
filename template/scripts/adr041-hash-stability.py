#!/usr/bin/env python3
"""adr041-hash-stability.py -- the ADR-041 migration check.

Before ADR-041 an evidence command was executed by handing the string to
/bin/sh; since ADR-041 the screen's own parse is executed as argv arrays
with shell=False.  Every claim already in a ledger carries an output_hash
produced by the OLD executor, so a divergence between the two is not a
test failure in the abstract -- it silently diverges live claims on the
next recheck.

This runs every distinct evidence command in a ledger BOTH ways and
reports any command whose (output_hash, returncode) pair moves, plus any
command the new parser refuses.  Run it once, in the repository root,
before adopting a truth CLI that carries ADR-041:

    python3 scripts/adr041-hash-stability.py .truth/claims.jsonl

Exit 0 when every command is identical and none is refused; 1 otherwise.
It EXECUTES the commands (twice each) -- that is the whole point -- so run
it where running your own evidence is safe, which is the same condition
`truth verdict --recheck` already imposes.
"""
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

from truthlib.evidence import parse_evidence_command   # noqa: E402
from truthlib.shellio import run_evidence              # noqa: E402


def commands(paths):
    """Every distinct evidence/capsule command in the given ledgers."""
    out = set()
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                payload = (json.loads(line).get("payload") or {})
                for key in ("evidence", "capsule", "evidence_capsule"):
                    cap = payload.get(key)
                    if isinstance(cap, dict) and cap.get("command"):
                        out.add(cap["command"])
    return sorted(out)


def through_the_shell(cmd):
    """What run_evidence did before ADR-041, verbatim."""
    r = subprocess.run(cmd, shell=True, capture_output=True)
    return hashlib.sha256(r.stdout).hexdigest(), r.returncode


def main():
    paths = sys.argv[1:] or [".truth/claims.jsonl"]
    same = diverged = refused = 0
    for cmd in commands(paths):
        plan, err = parse_evidence_command(cmd)
        if err:
            refused += 1
            print(f"REFUSED  {cmd}\n         {err}")
            continue
        old, new = through_the_shell(cmd), run_evidence(plan)
        if old == new:
            same += 1
        else:
            diverged += 1
            print(f"DIVERGED {cmd}\n         shell={old} runner={new}")
    print(f"\ncommands={same + diverged + refused} identical={same} "
          f"diverged={diverged} refused={refused}")
    return 1 if (diverged or refused) else 0


if __name__ == "__main__":
    sys.exit(main())
