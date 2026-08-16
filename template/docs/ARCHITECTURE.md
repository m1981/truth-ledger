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

The screen (`evidence.screen_evidence_command`) is a static pass over a
**quote-aware** token stream, and it is the only thing standing between the
ledger and `/bin/sh`. It refuses: command substitution (`$(`, backtick); any
ASCII control character except tab (a newline is `/bin/sh`'s statement
separator but word-whitespace to the screen's lexer — the tokenizer mismatch
that would smuggle an unscreened command); paths in program position; and any
segment — after `;`, `&&`, `|`, `&` — whose program is not on the allowlist.

Output redirection is admitted **only** to `/dev/null`. A digit is a valid
target after an fd dup (`2>&1`) and never after a plain `>`: they used to share
a branch, and `cat f >2` then wrote a file literally named `2`.

Input redirection is read-only and allowed, any source.

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

**No dead metadata.** A payload field is admitted only if the fold or a blocking
gate reads it. The rule is measured, not asserted: an AST sweep
(`instruments/field-consumers.py`) reports any key the ledger carries that
nothing reads — and distinguishes a real read from a mere presence test, because
a field whose only consumer asks whether it exists could have been a boolean.

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
