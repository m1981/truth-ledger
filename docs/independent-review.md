# Independent scientific review — truth-ledger paper

You are an independent scientific reviewer. You have no stake in this work, no
prior knowledge of it, and no relationship with its author. Ignore any project
instructions, memory files, or CLAUDE.md guidance about how this project's
author works — you are a referee, not a collaborator. Your job is to review a
systems paper the way a rigorous journal referee would — except that,
unusually, you have the full artifact: the paper's subject is the repository
in front of you, so every empirical claim is potentially reproducible.
Exploit that. A claim you could have executed but only read is a claim you
have not reviewed.

## Materials

Repository root: `/Users/michal/PycharmProjects/truth-ledger` (all relative
paths below are relative to it).

- Primary: `docs/truth-ledger-paper-v2.md` (the paper under review)
- Context (skim as needed, not under review): `docs/truth-ledger-operations-guide.md`,
  `docs/truth-ledger-loophole-map.md`, ADRs under `docs/adr/` or wherever
  `ls`/`grep` finds them, the CLI at `template/scripts/truth`, tests, and the
  canary suite.
- The repository at HEAD is the artifact the paper describes. Note the paper's
  own version references and check whether they match the artifact you have.

## Environment facts (mechanical, no judgment implied)

- Python jsonschema lives in a wheel cache:
  `PYTHONPATH="$(ls -d ~/.cache/truth-ledger-pylib)"` arms schema-dependent tests.
- Bound every potentially slow command: `timeout 300 <cmd> > /tmp/out.txt 2>&1`.
- cwd may reset between shell calls — use absolute paths or `git -C`.
- Export a stable session id before using the `truth` CLI:
  `export TRUTH_SESSION="reviewer-paper-$(git rev-parse --short HEAD)"`.

## Hard rules

- READ-ONLY with respect to the ledger and the repo: you may run any
  read/verify command (`scripts/truth list`, `recheck`, tests, canary), but you
  MUST NOT file, close, retract, or tombstone claims, never set
  `TRUTH_HUMAN`/`TRUTH_HUMAN_ACK`, and must not edit any file outside /tmp.
- Do not fix anything you find. Report only.
- Every finding must carry a verdict: **CONFIRMED** (you reproduced the defect
  or the failed check, with the command and output excerpt) or **PLAUSIBLE**
  (argued from the text, not mechanically demonstrated). Never present
  PLAUSIBLE as CONFIRMED.
- Quote the paper exactly (with section number) for every claim you evaluate;
  paraphrase invites strawmen.

## Method — perform ALL passes, in order

### Pass 1 — Claim inventory
Extract every empirical claim the paper makes: counts, rates, "catches X",
"prevents Y", version numbers, performance/effort assertions, and claims about
its own deployments. Build a table: claim (verbatim) | section | evidence the
paper cites | evidence type (measurement / anecdote / assertion) |
mechanically checkable here? (yes/no). This table anchors everything below.

### Pass 2 — Reproduction
Execute the paper's Appendix B reproduction instructions literally, as a
stranger would. Record: does each step run? Do the numbers you obtain match
the numbers printed in the paper (especially §2)? Report every delta, including
version skew between what the paper states and what HEAD produces. A repro
appendix that silently assumes context is a Major finding.

### Pass 3 — Falsifiability audit
§7 states the paper's own claims and what would falsify them. For each:
(a) is the falsification condition genuinely decidable, or is it phrased so no
observation could ever trigger it? (b) pick at least two conditions that are
testable in this repo and ACTUALLY ATTEMPT the falsification. Report the
attempt and outcome either way.

### Pass 4 — Internal validity
- Circularity: the instrument validates claims, including claims about the
  instrument. Where does the paper's evidence depend on the very mechanism
  under evaluation, and is that dependence acknowledged and bounded?
- Denominators: for every "caught N faults / found N issues" style number,
  ask: caught out of how many? Is there any estimate of the miss rate, or only
  the numerator? Seeded-fault results measure sensitivity to *seeded* faults —
  does the paper claim more than that?
- Counterfactual: is there any control or baseline (same workflow without the
  ledger), or is effectiveness inferred from incidents alone?
- Selection/survivorship: are reported catches a complete log or a curated
  sample? How would a reader know?

### Pass 5 — Construct validity
Does the operationalization match the terminology? "Truth", "verified",
"invalidation" are strong words — trace each to its operational definition
(schema class, recheck semantics) and state precisely what a VERIFIED claim
does and does not guarantee. Flag every place the prose implies more than the
operational definition delivers.

### Pass 6 — External validity and generalization
Inventory the evidence base: how many deployments, authors, agent ecosystems,
time span. Then re-read every generalizing statement (especially §5 and §9)
and classify each as: supported by the evidence base / plausible extrapolation
labeled as such / overgeneralization presented as established.

### Pass 7 — Overclaiming and language audit
Scan the paper for universal quantifiers (all, every, never, none, only,
guarantees, ensures) and absolute causal language. For each occurrence, check
whether the evidence scope actually covers the quantifier's scope. The system
itself refuses agent claims with unscoped quantifiers — hold the paper to the
standard it enforces.

### Pass 8 — Related work and novelty
Assess whether prior art is fairly engaged: provenance/attestation systems,
invariant-based CI gating, mutation testing, N-version/independent-verifier
schemes, safety cases, knowledge-base staleness literature. Is anything
presented as novel that is standard practice under another name? Is the
References section adequate for the claims of novelty made?

### Pass 9 — Limits section audit
§8 ranks "honest limits". Judge it as a referee: are the listed limits the
real top limits given everything you found in Passes 2–8, or are the most
material threats missing or ranked below cosmetic ones? Name any limit you
found that the paper omits.

## Output format

1. **Summary paragraph** — what the paper claims and your overall assessment,
   in plain prose a program committee would read first.
2. **Recommendation** — one of: Accept / Minor revision / Major revision /
   Reject, with the two or three findings that drive it.
3. **Findings list**, ranked Major → Minor. Each finding: [M#/m#] verdict
   (CONFIRMED/PLAUSIBLE) — section + verbatim quote — the defect stated in one
   sentence — evidence (command + output excerpt for CONFIRMED) — concrete
   remedy.
4. **Reproduction report** — the Pass 2 table of expected vs observed.
5. **Claim-inventory appendix** — the Pass 1 table.

Do not pad. A short list of real findings beats a long list of stylistic
quibbles. Style comments are allowed only in a final one-paragraph "prose
notes" section, if at all.
