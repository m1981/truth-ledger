# AGENTS.md redraft — verification of every factual claim before the fix

ADR-062 rule 4 in force: this is the measure role's output, written to disk
**before** the implement role edits the file and before any reviewer is
dispatched. The prior document, `agents-md-audit-and-review-2026-08-24.md`,
listed nine defects. That list was treated here as a **pointer, not evidence**:
every item was re-measured against the working tree. One item did not survive,
and one defect the list does not name was found — in the **committed** file as
well as the redraft.

Method: read the tree, run the command, record the output. `.truth/claims.jsonl`
was never written to; `git status` at the end of this pass shows only
`.truth/claims.jsonl` (pre-existing operator verdict) and `AGENTS.md`.

---

## The nine, re-measured

| # | claim under test | verdict | measurement |
|---|---|---|---|
| 1 | `--exit-ok` does not exist | **CONFIRMED** | `scripts/truth claim --help` lists `--evidence-exit-ok`; the flag set across `template/ scripts/ instruments/` is `--duplicate-ok --scope-ok --paths-ok --generated-ok --evidence-exit-ok --evidence-unsafe-ok --accept-unsafe-ok --orphan-ok --cause-ok`. `--orphan-ok` is real (it lives on `verdict`/`done`, not `claim`), so only `--exit-ok` is wrong. ADR-035 — the record ADR-059 cites for it — itself writes `--evidence-exit-ok` (`docs/archive/adr/035-*.md:61,107`), so this is not a historic name that was renamed; it was never the name |
| 2 | "the `.truth/` policy files are EACH pinned by a claim" | **CONFIRMED, 5 of 16** | pinned by a **live** claim: `accept-allow` (tr-96351a43), `citation-scope` (tr-48fc1f89), `evidence-allow` (tr-11701d6f), `evidence-deny` (tr-6a3c9fef), `generated-paths` (tr-165faff1). The other eleven — including `retracted-figures`, which the file two paragraphs earlier **instructs the reader to edit** — are watched by no claim in any status |
| 3 | "policy files by `sha256sum` and the scripts by a content recipe" | **CONFIRMED, four counterexamples** | pinned by `sha256sum` despite not being `.truth/` policy files: `scripts/truth-whisper.deny` (tr-45312cff), `.claude/settings.json` (tr-df856f43), `.githooks/pre-commit` (tr-bcd40e31), `scripts/test-release-battery.sh` (tr-f788e062, **diverged** — a human verdict is pending, which is the mechanism working). Pinned by a recipe: `scripts/fact-health.sh`, `.githooks/pre-push`, `scripts/release-battery.sh`. The split is real but does not fall where the sentence puts it |
| 4 | "no scan, no `invalidation` record, no bot" | **CONFIRMED** | ledger kinds: 2304 verdict, **1997 invalidation**, 266 claim, 103 issue_event, 93 issue. `kernel.py:339-356` skips TTL invalidations for status and says so in a comment naming the ~1997. The surrounding claims ARE true: `ttl-scan`, `reaffirm`, `invalidate-scan` all exit 2 (unknown verb); the subcommand list is 22 verbs and contains none of them |
| 5 | phantom citation of "the 2026-08-24 audit of this file" | **CONFIRMED, now resolvable** | `docs/reviews/agents-md-audit-and-review-2026-08-24.md` exists (74 lines, committed `d7735fa`). The citation must name that path or go |
| 6 | "the scope file and the ADR-036 retraction gate cannot drift apart" names the wrong pair | **CONFIRMED, and sharper than stated** | the gate is `citation_sweep()` in `template/truthlib/cli.py:201`, which calls `load_citation_scope()` — it reads the scope file **by definition**, so the stated pair is vacuous. The join that was actually made (`af6f7f5`, 2026-08-23) is **sweep-to-gate**: `fact-health.sh` stopped hardcoding its corpus and now reads the same loader (`scripts/fact-health.sh:119-134`). Measured today: gate corpus 37 files, sweep corpus 37 files — but not because they are derived from one source. The sweep then subtracts **six hardcoded `grep -v` prefixes** (`scripts/fact-health.sh:139-144`) which today exclude **zero** files, because no glob in `.truth/citation-scope` matches any of them. They are inert, not absent: adding `docs/reviews/*.md` to the scope file would silently re-open the divergence |
| 7 | `fact-health.sh:119` is a line-number citation of the kind ADR-037/ADR-012 lint | **CONFIRMED, true today** | `SCOPE_GLOBS=` is on line 119 exactly. That is the defect: it is correct now and becomes wrong on any insertion above it, with nothing to notice |
| 8 | ARM 17 / ARM 14 / ARM 6 quoted right after "do not quote a number" | **CONFIRMED, all three numbers correct today** | `TOTAL_ARMS=17`; ARM 6 = tag-check ahead of the battery, ARM 14 = the battery runs this gate when the battery moves, ARM 17 = retracted-figures blocks and an empty policy is not health. Correct, and ordinal — they renumber on any insertion, which is what the paragraph they sit next to warns about |
| 9a | restating `v0.10.0` makes AGENTS.md a seventh unpinned version surface | **CONFIRMED** | `TestCrossSurfaceVersions` (`template/scripts/test-truth-core.py:3136`) pins six: `scripts/truth` line 2 (the source), README title, `truth-ledger-loophole-map.md` header, `truth-ledger-operations-guide.md` header, `check-truth.sh` `current CLI:` comment, `truthlib/cli.py` docstring line 1. The CLI says `v0.10.0`. The **committed** AGENTS.md states no version at all — the redraft *added* the seventh surface |
| 9b | "the redraft removed the file's last three ledger ids" | **FALSIFIED** | `grep -o 'tr-[0-9a-f]\{8\}' AGENTS.md` → **0** in the working tree and **0** in `HEAD`, and 0 in each of the last 30 revisions of the file (`git show <c>:AGENTS.md` over `git log --format=%h -30 -- AGENTS.md`). AGENTS.md has never carried a ledger id. Nothing was removed |

