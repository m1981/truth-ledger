# Truth Ledger — Operations Guide: Triggers, Observability, and Automation

> Reader: any developer operating a truth ledger day-to-day | Enables: knowing every point where the ledger executes, spotting it firing, and automating everything except the three judgments that must stay human | Update-trigger: CLI trigger surface or hook wiring changes (current: v0.4)

## 1. The trigger map — every point where the ledger executes

There are exactly seven entry points. Four are human/agent-initiated, three can be fully mechanical.

| Trigger | What runs | Initiated by | Automatable? |
|---|---|---|---|
| Filing a fact | `truth claim` (intake gates + append) | Agent or human, mid-task | Already agent-driven via the AGENTS.md snippet |
| Trusting a fact | `truth list --live` | Agent, *before* relying on anything | Agent-driven via snippet |
| **Every commit touching the ledger** | `check-truth.sh` via pre-commit hook (INV-A prefix check + schema validation) | **git, automatically** | ✅ Fully |
| **Every merge/pull** | `invalidate-scan` via post-merge hook (paths, TTL, lost anchors) | **git, automatically** | ✅ Fully |
| Verification | `dispatch` → fresh session → `verdict --recheck` → judgment | Human routes the context today | ⚠️ Partially (see §3, rung 3) |
| Triage | `truth queue` | Human, daily | ✅ The *surfacing*; not the deciding |
| Health | `doctor` + canary | Human, weekly | ✅ Fully (CI cron) |

The two bolded rows are the system's heartbeat — they make knowledge decay *mechanical* instead of vigilance-dependent. If those two hooks are not firing, you do not have a truth ledger; you have a diary.

## 2. Spotting when it is triggered

The ledger is deliberately quiet, so learn its signatures.

**The pre-commit gate** announces itself on stderr during any commit that stages the ledger: `validate: N record(s) OK` scrolling by during `git commit` *is* the gate passing. A blocked commit prints `check-truth: INV-A violation` or `INV-B violation` and the commit dies.

**The post-merge scan** prints `stale: tr-xxxx (paths changed)` lines unless run with `--quiet`. Tuning tip: consider removing `--quiet` from the hook — a fact silently dying on merge is exactly the event a human should glimpse.

**Agent-side triggers** are visible in transcripts: watch for `scripts/truth list --live` early in a session (discovery working) and `truth claim` after verification work (filing discipline working). Their *absence* in transcripts is the leading indicator that a runtime is not loading the snippet — the silent-death failure mode.

**Forensics**: the ledger *is* the log. Every record carries `actor`, `session`, and `ts`, so `git log -p .truth/claims.jsonl` gives a complete, tamper-evident audit trail of who triggered what, when — including which invalidations fired on which merge commits.

## 3. Eliminating the human — the automation ladder

Work through these in order; each rung removes one manual step.

**Rung 1 — hooks that survive clones.** Local `.git/hooks` die on every clone, so shims-in-hooks protects one machine. Promote to a committed hooks dir: move the two shims into `.githooks/`, commit them, and have the bootstrap run `git config core.hooksPath .githooks`. One config line per clone instead of per-hook copying — and the hooks themselves now update through normal file diffs.

**Rung 2 — CI as the enforcement backstop.** Hooks are bypassable (`--no-verify`) and clone-fragile; CI is neither. Three jobs:

1. On every PR touching `.truth/`, run `check-truth.sh` (needs enough fetch depth that HEAD's version of the ledger exists for the prefix check).
2. On every merge to main, run `invalidate-scan` and — the key move — **auto-commit any resulting invalidation records back** with a bot identity (`TRUTH_ACTOR=ci-scanner`). That closes the loop with zero humans: teammate merges, scan fires, stale facts are demoted, and the demotions are themselves ledger history.
3. A weekly cron running the canary plus `pip install jsonschema && python3 scripts/test-truth-core.py` — the armed drift detector — failing the pipeline loudly.

**Rung 3 — automate the verification dispatch.** Today a human runs `dispatch` and pastes into a fresh session. Mechanize the routing: a scheduled job picks unverified P0/P1 claims (or queue items), feeds `dispatch` output to a fresh agent session via API — the isolation requirement (G11) is *easier* to guarantee programmatically than by human copy-paste discipline, since the script provably sends nothing but the fixed prompt and the record — and lets the verifier's `verdict --recheck` + judgment land as appends. The human courier is replaced while the fresh-context property is kept.

**Rung 4 — automate the queue's surfacing, not its verdicts.** Pipe `truth queue` into whatever the humans already look at (Slack, PR comments, dashboard), with the age numbers. `doctor` already warns past 14 days; wire that warning to a channel.

## 4. The three humans you cannot eliminate — and should not try

Over-automating a trust system quietly destroys it.

**Retraction** is enforced-human by design (`TRUTH_HUMAN=1`): the one irreversible act. v0.4 made "humans only" a property precisely so no automation pathway can tombstone a claim. Never set that variable in any script — a bot with `TRUTH_HUMAN=1` is the enforcement deleted.

**Divergence triage**: automation can *detect* that verifier and author disagree; deciding who is right is a judgment about reality, and auto-resolving it (e.g., "recheck agrees, so overwrite the diverge") would just re-encode the author's priors.

**The monthly hand-audit** against the day-0 baseline is irreducible for a deeper reason: it is the only check on whether the whole machine *helps*. Every automated signal (green canaries, empty queues) measures the mechanism, and a mechanism can run perfectly while agents have simply learned to file plausible claims that pass recheck. Only a human comparing claims to ground truth catches that.

## Summary

Automate every *trigger* and every *courier*; never automate a *judgment*. The end state is a system where humans are consulted exactly three times — to kill a fact, to resolve a disagreement, and to periodically ask whether the green lights mean anything — and everything else fires off git events and cron without anyone remembering to care. Which is the point: vigilance does not scale; hooks do.
