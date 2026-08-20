# System Architecture & Living Invariants

> Reader: anyone about to change the machinery, or deciding whether to trust it |
> Enables: the load-bearing rules in one place, without reading 54 decision
> records | Update-trigger: an invariant moves, a gate is added or retired, a
> module boundary changes

> **STATUS: OBSERVED (2026-08-16).** Every number, name and rule below was read
> out of `truthlib/*.py`, `.gitattributes` and the gate table at the time of
> writing — not transcribed from the decision records that argued for them. The
> ADR corpus that carried those arguments belongs to the machinery's own
> repository, not to the shipped contract, and is being retired out of the
> template. Where this document and one of those records disagree, **this
> document reports the code**; the record reports an intention, and the gap is a
> finding to file.

The structural view — modules, tiers, intake order — lives beside this in
`structure.md`. This document is the **behavioural contract**: what the system
guarantees, and what it refuses.

---

## 1. Model danych i zbieżność — Data Model & Confluence

**Storage.** One append-only file, `.truth/claims.jsonl`, one JSON record per
line. Records are `{id, kind, actor, session, ts, payload}` with
`kind ∈ {claim, verdict, invalidation, issue, issue_event}`. Nothing is ever
edited or deleted: a correction is a new record.

**Merge is the concurrency control.** `.gitattributes` pins
`.truth/claims.jsonl merge=union`. Two branches both append; the union
concatenates. There is no lock across machines and none is needed, because the
projection is order-insensitive.

**Total sort key** (`kernel.fold_key`). `(ts, id)` alone is **not** total: a
duplicate id carrying a copied timestamp ties on both components, and a stable
sort then breaks the tie by file position — the one thing the fold must ignore
to stay confluent. The third component is `canon(payload)`, so distinct records
never tie and every permutation a union merge can produce folds identically.

**Timestamp profile.** A fixed-width UTC microsecond form, enforced by
`registry.TS_RE`:

```
^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}\+00:00$
```

Append pushes the clock forward past the ledger's tail when the system clock has
not advanced, so two records written in the same microsecond still order.

**Derived state is never stored.** Status is computed by `kernel.fold` on every
read. Two fields were evicted for violating that rule (`concerns`,
`blast_forecast`) and remain legacy-admitted so append-only history keeps
validating.

**Status vocabulary**, served at runtime by `truth vocab --json` and never
hand-copied by a consumer:

| set | members |
|---|---|
| `ACTIVE_STATUSES` | `live`, `unverified` |
| `CITATION_BAD` | `stale`, `diverged`, `retracted`, `disputed` |
| `TIERS` | `P0`, `P1`, `P2` |
| `VERDICTS` | `agree`, `diverge`, `cannot_verify`, `retracted` |

**`retracted` is a terminal sink.** No verdict brings a retracted claim back;
the replacement is a new claim, and the retraction names it.

---

## 2. Kaskada bramek wejściowych i bezpieczeństwo — Intake & Security

**Order is data, not prose.** `gates.INTAKE_GATES` is a tuple of
`(stage, name, fn)` rows; `run_intake_stage` walks them in table order and the
**first** refusal wins. Adding a gate adds a row.

| stage | row |
|---|---|
| pre-execution | `text-nonempty` |
| pre-execution | `near-duplicate-g8` |
| pre-execution | `quantifier-scope-adr007` |
| pre-execution | `paths-inv-m` |
| pre-execution | `generated-paths-adr037` |
| pre-execution | `scope-decay-adr032` |
| pre-execution | `blast-forecast-adr039` |
| pre-execution | `class-precheck` |
| **execution boundary** | *the evidence screen, then the determinism double-run* |
| post-execution | `evidence-exit-adr035` |

The execution boundary is deliberately **not** a table row: the screen decides
*whether a command runs at all*, the double-run judges *only a command that
ran*. Drawing them as peers is the misreading that decision was made against.

