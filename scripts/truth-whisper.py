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
fatigue).

Aggregation (operator ruling 2026-08-28, ruling 3 in
docs/governance/operator-actions-2026-08-28.md): only P0 hits keep
their full WATCHED BY line; P1/P2 hits collapse into one line with
per-tier counts and a pointer to `truth impact <path>`. Basis: J-040's
recount measured 22.6 claims named per edit -- a whisper at that volume
is tuned out, not read, which is the fatigue half of the ADR-005
adoption gate. A line whose tier the regex cannot parse passes through
VERBATIM: an unrecognized form must degrade to noise, never to silence
(the RULING-8 fail-open class)."""
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
root = os.path.realpath(r.stdout.strip()) if r.stdout.strip() else ""
if r.returncode != 0 or not root:
    sys.exit(0)
# realpath BOTH sides: git returns a symlink-resolved root, so a symlinked
# path component (macOS /var->/private/var, symlinked homes, /tmp) must not
# make an in-repo file look external -- that would bail before the deny
# stage below, and deny must fail CLOSED, not silently allow.
rel = os.path.relpath(os.path.realpath(fp), root)
if rel.startswith(".."):
    sys.exit(0)

# ---- deny stage: fails closed on listed patterns -----------------------
deny_file = os.path.join(root, "scripts", "truth-whisper.deny")
if os.path.exists(deny_file):
    with open(deny_file, encoding="utf-8") as f:
        for n, pat in enumerate(f, 1):
            pat = pat.strip()
            if not pat or pat.startswith("#"):
                continue
            try:
                hit = re.match(pat, rel)
            except re.error:
                # One typo'd line must not disarm the WHOLE deny list via
                # a traceback the harness reads as allow (R9): this stage
                # fails CLOSED, so a pattern that cannot compile denies.
                # The reason names the defect, never a way around it.
                emit("deny", permissionDecisionReason=(
                    f"malformed deny pattern line {n} -- failing closed; "
                    "fix scripts/truth-whisper.deny. The deny list could "
                    "not be evaluated, so edits it may cover are blocked "
                    "until the pattern is repaired."))
            if hit:
                emit("deny", permissionDecisionReason=(
                    f"{rel} is deny-listed ({pat}): frozen, or "
                    "append-only through the truth CLI, by policy (see "
                    "AGENTS.md). A human must deliberately lift the freeze "
                    "before an edit here can land -- that is not a step "
                    "for you to take. Record status changes as new ledger "
                    "entries via `truth`, never by editing files."))

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
    # Resolve the cache path via git, not os.path.join(root, ".git", ...):
    # in a worktree root/.git is a FILE, so that hardcoded join names a
    # path under a non-directory and the append below would raise. Deny
    # stage aside, this is the whisper stage -- it must fail OPEN (ADR-005),
    # so the append is also wrapped: a cache failure degrades to
    # whisper-fires-without-dedup, never to a crash that eats the advisory.
    gp = subprocess.run(["git", "rev-parse", "--git-path",
                         "truth-whisper.seen"],
                        capture_output=True, text=True, cwd=root)
    cache = (os.path.join(root, gp.stdout.strip()) if gp.returncode == 0
             and gp.stdout.strip()
             else os.path.join(root, ".git", "truth-whisper.seen"))
    try:
        with open(cache, encoding="utf-8") as f:
            seen = set(f.read().split())
    except OSError:
        seen = set()
    if key in seen:
        sys.exit(0)  # fatigue budget: already whispered this state
    try:
        with open(cache, "a", encoding="utf-8") as f:
            f.write(key + "\n")
    except OSError:
        pass  # fail open: whisper still fires, just undeduped this time
    # Aggregate below P0 (ruling 3, 2026-08-28): full lines fatigue at
    # 22.6 claims/edit (J-040). Unparseable lines pass through verbatim.
    kept, counts = [], {"P1": 0, "P2": 0}
    for line in r.stdout.strip().splitlines():
        m = re.search(r"\((P[0-2]), ", line)
        if m and m.group(1) in counts:
            counts[m.group(1)] += 1
        else:
            kept.append(line)
    if counts["P1"] or counts["P2"]:
        kept.append(
            f"editing {rel} -> also watched by {counts['P1']} P1 and "
            f"{counts['P2']} P2 claim(s), aggregated per operator ruling "
            f"2026-08-28 -- full view: scripts/truth impact {rel}")
    emit("allow", additionalContext=(
        "truth-ledger whisper (mechanical prediction, not judgment):\n"
        + "\n".join(kept)))
elif r.returncode not in (0, 3):
    print(f"truth impact unavailable (exit {r.returncode}): "
          f"{r.stderr.strip()[:200]}", file=sys.stderr)
sys.exit(0)
