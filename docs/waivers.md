# Waivers — the gates that can be lifted, by the carriers this register can enumerate

> Reader: anyone asking "which refusals can be bypassed, by what, and how many
> uses are on record?" | Enables: reviewing the KNOWN escape surface as a
> population rather than as independent flags | Update-trigger: a CLI flag, an
> environment name or a `.truth/` policy file is added or removed (then re-run
> `instruments/waiver-index.py`, which refuses until it is classified) — and,
> UNGATED, whenever a bypass appears in a carrier this register cannot harvest

## What this register covers, and what it provably cannot

**THIS REGISTER IS NOT TOTAL.** It partitions the carriers it can enumerate
from a source, and there are carriers it cannot.

| carrier class | enumerated from | reverse direction |
|---|---|---|
| `flag` | `truth <verb> --help`, every verb | **gated** — every flag is a row here or an entry in `.truth/waiver-not-an-override` |
| `env` | every `os.environ` read in the Python tree, and `${NAME:-}` / `env NAME=` in the shell tree | **gated**, with the shell half a syntactic approximation that over-reports |
| `file` | the contents of `.truth/` | **gated** |
| `syntax` | — | **none.** A form like `<path>#<selector>` is not on any list |
| `config` | — | **none.** Git config, the filesystem, the environment of a CI runner |
| `code` | — | **none.** A branch that refuses is a branch that can stop refusing |

Rows in the last three carriers are recorded from what somebody happened to
find. **They are not, and cannot be, complete.** No sweep can walk back from
"every way a gate can be lifted" to a list, because that phrase has no source
to be harvested from. What the sweep can do — and does — is refuse a NEW flag,
environment name or policy file that nobody has classified.

### Why the title changed

The first version of this file was titled *"every gate in this system that can
be lifted, and by what"* and its content was a partition over **flags**. That
is a mis-scoped partition: a domain left unstated reads as universal, so a
register total over flags is taken as total over bypasses. The defect was
found by the operator against this file, one day after this file was built to
catch exactly that shape elsewhere.

The `<path>#<selector>` escape is the proof. It was discovered during the
build, described in the commit message as "recorded", and was in fact written
only into `.truth/waiver-not-an-override` — **the file for things that are NOT
overrides** — under `--paths`. A bypass filed in the complement of the
register, while the register's title claimed to hold every bypass.

### The limit statement is gated

`instruments/waiver-index.py` fails if the marker at the top of this section
is absent. A limit held by nothing is the first thing a redraft deletes: this
same effort lost a finding about six overdue gate-metrics reviews exactly that
way, replaced by a sentence that could not be checked.

## Why this register exists

Every other register here lists things that were *created*. This one lists the
places where a rule was *set aside*. It is the register whose absence is least
visible, because a waiver leaves a record only where somebody built one to
leave — and most of the rows below leave nothing at all. Read the counts off
`instruments/waiver-index.py`; none is restated here.

**No count in this file is authoritative.** Read them off
`python3 instruments/waiver-index.py`, which prints the escape surface, the
flag inventory and the population per stamp. Counts restated in prose are
exactly what this repository's one-home-per-fact rule forbids, and the first
draft of this file got three of them wrong.

DO-178C, IEC 61508 and ISO 26262 each require a deviation from a required
objective to be recorded with rationale, scope, owner and expiry, and require
the population of open deviations to be reviewed **as a population**. Before
this file there was no population — only independent flags.

## Two findings this register was built on

**1. "Every override in this system is admitted on a sentence" is false.** It
was the opening claim of ADR-059, repeated in `AGENTS.md` and in
`instruments/semantic-audit.py`. Of the CLI flags below, six take a
`SENTENCE`, one takes a number and four take nothing — and the four are not a
random four:

> The six that carry a sentence lift a **quality-of-justification** gate: a
> quantifier wider than its evidence, a watch set over budget, a generated
> artifact watched, a positive claim on a failing probe, a retraction leaving
> citations dangling, an anchor advanced past a capsule that no longer
> reproduces.
>
> The four that carry nothing lift an **execution** gate: run an unscreened
> evidence command, close a work item without running its unscreened
> acceptance oracle, admit a near-duplicate over G8, skip the determinism
> double-run.