**Near-duplicate refusal.** Jaccard similarity over the claim sentence,
`registry.DUPLICATE_THRESHOLD = 0.6`. Override: `--duplicate-ok`.

**Unjustified quantifiers.** A sentence asserting universal scope ("nowhere",
"anywhere in the codebase") is refused unless `--scope-ok <reason>` records why
the scope is real. The stored justification decays: re-filing it verbatim after
expiry is reported by the override instrument.

**Shell safety.** Evidence commands re-execute later, in a *verifier's* session,
so they are deferred code execution across a trust seam. Two policy files govern
them, and **deny wins over allow**:

* `.truth/evidence-allow` — consumer-owned allowlist of bare program names.
* `.truth/evidence-deny` — template-owned baseline. Shells and generic
  executors are never valid evidence, even if a consumer allowlists one.

**There is no `/bin/sh` on the evidence path (ADR-041).** There used to be
two interpreters: the screen tokenized the command with `shlex`, and the
executor handed the same string to `subprocess.run(shell=True)`. Every
divergence between those two models was a channel — a newline (ADR-021), then
`uniq *` (one word to shlex, N to the shell), `cat <>F` (a *write* the `<`
branch read as input), `>1` (a file named `1` behind the fd-dup carve-out) —
and enumerating them does not terminate, because only `/bin/sh` implements
`/bin/sh`.

So the parse **is** the execution. `evidence.parse_evidence_command` is the one
reader of an evidence command; it emits a plan of argv arrays with descriptors
and glob patterns already resolved, and `shellio.run_evidence` executes that
plan with `shell=False` — plumbing pipelines, `&&`/`||`/`;`, `>/dev/null`,
`2>&1` and `<FILE` in Python. The screen
(`evidence.screen_evidence_command`) is a pass over that same plan, so the
words it checks are the words that reach `execve`.

It refuses, structurally rather than by out-guessing a shell: command
substitution (`$(`, backtick); every ASCII control character except tab (kept
after it became redundant here — the ADR-014 oracle below still runs through a
shell); `$`/`~` expansion, `&` backgrounding, `<>`, a here-document, a subshell
— constructs with no argv equivalent; paths or patterns in program position;
and any segment whose program is not on the allowlist.

Output redirection is admitted **only** to `/dev/null`, and a `>&` target is a
descriptor — both are now `subprocess` parameters rather than characters a
screen has to model. Input redirection opens read-only, by flag, so `<>` cannot
exist. Globs are expanded by the runner with stdlib `glob`, sorted, and an
unmatched pattern passes through literally, as the shell does.

**Residual, named rather than closed** (ADR-041 decision 3 claimed this was
closed; it is not): expansion still happens at run time, so
a glob whose *expansion* lands a written positional (`uniq *`) or a denied flag
is not stopped by the word-level screen. That is ADR-040's positional cap
(R1-R3), not this change; the shell had the same exposure.

**No hollow success.** A positive sentence whose recorded evidence exit signals
failure is refused at intake; absence proofs keep an advisory path. Override:
`--evidence-exit-ok <reason>`, stored on the record.

**Every refusal has a named override, and every override stores its
justification on the record.** That is what makes the bypass rate measurable
rather than invisible.

---

## 3. Cykl życia prawdy i zadań — Epistemics & Work Kernel

**A claim is born `unverified`.** The filer cannot verify their own claim: an
`agree` from the authoring session is refused. Verification means a *different
session* re-read the evidence.

Separation is enforced on session identity, not elapsed time. A refusal keyed on
elapsed time is defeated by `sleep` and would teach that bypass, so the elapsed
distribution is **reported by an instrument, never gated** — the honest limit is
that "live" sometimes means "named a verifier".

**Premise matrix.** A work item may declare ground truths as premises. Whether a
dead premise blocks starting work is tier-sensitive: a `cannot_verify` premise
blocks at `P0` and warns below it. `truth ready` applies the matrix; a ground
truth that is premise of no issue is invisible to it.

