---

1 RECONSTRUCTION

Written from artifacts alone and committed to disk (scratchpad/RECONSTRUCTION.md) before I opened README.md, AGENTS.md, or any document under docs/.

The sortals

.truth/claims.jsonl, 4765 records, 0 unparseable, one envelope shape for all 4765: {actor, id, kind, payload, session, ts}. Five kinds are instantiated — verdict 2304, invalidation 1997, claim 268, issue_event 103, issue 93. truth vocab declares seven (registry.py:144): premise and contradicts have zero instances. The declared set properly includes the instantiated one; that is a refutation of "the vocabulary describes the ledger" read as set equality, and it is mechanical, not interpretive.

The id prefix is itself a sortal marker: wk- on all 93 issues, tr- on everything else — including issue_event, which is about a wk- object but carries a tr- id.

Status is derived, never stored

kernel.fold(events, now_dt=None) sorts by fold_key = (ts, id, canon) and replays. Nothing writes a status. Running the fold directly against the real ledger gives live 66, retracted 151, unverified 31, diverged 20 = 268 = the claim count, so status is a total function on claims.

Three consequences I verified by execution, not by reading:

- invalidation is wholly inert. kernel.py:339 is elif kind == "invalidation": if ttl_invalidation(p): continue — and nothing follows. Both arms are a no-op. 1997 of 4765 records (41.9%) contribute nothing to any derived state.
- stale is reachable from no record. It is a projection over (claim ts, ttl_days, now_dt), computed at read time. Only 26 of 268 claims carry a non-null ttl_days.
- now_dt=None means "do not ask the clock." A claim's status is a function of when you ask.

Two things are called "verified", and the system keeps them apart

evidence_class is a property of the capsule; status is a property of the claim. Cross-tabulated over all 268:

             diverged   live  retracted  unverified
INFERRED            0      0          1          15
UNVERIFIED          0      0          4           5
VERIFIED           20     66        146          11

VERIFIED × unverified = 11 is non-empty, so these are two sets, not two names for one. Also measured: zero claims carry evidence_class=VERIFIED with no capsule. That is a real division at a joint, and the system holds it.

Rule of recognition — partial, and only for one sortal

gates.py:454 INTAKE_GATES is 11 rows, first-refusal-wins, and it gates truth claim only. cmd_verdict (cli.py:277) runs its own ad-hoc argument checks, not the table. issue has neither. There is no single rule saying what counts as a record of this system — there are three admission regimes by kind plus a fourth path, appending to the file.

The one rule that reaches every record is check-truth.sh (INV-A prefix extension + INV-B schema). I broke it in a scratch copy and restored byte-identically (sha256 842fc85e… before and after):

┌────────────────────────────────────────────┬─────────────────────────────────────┐
│                  mutation                  │                exit                 │
├────────────────────────────────────────────┼─────────────────────────────────────┤
│ untouched staged ledger (negative control) │ 0                                   │
├────────────────────────────────────────────┼─────────────────────────────────────┤
│ mid-file edit, one character               │ 1 INV-A                             │
├────────────────────────────────────────────┼─────────────────────────────────────┤
│ mid-file edit, flip a verdict              │ 1 INV-A                             │
├────────────────────────────────────────────┼─────────────────────────────────────┤
│ delete a line                              │ 1 INV-A                             │
├────────────────────────────────────────────┼─────────────────────────────────────┤
│ mid-file insert                            │ 1 INV-A                             │
├────────────────────────────────────────────┼─────────────────────────────────────┤
│ append with bad id shape                   │ 1 INV-B (id does not match tr-hex8) │
└────────────────────────────────────────────┴─────────────────────────────────────┘

INV-A is real and fires. It says nothing about whether a record could have passed the intake gates.

Derivation order

L0 code and tree → L1 append-only ledger → L1′ status = fold(L1, now) → L2 policy files under .truth/ → L3 prose citing tr- ids, policed by fact-health.sh (31 citations, 13 foreign) → L4 instruments → L5 release-battery.sh at pre-push.

Self-reference, stated rather than accidental

171 of 268 claims (64%) name the apparatus in their own evidence_paths. Exactly one claim's evidence command reads the file containing it: tr-d0759df4, grep -c '"verdict": "retracted"' .truth/claims.jsonl — its text asserts 49, the command returns 151 today, its evidence_paths is [], and its status is unverified. Object and metalanguage are layered deliberately: the fold is pure, the clock is a parameter, and scripts/epistemic-isolate.sh exists specifically to hand a judging run an instrument it did not author. Whether that layering holds is section 3. Following Franzén, I draw no conclusion about self-limitation from the presence of self-reference; the layering here is stated, and the interesting question is only whether it is wired.