### What survives of 9b

The consequence half is true and was always true, so it is a standing defect
rather than a regression: `AGENTS.md` **is** in the fact-health corpus (glob 2
of 17 in `.truth/citation-scope`) and contributes **zero** citations, and
`fact-health.sh` matches ledger ids only. Zero-citation docs pass silently by
design. So the file that states "one home per fact" is the one file in the
corpus that mechanism cannot check — not because the redraft broke it, but
because it was never wired. Recorded as a finding in its own right.

---

## The tenth defect, which the list does not name

`AGENTS.md` — **both the committed version and the redraft** — says:

> `mkrepo()` in `template/scripts/truth-canary.sh` does a bare `cd "$1"` with
> no `|| exit`, under `set -u` and NO `set -e`, so a failed cd lets
> `git init -b main .` run wherever the shell happens to be standing.

and the redraft adds: *"Nothing prevents any of this today. It is prose."*

**This is false.** The guard landed on 2026-08-21 in `441de48`
(*"strażnik sandboxa — norma z 64f278c staje sie mechanizmem"*), three days
before the redraft. `template/scripts/truth-canary.sh:30-37` reads:

```
  cd "$1" || { echo "canary: cannot enter sandbox '$1' -- refusing to run" >&2; exit 1; }
  if owner=$(git rev-parse --show-toplevel 2>/dev/null); then
    echo "canary: sandbox '$PWD' is INSIDE an existing git repository ($owner)." >&2
    ...
    exit 1
  fi
```

It is the **fifth** falsehood in the committed file and the audit missed it.
It is also the only one stale in the *pessimistic* direction: the other four
told agents a gap was open that had closed; this one tells them a mechanism
does not exist when it does, which invites re-implementing it or ignoring it.

### Demonstration (ADR-061: the guard was made to answer both ways)

The eight shipped lines were extracted verbatim with
`sed -n '30,37p' template/scripts/truth-canary.sh` into a scratch harness and
run in three conditions. No canary run; the repository was not touched.

| condition | result |
|---|---|
| sandbox outside any repository (`mktemp -d`) | `GUARD PASSED -- git init would run in: /var/…/tmp.w7oL…`, **exit 0** |
| sandbox inside the truth-ledger worktree | `canary: sandbox '…/.canary-guard-probe' is INSIDE an existing git repository (…/truth-ledger).` **exit 1** |
| sandbox inside a freshly `git init`-ed dir — the incident shape | same refusal naming that repo as owner, **exit 1** |
| sandbox path that does not exist | `canary: cannot enter sandbox '/nonexistent…' -- refusing to run`, **exit 1** |

`git status` after: `.truth/claims.jsonl` and `AGENTS.md` only, as before.

**Two limits, recorded rather than asserted away.**

