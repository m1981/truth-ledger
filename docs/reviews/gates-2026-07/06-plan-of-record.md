# Target architecture and algorithms — plan of record

> Reader: the truth-ledger operator | Basis: rev-2 + rev-3 fixes +
> architecture review, refined by a 14-agent structured review
> (7 lenses × ≤5 findings, top finding per lens adversarially
> verified by an independent skeptic; novelty rule barred re-reporting
> known findings) | Verification bill: 4 top findings CONFIRMED,
> 3 REFUTED (residuals kept); unverified findings carried as
> PLAUSIBLE and marked | Date: 2026-07-31.

## 0. The review process that produced this plan (reusable)

Seven single-lens reviewers (corpus coherence, CLI contract, core
purity/testability, degradation matrix, performance, security,
migration/rollout), each returning ≤5 structured findings
(component, claim, severity, evidence, fix), each forbidden from
repeating anything already in the plan documents. Each lens's top
critical/major finding got a fresh adversarial skeptic instructed
to refute (default-refuted on weak evidence). Confirmed findings
bind this plan; refuted ones land in §7 with their residuals so no
future review re-litigates them. Pipeline, no barriers; all agents
read-only.

---

## 1. Structural invariants (the spine of the target architecture)

The review's strongest result: most confirmed defects are instances
of four cross-cutting invariants that must exist as *rules with
faults*, not per-gate fixes. They become the opening section of the
gate-system ADR.

**SI-1 — One glob grammar, everywhere.** No git verb ever receives
*any* CLI-owned glob (evidence paths, citation-scope, generated-
paths) as a pathspec. Git is invoked bare; the core filters results
through `match_paths()`. Rationale, now thrice-proven: git `*`
crosses `/` (v0.4 over-invalidation; rev-2 dirty-watch; and the
review's CRITICAL find — a citation-scope line written as
`:(exclude)…` or `:!…` silently *inverts* the sweep to
everything-except, and a typo'd scope exits rc=1, byte-identical to
"clean", so the fail-closed tombstone gate fails open). Policy-file
loaders additionally refuse any line starting with `:`/`-`/`!`.

**SI-2 — Subprocess discipline for name-emitting git.** Every gate
subprocess runs with `cwd=repo_root()` (CONFIRMED: `git grep` from
`template/` finds nothing, rc=1 = "clean", and the retracting human
is mid-ceremony in an arbitrary terminal cwd; the CLI passes `cwd=`
on only 3 of 13 subprocess sites today). Name-emitting verbs use
NUL/unquoted output: `git status --porcelain=v1 -z`,
`git log --name-only -z --no-renames` or `-c core.quotepath=off`
(CONFIRMED: kuchnie has 27 tracked filenames git octal-quotes today
— `match_paths` can never match a C-quoted string, so dirty-watch
and blast would go silent on real pilot files; `--no-renames`
mirrors the recorded `changed_files_since` lesson). Exit-code
semantics are pinned per verb in the ADR text — for `git grep`:
0 = hits, 1 = clean, ≥2/spawn-failure = unavailable→refuse.

**SI-3 — Advisories are a contract, not decoration.** CONFIRMED
(the QB-011 rhyme): the plan multiplied advisory classes while
keeping them stderr-only — the exact channel a `tail -1` capture
already swallowed once. Target: under `--json`, stdout carries
`{"record": …, "advisories": […]}`; without it, every advisory line
gets the stable prefix `truth: advisory:`. Every claim-derived
substring (paths, command tokens, git-emitted names) renders
through the house `!r` convention — INV-M refuses only whitespace,
so ESC bytes survive intake and raw interpolation would allow
terminal-escape injection into the advisory block and spoofing of
injection-asserted canary strings.