What I could not determine

Whether the 1997 inert records await compaction; whether premise/contradicts are dead vocabulary or template surface for consumer repos; and — load-bearing for section 3 — what "check" means, because gate-reachability.sh partitions on that word and nothing in the executable surface defines it.

---

2 DELTA

The reading order is broken at item 3 of 3. README §"Reading order" sends you to template/docs/adr/truth/ for "Fifty-two records". That directory does not exist — removed by commit 687dbdc ("archive 54 ADRs to docs/archive/adr/"). docs/machinery-atlas.md, also named, does not exist either. Document wrong, mechanism moved.

The README's headline sentence describes a mechanism that was deliberately removed. Line 5: "commits that touch the evidence mechanically demote the fact to stale before anyone trusts it again." Measured: .githooks/post-commit is exit 0 with a comment saying it no longer writes; no code path writes an invalidation record; the last such record is dated 2026-08-16 while the ledger runs to 2026-08-24; and the fold's invalidation branch is inert. Document wrong, and knowingly so — the post-commit hook's own comment gives the measurement that retired it (PPV 3.6%).

docs/registers.md and I independently reached the same ontology, and it got there first. It states the ISO/IEC 11179 move (the registry is registered), it distinguishes "currency evidence" from "is fresh", and it says plainly: "Not checked: whether the mechanism a cell names is wired into any gate… A cell can therefore name a live path and still be a promise nobody keeps." It then delegates that question to scripts/gate-reachability.sh. That delegation is the subject of finding 1 — they are not describing different things, the delegate simply cannot answer.

ADR-060 already names my norms-vs-descriptions finding, and names it better than I did. It splits a normative sentence carrying a falsifier (an article, which gets a gate) from one that does not (a recital, which "stays prose and nothing polices it"), and it reports its own measurement: §1: 18 paragraphs | carrying a normative modal: 13 | citing no position: 3. The README sentence above is exactly a recital. README.md is inside .truth/citation-scope, so fact-health.sh reads it — but that machinery polices citations, and a false sentence that cites nothing is invisible to it by construction. Document and mechanism agree; the gap between them is stated and accepted.

Where I was wrong about the ADR tail. labels-deps and my own grep agree that ADR-054…062 — nine consecutive decisions — have zero ledger records, while ADR-040…053 have 1–31 each, and that 45 claims were filed the same week. I was building this into a finding about a stopped practice. docs/registers.md refutes it: the ADR register is explicitly "docs/decisions (live, 054+) and docs/archive/adr (frozen, 001–053)", and ADR currency is measured by register-index.py check (b) and by arm-index prose hashes — not by ledger records. Ledger coverage of an ADR is incidental. The discontinuity is a directory boundary, not a lapse. Finding withdrawn.

---

3 FINDINGS

Ranked by what breaks if untreated.

F1 — The dark-gate sweep reports a closed-world verdict over an open-world population

gate-reachability.sh:91 builds its population from a hardcoded roster of eleven globs, three of which are literal filenames. Its own comment two lines above reads "enumerate, never hardcode — … A hardcoded roster is the same defect one level up: it falls behind in silence, and the sweep reports 'all reachable' over a list that stopped growing." The roster is exactly that, one level of indirection out: it enumerates files but hardcodes patterns.

Twenty-two tracked files in scripts/ and instruments/ fall outside it, including 10 of the 13 instruments. The sweep then prints examined 14 check(s), 14 reachable, 0 unreachable, 0 opted out and the battery renders it as every one reached by a root — a universal quantifier over a set built by search.

Reproducer (run in a scratch copy):
sed -i 's#scripts/retracted-figures.sh#scripts/DISABLED-retracted-figures.sh#g' \
    scripts/release-battery.sh Makefile
bash scripts/gate-reachability.sh; echo "EXIT=$?"
# -> gate-reachability: examined 14 check(s), 14 reachable, 0 unreachable, 0 opted out
# -> EXIT=0
retracted-figures.sh is a genuine check — it emits findings and the battery parses its summary and exit code at release-battery.sh:151-162. Unwired from every root, the sweep stays green.