So the overrides with the largest blast radius are the ones admitted on a bare
boolean, and `instruments/semantic-audit.py` — the extractor built to hand
every override's rationale to an outside reader — is structurally blind to
them. Not through an oversight in its field list: there is no rationale to
extract. The L2 reader ADR-059 designs cannot tell "no override happened" from
"an override happened and said nothing", because both produce no row.

**2. `--single-run` is worse than the other three, and nothing had noticed.**
It skips the G6 determinism double-run — the check that catches a
non-deterministic evidence command before its output is frozen into a claim —
"accepting false-divergence risk", and it writes **no field whatsoever** into
the record. The other three at least leave `screened: false` or
`overridden_duplicates`. This one is invisible in the ledger, so its
population cannot be counted at all, by this instrument or any other. The
sweep prints that fact rather than printing a zero.

## The register

`admitted on` is a controlled vocabulary — exactly `SENTENCE`, `a value` or
`nothing` — and is checked on every carrier. See "What is checked" for the
columns that are not.

| carrier | name | where it applies | gate it lifts | admitted on | stamp on the record | decays | governing record |
|---|---|---|---|---|---|---|---|
| flag | `--scope-ok` | claim, done | the quantifier-scope refusal: a sentence claiming more than its evidence covers | SENTENCE | `scope_basis` | yes, 30d (ADR-032 default expiry) | ADR-007 |
| flag | `--paths-ok` | claim, done | the freehand watch budget: a watch set larger than the churn floor allows | SENTENCE | `paths_basis` | yes, 30d (ADR-032) | FAZA 3, ADR-055 |
| flag | `--generated-ok` | claim, done | the refusal to watch a generated artifact | SENTENCE | `generated_ok_basis` | yes, like `--scope-ok` (ADR-032) | ADR-037 |
| flag | `--evidence-exit-ok` | claim, done | the positive-claim exit gate: a positive claim whose probe exits non-zero | SENTENCE | `evidence_exit_basis` | no | ADR-035 |
| flag | `--orphan-ok` | verdict, done | the tombstone citation gate: retracting while citations still point at the id | SENTENCE | `orphan_basis` | no | ADR-036 |
| flag | `--refresh-evidence` | verdict | the ADR-051 refusal to advance a claim's anchor past a capsule that no longer reproduces (`policy.py`: *"Nothing was filed."*) | SENTENCE | `evidence_refresh.basis` | no | ADR-051 |
| flag | `--single-run` | claim, done | **the G6 determinism double-run** — files without re-running the evidence command, "accepting false-divergence risk" | **nothing** | NOT COUNTABLE — **nothing at all**; see below | no | G6 |
| flag | `--ttl-days` | claim, done | **ADR-032's default override decay** — an explicit value suppresses the 30-day shelf life that would otherwise be stamped on a claim carrying `--scope-ok`, `--paths-ok` or `--generated-ok`, so the override judgement is never re-asked. ADR-032 calls it "the visible opt-out". On a claim with no override basis it lifts nothing; that condition is prose and is not checked | **a value** | `(scope_basis/paths_basis/generated_ok_basis) + ttl_days + !ttl_default` — an explicit shelf life on a claim that carries a decaying override basis. `ttl_days` alone is on every claim; the separating predicate is this one | n/a — it is what suppresses a decay | ADR-032, G10 |
| flag | `--duplicate-ok` | claim, done | the G8 near-duplicate refusal | **nothing** | `overridden_duplicates` (the predecessor ids — provenance, not rationale) | no | G8, ADR-031 |
| flag | `--evidence-unsafe-ok` | claim, done | **the evidence screen** — files a claim whose evidence command the screen refused | **nothing** | `evidence.screened = false` | no | ADR-009 |
| flag | `--accept-unsafe-ok` | issue, done | **TWO different refusals, one flag.** On `issue` it lifts the ADR-014 *screen*: an `--accept-cmd` the allowlist rejects is refused, and this files it anyway. On `done` it lifts *execution*: a stored oracle that is unscreened will not be run, and this closes the item without running it. The first admits an unchecked oracle; the second never learns whether the finish line was crossed | **nothing** | `accept.screened = false` on the filing; `accept.executed = false` additionally on the close. Measured 2026-08-25: 5 records and 2 records, and the second set is a strict SUBSET of the first, so the flag's population is 5 — never 7 | no | ADR-014 |
| env | `TRUTH_SELF_VERDICT` | `template/truthlib/cli.py` | **G11 / ADR-010, the author-is-not-verifier refusal** — `=1` allows `agree` on a claim the SAME session filed. This is the separation INV-O is about and the paper calls the property most worth admiring | **nothing** | NOT COUNTABLE — **nothing at all**; the record cannot show it was used | no | ADR-010 |
| env | `TRUTH_HUMAN` | `template/truthlib/shellio.py` | G12's human-only tombstone refusal; `=1` is the first half of the ADR-011 ceremony | **nothing** | NOT COUNTABLE — **nothing at all** | no | ADR-011 |
| env | `TRUTH_HUMAN_ACK` | `template/truthlib/shellio.py` | the INTERACTIVE half of G12 — an id-specific value replaces a typed confirmation, which is what makes a human-only gate scriptable. Deliberately absent from the refusal text: an error that names its own bypass instructs a compliant agent | **a value** | NOT COUNTABLE — **nothing at all** | no | ADR-011 |
| env | `TRUTH_ALLOW_NO_JSONSCHEMA` | `scripts/release-battery.sh`, `template/scripts/test-truth-core.py` | the schema half of the record contract — `=1` waives the arm that fails when `jsonschema` is absent, leaving the shape UNCHECKED | **nothing** | NOT COUNTABLE — **nothing at all** | no | F1 arm |
| env | `TRUTH_BATTERY_NO_META` | `scripts/release-battery.sh` | **the battery meta-gate** — the gate that guards every other gate. `release-battery.sh` sets it for its own nested run and its comment says it "is not a skip flag for operators"; NOTHING enforces that, and exporting it before a push skips the meta-gate | **nothing** | NOT COUNTABLE — **nothing at all** | no | the battery header |
| env | `TRUTH_BATTERY_SCOPE` | `scripts/release-battery.sh` | every scope-guarded battery arm. The hook sets it from the pushed range and the comment says unknown scope means MORE checking — true of the `ALL` fallback, false of a value set deliberately: `TRUTH_BATTERY_SCOPE=zzz` matches no pattern, so every `touches`-guarded arm skips | **a value** | NOT COUNTABLE — **nothing at all** | no | the battery header |
| env | `TRUTH_NOW` | `template/truthlib/shellio.py` | the clock. Its own docstring says "test hook; never in prod"; nothing enforces that, and a chosen `ts` moves TTL expiry and the ADR-016 fold order | **a value** | NOT COUNTABLE — the `ts` it produces is indistinguishable from a real one | no | ADR-015 |
| env | `TRUTH_SESSION` | `template/truthlib/shellio.py` | not a refusal, but the LEVER on one: the separation gate compares this string, so choosing a different value makes self-verification undetectable without `TRUTH_SELF_VERDICT`. AGENTS.md already says separation by PID accident is not separation | **a value** | NOT COUNTABLE — the `session` field is indistinguishable from a real one | no | ADR-010 |
| file | `.truth/waiver-not-an-override` | `instruments/waiver-index.py` | **this register's own scope.** A line here removes a carrier from the register. The escape surface's escape surface | SENTENCE | `ENTRIES` — each non-comment line is one standing excusal | no | this file |
| file | `.truth/evidence-allow` | `template/truthlib/registry.py` | the ADR-009 evidence screen, for every future filing rather than one — the standing form of `--evidence-unsafe-ok` | **nothing** | `ENTRIES` — each non-comment line is one standing excusal | no | ADR-009 |
| file | `.truth/accept-allow` | `template/truthlib/registry.py` | the ADR-014 acceptance screen, standing form of `--accept-unsafe-ok` | **nothing** | `ENTRIES` — each non-comment line is one standing excusal | no | ADR-014 |
| file | `.truth/citation-scope` | `scripts/fact-health.sh`, `template/truthlib/shellio.py` | BOTH the ADR-036 retraction gate and the fact-health sweep at once: a glob removed here takes documents out of the corpus both read | **nothing** | `ENTRIES` — each non-comment line is one standing excusal | no | ADR-036 |
| file | `.truth/generated-paths` | `template/truthlib/evidence.py` | the ADR-037 generated-artifact refusal, standing form of `--generated-ok` | **nothing** | `ENTRIES` — each non-comment line is one standing excusal | no | ADR-037 |
| file | `.truth/arm-subject-opt-out` | `instruments/arm-index.py` | arm-index's subject rule, per family | SENTENCE | `ENTRIES` — each non-comment line is one standing excusal | no | arm-index |
| file | `.truth/label-coupling-opt-out` | `instruments/label-coupling.py` | label-coupling's pair rule | SENTENCE | `ENTRIES` — each non-comment line is one standing excusal | no | label-coupling |
| file | `.truth/reachability-opt-out` | `scripts/gate-reachability.sh` | the reachability sweep, per check | SENTENCE | `ENTRIES` — each non-comment line is one standing excusal | no | gate-reachability |
| file | `.truth/field-consumer-opt-out` | `instruments/field-consumers.py` | the field-consumer sweep | SENTENCE | `ENTRIES` — each non-comment line is one standing excusal | no | field-consumers |
| file | `.truth/register-index-baseline` | `instruments/register-index.py` | register-index checks (b) and (c), per entry | SENTENCE | `ENTRIES` — each non-comment line is one standing excusal | no | register-index |
| file | `.truth/arm-index-paper-baseline` | `instruments/arm-index.py` | arm-index's Appendix A reconciliation | SENTENCE | `ENTRIES` — each non-comment line is one standing excusal | no | arm-index |
| env | `TAG_CHECK_VERSION` | `.githooks/pre-push` | **the pre-push tag check** — it overrides the version the check detects, and the check `exit 1`s when a tag's tree states a different version. Its own comment says "test hook only"; nothing enforces that, and the shape is identical to `TRUTH_NOW`, which is registered | **a value** | NOT COUNTABLE — **nothing at all** | no | the pre-push header |
| config | `git push --no-verify` | any push | **the entire pre-push boundary** — the battery, the tag check and everything they carry. `template/scripts/install-hooks.sh` calls it "the Emergency exit" in its own text, so it is documented as a bypass and was registered nowhere | **nothing** | NOT COUNTABLE — **nothing at all**; a skipped hook leaves no trace anywhere | no | install-hooks.sh |
| config | `.claude/settings.json` | the harness | the ADR-005 PreToolUse whisper stage in full — deleting the `PreToolUse` entry unwires `scripts/truth-whisper.py`, including its deny half. Outside `.truth/`, so the `file` harvest does not reach it | **nothing** | NOT COUNTABLE — the file is pinned (tr-df856f43) but its CONTENT is not a ledger record | no | ADR-005 |
| config | `scripts/truth-whisper.deny` | `scripts/truth-whisper.py` | the edit-tool block on `docs/archive/` and `.truth/claims.jsonl` — removing a line lets an agent edit the ledger directly, against INV-A. A policy file outside `.truth/`, which is why the `file` carrier does not see it | **nothing** | NOT COUNTABLE — the file is pinned (tr-45312cff); its content is not a record | no | ADR-005, ADR-003 |
| syntax | `<path>#<selector>` | `--paths` entries | **the one-path and churn budgets** — ADR-055 exempts a structural selector target from both. Carried by PATH SYNTAX, so no flag names it and no list enumerates it | **nothing** | NOT COUNTABLE — the selector sits in `evidence_paths` and reads as an ordinary watch entry | no | ADR-055 |
| config | `core.hooksPath` | local git config | `.githooks/pre-commit` and `pre-push`, hence the whole push boundary. Unsetting or repointing it disables both; it is LOCAL config no mechanism keeps true, and only `truth doctor` reports it | **nothing** | NOT COUNTABLE — **nothing at all** | no | ADR-025 |