**SI-4 — Policy-file semantics.** Both new files are consumer
policy: `_skip_if_exists` in copier.yml — and the plan's cited
precedent must be *corrected, not copied*: `accept-allow` is
NOT in `_skip_if_exists` today (CONFIRMED; kuchnie carries a
16-line local policy block in it that a template-side edit would
merge over — a live pre-existing bug, fixed in the same release).
Absent vs committed-empty are distinct states with distinct
meanings: **committed-empty = consciously configured = fully
silent; absent = built-in default applies, one-line notice**
(CONFIRMED: rev-2's "absent or empty → notice" leaves a
zero-generated-paths consumer no reachable silent state and prints
on every path-carrying filing in all three deployments forever,
contradicting CC-1's own silence faults — which copier runs
fail-closed at scaffold). Loaders read `utf-8-sig` (a BOM turns the
first glob into dead scope silently). A non-empty scope file
matching zero tracked files prints a loud notice (dead-scope
tripwire), never a clean sweep. `citation-scope` gets an explicit
absent-file branch (default `docs/specs/**` + notice) — today it is
the only policy file whose absent case is unspecified while the
rollout guarantees that intermediate state exists.

## 2. Gate system (the target shape)

**Staged gate table.** Rows are `(stage, name, gate_fn)` with
stages `pre-execution | execution | post-execution`; the ADR-009
screen and the double-run are **stage boundaries, not rows** (the
review's flattening claim was refuted — the plan was already staged
— but the surviving residual binds: the gate-system ADR cites
ADR-029 explicitly and its whole-sequence canary fault preserves
FAULT SD's non-flat contrast rather than asserting a flat refusal
order). Gate functions are pure: `gate_fn(ctx) → Refusal | Advisory
| Silence`; the shell pre-gathers everything (`ctx` carries status
entries, log history, policy globs, rc, text tokens).

**CC-1 assembler, with the shipped-surface inventory.** CONFIRMED:
"at most one advisory block" is unimplementable without deciding
the four *existing* stderr surfaces. Target: decay notice and
hollow warning (both post-append today) fold into the block; the
commit-gate banner is **exempt with reason** (it must fire at
dispatch, even on refused filings — fail-open-with-noise is its
documented property); the FS-1 half-life note moves post-append and
folds. The budget sentence becomes: *one advisory block plus the
named exempt surfaces*. Faults: CC1 (two classes → one block), CC2
(clean filing → nothing), CC3 (JSON surface carries the block), CC4
(ESC-bearing glob renders escaped).

