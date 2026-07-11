#!/usr/bin/env python3
"""Session-start ledger digest (FS-4, consumer-side half). META-REPO
ONLY -- deliberately not shipped by the template: harness wiring is
consumer policy (ADR-003 rule 2), same placement as the whisper hook.

ADR-005's whisper fires at EDIT intent; a session that only reads,
answers, or plans -- and asserts repository facts while doing so -- can
still live and die without discovering the ledger. This hook closes the
remaining discovery hole at session BIRTH.

SessionStart hook: stdout is injected into the agent's context.
Fatigue budget, designed in (the ADR-005 lesson, applied at birth):
once per session by construction (SessionStart fires once), P0/P1
claims only, hard cap on lines, and an empty ledger or empty queue
contributes nothing -- silence stays the default. Advisory machinery
fails OPEN, visibly: any error is one stderr line and an empty digest,
never a blocked session (the F1 lesson: visible, not silent)."""
import json
import os
import subprocess
import sys

MAX_CLAIMS = 5
MAX_LINES = 15


def run(args, cwd):
    return subprocess.run(args, capture_output=True, text=True, cwd=cwd,
                          timeout=15)


try:
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True)
    root = r.stdout.strip()
    if r.returncode != 0 or not root:
        sys.exit(0)
    cli = os.path.join(root, "scripts", "truth")
    if not os.path.exists(cli):
        cli = os.path.join(root, "template", "scripts", "truth")
    if not os.path.exists(cli):
        sys.exit(0)

    lines = []
    q = run(["python3", cli, "queue", "--json"], root)
    queue = json.loads(q.stdout) if q.returncode == 0 and q.stdout else []
    for row in queue[:MAX_CLAIMS]:
        lines.append(f"  ATTENTION {row['id']} ({row['tier']}, "
                     f"{row['status']}): {row['reason']}")

    l = run(["python3", cli, "list", "--live", "--json"], root)
    live = json.loads(l.stdout) if l.returncode == 0 and l.stdout else []
    top = [r_ for r_ in live if r_.get("tier") in ("P0", "P1")][:MAX_CLAIMS]
    for row in top:
        lines.append(f"  LIVE {row['id']} ({row['tier']}): {row['text']}")

    if not lines:
        sys.exit(0)  # silence is the default; nothing to say, say nothing
    digest = ["truth-ledger digest (mechanical; verify before relying):"]
    digest += lines[:MAX_LINES - 2]
    digest.append("  check facts: scripts/truth list --live | file what you "
                  "verify (AGENTS.md)")
    print("\n".join(digest))
except Exception as e:  # advisory: fail open, visibly
    print(f"truth session digest unavailable: {e}", file=sys.stderr)
    sys.exit(0)
