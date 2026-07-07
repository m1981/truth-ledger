# .truth — append-only claims ledger (v0.4)

> Reader: any agent or human about to assert, trust, or re-verify a fact about this repository | Enables: filing a claim in one command, and knowing which claims are still live before acting on them | Update-trigger: the record schema, invariants, or CLI contract change

A plain-JSONL truth layer that lives beside a work tracker (e.g. Beads;
optional — the ledger works standalone, see docs/adr/001). Work records
answer *what to do*; this ledger answers *what is known and how*.

v0.4 hardens the fold for confluence (order-independent under
`merge=union`), enforces human-only retraction, makes re-verification
durable, fixes glob path-matching to respect `/`, and closes a
duplicate-claim-id resurrection path. See docs/adr/001 for the
readiness-join semantics.

## Layout

    .truth/claims.jsonl                the ledger (append-only, event-sourced)
    .truth/schema/claims.schema.json   the formal contract (survives fires)
    scripts/truth                      the CLI: pure core over imperative shell
    scripts/test-truth-core.py         unit + schema-conformance tests (ms)
    scripts/test-truth-v04.py          v0.4 regression tests (confluence, anchors, globs)
    scripts/check-truth.sh             pre-commit/CI gate: strict append-only + schema
    scripts/truth-canary.sh            19 seeded faults (run weekly)
    prompts/truth-verifier.md          fixed verifier prompt (use `truth dispatch`)
    docs/adr/001-*.md                  premise-validity decision

## Install (day 1)

1. `.gitattributes` already sets `.truth/claims.jsonl merge=union`.
2. Hooks are wired in `.git/hooks/` after `git init`/`git clone` — see
   `scripts/install-hooks.sh`, or use CI instead (one of the two MUST exist).
3. `AGENTS.md` already carries the discovery snippet — copy it into
   `CLAUDE.md`, `.cursorrules`, `copilot-instructions.md`, etc. too.
4. `pip install jsonschema` — required so the drift detector runs armed.
5. `scripts/truth doctor` — installation must pass.
6. `bash scripts/truth-canary.sh` — nineteen faults, all CAUGHT, or stop.

## Daily operation

Daily (~2 min): `scripts/truth queue` — empty means carry on.
Weekly (~30 s): `scripts/truth-canary.sh`.
After repo surgery (rebase spree, hook changes, new agent runtime):
`scripts/truth doctor`.
Monthly: re-audit a few fresh sessions' claims by hand against your day-0
baseline — if false-VERIFIED rates haven't moved, the green checkmarks
mean nothing.

## Seeding

Do not bulk-backfill claims. Let them accrete as agents do real work.
At install time, seed only a handful (3-5) of P0 load-bearing facts,
file them properly with real evidence, and dispatch each to a fresh
verifier session so they start `live`. Record a day-0 hand-audit baseline
of recent agent sessions' factual accuracy to compare against later.