**Override discipline, completed.** Two confirmed/plausible gaps
close: (1) every new stored basis gets an **explicit ADR-032 decay
decision** in the ADR text — include-with-decay or
decline-with-reason (likely decline for `evidence_exit_basis`: a
differential-proof's non-zero exit is a permanent property and
re-verification re-runs the command anyway; decide
`generated_ok_basis` explicitly either way); (2) counters are
**single-homed**: `override_report` is the one load-bearing
override instrument (ADR-033); the hollow section counts
warned/refused only and *points at* the override row. Flag renamed
`--evidence-exit-ok` / field `evidence_exit_basis` (house pattern
names the overridden thing; `--exit-ok` is ambiguous on `done`).
Refusal texts cite doctrine ("a hollow VERIFIED, ADR-0xx"), never a
foreign ledger id (`tr-0e884e02` resolves to nothing in any
consumer repo — it stays in the ADR's Context). The `--orphan-ok`
mention in the tombstone refusal is decided, not implied: either
moved to `--help`/README per ADR-011's surface rule, or exempted
with the stated reason that the audience already passed the human
ceremony (one paragraph, either way).

## 3. Algorithms — final contracts

**A-1 blast (advisory + report).** Shell: one
`git log --since=<window> --name-only -z --no-renames
-c core.quotepath=off` at `cwd=repo_root()`; window applied at the
shell edge (house style per `override_report`'s "--since applied by
the shell" precedent — the purity objection was refuted; the
surviving residual is a **window-boundary negative-control arm**
using a `GIT_COMMITTER_DATE`-backdated commit: in-window counts,
out-of-window does not). Core: dedupe file lists to a distinct set,
match once via memoized `match_paths`, count commits whose set
intersects. `functools.lru_cache` on `_glob_rx` (pure; also speeds
the existing invalidation scan — the "Python hotspot" claim was
refuted at real deployment scale, but the one-liner is kept as
polish). Unborn HEAD / rc≠0 from the traversal → loud
`blast: history unavailable` notice in the block, `blast_forecast`
stored *absent*, never 0. Optional saturation cap at
10×floor with `>=N` semantics (minor; report survives saturation).

**A-2 dirty-watch.** Shell: `git status --porcelain=v1 -z` at repo
root. Core: an entry is dirty iff `XY ∉ {'  ', '!!'}` — the
structural definition, not a letter list (CONFIRMED: a letter list
misses `UU`, the both-modified conflict state — dirty *precisely
during merge/rebase conflict resolution*, the scenario that minted
QB-011); `??` entries count when the watch is a glob (INV-M refuses
untracked literals but exempts globs); rename records match either
path (NUL format emits both as separate fields, no unquoting
needed). Faults: DW1–3 as planned, plus DW4 (untracked-under-glob →
advisory), DW5 (untracked outside the watch → silence), DW6 (`git
mv` uncommitted → advisory on either path), and a unicode-named
fixture file proving SI-2 end-to-end.

**A-3 polarity.** Unchanged (empirically excellent: 244 real
filings → 5 refusals all defensible, 6 warnings all legitimate).
X6 documented as a one-directional tripwire.

**A-4 recipe lints.** The whitespace tokenizer is dropped — it
would be a *third* parser of evidence commands, violating the
recorded one-screen-parser rule (F1/F5 drift lesson) and gameable
by quote-splitting. `recipe_lints` consumes the **same shlex token
stream** `screen_evidence_command` already produces; path-context
and carve-outs (path-segment, schema-`$id`, frozen-date) are
defined per shlex token. Warnings only; constants beside lexicons
with RC faults; committed-empty `generated-paths` is silent
(SI-4).

**A-5 citation sweep — redesigned I/O boundary.** Shell:
`git grep -l -F <id>` **bare** (no pathspecs), `cwd=repo_root()`,
rc pinned 0/1/≥2. Core: filter hits through
`match_paths(scope_globs)`; `claims.jsonl` excluded structurally in
the core (avoiding the `:(exclude)` magic the pathspec design would
have forced); TG4 becomes a pure-core property test. Batch: the
carrier decision resolves to **repeated invocation + a read-only
preflight verb** — `truth citations <id>…` (no ceremony, exit 0 =
clean / N = hits, `--json`), because a multi-id ack would violate
ADR-011's one-id-per-ack principle ("a lingering environment
variable may not authorize arbitrary tombstones") and the
citations-found refusal gets its **own exit code** (the
impact/baseline precedent) so a sweep driver can distinguish it
from unknown-id, ack-mismatch, and grep-unavailable, which all exit
1 today. A 25-id sweep = one preflight pass, then 25 ceremonial
verdicts on the already-clean set. (The performance lens's
batch-verb preference was based on ledger-reparse cost — real, but
the preflight amortizes the expensive part without touching the
ceremony; note the O(ids × ledger-parse) cost in the ADR.) Faults:
TG1–5 as planned with TG5 written via the PATH-shim pattern (a
`git` wrapper passing everything through except `grep` → 128), TG6
rewritten against the preflight verb, TG7 subdir fixture (SI-2),
TG8 dead-scope notice, TG9 id-cited-only-in-claims.jsonl proceeds.

**A-6 assembler.** As in §2; refusals short-circuit at their gate,
advisories fold post-append, JSON carries the block, `!r` escaping
on all claim-derived substrings.

**Reports.** `cmd_stats` folds **once** and passes the shared
`(claims, ordered_events)` pair into all consumers (today each
consumer re-folds and re-sorts; three new sections would make five
O(n log n) passes — ~3 s at 100k records). Each consumer stays a
pure function; only the redundant sorts go.

## 4. Records and schema

New fields: `evidence_exit_basis`, `generated_ok_basis`,
`blast_forecast` (absent = not computed, never 0-as-unknown),
verdict-side orphan basis. Validate tolerates all legacy records
(the entire meta and kuchnie ledgers must pass unchanged). The
schema `$id` bumps **only where the record shape changes**
(ADR-026): four of the five gate releases; the dirty-watch release
ships no schema/mirror/FS-2 work at all — its sync surface is
stderr + docs (the CC-4 checklist is reworded accordingly; the
fingerprint test cannot catch a gratuitous bump in that direction).

## 5. Canary plan (prefix registry + new arms)

Prefixes verified free at HEAD: **DW, X, TG, RC, CC** — and **BF
replaces BL** (BL1–BL4 exist in the shipped suite; the CC-3 check
is anchored as `FAULT <prefix>[0-9]` to avoid C/CC aliasing). New
cross-cutting arms beyond the per-gate lists: the SI-2 subdir
fixture (sweep from a subdirectory still refuses), the unicode
filename fixture (DW + BF fire on a quoted-by-default name), the
ESC-injection arm (CC4), the dead-scope notice (TG8), the
window-boundary arm (BF), and the committed-empty-silence arm (RC).

## 6. Release roadmap (six releases, foundation first)

- **R0 — gate-system infrastructure** (new ADR): staged gate table
  citing ADR-029, CC-1 assembler + shipped-surface inventory,
  SI-1/2/3/4 as faults, `--json` advisory contract, single fold in
  stats, `lru_cache` polish, copier `_skip_if_exists` corrections
  (incl. the pre-existing accept-allow bug). No behavior change for
  users; everything after is a table row.
- **R1 — exit gate** (ADR-035): NEGATION_TOKENS, refusal +
  `--evidence-exit-ok`, decay decision, hollow counters
  (single-homed), X1–X7.
- **R2 — tombstone citation gate** (ADR-036): A-5 as redesigned,
  `truth citations` preflight, citation-scope with absent-branch,
  distinct exit code, TG1–TG9.
- **R3 — recipe linter** (ADR-037): shlex-token lints, carve-outs,
  generated-paths at INV-M position, RC arms.
- **R4 — dirty-watch** (ADR-034): A-2 final, DW1–DW6 (+unicode).
- **R5 — blast advisory + churn report** (ADR-038): A-1 final, BF
  arms; the refusal-gate question returns only after one field
  window of forecast-vs-observed data plus the reaffirm-trial read.

Order rationale unchanged from the audit (exit gate first: proven
defect class, smallest diff), with R0 pulled ahead because five of
the review's confirmed findings are *system* properties no single
gate release can own.

## 7. Considered and rejected (so no future review re-litigates)

1. **"The gate table flattens the ADR-009 screen into a peer
   refusal (ADR-029 violation)"** — REFUTED: the table is staged by
   design, stages are first-class data, and the pipeline already
   routes screen-refusals before execution. Residual kept: cite
   ADR-029 in the gate-system ADR; the sequence fault preserves
   FAULT SD's contrast.
2. **"Python glob matching, not git, is the per-filing hotspot;
   the cost claim is falsified"** — REFUTED: the benchmark's scale
   was fictional (its "30d window" was actually full history on a
   dormant repo; real 30-day volumes are 84–447 commits across all
   deployments, where matching costs 6–34 ms and git dominates
   10–15×, a cost ADR-038 already owns). Residual kept:
   `lru_cache` on `_glob_rx`, distinct-set matching, optional
   saturation cap.
3. **"The 30-day window is impure — TRUTH_NOW cannot steer it"** —
   REFUTED: shell-edge window application is the codified house
   style (`override_report`'s documented contract), and the
   window-boundary canary arm is writable today via
   `GIT_COMMITTER_DATE` in the sandbox. Residual kept: that arm is
   added (BF), because BLAST_WINDOW is a constant paired with
   faults and currently no arm tests the boundary.

Findings below the verified line (each lens's non-top findings)
are carried as PLAUSIBLE and are absorbed above where their
mechanism was independently demonstrable (rc trichotomy, BOM,
`--no-renames`, exit-code differentiation, one-parser rule,
double-homed counters, $id bump scope); none contradicts a
confirmed finding.
