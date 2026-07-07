# truth-ledger

**Git tracks what changed. The truth ledger tracks what you still believe — and lets the changes kill the beliefs.**

An append-only claims ledger for repositories where AI agents (and humans) assert facts. Every fact gets provenance, an evidence recipe, and a tripwire; commits that touch the evidence mechanically demote the fact to `stale` before anyone trusts it again. No database, no daemon, no dependencies beyond Python 3 and git.

---

## Init a new repo — one command

```bash
git init my-project && uvx copier copy --trust gh:m1981/truth-ledger my-project
```

No `uv`? Any of these work identically:

```bash
pipx run copier copy --trust gh:m1981/truth-ledger my-project     # pipx
pip install copier && copier copy --trust gh:m1981/truth-ledger my-project
```

## Add to an existing repo — same command, dot target

```bash
uvx copier copy --trust gh:m1981/truth-ledger .
```

Safe on existing projects by contract (each clause is tested, see below):
your `AGENTS.md` is never clobbered, your `.gitattributes` gains exactly
one line, **no commit is made on your behalf**, and the scaffold runs the
full 19-fault self-test — if anything is wrong it **aborts loudly**
instead of leaving you a broken install.

## After scaffolding (printed at the end of the copy, repeated here)

```bash
cd my-project
git config core.hooksPath .githooks   # hooks that survive clones
pip install jsonschema                # arms the schema-drift detector
git add -A && git commit -m "scaffold: truth ledger"   # your history is yours
scripts/truth doctor                  # must pass — checks YOUR wiring
```

Then paste the 4-line snippet from `AGENTS.md` into every instruction file
your agent runtimes load (`CLAUDE.md`, `.cursorrules`, …). A snippet in a
file no runtime reads is silent death.

## Pull tooling upgrades later — without touching your claims

```bash
copier update --trust -a .copier-answers.truth-ledger.yml
```

Your `.truth/claims.jsonl` is **not managed by copier** — updates ship new
tooling and never diff, rewrite, or conflict your ledger. This is tested,
not promised: a populated ledger is byte-identical (md5-verified) across
template updates.

## 60-second tour

```bash
# an agent verifies a fact and files it — one command, with a recipe + tripwire
scripts/truth claim "no call sites remain for legacyAuth()" \
  --class VERIFIED --evidence-cmd "grep -rn legacyAuth src/" \
  --paths "src/**" --tier P0

scripts/truth list --live      # what can be trusted right now
scripts/truth queue            # what needs a human (empty = carry on)
scripts/truth dispatch tr-xxxx # verification context for a FRESH agent session
```

Someone commits a change under `src/` → the post-commit hook demotes the
claim to `stale` automatically. That's the whole trick: knowledge decay
made mechanical instead of vigilance-dependent.

## What you get

| Piece | Job |
|---|---|
| `.truth/claims.jsonl` | the ledger — append-only, event-sourced, merge-safe (`merge=union`) |
| `scripts/truth` | the CLI — intake gates, fold, invalidation scan, verifier dispatch |
| `.githooks/` | pre-commit gate (append-only + schema) · post-commit/post-merge scan |
| `.github/workflows/` | PR gate · post-merge scan with bot commit-back · weekly 19-fault canary |
| `prompts/truth-verifier.md` | fixed prompt for independent verification (isolation is scripted) |
| `docs/adr/001` | the readiness semantics: which premises block work, by cost tier |
| `scripts/truth-canary.sh` | 19 seeded faults — run weekly; all CAUGHT, or stop trusting green |

## The non-interference contract (why scaffolding can't hurt you)

| # | Clause | Verified by |
|---|---|---|
| N1 | copier never creates, diffs, or rewrites the ledger | md5-identical populated ledger across a real `copier update` |
| N2 | `.gitattributes` merged idempotently, never owned | user rule preserved; union line count = 1 after copy + update |
| N3 | no `git init`, no auto-commit, hooks only if `.git` exists | `git log` unchanged across scaffold and update |
| N4 | existing `AGENTS.md` never clobbered | pre-existing file survives verbatim |
| N5 | self-test fails **closed** | sabotaged template → scaffold aborts, non-zero exit |

## Docs

- [Operations guide](docs/truth-ledger-operations-guide.md) — every trigger,
  how to spot it firing, the automation ladder, and the three judgments
  that must stay human (with diagrams)
- [`.truth/README.md`](template/.truth/README.md) — the layer's own manual,
  installed into every child repo
- [ADR-001](template/docs/adr/001-premise-validity-semantics.md) — premise
  validity semantics for `truth ready`

## Requirements

POSIX, git, Python 3. `jsonschema` (dev/CI) so the drift detector runs
armed. Optional: a work tracker (e.g. Beads) unlocks `truth ready` —
issues premised on dead facts are HELD before an agent picks them up; the
ledger works standalone without it.