## What is checked, and what is not

`instruments/waiver-index.py` sweeps this table against three sources, one per
harvested carrier. It does **not** scope itself to a naming convention: that
scoping was wrong three times in this file alone — `--refresh-evidence` takes
a sentence with no `-ok` suffix, `--single-run` has neither, `--ttl-days` takes
a number — and scoping to FLAGS was wrong again, which is what the carrier
column is for.

**Checked, per carrier:**

- **forward** — a `flag` row must name a flag the parser accepts, on verbs it
  accepts it on, taking the argument the row declares; an `env` row must name
  a name some source really reads; a `file` row must name a file that is
  there. The `where it applies` cell is checked as a SUBSET: it may name the
  place that matters rather than all six readers of a policy file, but it may
  not name somewhere the thing does not apply.
- **reverse, and total per carrier** — every flag the parser accepts, every
  environment name any source reads, and every file in `.truth/` must be a row
  here or an entry in `.truth/waiver-not-an-override` with a finished reason.
- **`admitted on`** — a controlled vocabulary, `SENTENCE` / `a value` /
  `nothing`, checked against the parser for flags and checked for being one of
  the three on **every** carrier. It was briefly checked only for flags, so 21
  of 32 rows could hold prose and the summary line counted neither.
- **mirror** — a declaration whose subject is gone, or a name on both sides.
- **the limit statement** — the marker above must be present.