1. The detector is `git rev-parse --show-toplevel`, which returns non-zero
   from *inside* a `GIT_DIR`. A sandbox at `<repo>/.git/probe` passes the
   guard (measured: exit 0). Unreachable in practice — every `mkrepo` argument
   in the file is a `mktemp -d` — so this is a noted edge, not a defect.
2. **The guard itself has no arm.** No case in
   `scripts/test-release-battery.sh`, `template/scripts/test-integrations.py`
   or `test-truth-core.py` exercises it. Under ADR-061 the guard is a
   mechanism but not DONE: nothing makes it go red if a later edit removes it.
   The prose must say that, not "nothing prevents this" and not "this is
   handled".

---

## Claims in the redraft that were checked and stand

Recorded so a later reader knows what was covered, not only what failed.

- `.githooks/pre-commit` refuses staged paths under `docs/archive/` (line 6).
- `scripts/truth-whisper.deny` denies **both** `docs/archive/` and
  `\.truth/claims\.jsonl$` — the redraft's pair is right.
- Whisper count accumulates in `.git/truth-whisper.seen`
  (`scripts/truth-whisper.py:111,115`); ADR-005 names the fatigue half
  "still accumulating" with no numeric threshold and no reader. Stands.
- ADR-045's flock is placed under `git rev-parse --git-dir`
  (`template/truthlib/shellio.py:428-441`). Stands.
- The canary's tracker arms run `truth ready` under `PATH="/usr/bin:/bin"`
  (`truth-canary.sh:819,855,858`); `structural.py:35-54` guards `tomllib`
  with `try/except` and degrades to `tomllib = None`. Stands.
- `scripts/retracted-figures.sh` is wired at
  `scripts/release-battery.sh:138` (`# --- 3b.`), and section 3b fails on a
  sweep that printed no summary. Stands.
- All five consumer-hook test classes exist verbatim in
  `template/scripts/test-integrations.py`: `TestCLIContractsAndRefusals` (115),
  `TestClaudeWhisperHook` (372), `TestClaudeSessionDigest` (465),
  `TestTierCInstruments` (517), `TestMarkdownAndSpecHealth` (843).
- `truth doctor` is the reporter of `core.hooksPath`
  (`cli.py:1592`, `shellio.py:964-975`). Stands.
- `--paths-ok` is "stored, decays at 30 days, counted" — the decay is
  **ADR-032**, not ADR-055 (`cli.py:1747` states it). The sentence does not
  attribute it, so it is not wrong; noted so nobody later attributes it to
  ADR-055.
- 221 hashed normative paragraphs: `arm-index` reports
  `prose cites 221 hashed`. Stands.
- `.venv/` is gitignored (`.gitignore:6`). Stands.

---

## Scope ruling on the `--exit-ok` name

**FOUR live surfaces carry it, not three** — corrected after the adversarial
review found the fourth. The original count here came from grepping three
directories and then reporting the result as if it were the repository. That
is the same defect this document was written to catch, committed inside it.
The ruling taken here:

- **`AGENTS.md`** — in scope. It is new prose in the file every agent reads
  first, and a wrong flag name propagates by being copied.
- **`instruments/semantic-audit.py`** — in scope. Two docstring comments name
  the flag; the field names the extractor actually reads
  (`evidence_exit_basis`) are correct, so this is prose-only and cannot change
  behaviour.
- **`docs/decisions/059-*.md`** — in scope, body edit permitted: its status
  line is `PROPOSED (2026-08-23, agent-authored)`, so the ADR-002 immutability
  rule (which binds *accepted* records) does not apply. Three occurrences,
  all naming ADR-035's flag by a name ADR-035 never used.

- **`template/CHANGELOG.md:225`** — the fourth surface, missed on the first
  pass. It sits inside the entry that documents `instruments/semantic-audit.py`
  itself, and `CHANGELOG.md` is listed under `_skip_if_exists` in
  `copier.yml`, so the file is delivered to any consumer that does not
  already keep one. In scope, and the most outward-facing of the four.

The remaining occurrences are all under `docs/reviews/`, and are correctly
left alone: `docs/reviews/gates-2026-07/*` are the JULY PROPOSAL DRAFTS, in
which `--exit-ok` was the name being proposed. ADR-035 shipped
`--evidence-exit-ok` instead. A frozen record quoting what was proposed then
is right; changing it would be the error.