**Supersede is authority-gated.** Redirecting a premise away from a *retracted*
claim requires the human gate — `TRUTH_HUMAN` plus an id-specific
acknowledgement. Mechanical dead states stay ungated. The redirect walk resolves
to the first repeated value, so a 2-cycle returns to its start and a chain into
a cycle resolves to the cycle entry point.

**Work closes on a demonstration, not an assertion.** `issue --accept-cmd`
stores a screened acceptance oracle at birth, against `.truth/accept-allow`.
`done` executes it from the repository root and refuses the close on a failing
exit. `--accept-unsafe-ok` covers an *unexecutable* oracle and is refused for a
*failing* one. `cancel` and `reopen` skip the oracle.

**Retraction records why.** `registry.RETRACTION_CAUSES`:

| cause | meaning | successor |
|---|---|---|
| `restated` | same substance, new record | **required** |
| `expired` | it WAS true and the world moved past it | optional |
| `wrong` | it was never true | optional |

Retraction is refused while a file in `.truth/citation-scope` still cites the
id: swap the citation to the successor first. Override: `--orphan-ok <reason>`.

---

## 4. Reproduce-on-Read i samoregulacja — Verification & Health

**Direct measurement beats the proxy.** A claim's evidence capsule stores the
command, the output hash and the return code. `truth reproduce` re-runs every
live capsule and compares. On this repository that costs **~8 ms per capsule**
— half a second for the whole live ledger.

**Capsule coherence.** An `agree` filed over an output that no longer matches
the stored capsule is refused: the verdict would silently orphan the evidence it
claims to rest on. Either file `--refresh-evidence <reason>`, which stores the
observed capsule and says why the sentence survived the change, or file
`diverge` and let a human judge. This is the difference between "I re-read it"
and "I re-read something else".

**Recipe quality is the aperture, and it is not enforced.** A recipe that counts
lines (`grep -c`) cannot detect a value change; one that hashes a whole file
diverges on a comment. The screen guarantees the command is *safe* and
*deterministic*, never that it is *informative*. That judgment is the filer's,
and no gate substitutes for it.

**Every mechanical gate here is syntactic; the only semantic instrument is a
human.** The paragraph above states this for recipes, and it is not a property
of recipes — it is the shape of the whole gate layer. Prefix checks, JSON Schema,
glob matching, token sets, Jaccard similarity, hash equality, the reachability
sweep's invoker grep: all of them read FORM. Meaning is judged in exactly one
place, the verdict, and a verdict is a person.

Naming that gap turns blind spots from discoveries into predictions. The
question to ask of any gate is: **at what level does the defect live, and at
what level does this instrument read?** The distance between the two is the
residual, and it is disclosed rather than closed — more grep does not climb a
level.

The instance worth memorising, because it has now happened twice: **a textual
gate can pass on its own retirement notice.** A `doctor` row greped
`post-merge` for a verb name and matched the comment explaining that the verb
had been removed, reporting the invariant enforced over a hook that enforces
nothing. A claim reproduced green for weeks on the prose retiring the verb its
sentence named. A grep cannot tell an assertion from its obituary, because that
difference is one level above where a grep reads. The operational test is one
question: *would deleting the thing this gate guards make it stop passing — or
start passing, on the note announcing the deletion?*

**It happened a third time, and the third time named the rule.** The same row,
re-aimed from the retired verb to `truth reproduce` at `pre-push`, kept the
one-hop grep and so inverted its own error: this repository's `pre-push` ends
`exec bash scripts/release-battery.sh`, the battery runs the verb and blocks on
its exit 7 — an armed gate, reported FAIL. Meanwhile `pre-merge-commit`, which
shares the `pre-commit` body by delegation, was still passing on the word
`check-truth` in the comment describing that delegation. One check, one wiring,
both errors at once. The correction is not a better grep but a stated position
on what the check examines: **the gate is the composite hook + runner + verb,
not the hook file**, and the needle must appear in an INVOCATION — a non-comment
line of the hook, or of a file it hands off to, one hop. `doctor` now renders
the resolved chain (`.githooks/pre-push -> scripts/release-battery.sh`), so the
row reports where the verb runs instead of asserting the file contains it. The
residual is named and kept: at the leaf this is still a substring test, so use
and mention remain indistinguishable there, exactly as the reachability sweep
says of its own edges. The mereology moved up a level; the semantics did not
(ADR-054).

