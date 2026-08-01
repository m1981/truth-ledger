# Field notes — the coverage session (2026-08-01)

> Dated session record, not a contract. Excluded from `fact-health` by the
> `docs/field-notes` scope rule, which means **its citations are not swept
> and will rot**. Read it once, verify anything you intend to act on, and
> do not treat a number here as current. The live sources are the ledger,
> the work queue, and the ADRs — this file is a pointer, not a second home.

## Read this first

Everything below was produced in one session on 2026-08-01, which started
at `92bd641` (v0.9.25) and ended around `debc0ee` (v0.9.26). Two releases
shipped, a proposed patch was rejected, a tripwire was recalibrated, and a
coverage audit found the enforcement layer was largely outside the
enforced set. The most important finding arrived last and is **not fixed**.

Before trusting any of it:

```
scripts/truth doctor                       # wiring
bash scripts/fact-health.sh                # prose citations
scripts/truth queue                        # what wants judgment
scripts/truth ready                        # what is startable
scripts/truth impact --inverse | wc -l     # files no claim watches
PYTHONPATH=~/.cache/truth-ledger-pylib \
  bash scripts/release-battery.sh          # the push-boundary checks
```

That last one matters: **`python3` on this machine cannot import
jsonschema** (Homebrew python@3.14's pyexpat is broken, so `pip` itself
fails). A pip-less wheel lib is cached — see `.local/machine.md`, which
has the one-line remedy. Without it the battery blocks with exit 2 and
half the schema contract is unverified.

## The one finding that should shape the next session

**Verifier independence is a self-declared string, and the ledger holds
no evidence of it.** `session()` returns whatever `TRUTH_SESSION` says.
ADR-010's author≠verifier gate compares those strings, so it has never
fired — measured over 133 first-agree pairs, zero same-session agrees
exist. Median author-to-first-agree is 3.3 minutes; 33 are under a
minute; the fastest is **0.282 seconds**, author `operator-gates-implementation`,
verifier `verifier-v0922-sweep`. No fresh session judged a claim that had
existed for a third of a second.

Reproduce it: pair each claim record with its first `agree` verdict
(`payload.claim` links them) and diff the timestamps.

This is a different shape from everything else in the backlog. Sentinels,
the release battery and ADR-042's liveness rule all check **artifacts**;
this defect lives in **who ran what**, which no artifact check can see.
`wk-0691c742` names the neighbourhood ("nothing checks the checkers") but
was scoped to sampling. It should probably be rewritten as *make
separation evidenced rather than declared* — and the honest answer may be
that independence is a process property the paper should disclose as
such, rather than a mechanical one. That is a decision for the operator,
not a task to pick up.

The same shape recurs wherever a property crosses a boundary the process
cannot see across: `TRUTH_HUMAN=1`, `TRUTH_HUMAN_ACK`, `TRUTH_SELF_VERDICT`,
and doctor's self-certified CI arm.

## What shipped, and where to read it

- **v0.9.26 / ADR-040** — the evidence allowlist was audited per program
  for the first time; `rg`, `file` and `date` removed (they execute
  programs, write files, set the clock) and added to doctor's grey zone,
  which is the half that reaches consumers whose own allowlist copier
  never clobbers. ADR-040's Residuals section lists R1–R4, all still open.
- **ADR-041 (PROPOSED)** — shell-free evidence execution. Not built. It is
  the prerequisite for anything that widens automatic execution, and the
  three write channels it names are demonstrated, not theoretical.
- **ADR-042 (PROPOSED)** — check liveness: a check's result is
  `(verdict, coverage)`, and a check that examined nothing fails. Not
  built. `scripts/release-battery.sh` is the worked reference.
- **The release battery** — the content-judging checks now run at the push
  boundary instead of when someone remembers. Its regression gate is
  `scripts/test-release-battery.sh`.
- **Guard-rail sentinels** — the control surfaces (`.truth/*` policy files,
  the hooks, the whisper deny list, fact-health, the battery, the harness
  wiring) each carry a `sha256sum` claim, so editing one forces a human
  verdict rather than staling silently.
- **Two dark gates armed** — `.truth/citation-scope` and
  `.truth/generated-paths` were never committed, so ADR-036 and ADR-037
  had been reporting clean over zero files since they shipped.
- **fact-health recalibrated** from 108 failures (~93% noise) to 0, on
  three scope rules documented in the script's own header.