Observation that would have refuted it: that the gate is vacuous or unreachable and never fires at all. Sought and not found — the positive control fires correctly: renaming instruments/label-coupling.py (which is in the roster) yields 13 reachable, 1 unreachable, exit 1. The mechanism works; the population is wrong.

The bundle this condemns (Duhem–Quine): not gate-reachability.sh alone, but the conjunction of its glob roster, the empty-means-armed reading of .truth/reachability-opt-out, and docs/registers.md's delegation of the wiring question to this sweep. Of the five instruments registers.md names as currency evidence, three — register-index.py, waiver-index.py, check-truth.sh — are outside the population, so the document's one escape hatch ("that is a separate question, answered by gate-reachability.sh") points at an instrument that cannot see them.

This is where I caught myself monster-barring, and I name it because the repair move is available to the reader too: when epistemic-isolate.sh turned out to be unreachable, the tempting reply is "it is not a check, so it is not in the population." Nothing in the executable surface defines "check". .truth/reachability-opt-out carries the descriptive sentence "every check in this repository is reached by a root today" — a claim whose truth depends entirely on a word the mechanism never defines, sitting inside a policy file, where being a decision protects it from measurement.

Shape, not defect (Wittgenstein, PI 143–242): the roster is a rule applied by matching examples, and no finite list of globs fixes the next case. Adding register-index.py to line 96 makes the report true tomorrow and false again the first time somebody writes instruments/whatever.py.

F2 — epistemic-isolate.sh reverts and stages seven core modules, and nothing restores them

scripts/epistemic-isolate.sh:88 runs git checkout origin/main -- template/truthlib scripts/truth .truth/evidence-allow. That mutates the working tree and stages it. Its header states the design plainly: "CALLER CONTRACT: restore the working tree when you are done… This script deliberately does NOT restore on its own exit." It also states "WHERE THIS RUNS: nowhere yet, deliberately" — and I confirmed that: no hook, no battery arm, no Makefile target, no .claude/settings.json entry references it.

So the only way it can currently run is by hand, and run by hand it leaves seven modules reverted to origin/main and staged for commit. origin/main is 7252d30, behind HEAD by 7 files changed, 183 insertions, 346 deletions.

I hit this myself. I ran it, then ran the canary, and got 287 caught, 3 missed — all three misses in the read-time TTL arms. I had a finding drafted. It was my own contamination: the reverted kernel.py has no ttl_expiry and its fold takes no now_dt, so HEAD's canary was testing HEAD's expectations against origin/main's implementation. On a pristine copy: 290 caught, 0 missed, exit 0. The finding died; the hazard that produced it did not.

Observation that would have refuted it: that the script restores on exit, or that a caller wires it with a trap. Sought and not found — no caller exists, and the header says non-restoration is deliberate.

F3 — The README's first description of the product is false, and is structurally unreachable by the freshness machinery

Covered in section 2. README.md line 5. Reproducer: cat .githooks/post-commit (it is exit 0); sed -n '339,341p' template/truthlib/kernel.py (the inert branch); and

python3 -c "import json;i=[json.loads(l) for l in open('.truth/claims.jsonl') if l.strip()];\
i=[r for r in i if r['kind']=='invalidation'];i.sort(key=lambda r:r['ts']);print(i[-1]['ts'])"
# -> 2026-08-16T23:33:44.867505+00:00   (ledger runs to 2026-08-24)