Editing ADR-059's body will move any ADR-060 prose hash that cites it; the
refresh discipline applies — read the suspect paragraphs, then
`--record-links`, never the reverse. Measured before editing: no paragraph in
the hashed corpus cites ADR-059 (`grep -c 'ADR-059' .truth/arm-index-prose-hashes`
→ 0), so nothing moved.

---

## What was changed, and the gate that now holds it

Ten sites in `AGENTS.md`, three in `docs/decisions/059-*.md`, two in
`instruments/semantic-audit.py`.

| defect | change |
|---|---|
| 1 | `--exit-ok` → `--evidence-exit-ok` in AGENTS.md, ADR-059 (3 sites) and the `semantic-audit.py` docstring (2 sites). Residual across `docs/decisions/`, `instruments/` and `AGENTS.md`: zero |
| 2 | the false generalisation is gone. The pinned set is **enumerated with its ledger ids**, and the eleven unpinned `.truth/` files are named as unpinned in the same breath — including `retracted-figures`, with an explicit note at the paragraph that instructs editing it that the edit stales nothing |
| 3 | the "policy files by digest, scripts by recipe" split is replaced by the measured split, which does not fall that way |
| 4 | "no `invalidation` record" → "no NEW `invalidation` record"; the ~2000 inert ones are named, with a command to count them instead of a number in prose |
| 5 | the citation names `docs/reviews/agents-md-audit-and-review-2026-08-24.md` |
| 6 | rewritten to the real join (sweep-to-gate), with the inert `grep -v` exclusion list disclosed and the condition that would reopen the divergence stated |
| 7 | `scripts/fact-health.sh:119` → `grep -n load_citation_scope scripts/fact-health.sh`, with the reason named in place |
| 8 | all three arm ordinals replaced by greps on what the arm asserts. `grep -n 'ARM [0-9]' AGENTS.md` now returns nothing |
| 9a | the `v0.10.0` restatement is gone; the file points at `scripts/truth` line 2 and `TestCrossSurfaceVersions` and says why it does not restate |
| 9b | the list item was false, so nothing was restored. The underlying gap was closed instead: **ten ledger ids added**, so the file now stands inside the mechanism it invokes |
| 10 | the mkrepo paragraph is corrected to past tense, `441de48` is named, the guard is quoted, and it is marked **MECHANISM, UNGATED** — because no arm exercises it. "Demonstrated" below means the eight shipped lines extracted verbatim and run in a harness, not a run of `truth-canary.sh`; and the in-repo case used the MAIN worktree, since the incident's linked-worktree shape cannot be reproduced without creating one |

### Gates, after

```
bash scripts/fact-health.sh              0 failure(s), 2 warning(s), 31 citation(s)   [was 21]
bash template/scripts/doc-health.sh      0 failure(s) across 16 live doc(s)
python3 instruments/arm-index.py         1245 arm(s), 0 failure(s)
python3 instruments/semantic-audit.py    11 basis sentence(s), exit 0
python3 template/scripts/test-integrations.py   Ran 29 tests -- OK
python3 instruments/register-index.py    1 failure -- PRE-EXISTING (ADR-062 unaccounted), untouched here
```

### The red-gate demonstration for the change itself (ADR-061)

The ten ids are not decoration; they are what puts this file inside
`fact-health`'s net. Made to fail and restored:

```
sha256 AGENTS.md before   24493a33e0355f575e312f880673c4e35dc1a1cab3929afbe03c7d8ca3a1694f
sed  tr-96351a43 -> tr-deadbeef
  AGENTS.md
    FAIL  tr-deadbeef  missing from ledger -- a bare id must be OURS ...
  fact-health: 1 failure(s), 31 citation(s)        exit 1
sed  tr-deadbeef -> tr-96351a43
sha256 AGENTS.md after    24493a33e0355f575e312f880673c4e35dc1a1cab3929afbe03c7d8ca3a1694f   IDENTICAL
  fact-health                                       exit 0
```

Named failure condition, **stated narrowly because the gate is narrow**: a
pin cited in AGENTS.md reaches `stale`, `diverged`, `retracted` or `disputed`,
or its id stops resolving. Those four are `citation_bad` in
`truth vocab --json`; the sweep FAILs on them and on a missing id.
`cannot_verify` and `unverified` produce a **WARN and exit 0** — the hole is
documented rather than papered over, and AGENTS.md now says so in the same
paragraph as the ids.