**NOT checked, named rather than left blank:**

- **`gate it lifts`** — free prose on every row. Nothing verifies that the
  gate named is the gate lifted.
- **`stamp on the record`** — nothing verifies the kernel writes that field.
  A row whose stamp cannot separate the waiver's use from ordinary traffic
  carries `NOT COUNTABLE`, and that judgement is prose too.
- **`decays`** — nothing verifies the decay is implemented. Hand-checked
  2026-08-24: `gates.py` passes exactly `scope_basis`, `paths_basis` and
  `generated_ok_basis` to `override_decay`, at 30 days; an explicit
  `--ttl-days` suppresses it (ADR-032), and this ledger carries a scope
  override with a 3650-day shelf life.
- **`governing record`** — nothing verifies the ADR says what the row says.
- **every row in `syntax`, `config` and `code`** — no source enumerates them,
  so nothing checks them in either direction. Five are recorded. There is no
  reason to believe five is what exists.

**Known holes in the harvests themselves**, because a harvest that overstates
its reach is the same defect one level down:

- The shell half of the `env` harvest reads three idioms — `${NAME:-}`,
  `${NAME:?}` and `env NAME=`. A bare `$NAME` read of an inherited variable is
  missed. Extensionless files are read by shebang, so the CLI entry point
  itself is covered; a Python file with no shebang and no `.py` is not.
