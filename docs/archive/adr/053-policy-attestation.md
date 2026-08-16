# ADR-053: an empty policy file must say that it is empty

Status: **PROPOSED** (2026-08-13, drafted by the implementing session) — NOT
accepted. This record resolves a contradiction between two accepted-and-drafted
records; which way it resolves is the operator's call, and the counter-argument
is stated in full below rather than left for a reviewer to reconstruct.
Date: 2026-08-13
Amends: **ADR-034 SI-4** (policy-file semantics — the committed-empty clause,
narrowed here).
Extends: ADR-042 rule 2 (zero coverage is a failure, not a pass), ADR-037
(`.truth/generated-paths`, SI-4's first consumer), ADR-036
(`.truth/citation-scope`, its second).
Cites: ADR-045 (the adoption-gated WARN precedent, considered and declined
below), ADR-048 (a check no root invokes is prose — this is its twin: a policy
nobody stated is a default), ADR-047 (adoption metric), ADR-014 (a gate that
refuses legitimate work teaches its own bypass — the test this must pass).
Supersedes: —

## Context

Two records on file say opposite things about the same bytes.

**ADR-034, SI-4:** policy files *"distinguish committed-empty (consciously
configured — silent) from absent (built-in default + one-line notice)"*.

**ADR-042, rule 2:** *"Zero coverage is a failure, not a pass."*

A committed-empty policy file is zero coverage. SI-4 says it is a statement and
stays silent; ADR-042 says it is a failure. Today SI-4 wins — **not on merit,
but by being older and Accepted while ADR-042 is still PROPOSED.** Nothing has
ever forced the question, because the question is invisible: silence is what
both a decision and an omission look like.

The gap is precise. SI-4's committed-empty clause assumes someone *chose*
emptiness. But the template **ships these files empty**, so a consumer who never
opened one is byte-for-byte indistinguishable from a consumer who studied their
repository and concluded nothing belonged there. SI-4 reads both as policy. One
of them is a default.

### The evidence is this repository's own file

`.truth/generated-paths` in the meta-repo has carried, since 2026-08-01:

> *"THIS FILE IS DELIBERATELY EMPTY, and empty is a statement, not an omission:
> nothing in this repository is generated. Every tracked file is hand-authored
> except `.truth/claims.jsonl` ... Committed 2026-08-01 alongside
> `.truth/citation-scope`, for the same reason: a coverage audit found two
> ADR-shipped gates reporting nothing because their policy file had never been
> written."*

A correct, dated, reasoned attestation — **in prose, which nothing can check**.
The decision was made and recorded, and no mechanism could tell it apart from
the untouched default sitting in the consumer repo next door. This is the same
shape ADR-048 named for checks and ADR-049 measured for retraction bases: the
information existed, was correct, and was unstructured.

The measurement that closes the argument came from the other side. On the
kuchnie ledger, `.truth/generated-paths` is committed empty — SI-4 reads that as
*"nothing here is generated"* — while the repository tracks **25 files** under
`exercises/*/generated/`, including `rozrys.csv`, which
`run_production_leg.py` writes and which is evidence for two live claims. The
template's own shipped comment block even offers `exercises/*/generated/**` as
an example. SI-4 silently accepted a statement the repository contradicts.

## Decision

**A policy file that is committed and empty must carry a dated attestation, or
`doctor` FAILS.**

### 1. Three states, decidable

`policy_file_state(text)` — pure, given the file's bytes or `None`:

| state | meaning |
|---|---|
| `absent` | not committed. A different question with its own voice; never an attestation problem. |
| `populated` | ≥1 non-comment, non-blank line. **The entries are the statement.** Nothing to attest. |
| `attested` | no entries, and a `# attested YYYY-MM-DD: <reason>` line. |
| `unattested` | no entries, no such line — the untouched default. |

The attestation must be a **comment**: written without its `#` it would be an
entry, and a file populated with a garbage glob must not read as attested.
The date and the reason are both required, because an undated "we thought about
this" ages into the same silence it replaces.

Applies to the template-owned policy files — `.truth/generated-paths` and
`.truth/citation-scope` — via one registry tuple, so a future policy file joins
by being added to it.

### 2. The cross-check, because an attested empty file can still be wrong

`generated_blind_spot(globs, tracked)` names tracked files under conventionally
generated directories that the committed list does not cover. **WARN, never a
refusal:** a directory called `generated/` can hold hand-written files, so
naming is evidence and not proof. The arm exists because the attestation check
alone cannot see this — *"nothing here is generated"* is a claim about the
repository, and only the repository can contradict it.