An earlier draft of this line said "leaves `live`", which is broader than the
gate: an adversarial review caught it, and it was the same error as citing a
mechanism without checking its branches. The demonstration above used the
`missing` branch (`tr-deadbeef`), which is a fifth branch again — real, and
not the one the sentence is about.

Gate: `scripts/fact-health.sh`, which rides the release battery. Before this
change the file carried zero citations and the gate could say nothing about
it in either direction.

### What this change does NOT fix, stated so nobody reads silence as coverage

- **AGENTS.md is outside the ADR-060 prose corpus.** `.truth/arm-index-prose-hashes`
  covers `docs/truth-ledger-explained.md` (149 paragraphs) and
  `docs/truth-ledger-paper-v3.md` (72). AGENTS.md's own normative paragraphs
  cite ADR-057, ADR-061 and ADR-062 and are **not** freshness-checked. The
  file already says *"ENFORCED for the corpus the arm-index covers; NORM for
  prose outside it"* — true, and this is which side it is on.
- **The canary sandbox guard has no arm** (defect 10). Marked in the prose;
  not built here.
- **The six `grep -v` exclusions in `fact-health.sh` are still hand-written.**
  Disclosed in the prose; not fixed.
- **No mechanism prevents the next false generalisation.** The enumeration in
  the control-surfaces paragraph is now checkable only in the direction of
  "these ids are live" — nothing fails if a sixth `.truth/` file gains a pin
  and the list is not updated. That is the residue this class of defect keeps
  leaving, and it is the same shape as everything in the mechanism-layers
  brief.

---

# The adversarial review, and what it changed

An adversarial reviewer was dispatched on the diff per ADR-062 rule 3 — given
the house conventions and the diff, and **not** the defect list this work was
carrying. It ran read-only, restored every probe, and returned thirteen
findings. Ten survived my own re-measurement and are fixed; one is falsified
below; two are recorded rather than fixed.

**The reviewer's own opening finding was about the process, and it is
correct.** The working tree changed under it mid-review: `register-index.py`
and `test-integrations.py` were being rewritten in the same tree by the work
described in the next document while the review was reading. The review was
scoped to `AGENTS.md`, ADR-059 and `semantic-audit.py`, and its verdict on
those stands — but this is AGENTS.md's own `git add <file>` hazard, live.
**Before any commit: read `git diff --cached` hunk by hunk.**

## Fixed, each re-measured before acting

