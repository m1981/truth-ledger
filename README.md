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

Safe on existing projects by contract (see the non-interference table
below for how each clause is enforced): your `AGENTS.md` is never
clobbered, your `.gitattributes` gains exactly one line, **no commit is
made on your behalf**, and the scaffold runs the full seeded-fault
self-test — if anything is wrong it **aborts loudly** instead of leaving
you a broken install.

## After scaffolding

The scaffold prints these steps when it finishes; they are repeated here:

```bash
cd my-project
bash scripts/install-hooks.sh         # wires pre-commit + post-merge shims
pip install jsonschema                # arms the schema-drift detector
git add -A && git commit -m "scaffold: truth ledger"   # your history is yours
scripts/truth doctor                  # must pass — checks YOUR wiring
```

Local hooks die on every clone. For hooks that survive them, commit the
shipped `.githooks/` dir route instead: `git config core.hooksPath
.githooks` per clone (the installer will refuse to double-wire and point
you here if `core.hooksPath` is already set) — or lean on the CI
workflows, which enforce the same gates without any local hooks.

Then paste the snippet from `AGENTS.md` into every instruction file
your agent runtimes load (`CLAUDE.md`, `.cursorrules`, …). A snippet in a
file no runtime reads is silent death.

## Pull tooling upgrades later — without touching your claims

```bash
copier update --trust -a .copier-answers.truth-ledger.yml
```

Your `.truth/claims.jsonl` is **not managed by copier** — updates ship new
tooling and never diff, rewrite, or conflict your ledger. This holds by
construction rather than by test: the ledger is not a template file, so
copier has nothing to diff it against — see clause N1 below.

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
| `.github/workflows/` | PR gate · post-merge scan with bot commit-back · weekly seeded-fault canary |
| `prompts/truth-verifier.md` | fixed prompt for independent verification (isolation is scripted) |
| `docs/adr/001` | the readiness semantics: which premises block work, by cost tier |
| `scripts/truth-canary.sh` | the seeded-fault suite — run weekly; it prints its own count; all CAUGHT, or stop trusting green |

## The non-interference contract (why scaffolding can't hurt you)

| # | Clause | Enforced by |
|---|---|---|
| N1 | copier never creates, diffs, or rewrites the ledger | structural: the ledger is not a template file — it is `touch`ed into existence by an idempotent task, so copier has nothing to manage |
| N2 | `.gitattributes` merged idempotently, never owned | a grep-guarded append task: copy + N updates yield the union line at most once, user rules untouched |
| N3 | no `git init`, no auto-commit, hooks only if `.git` exists | no git commands in any task except the `.git`-guarded hook installer; nothing commits |
| N4 | existing `AGENTS.md` never clobbered | copier's `_skip_if_exists` |
| N5 | self-test fails **closed** | verified by execution: the scaffold runs the full seeded-fault canary and aborts non-zero on any miss |

N5 is the only clause verified by running something; N1–N4 hold because
copier is never told about the things they protect. What the tool cannot
see, it cannot touch.

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
armed. No external work tracker is required for `truth ready`: the ledger
ships a native work kernel (v0.5, ADR-002) — `truth issue --premise` /
`start` / `done --claim` file work items in the same ledger, and issues
premised on dead facts are HELD before an agent picks them up. Prefer an
external tracker? The seam is tracker-agnostic (v0.4.1): any tracker via
`TRUTH_TRACKER_CMD="<cmd printing a JSON array of {id, title}>"` or a pipe
(`my-tracker export | scripts/truth ready --stdin`), with Beads as the
fallback default (`bd ready --json`) — note the native kernel outranks
that default the moment any issue record exists. With neither kernel
records nor a tracker, the ledger still works standalone — a dashboard
(`queue`, `list --live`) instead of a gate.