- The `file` carrier is scoped to `.truth/`. Policy files elsewhere —
  `.claude/settings.json`, `scripts/truth-whisper.deny` — are recorded under
  `config`, which has no reverse direction. There may be others.
- The `flag` harvest reads `truth <verb> --help`. A bypass that is not a flag
  of that program — `git push --no-verify` is the documented one — is
  `config`, and unbounded.

### When a population is NOT COUNTABLE — the criterion

`NOT COUNTABLE` is a **claim that no separating predicate exists**, and it is
earned, not asserted. Over-suppression reads as humility and hides a number;
it is the exact mirror of the rule that a WRONG population is worse than none,
and both were got wrong here in the same week. Decide the next case by this,
rather than judging it:

1. **A ledger predicate exists → count it.** A field whose presence, or
   presence-with-value, holds exactly when the waiver was used. `scope_basis`,
   `accept.screened = false`.
2. **The field is also in ordinary traffic → REFINE before giving up.**
   `ttl_days` is on every claim, so counting its presence measured the ledger.
   The separating predicate is
   `(scope_basis/paths_basis/generated_ok_basis) + ttl_days + !ttl_default`,
   and it answers **2**. This row said "the ABSENCE of `ttl_default`, which no
   presence test separates" — a stated impossibility that was one line of
   grammar away from false. **A claim that no predicate exists must name the
   predicate that was tried.**
3. **The waiver lives in a FILE → the file is the record.** One non-comment
   line is one standing excusal; `ENTRIES` counts them. Marking these
   unmeasurable suppressed **209**, and turned the deliberate emptiness of
   `.truth/generated-paths` — whose own header says emptiness is a statement —
   into an absence. **Zero is a result.**
4. **Only then: NOT COUNTABLE.** Nothing is written that separates the
   waiver's use from ordinary traffic — `--single-run` writes no field at all;
   `git push --no-verify` leaves a hook simply not run. Say which, in the cell.

A `null` is not a value. `ttl_days: null` is what a claim filed WITHOUT the
flag looks like, and counting it turned 2 into 6.

**The population is a count over HISTORY, not over live claims**, and it is a
**lower bound**: 27 of the 36 waivers leave no field that separates their use
from ordinary traffic, so no count exists for them at all. For sentence-bearing
overrides on ACTIVE claims, ask `instruments/semantic-audit.py`, which folds.
