# ADR-050: the false-stale rate is a shipped report, not an ad-hoc script

Status: Accepted (2026-08-04, operator) — prompted by a measurement of
630 resolved stalings in the pilot ledger (2026-08-03, filed there as
claim `tr-13d16cc0`, self-diverged the next day over walk order and
succeeded by `tr-e1225a78`), which was computable only by a
hand-written `jq` recipe. Implemented in
`truthlib.advisory.staling_report` + `truth staling`; no schema change,
no gate, no fold change. Core tests TestStalingReport (17); canary
FAULT ST (8 arms incl. two negative controls and the two order arms).
Date: 2026-08-04
Amends: — . Extends: ADR-030 (the mechanical/genuine split of *labor*,
whose `reaffirm:` basis and `reaffirm_cleared` record are the two marks
this report reads), ADR-012 (the same split applied to verdicts),
ADR-039 (the other churn instrument — the blast forecast predicts
stalings, this counts what they were WORTH), ADR-043 (pure core, and
the shell owns every fact it is handed — here, the walk order),
ADR-047 (ships with a named metric and a review date). Cites: ADR-016
(whose total order the shipped verb USES, and whose absence from the
first measurement is decision 4's whole subject), ADR-031/ADR-008
(order_check, the one consumer that legitimately stays order-SENSITIVE
on the raw stream — and the reason the file walk looked defensible),
ADR-046 (the tiering rule this report is an argued exception to),
ADR-019 (TTL expiries are stalings too, and they name no path).
Supersedes: —

## Context

The ledger's central mechanism is *a watched path changed, therefore
this claim is stale*. Nothing in the system has ever reported what that
rule costs. `stats` reports how many claims are stale and how fast they
go stale (half-life); `blast_report` forecasts how many stalings a
watch will produce. Neither answers the only question that decides
whether the rule pays: **when a claim staled, had the fact actually
changed?**

Measured on the pilot's consumer ledger (2,168 records, 2026-08-03,
walked in the fold's canonical order) the answer is that it usually had
not:

* 630 stalings had been resolved by a later verdict;
* in **555** the resolving verdict was `agree` — the fact had not
  changed and the staling was a false alarm;
* in **75** it had — `diverge`, `cannot_verify`, or `retracted`;
* within the false half, **262** were provable by an unchanged evidence
  hash (ADR-030's mechanical arm) and **293** needed a human to re-read
  the evidence and agree.

A false:true ratio above 7:1, with the *mechanically healable* share
under half — so `reaffirm` cannot automate the problem away; most of
the false alarms still cost a person a reading. This reproduces Estler
et al. (2014) locally — specifications change far less than
implementations — and the path-kind column says why: the majority of
those stalings were triggered by watches on implementation files (as
the pilot ledger stands, 375 of 641 stalings touched a `.py` path
against 146 touching a `.md`). Under a path-touched-means-stale rule a
high false rate is therefore **structural, not incidental**: it is what
happens when a claim about a slow-moving fact watches a fast-moving
file.

The first pass at that measurement read the same ledger in FILE order
and reported 608 / 530 / 78 / 242 / 288 — same conclusion, different
counts. Decision 4 is the record of why, and why it is the thing this
ADR is most careful about.

Either way, the number was computable only by a `jq` one-liner living
inside one claim's evidence field. Every repository adopting this
template has the same question about its own ledger and no way to ask
it.

## Decision

**1. One pure fold, `staling_report(events)`.** Beside
`retraction_cause_report` in `truthlib/advisory.py`: records in, data
out; no clock, no fold, no I/O. Every consumer that ships this template
gets it.

**2. A staling is an EPISODE, not an invalidation record.** The
episode opens at the first invalidation and closes at the **next
verdict on that claim**. An invalidation landing on a claim that is
already stale did not stale it a second time — it is a re-scan of a
question nobody has answered yet — and is reported separately as
`restaled` rather than inflating the denominator. As the pilot ledger
stands, 674 invalidation records fold to 641 episodes; counting records
instead would move every ratio.

Episodes still open when the stream ends are `unresolved` and count in
**neither** numerator. Their answer is not in; assigning them to a
column would be inventing it. They stay visible in the shape — the F1
fail-loud rule applied to a remainder, the same move ADR-049 made with
`unrecorded`.

**3. The three arms, and who paid.** An `agree` says the fact had not
changed. It splits by *who established that*: a machine, when the basis
starts with `reaffirm:` or the record carries `reaffirm_cleared`
(ADR-030's two marks — read as an OR precisely so a hand-written basis
cannot launder an auto-agree into the human column); otherwise a human
who re-read the evidence. Every other verdict says the fact moved. The
prefix is **derived** from `REAFFIRM_BASIS`, never hand-copied, so a
reworded basis cannot silently empty the mechanical column (the
ADR-018/021 lesson applied to a literal).

**4. Fold order, because a staling IS a status transition — and the
question cost the pilot a self-diverge.** `staling_report` never
re-sorts: it reads the stream in the order given, and the shell owns
the order (ADR-043's division). The shipped caller sorts by `fold_key`
first.

This was decided the hard way, and the record is worth keeping. The
measurement that motivated this ADR walked the ledger in FILE order —
which within one repository is append order, and which `order_check`
already treats as legitimate for its own deliberately order-SENSITIVE
purpose. On a union-merged ledger it is not the same as time: worktree
branches append blocks whose wall-clock timestamps interleave, and the
two walks disagree on 30 of the pilot's 219 claims and ~3.5 % of its
stalings. The pilot's own author filed a **self-diverge** on the
measurement (kuchnie `tr-0e4c30d7`) and a fold-ordered successor
(`tr-e1225a78`) on the argument that settles it: **status is DEFINED by
the fold's `(ts, id, canon)` order (ADR-016), so a count of status
transitions must use that order or it is measuring the file rather than
the history.** Reading the disagreeing claims by hand confirms it — file
order pairs an invalidation with a verdict filed *before* it, which is
not an answer to anything.

The conclusion survived both walks (the ratio band was unchanged; that
is why the band-based evidence recipe did not catch the error), but the
counts were method artifacts. So: fold order is the report, and
`truth staling --append-order` keeps the file-order walk reachable for
exactly one purpose — reproducing measurements taken that way before
this verb existed. A ledger holds both numbers, permanently, and a
system whose thesis is that recorded facts must be re-runnable may not
strand one of them. **The order is stamped on the output** (`order` in
`--json`, in the first line of the text): two orders can disagree, so a
number that does not say which produced it is not a result.

**5. `by_path_kind` is structural, never semantic.** The kind of a
watched path is its lowercased file suffix, or `<none>` for a
suffix-less basename (`Makefile`, `scripts/truth`; a *leading* dot
names a dotfile and is not a suffix). The template cannot know which
directories a given repository calls "specification" and which
"implementation" — a shipped guess would be wrong in most of them — and
the suffix is the language-agnostic proxy the Estler reading needs.
Attribution is per EPISODE, from the opening invalidation's `touched`
list, deduplicated: a staling touching two `.py` files counts `.py`
once. A staling touching two *kinds* counts under both, so the column
sums to ≥ `stalings`; a staling with no touched path at all (TTL
expiry, ADR-019; unreachable anchor) is counted in `pathless` and
attributed to no kind, so the column can also sum to less. Both facts
are in the returned shape rather than in a footnote nobody reads.

**6. Tier: the template CLI, as an argued exception to ADR-046.**
ADR-046 sent the report family out of the template CLI into meta-repo
`instruments/*.py`, on the ground that instruments judge whether Tier B
pays and are not product. This report is the case that rule does not
cover: `instruments/` is meta-repo-only and is not templated, so a
Tier C placement would put the question permanently out of reach of the
consumers who have it. And the thing being judged is not a gate — it is
the **kernel's central rule**, which every consumer runs and no
consumer can currently price. A read verb (`truth staling
[--since ts] [--json]`, `stats`' own window convention), not in
`WRITE_VERBS`, so no commit-gate banner: satellites poll read verbs and
stderr noise there trains `2>/dev/null`.

## Explicit non-goals — residuals owned

**No gate, no advisory, no refusal.** Nothing in this ADR blocks, warns
at intake, or changes an exit code. A high false-stale rate is not a
defect to refuse — narrowing a watch trades false stalings for missed
ones, and this report deliberately cannot see the second kind (a fact
that quietly died while nothing it watched moved is invisible to a
ledger, and no fold will ever find it). The report exists so that
trade-off is made on numbers instead of vibes. Whether a *narrower
--paths advisory* is worth building returns as its own ADR once a field
window of this data exists — the same posture ADR-039 took on its own
refusal gate.

**A mechanical `agree` is not proof the fact held.** ADR-030 is
explicit that a hash match means the COMMAND OUTPUT is unchanged and
nothing more; when `evidence_paths` is wider than what the command
reads, the reaffirm re-agrees and records what it buried in
`reaffirm_cleared`. So `mechanical_agree` is an upper bound on
machine-cleared truth, and its own `reaffirm_cleared` records are where
an auditor goes to check. Not corrected here: correcting it would mean
re-judging burials, which is a human verb.

**`diverge --mechanical` counts as `true_stale`, and that is a known
overcount.** ADR-012's mechanical subtype says the *recipe* moved and
the fact may well hold — arguably a false alarm of a third kind. It is
not split out, because the ADR-046 admission logic applies to reports
too: the split would be a distinction nothing else reads, and on the
pilot corpus it is 6 verdicts against 75. If a review finds it
material, it becomes a fourth key with no schema change.

**The suffix is a proxy and will be wrong somewhere.** A repository
whose specs are `.py` docstrings, or whose implementation is `.md`
literate source, gets a misleading column. The answer is to read one's
own repository, not to make the template guess harder.

**No `--since` semantics beyond `stats`'.** The window filters events
before the fold, so a window that cuts between an invalidation and its
verdict shows the staling as `unresolved`. That is honest for a window
("no answer arrived inside it") and it is why `unresolved` is reported
rather than dropped.

## Adoption gate (ADR-047)

Not a blocking gate — nothing refuses, so there is no false-refusal
budget to watch. The metric this report must EARN is that it is read:
**the false:true ratio and the mechanical share, recorded at the
monthly audit** (`.truth/README.md` "Daily operation"), from
`truth staling --json` over the consumer's own ledger. Next review:
**2026-11-04**, in the same monthly slot as ADR-049's.
Retirement test: if two consecutive reviews record the ratio and no
decision — no watch narrowed, no claim re-homed, no reaffirm policy
changed — turns on it, the report is decoration and leaves the CLI for
`instruments/`, where ADR-046 would have put it.

## Consequences

The template's central rule becomes priceable by the people who run it,
in one verb, on their own data — and the pilot's headline number stops
living inside a `jq` string in one claim's evidence field. The immediate
finding it makes reproducible is uncomfortable and worth stating
plainly: on the corpus that motivated it, roughly seven of every eight
resolved stalings found nothing changed, and more than half of those
still cost a human a reading. Cost: one read verb, one pure function,
no record shape change, no version-pinned surface moved (the ADR-026
lockstep stamp moves at the next release, not in this diff).

**Canary faults (FAULT ST).** A synthetic ledger whose answer is known
by construction: four claims, seven invalidation records forming five
episodes, four resolving verdicts placed one per arm plus a second
mechanical one carried by `reaffirm_cleared`. ST1: the three arms
reproduce the hand-built answer. ST2: seven invalidation records fold
to five stalings, two counted as `restaled`, and
`stalings == resolved + unresolved`. ST3: the path kinds rank
`.py`=3 over `.md`=2 and the pathless staling is never invented as a
kind. ST4 (**negative control**): a ledger of verdicts with no
invalidation reports zero and says so in plain text — an implementation
counting verdicts instead of answered stalings reddens here. ST5
(**negative control, by deletion**): removing the one verdict on the
never-invalidated claim leaves the report byte-identical, proving it
was credited to nothing. ST6: the fixture passes `validate` (so the
arms are reading a legal ledger, not junk only this verb tolerates) and
the read verb stays banner-free on an unwired clone. ST7/ST8 run a
second fixture in which append order and fold order genuinely disagree
(a verdict appended before an invalidation that predates it — the
union-merge shape): the verb must produce the FOLD answer, the flag
must produce the FILE answer, and the two must DIFFER, so a fixture
with no teeth or a no-op flag reddens. Every arm was verified red
against a seeded mutation — of the fold for ST1–ST6, of the shell's
sort for ST7/ST8 — before being committed.

Falsifier: a consumer whose `human_agree` column is dominated by
verdicts that a reader, examining them, would call genuine
re-verification of a fact that had in fact moved — which would mean the
verdict vocabulary, not the staling rule, is where the imprecision
lives.
