# Backtick paths — the measurement, and why open item 1 names the wrong script

`docs/reviews/mechanism-layers-brief-2026-08-24.md` open item 1 (L1(a)) reads:

> `doc-health` checks backtick paths, not only links — the gap §7 row 4 names.
> **20 of 183 backtick paths are dead (11%)**, two of them inside the paper.

This is the measure role's output under ADR-062 rule 4, written **before** any
patch. A previous attempt at this item was reverted for patching
`doc-health.sh` on an assumption about a variable it does not have. So this
pass read the script first, and reading it changed the item.

## 1. `doc-health.sh` does not sweep the corpus the finding was measured in

```
$ sed -n '24,27p' template/scripts/doc-health.sh
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
FILES="$(git ls-files '*.md' | grep -vE '(^|/)(archive|archived|attic|adr|freeze)/' | ...)"
```

`ROOT` is `template/`, not the repository. The variable is `FILES` — there is
no `LIVE_DOCS`, and `set -euo pipefail` on line 22 means a reference to one is
fatal, which is what reverted the last attempt.

```
$ find . -name 'doc-health*' -not -path './.git/*'
./template/scripts/doc-health.sh
```

**One copy, and the meta-repo has no doc-health of its own.** Its corpus is
sixteen files, all under `template/`:

```
$ bash template/scripts/doc-health.sh
doc-health: 0 failure(s) across 16 live doc(s)
```

The 20-of-183 finding — and the two occurrences "inside the paper" — are in
`docs/`, in the **meta-repo**, which this script never opens. Teaching
`doc-health` to check backtick paths would add a check to sixteen template
files and leave every measured occurrence untouched.

## 2. In the corpus `doc-health` DOES sweep, the check is worthless

Measured with the loosest plausible rule (a backticked token containing `/`,
no whitespace, no URL, no wildcard):

```
--- template/ ---
live docs: 16 | backtick path candidates: 66 | dead: 28
```

**28 of 28 are legitimate.** A sample, and the sample is the whole character
of the set:

| token | why it is not a defect |
|---|---|
| `` `|A∩B|/|A∪B|` `` | a Jaccard formula |
| `` `>/dev/null` `` | a shell fragment |
| `` `.circleci/config.yml` ``, `` `.github/copilot-instructions.md` `` | files in a CONSUMER's repo |
| `` `.truth/claims.jsonl` ``, `` `.truth/citation-scope` `` | exist in the meta-repo; the script's root is `template/` |
| `` `instruments/concern-tag.py` ``, `` `instruments/blast-report.py` `` | meta-repo instruments, correctly named by template docs |
| `` `src/pkg/` ``, `` `<component>/docs/specs/` ``, `` `scripts/session-gates.d/` `` | placeholders in archetype templates |

The script's own docstring already says this, and the measurement agrees with
it:

> Backtick path mentions are deliberately NOT checked — shorthand like
> `pkg/module.py` is endemic and legitimate; links are the load-bearing refs.

**The exemption is not an oversight. It is correct for this script's corpus,
and it should stay.** `doc-health.sh` also ships to consumers by copier, so a
patch here reddens repositories that never asked for the check.

## 3. In the meta-repo's live corpus the finding is real

Same rule, run against the repository root, is still unusable — 165 dead of
754 — and for the same reason: `origin/main` (5×), `path.json#/a/b` and
`package.json#/dependencies/stripe` (ADR-055's structural selectors),
`PATH="/usr/bin:/bin"`, `2329/6,8`, `claude/git-hooks-architecture-zc97y3`,
`kuchnie/docs/...` in another repository entirely.

**A rule that opts in by SHAPE, rather than opting out by exception**, is what
makes the signal appear. Three conditions, each stated so a reader can predict
what will be checked:

1. the token's first segment is a directory this repository actually has
   (`docs`, `scripts`, `template`, `instruments`, `.truth`, `.githooks`, …) —
   this alone removes `origin/main`, `src/`, `.github/workflows/`;
2. no shell metacharacter, no `#` (selectors and anchors), no wildcard, no
   scheme, not absolute or `~`-rooted;
3. a trailing `:NNN` or `:NNN-MMM` line reference is stripped before the
   existence test — a file:line citation is a path claim about the file.

Applied to the **live** corpus (`.truth/citation-scope` minus the six
frozen-reference prefixes `fact-health.sh` subtracts — the same corpus the
citation sweep judges):

```
live docs: 37 | backtick path candidates: 315 | dead: 26
```

Three of the 26 are inside `docs/truth-ledger-paper-v3.md`, which is what the
brief meant by "two inside the paper". The brief's 20/183 over 57 docs and
this 26/315 over 37 docs are the same finding under two corpus definitions;
neither number should be carried in prose without its rule.

### The 26, triaged — and they are three different things

**Genuinely dead, in prose a reader is meant to act on today (the finding):**

| citation | measured |
|---|---|
| `docs/truth-ledger-paper-v3.md:980` → `scripts/test-instruments.sh` | **deleted by `32022c6`** ("replace bash test scaffolding with stdlib test-integrations.py"). This is the relocation mechanism the navigation analysis names, caught in the act |
| `docs/governance/gate-metrics.md:13` → `template/docs/adr/truth/047-*.md` | the pre-move ADR location, in a LIVE governance doc |
| `docs/decisions/056-*.md:157` → `scripts/adr041-hash-stability.py` | never on disk in recorded history |
| `README.md:24` → `docs/machinery-atlas.md` | never on disk |
| `docs/growth-gate/spec-coverage-manifests.md:150`, `docs/truth-ledger-operations-guide.md:24,438` → `docs/specs/sc-slugs.txt` | never on disk; a design naming an artefact nobody built |
| `docs/growth-gate/symbol-tracing-design.md:120` → `docs/contract-symbols-core.txt` | same |

**CONSUMER-RELATIVE, and this is a third category the check must carry:**
`.truth/README.md` (README, explained, loophole-map) and `docs/ARCHITECTURE.md`
(RUNBOOK) are missing from the repository root and **present under
`template/`**. The sentence is right for a consumer standing in their own
repo and wrong for anyone standing here. Reporting these as "dead" would be
false; reporting them as nothing would lose a real ambiguity. They resolve
under `template/`, which is mechanically checkable, so the check can say
exactly that.

**Legitimately not repository paths:** `docs/adr/001`, `docs/adr/NNN`,
`docs/adr/`, `docs/adr/truth/` — consumer conventions and placeholders;
`.truth/README` — shorthand without the extension; `template/…` — a literal
ellipsis my rule's metacharacter class did not catch, which is a defect in the
rule and is why the rule needs a baseline like every other instrument here.

## 4. What follows

**Open item 1 should be re-aimed, not executed as written.** Patching
`doc-health.sh` would (a) add a check to sixteen files where it produces 28
false findings and 0 true ones, (b) reverse a documented decision that the
measurement supports, and (c) ship that to every consumer. The check belongs
in a meta-repo Tier C instrument over the live corpus, with:

- the shape rule above, stated in the docstring rather than inferred;
- a third verdict, `consumer-relative`, for paths that resolve under
  `template/`;
- a baseline for today's set, so the NEXT dead path fails rather than the
  current backlog being relitigated — the arrangement `arm-index`,
  `label-coupling` and `register-index` already use;
- and, per ADR-061, a demonstration of it going red before it is called done.

**Falsifier for everything above:** if `doc-health.sh` is ever pointed at the
repository root rather than `template/`, §1 and §2 stop applying and the item
becomes executable as written. Check `ROOT=` on line 24 before trusting this
document.
