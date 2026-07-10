#!/usr/bin/env python3
"""Pre-edit whisper hook (ADR-005, consumer-side half). META-REPO ONLY —
deliberately not shipped by the template: harness wiring and deny-list
policy are consumer policy (ADR-003 rule 2; ADR-005 Decision part 2).

PreToolUse hook for Edit/Write tools. Two stages, opposite failure
policies (ADR-005):
  deny stage, fails CLOSED  — paths matching scripts/truth-whisper.deny
                              block with the reason (frozen archive, the
                              append-only ledger).
  whisper stage, fails OPEN — visibly: runs `truth impact`; exit 3
                              injects the prediction as context; any
                              error prints one stderr line and allows
                              the edit. Advisory machinery never blocks
                              work, but may not fail silently (the F1
                              lesson).
Fatigue budget: first-touch-per-session dedup keyed on
(session, file, ledger hash), re-whispering only when the ledger has
changed since (ADR-005 "fatigue budget, designed in"). The cache file
doubles as the trial's whisper counter (adoption gate: signal without
fatigue)."""
import hashlib
import json
import os
import re
import subprocess
import sys


def emit(decision, **fields):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision, **fields}}))
    sys.exit(0)


try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
fp = (data.get("tool_input") or {}).get("file_path") or ""
if not fp:
    sys.exit(0)

r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                   capture_output=True, text=True)
root = r.stdout.strip()
if r.returncode != 0 or not root:
    sys.exit(0)
rel = os.path.relpath(os.path.abspath(fp), root)
if rel.startswith(".."):
    sys.exit(0)

# ---- deny stage: fails closed on listed patterns -----------------------
deny_file = os.path.join(root, "scripts", "truth-whisper.deny")
if os.path.exists(deny_file):
    with open(deny_file, encoding="utf-8") as f:
        for pat in f:
            pat = pat.strip()
            if not pat or pat.startswith("#"):
                continue
            if re.match(pat, rel):
                emit("deny", permissionDecisionReason=(
                    f"{rel} is deny-listed ({pat}): frozen or "
                    "append-only-by-CLI. See AGENTS.md; amend flow: "
                    "status changes are new ledger records, archive "
                    "edits need the deny list changed first."))

# ---- whisper stage: fails open, visibly --------------------------------
try:
    r = subprocess.run(
        ["python3", os.path.join(root, "scripts", "truth"), "impact", rel],
        capture_output=True, text=True, cwd=root, timeout=15)
except Exception as e:
    print(f"truth impact unavailable: {e}", file=sys.stderr)
    sys.exit(0)

if r.returncode == 3 and r.stdout.strip():
    sid = data.get("session_id", "nosession")
    try:
        with open(os.path.join(root, ".truth", "claims.jsonl"), "rb") as f:
            lh = hashlib.sha256(f.read()).hexdigest()[:12]
    except OSError:
        lh = "noledger"
    key = f"{sid}:{rel}:{lh}"
    cache = os.path.join(root, ".git", "truth-whisper.seen")
    try:
        with open(cache, encoding="utf-8") as f:
            seen = set(f.read().split())
    except OSError:
        seen = set()
    if key in seen:
        sys.exit(0)  # fatigue budget: already whispered this state
    with open(cache, "a", encoding="utf-8") as f:
        f.write(key + "\n")
    emit("allow", additionalContext=(
        "truth-ledger whisper (mechanical prediction, not judgment):\n"
        + r.stdout.strip()))
elif r.returncode not in (0, 3):
    print(f"truth impact unavailable (exit {r.returncode}): "
          f"{r.stderr.strip()[:200]}", file=sys.stderr)
sys.exit(0)