**A number that justifies a decision needs a recipe, exactly as a claim does.**
This system's entire thesis is that a belief must carry a reproducible capsule.
The measurements that justified its own architecture carried none, and it showed:
during the refactor that produced this chapter, one metric summed per FILE what
is emitted per CLAIM (overstating a total by 40% while understating its ratio
threefold), and another argued from a 200-commit window for a gate whose
threshold is measured over 30 days. Both survived review and were caught only by
recomputation. Two rules follow, and they are the same rule twice: state how a
governing number was produced, and **when the regime changes, re-measure the
motivation and not only the code** — a conclusion can outlive the evidence that
earned it, and usually looks strongest exactly then.

**No dead metadata.** A payload field is admitted only if the fold or a blocking
gate reads it. The rule is measured, not asserted: an AST sweep
(`instruments/field-consumers.py`) reports any key the ledger carries that
nothing reads — and distinguishes a real read from a mere presence test, because
a field whose only consumer asks whether it exists could have been a boolean.

**One projection, and it ships.** Every number describing this ledger's health
comes from `health_report()` — a single fold, composing the pure functions that
already own each number. The rule it enforces is not "one file" but **one
implementation per measurement**: a second function computing override velocity
or churn would drift from the first, and the drift would be invisible because
both would look authoritative.

The correction it embodies is worth stating plainly, because it reverses an
earlier decision of this system. Tiering (the 2026-08 migration) moved five pure
ledger projections out of the CLI into meta-repo instruments — and the
meta-repo's instruments are **not templated**. A generated repository could see
its claim counts and its queue, and nothing else: no override velocity, no
verifier-separation evidence, no churn report, no retraction causes, no staling
breakdown. The measurements that say whether a ledger is being operated honestly
existed only in the repository that ships the tool. `truth health` is where that
asymmetry ends: the same sections, in the consumer's own CLI. The instruments
that remain in the meta-repo are the two that sweep SOURCE rather than the
ledger — the payload-key AST sweep and the arm index — and that is the line: a
projection over records ships, an analysis of this repository's own code does
not.

**A health view reports; it does not refuse.** Every surface that blocks already
exists and owns one question — the commit gate, the intake table, the
reproduction sweep's exit codes, the release battery. A second blocking surface
over the same facts would be a second place to disagree about them, and the
disagreement would be silent because both would be "the gate". So `health`
carries `ok` and `warn` and no `fail`, and its thresholds are the ones already
on record rather than new limits arriving under the authority of looking
official.

**A section that was never computed says so.** Reproduction executes recorded
commands, so no pure projection can perform it; the section is `null` and the
signal reads "not run" rather than reporting zeros. This is the same rule as the
one below, applied to a *view* instead of a gate: the difference between "clean"
and "unmeasured" is the whole value of the report, and a view that blurs it is
worse than one that omits the section.

**Sensors that cannot run must scream.** A check that degrades to a zero count
reads as "clean" and is worse than no check. Health gates fail loudly when their
inputs are unavailable, and a sweep that examined nothing is a failure, never a
pass.

---

## Where the arguments went

The 54 decision records that argued for the rules above live in the machinery's
own repository and are being retired out of the shipped template. They are
history, not documentation: they record how these decisions were reached,
including the ones later reversed. Nothing in the shipped template depends on
them — this document is the contract.

If a rule here looks wrong, the fix is to change the code and this document
together — not to reopen the record that proposed it.