Observation that would have refuted it: some other writer of invalidation records, or a path-touch route to stale. Sought and not found — grep -rn '"invalidation"' template/truthlib/*.py returns readers only (evidence.py, reports.py, the registry constant, the inert branch).

F4 — The stated reading order's third document does not exist

template/docs/adr/truth/ and docs/machinery-atlas.md are both absent. find template/docs -maxdepth 2 shows the tree; git log --diff-filter=D -1 -- 'template/docs/adr/truth/*' names commit 687dbdc.

Refuting observation sought and found partially: I expected the 78 claims whose evidence_paths name template/docs/adr* to be a live tripwire pointing at nothing. All 78 are retracted (75) or diverged (3); zero are active. And across the whole ledger, active claims whose watch pattern matches no tracked file: 0. The path-hygiene concern is dead; only the README text is wrong.

F5 — Three live claims no longer reproduce; this is reported, blocking, and outstanding

python3 template/scripts/truth reproduce → exit 7, 66 live claim(s) — 63 reproduces, 3 capsule-stale: tr-4df1a9fd, tr-56a8e36c, tr-d0191e65. The battery treats exit 7 as FAIL (release-battery.sh:358), so a push is blocked. Recorded as state, not as a mechanism defect — the mechanism did exactly what it should.

Hypotheses of mine that died

Four, and they are the evidence that this audit could have been wrong:

1. Read-time TTL is broken (canary 3 missed) — my own contamination via F2. Pristine run: 0 missed.
2. The integration suite is red — my snapshot was torn across a concurrent editor's in-flight edits: all four waiver-cluster files changed under me mid-copy. The live suite is green at 55 tests. I excluded that entire cluster from findings.
3. 78 claims watch a deleted directory — all 78 inactive; zero active claims watch a dead path.
4. The ADR tail abandoned ledger backing — refuted by docs/registers.md; the boundary is a documented register split.

A fifth was vacuous rather than wrong: my first INV-A mutation edited line 100 expecting a verdict, but line 100 is an issue record with no verdict field, so cmd compared identical bytes and passed. A check that "passes" because the mutation never happened is the failure mode the whole severity lens exists to catch, and I caught it in my own test before reporting it.

Lenses that failed to apply

Searle's constitutive/regulative split found nothing measurable here. The natural candidate — the waiver register, which is precisely a list of "X counts as lifting gate Y in context C" — was under active edit by a parallel agent throughout, and I excluded it on evidence rather than reason about it. I have no measurement, so I claim nothing.

Mayo's severity applied only in its crude form. I broke things and watched for red, with positive controls. I did not quantify severity or establish that any check probes a space of errors rather than the one I happened to seed.

Franzén applied as a restraint and produced no finding — which is his purpose on the list. There is abundant self-reference here (64% of claims are about the apparatus), and the correct reading is layering, which is stated in epistemic-isolate.sh's header and in the fold's clock-as-parameter design. I record that I found nothing about incompleteness because there is nothing there to find.

Strawson and Lowe reduce, here, to Aristotle. The sortal analysis paid off (evidence_class vs status), but nothing distinctively about criteria of identity or individuation added anything the kind census had not already given me.

---

4 WHAT WOULD BE BETTER

(a) Defects to repair. README line 5 is false and README's reading-order item 3 points at two absent paths — both are text edits against measurements already in this report. epistemic-isolate.sh should refuse to run unless it detects a caller trap, or should restore on EXIT and let a caller opt out; leaving a hand-run in a staged-revert state is a footgun with no upside, and the fail-closed philosophy stated in its own header argues for it.

(b) A mechanism whose shape is wrong. gate-reachability.sh's population. It cannot be fixed by adding globs, because the roster is a list of examples and the next case is always outside it. The shape that would work inverts the question the way test_every_instrument_is_classified already does for instruments/ — that test is a genuine partition, checked in both directions, with unclassified forced to zero, and it is fifteen lines. The same move here means: enumerate every executable under scripts/, instruments/, template/scripts/, require each to be classified as check-or-not in a committed file, and fail on anything unclassified. The repo has already built this shape once and knows it works; the reachability sweep predates it.

(c) Absent, with the cost named. There is no rule of recognition covering verdict and issue records — no gate table, only ad-hoc argument checks in cmd_verdict. Building one means a second INTAKE_GATES-shaped table and its canary arms: on the evidence of the existing table, a few hundred lines and a week. I judge that cost not worth paying. Verdicts are the cheap, reversible half of this system — diverge and cannot_verify are recoverable, only retracted is terminal and it already has ADR-049's ceremony — and the gate table exists because claims are the expensive, load-bearing assertion. Adding symmetry for its own sake would buy uniformity, not safety.

What this system cannot detect, by construction (Leveson): a check that no root invokes and whose filename does not match one of eleven globs. That is not a hypothetical class — retracted-figures.sh is in it today, and the experiment in F1 shows it can be silently unwired. "The component met its specification" is exactly what gate-reachability.sh reports.

---

Two operational notes, outside the findings. A parallel agent edited this repository throughout the audit — one measurement flipped from red to green under me with no action on my part, so everything above is pinned to HEAD 553171d with the finding-relevant files verified byte-identical to the live tree at report time. And I never staged, committed, or modified anything in your repo; every mutation ran in scratchpad/, with the ledger restored to sha256 842fc85e….