## The backlog

Twelve work items, filed 2026-08-01. `scripts/truth ready` lists them
flat — **no `--deps` are wired**, so the ordering below lives only here
and in ADR-042's sequencing section. Wiring dependencies would make the
queue enforce it.

| # | id | what |
|---|---|---|
| 1 | `wk-590356b2` | accept + implement ADR-042 (check liveness) |
| 2 | `wk-ec243a48` | give audit fields a consumer (`reaffirm_cleared` first) |
| 3 | `wk-9ede9268` | implement ADR-041, landing R1–R3 in the same pass |
| 4 | `wk-d1f6ac53` | the refs sweep: one resolver replacing five bespoke pins |
| 5 | `wk-97e27acf` | refuse version/count literals at intake |
| 6 | `wk-f64d3a43` | formal supersession (fold change — full ADR-016 treatment) |
| 7 | `wk-71dcd73c` | advisories earn loudness: response counters + demotion |
| 8 | `wk-71694410` | mutation discipline: no arm credited until seen red |
| 9 | `wk-36066db9` | refusal messages must not teach their own bypass |
| 10 | `wk-0691c742` | verifier quality — **see the finding above; rescope first** |
| 11 | `wk-d8a1d61c` | the sentence-altitude genus, closed procedurally |
| 12 | `wk-24ae8ff4` | fleet state gets a trigger instead of a timer |

Each item's `--text` carries its own implement-and-validate plan; read it
with `scripts/truth issue --json` or straight from the ledger. The
validation halves are the part worth preserving — several are designed to
be able to fail (item 10 states its own kill condition; item 8 expects to
find real vacuous arms and says to suspect the harness if it finds none).

Order rationale: make darkness visible (1, 2) before building more
machinery that could go dark; close the execution channel (3) before
anything widens automatic execution; consolidate (4) before migrating;
then the attention economics (5, 6, 7).

## Traps this session actually fell into

Not hypotheticals — each of these cost real time here.

1. **The author is the worst judge of their own work.** A drafted screen
   patch passed 235 canary arms and was then broken three ways by a red
   team. A regression arm I wrote was vacuous and an independent reviewer
   caught it. Dispatch adversaries; do not self-certify.
2. **A green suite proves you tested what you thought of.** Prove new
   arms red against a mutated copy — and then *read the mutation output*.
   Mine showed arms 5 and 6 never reddening and I missed it.
3. **`set -e` does not restore errexit.** It enables it. That silently
   killed a test suite mid-run here.
4. **Sentences outrun their evidence.** One claim was falsified by four
   successive verifiers, each finding a different stale stamp — the fourth
   created by the third's fix. It ended only by cutting the sentence to
   what its two greps prove.
5. **Restated counts rot.** "33 ADRs", "17 ADRs", "176-entry glossary" all
   went stale. Cite an id or state no number.
6. **The quantifier gate matches substrings.** "read-only" contains
   "only"; a claim was refused for a word in its explanation. Rewording to
   satisfy it is compliance theatre — that is `wk-36066db9`.
7. **Pin the logic, not the wrapper.** A sentinel on `.githooks/pre-commit`
   left `check-truth.sh` — where the logic lives — unwatched.

## Loose ends

- `tr-99113e85` (the battery sentinel) is `unverified`; reaffirm correctly
  refuses to auto-confirm a first verification. It needs a dispatched
  verifier, as do the three sentinels filed last.
- `tr-f788e062` is **self-diverged**: its sentence claimed six arms proven
  red when only four were. Fixed in the script; the claim needs a
  successor.
- `docs/roadmap-v3.md` declares "Status: living document" but reads as
  finished history. Either it returns to the sweep (~19 citation fixes) or
  its header should say what it is. Fixing the header is the cheaper truth.
- The three `template/.github/workflows` are inert here (wrong location
  for this repo, correct for consumers), `spec-health` resolves zero
  files, and doc-health's pattern arm has no patterns file. All three are
  ADR-042's genus and none is catalogued in it yet.
- Deployment facts still have only a TTL. A claim asserting the pilot was
  at v0.6.4 was wrong by twenty releases; nothing here could see it.

## How to pick up

Start with `scripts/truth ready` and the table above, not with this file.
If you change anything under `docs/` or `template/.truth/README.md`,
AGENTS.md requires an independent reader before the commit lands — that
rule caught three real defects today and is not ceremony.