The probe set carries both `dist/**` and `**/dist/**` per name. That is not
redundancy: `**` compiles to `.*`, so `**/dist/**` requires a `/` before `dist`
and silently misses a top-level `dist/` — the most common shape there is. The
pair is the fix for a probe set that would have looked thorough and skipped the
obvious case.

### 3. The template does not ship the attestation line

It ships the *instruction* and an example. An attestation the consumer never
made records nothing, and inheriting one would reproduce exactly the defect this
record closes, one level up.

## Why FAIL, and the case against

ADR-014's test: a gate that refuses legitimate work teaches its own bypass.
Applied here — **decidability is total** (is there a line matching the shape?),
so a false refusal is impossible, and **the fix is one line** that the refusal
message states verbatim.

ADR-045 faced the same adoption shape and chose **WARN**: pre-v0.9.29 installs
lacked the `pre-merge-commit` hook *blamelessly*, so failing them punished
people for a decision that had not existed yet. **That precedent applies here
and I am declining it — the operator should weigh this, because it is the one
genuinely contestable point in this record.**

The case for WARN: the template shipped the file empty and wrote *"empty is a
statement"* inside it. Consumers who left it alone believed the documented
contract. Failing them for that is retroactive.

The case for FAIL, which I judge stronger:

- A WARN here is decorative in a way ADR-045's was not. ADR-045's WARN pointed
  at a **missing artifact** someone would eventually install; this one points at
  a **decision nobody will ever make** unless something stops. The measured
  outcome of "advisory on every filing" is already on record: kuchnie's file has
  been unattested through 2216 records.
- ADR-042 rule 2 is the more fundamental rule, and it is only PROPOSED because
  nothing forced it. Resolving the contradiction by deferring to whichever
  record is older is not a decision.
- **Scale makes it cheap.** There is one consumer. At fifty, staging this
  (WARN for existing files, FAIL for newly created ones, by mtime or by a
  template version marker) would be right; at one, the staging machinery costs
  more than the migration.

If the operator prefers WARN, the change is one line in `cmd_doctor` and the
rest of this record stands unaltered.

## Consequences

`doctor` gains three checks and one WARN. **Every existing consumer's `doctor`
goes red on adoption** until one line is written per empty policy file — that is
the intended and only effect on them.

On kuchnie it fires immediately: one FAIL on the unattested list, one WARN
naming 25 tracked files under `exercises/*/generated/`. That WARN is the
mechanical form of an open question (*do those paths belong on the list?*) which
had been carried in a handoff note. It stops depending on anyone remembering it.

On this repository, the 2026-08-01 prose attestation was transcribed into the
machine-readable form. **Nothing was decided; an existing decision was made
checkable** — which is the whole content of this record, applied to itself.

## Non-goals — residuals owned

**Not a claim that an attestation is true.** It records that a human made a
statement on a date; nothing verifies the statement. The cross-check is one
narrow contradiction test, not verification.

**Not extended to meta-repo instrument policy files.**
`.truth/reachability-opt-out` and `.truth/field-consumer-opt-out` follow SI-4's
original semantics, are checked by their own instruments, and are out of the
template. Whether they should join this rule is a separate question with a
different blast radius.

**Not a lint on attestation quality.** `# attested 2026-08-13: x` passes. The
date and the requirement to write something are the whole gate; judging the
reason is a human's job and a gate that tried would be the ADR-037 lint class.

**Not retroactive to the ledger.** No record changes; this is an installation
check, which is what `doctor` is for (G4). A refusal at filing time would
punish the filer for a policy decision that is not theirs to make.

## Adoption gate (ADR-047)

**Metric:** the count of attestable policy files in each state, per repository.
**Data source:** `truth doctor --json` (`fail`/`ok` rows named
`policy file attested (<rel>)`), plus the blind-spot WARN.
**Next review:** 2026-11-13, in the R11 monthly slot.
**Retirement test:** if every consumer reaches `attested` or `populated` within
one review cycle and no blind-spot WARN has ever named a file that turned out to
be generated, the check has done its migration and drops to an advisory. If
instead blind-spot WARNs keep finding real generated artifacts, the finding is
that `.truth/generated-paths` needs discovery help, not that this gate needs
loosening.

**Falsifier:** a repository that passes both checks and still watches a
generated artifact — i.e. an attestation and a covered probe set that together
miss the very thing ADR-037 exists to refuse.