| # | finding | my measurement | fix |
|---|---|---|---|
| **1** | **The pin paragraph named a mechanism that cannot observe the condition.** "A pinned file stales or diverges when you edit it … a human verdict is forced. *ENFORCED:* `truth list --live` and `--diverged`" | **CONFIRMED, and it is the worst thing in the diff.** `truth list --stale --json` → **0**, and `kernel.py:281` says `stale` "is no longer reachable from ANY record … a PROJECTION". Editing a pinned file changes NO status. Both named verbs are read verbs: `truth list --live` → exit 0, `--diverged` → exit 0, whatever the ledger holds. The verb that DOES see it is `truth reproduce` (exit 7), which rides `scripts/release-battery.sh:350`. And the remedy is not human-only: `release-battery.sh:361` prescribes "`truth verdict <id> diverge` or an agree with `--refresh-evidence`"; only retraction is G12 | paragraph rewritten on the measured mechanism; `truth reproduce` named as the gate; "human verdict" corrected to "judgement"; the same correction applied to the `.truth/evidence-allow` rider and to the whisper paragraph's "what your commit will stale" |
| **2** | **AGENTS.md dropped ADR-062 rule 4** — the rule this whole incident chain produced | **CONFIRMED.** ADR-062 numbers four rules; both it and AGENTS.md said "Three rules follow". This document opens by invoking rule 4 while the operational file omitted it | rule 4 restored in AGENTS.md with the incident that produced it; **ADR-062's own stale header corrected too** — it had been counting three since before rule 4 was appended |
| **3** | The replacement enumeration is itself incomplete, and its summary count is wrong on every reading | **CONFIRMED.** "three of the four scripts" is 3-of-5 or 2-of-4, never 3-of-4. `scripts/test-release-battery.sh` (digest, **DIVERGED today**) and `scripts/release-battery.sh` (five pins at once) were omitted — I had measured the first and left it out | both battery scripts named, with the reason their ids are deliberately absent (a diverged id in live prose reddens `fact-health`); the count replaced by the actual split; the "one `.truth/` file by nothing" / "eleven of sixteen" contradiction removed |
| **4** | Two of the four `grep -n` recipes have **no file operand** — run verbatim they hang on stdin, then exit 1 | **CONFIRMED**, and sharp: these are the pointers that REPLACED arm numbers so a reader could find the arm. As written they read as "the arm is gone" | file operands added; all four recipes re-run verbatim and return the promised line |
| **5** | A still-true, checkable finding was deleted and replaced by an unfalsifiable sentence, optimistic direction | **CONFIRMED.** The old text named six gate-metrics rows whose review date had passed with nothing enforcing them. Still true: `grep -c '2026-08-08' docs/governance/gate-metrics.md` → **7** (six rows plus the prose line naming the audit they were due at), and `grep -rn 'Next review' scripts/ instruments/ template/ .githooks/` → **0**. The redraft's "that registry NOW carries review dates" implies a repair; it has carried them since `6f3e9b1`, 2026-08-02 | the finding restored with both commands inline, and tied to the open L4(c) item in the mechanism-layers brief |
| **6** | "Every rule below is marked ENFORCED or NORM" is false of the file it introduces | **CONFIRMED**, and partly my doing: I added a third marker, `MECHANISM, UNGATED`, without amending the taxonomy | taxonomy widened to three markers, and the unmarked paragraphs are declared as unmarked rather than left to read as implied NORMs |
| **7** | `--exit-ok` survives on a **fourth** surface, `template/CHANGELOG.md:225`, which ships to consumers | **CONFIRMED.** It sits inside the entry documenting `semantic-audit.py` itself; `copier.yml` lists `CHANGELOG.md` under `_skip_if_exists`, so it is delivered unless the consumer keeps their own. My "three surfaces" came from grepping three directories and reporting the result as the repository | fixed; the scope ruling above corrected, with the frozen July drafts explicitly excluded and why |
| **9** | "Three of the four falsehoods were status sentences" — a number with no source | **CONFIRMED.** Neither the audit nor this document supports the 3/4 split | replaced with what the audit actually says, plus the fifth falsehood it missed |
| **11** | The gloss under "eleven of the sixteen" enumerates eight | **CONFIRMED.** It missed both `arm-index-*-hashes` files and `claims.jsonl` | all eleven named |
| **13** | ARM 17's second half is a `grep -q` for a sentence, not a run of the empty-policy path | **CONFIRMED** (`test-release-battery.sh:584`) | "proves both halves" → "covers both halves, unevenly", with what each half actually does |

Findings 10 and 12 were about **this document**, not AGENTS.md, and are
corrected in place above: the named failure condition was broader than the
gate (`cannot_verify` WARNs at exit 0), and "Demonstrated both ways" was doing
more work than a harness built from eight extracted lines can carry.

## Falsified — the one finding that did not survive

> "`tr-48fc1f89`'s `live` status rests on the **uncommitted** verdict
> `tr-06ef0af9`; if `.truth/claims.jsonl` is not committed alongside
> AGENTS.md, that citation goes red."

**It does not.** Folded both ledgers with the same clock:

```
committed-only (git show HEAD:.truth/claims.jsonl) : live
working tree                                       : live
```

The uncommitted record is an `evidence_refresh` verdict on an already-live
claim, so it moves nothing. The hazard the reviewer was reaching for is real
in general — a cited id whose liveness depends on an unstaged record — but it
is not true of any of the ten ids added here. All ten fold to `live` on the
committed ledger.

## Recorded, not fixed

- **`truth reproduce` is RED in this tree right now**, and was before this
  work: exit 7, three `capsule-stale` claims (`tr-4df1a9fd`, `tr-56a8e36c`,
  `tr-d0191e65`), all `watched-moved`, all watching files nobody touched
  here (`template/truthlib/kernel.py`, `policy.py`). **The pre-push battery
  is therefore already blocked**, independently of anything in this change.
  That is an operator judgement — ADR-051 refresh or a diverge verdict — and
  it is named here so it is not discovered as "the commit broke the push".
- **The reviewer's parenthetical about Tier C was right and my brief was
  wrong.** ADR-046 defines Tier C as the instrument tier; it carries no
  stdlib-only rule, and every file in `instruments/` imports `truthlib`.
  What `semantic-audit.py` is actually pinned on is having no network I/O.
  Recorded because the wrong version has now been repeated in at least two
  briefs.
