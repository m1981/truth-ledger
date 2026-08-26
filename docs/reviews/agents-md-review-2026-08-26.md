# AGENTS.md — independent review of the uncommitted change, 2026-08-26

Reviewer session: not told the specification (ADR-062 rule 1). Subject:
`AGENTS.md`, modified and uncommitted, 601 lines,
`sha256 61421cf165b84b254e45628ba7ca8a2494eb92a8c770b91da8629bdbcaf80e06`.
Every number below carries the command that produces it. Two figures are
marked TESTIMONY because I could not give a command a later reader can run.

**Verdict: do not commit as it stands.** Four counted assertions are false
against this tree and one is a totality claim the instrument it cites
refuses in its own output. All five are fixable by deleting or re-measuring
a sentence; none require restructuring. The change is a large net
improvement and its ten new ledger ids are real and held — see *Verified
sound*.

---

## Findings, ranked by how well the defect hides a regression

### F1 — FALSE, and it is the file's own fail-open list

> line 514: "Ask `python3 instruments/waiver-index.py` instead — it
> carries the whole escape surface"

The instrument denies this in the last lines of its own output.

```
$ python3 instruments/waiver-index.py | tail -4
  unbounded carriers     5 recorded by hand, from NO list: .claude/settings.json,
                         <path>#<selector>, core.hooksPath, git push --no-verify,
                         scripts/truth-whisper.deny
                         syntax, config and code cannot be harvested, so this
                         register is NOT total and says so in its own text
```

`docs/waivers.md` was **retitled on 2026-08-25** to kill exactly this
sentence shape:

```
$ sed -n '12,13p;31,36p' docs/waivers.md
**THIS REGISTER IS NOT TOTAL.** It partitions the carriers it can enumerate
from a source, and there are carriers it cannot.
### Why the title changed
The first version of this file was titled *"every gate in this system that can
be lifted, and by what"* ... That is a mis-scoped partition: a domain left
unstated reads as universal, so a register total over flags is taken as total
over bypasses.
```

**Severity: HIGH.** Misleads: **yes**. An agent that believes it concludes
every bypass is either registered or refused. `git push --no-verify`,
`core.hooksPath`, `TRUTH_BATTERY_NO_META` and `<path>#<selector>` are
neither. This is a correction one day old being re-imported into the file
every agent reads first — the optimistic direction, and the fifth time this
repository has shipped a totality claim over a partial harvest.

The sentence immediately after it is *also* narrowed wrongly: "It is swept
against the CLI parser in both directions, and the reverse direction is
**total**". The reverse direction is total **per harvested carrier** — flags,
env names AND `.truth/` files, three sources, not one:

```
$ python3 instruments/waiver-index.py | grep inventory
  flag inventory         50 harvested: 11 waiver(s), 39 declared not-an-override, 0 unclassified
  env inventory          19 harvested: 10 waiver(s),  9 declared not-an-override, 0 unclassified
  file inventory         17 harvested: 11 waiver(s),  6 declared not-an-override, 0 unclassified
```

Fix: replace with what the instrument says — total per harvested carrier,
and three carriers cannot be harvested at all.

---

### F2 — FALSE in both numbers, and the enumeration omits a file the same diff introduces

> line 169: "**Eleven of the sixteen files in `.truth/` are pinned by no
> claim in any status:** the four `*-opt-out` files, `arm-index-paper-baseline`,
> `register-index-baseline`, `arm-index-link-hashes`, `arm-index-prose-hashes`,
> `watch-policies`, `claims.jsonl` itself, and `retracted-figures`"

It is **twelve of seventeen**. The paragraph prints its own falsifier three
lines later ("Recount it with `ls .truth | wc -l`"), and that command already
disagrees with it:

```
$ ls .truth | wc -l
      17
$ p=0; u=0; for f in .truth/*; do \
    n=$(python3 scripts/truth impact "$f" 2>&1 | grep -c 'WATCHED BY'); \
    [ "$n" -gt 0 ] && p=$((p+1)) || u=$((u+1)); done; \
  echo "pinned=$p unpinned=$u total=$((p+u))"
pinned=5 unpinned=12 total=17
```

Confirmed independently over **every status**, not only live, by reading
`evidence_paths` off every `kind: claim` record: the same five
(`accept-allow`, `citation-scope`, `evidence-allow`, `evidence-deny`,
`generated-paths`) and no others.

The missing twelfth is **`.truth/waiver-not-an-override`** — which this same
uncommitted change cites 350 lines further down as the thing that decides
whether a new CLI flag is an override:

```
$ git diff -U0 AGENTS.md | grep -n 'waiver-not-an-override\|Eleven of the'
364:+**Eleven of the sixteen files in `.truth/` are pinned by no claim in any
759:+`.truth/waiver-not-an-override` with a reason, so a new flag of any shape
```

Both are `+` lines. The change contradicts itself. The file arrived on
2026-08-25 (`1bfd30e`), one day before this review, and `.truth/` has held 17
files since:

```
$ git ls-tree --name-only HEAD .truth/ | wc -l
      17
```

**Severity: HIGH.** Misleads: **yes**. `waiver-not-an-override` is the escape
surface's escape surface — a line in it removes a carrier from the waiver
register entirely. An agent reading this list concludes the file is either
pinned or does not exist. It is neither: it is unpinned, unenumerated, and
governs what the register can see.

Fix: the paragraph already says the right thing about itself — "Do not
maintain the membership here — ask the ledger". Take its own advice and drop
both counts and the enumeration; keep the mechanism sentence and the recount
command.

---

### F3 — FALSE, and it conceals an open judgement on the push-boundary script

> line 159: "`scripts/release-battery.sh` carries five pins at once, digest
> and recipe, live and unverified"

There is no such five. Non-retracted pins on that path:

```
$ python3 scripts/truth impact scripts/release-battery.sh
  tr-722b9cff (P1, live)         recipe  (grep -A8 … skipped=)
  tr-017e6487 (P1, unverified)   recipe  (grep -e venv/bin/activate …)
  tr-7f8d4a83 (P1, unverified)   recipe  (grep -oE '^# --- [0-9]+b?[.] [a-z]+')
  tr-d2aa8783 (P1, unverified)   recipe  (grep -E '^# --- [0-9]' | grep -vE …)
$ python3 scripts/truth list --diverged | grep tr-7cccc674
tr-7cccc674  diverged  P1  VERIFIED  the release battery at scripts/release-battery.sh
                                     carries the ADR-048 arm set wired at the push boundary…
```

`truth impact` reports only active claims, which is why the fifth is invisible
to it. The five are **four recipes and one digest**, and the statuses are
**one live, three unverified, and one DIVERGED** — not "live and unverified".
All four active pins are recipes; there is no live digest pin at all.

**Severity: MEDIUM-HIGH.** Misleads: **yes, in the optimistic direction.**
The sentence *immediately before it* correctly flags
`scripts/test-release-battery.sh`'s pin as "**DIVERGED right now**" and
explains that its id is withheld so a dead id in live prose cannot redden
`fact-health`. Then the very next sentence describes the *other* battery
script — the one the pre-push hook actually execs — as though its pin state
were entirely active. The mechanism (withholding both ids) is right; the
description of what the reader will find is wrong, and what it hides is a
second open judgement on the push boundary.

Fix: "carries five pins at once — four recipes and a digest, one live, three
unverified and one diverged." Or drop the adjectives entirely; "Ask the ledger
for both" is already the correct instruction and needs no preview.

---

### F4 — FALSE, and it rotted inside this working tree

> line 144: "of the six `evidence_refresh` verdicts in the ledger, three were
> filed by an agent and three by the operator"

Seven, split three and four:

```
$ grep -c '"evidence_refresh"' .truth/claims.jsonl
7
$ grep '"evidence_refresh"' .truth/claims.jsonl | grep -c '"actor": "claude"'
3
$ grep '"evidence_refresh"' .truth/claims.jsonl | grep -c '"actor": "michal"'
4
```

The sentence was **true at HEAD** — `git show HEAD:.truth/claims.jsonl` yields
six, split 3/3. The seventh, `tr-857ab225`, was filed by the operator today at
`2026-08-26T13:56:18Z` and is sitting **uncommitted in the same tree**:

```
$ git show HEAD:.truth/claims.jsonl | grep -c '"evidence_refresh"'
6
$ git show HEAD:.truth/claims.jsonl | grep -c 'tr-857ab225'
0
```

**Severity: MEDIUM-HIGH.** Misleads: mildly — the paragraph's argument ("an
agent can clear a diverged pin, and does") is sound; only its evidence is
wrong. But this is the file's own doctrine failing on itself: a count in
DOCTRINE prose, held by no gate, that went stale in under two days, and
would be committed **alongside the record that falsifies it**.

Fix: delete the tally. The claim that matters — an agent can and does file
`evidence_refresh` — needs no census; if a census is wanted, the grep above
is the home.

---

### F5 — CONTRADICTION: a NORM whose procedure the next paragraph's ENFORCED gate forbids

> line 111: "**Accepted ADRs are immutable in body**; corrections land as
> `Amended by:` lines in the status block (see ADR-002, ADR-004). *NORM.*"
> line 114: "**`docs/archive/` is frozen verbatim**; never update it.
> *ENFORCED, twice*"

Both example ADRs are inside the frozen tree, along with all 54 pre-054 ADRs:

```
$ ls docs/archive/adr/002-* docs/archive/adr/004-*
docs/archive/adr/002-native-work-kernel.md
docs/archive/adr/004-tracker-adapter-seam.md
$ ls docs/archive/adr | wc -l
      54
$ grep -c 'Amended by' docs/archive/adr/002-native-work-kernel.md
3
```

Demonstrated red (in a scratch copy; the tracked tree was never staged):

```
$ printf '\nAmended by: probe\n' >> docs/archive/adr/002-native-work-kernel.md
$ git add docs/archive/adr/002-native-work-kernel.md && bash .githooks/pre-commit
pre-commit: docs/archive/ is frozen verbatim (AGENTS.md); staged:
  docs/archive/adr/002-native-work-kernel.md
A human must lift the freeze deliberately before this can land.   # exit 1
```

**Severity: MEDIUM.** Misleads: **yes**, into work that cannot land. It fails
CLOSED — the cost is a blocked commit and a confused agent, not silent
damage. **Pre-existing**, not introduced here: both lines stand adjacently at
HEAD (`git show HEAD:AGENTS.md | sed -n '34,36p'`). It is carried forward
unrepaired into a redraft whose whole purpose is marking which rules can go
red.

Fix: say that the `Amended by:` convention applies to `docs/decisions/` only,
and that archived ADRs are corrected by a superseding record, never in place.

---

### F6 — REMOVED: the only warning that this repo's CLI path is a symlink

The change deletes:

> "`scripts/truth` is a SYMLINK to `template/scripts/truth`: watch the real
> path in evidence_paths (a watch on the symlink can never fire — git only
> sees the link itself, which never changes)."

and, in the same diff, adds a new pointer *at that path* (line 13: "The CLI
states its own version on `scripts/truth` line 2").

Nothing refuses a symlink watch — it is the documented undecidable residual of
INV-M. Demonstrated in the copy:

```
$ python3 scripts/truth claim "probe" --class VERIFIED \
    --evidence-cmd "sha256sum scripts/truth" --paths "scripts/truth" --tier P2
tr-ca7e05a2        # exit 0, filed, no warning
$ ls -la scripts/truth
scripts/truth -> ../template/scripts/truth
```

**Counter-evidence against my own finding, per house rule 7:** the rule
survives in four other documents —

```
$ grep -rn 'symlink' docs/truth-ledger-paper-v3.md docs/truth-ledger-loophole-map.md \
      docs/truth-ledger-tutorial.md template/.truth/README.md | grep -ci 'can never fire'
4
```

so it is not lost from the repository, only from the meta-repo file, and
"cite, don't restate" arguably licenses the deletion. The residue that is
*not* covered elsewhere is the meta-repo-specific half: that in **this** repo
`scripts/truth` is the symlink, and the file now sends readers there.

**Severity: MEDIUM-LOW.** Misleads: only by omission.

Fix: one clause on line 13 — "(`scripts/truth` is a symlink; watch
`template/scripts/truth`, never the link)".

---

### F7 — UNDERSPECIFIED: an ENFORCED marker that never names its corpus, and the paragraph carrying it is outside that corpus

> line 108: "*ENFORCED for the corpus the arm-index covers; NORM for prose
> outside it.*"

The corpus is two files, and `AGENTS.md` is not one of them:

```
$ grep -n 'PROSE_DOCS' instruments/arm-index.py
116:PROSE_DOCS = ("docs/truth-ledger-paper-v3.md", "docs/truth-ledger-explained.md")
$ grep -c 'AGENTS.md' .truth/arm-index-prose-hashes
0
$ python3 instruments/arm-index.py | grep 'prose cites'
  prose cites      221 hashed [.truth/arm-index-prose-hashes]
```

Every ADR citation in `AGENTS.md` — including the one in this very paragraph —
is unchecked for freshness. The marker is *technically true*, and I want to be
fair about that: it is not a falsehood. But the file's own "How to read this
file" promises the marker tells you "which side of the line you are standing
on", and here it does not: the reader is standing on the NORM side while
reading a sentence that begins ENFORCED.

**Severity: MEDIUM-LOW.** Misleads: mildly.

Fix: name the two documents, or give the grep the file gives everywhere else.

---

### F8 — IMPRECISE, in the conservative direction

> line 513: "it can only see the six that carry a sentence, and only on
> ACTIVE claims"

One of the six is deliberately read from **retracted** claims:

```
$ sed -n '3,4p;98,101p' instruments/semantic-audit.py
Emits the JUSTIFICATION SENTENCES carried by active claims and their
verdicts -- plus `orphan_basis` from retracted ones, which is the single …
# `orphan_basis` is valid ONLY on a retracted claim … so under an
# active-only scope this field would read 0 on every ledger, forever.
```

The error is toward under-claiming coverage, and the sentence's purpose —
"do not read a small count as few gates were bypassed" — survives it.

**Severity: LOW.** Misleads: no.

---

### F9 — the framing sentence is falsified by the body it introduces

> line 40: "Current readings — arm counts, review dates, hook state, which
> pins are stale — live in the mechanisms that report them, and this file
> points at those mechanisms instead of quoting them."

Arm counts and hook state: honoured, and well (F-sound 5, 6). The other two
are not. The file quotes **which pins are stale** (F3) and quotes **review
dates** ("six rows whose next review date had already passed" — true, and
reproducible, but quoted), and carries two `.truth/` counts (F2) which the
same paragraph then apologises for carrying.

**Severity: LOW as a falsehood**, but it is the sentence that licenses a
reader to trust the rest of the file's numbers, so it is worth making true.
This one is a **reading, not a measurement** — I have no single command for
it; the four findings it summarises each have theirs.

---

## Off-scope findings, filed in the same sitting (AGENTS.md line 331)

### O1 — a live instrument's provenance record names the wrong file

`instruments/waiver-index.py:14-16`:

> "The measured cost of having no such list: `--exit-ok`, A FLAG THAT HAS
> NEVER EXISTED, was carried simultaneously by **AGENTS.md**,
> `docs/decisions/059-asynchronous-semantic-audit.md` and
> `instruments/semantic-audit.py`"

`AGENTS.md` has never contained that string, in any revision, anywhere in
history:

```
$ git log --oneline -S '--exit-ok' --all -- '*AGENTS.md'
                       # no output
$ git log --oneline -S '--exit-ok' --all --name-only --pretty=format:'--- %h' \
    | grep -v '^docs/reviews/' | grep -v '^---' | sort -u
docs/decisions/059-asynchronous-semantic-audit.md
instruments/semantic-audit.py
template/CHANGELOG.md
template/scripts/test-integrations.py
```

The real third surface was `template/CHANGELOG.md` — which is also why a
later pass "discovered" it as a *fourth*. The same false attribution is the
origin of item 1 on the handoff's list of nine, and it is the entry on that
list which is measurably false as a defect against `AGENTS.md`.

### O2 — the working tree's `fact-health` is RED, and it rides the battery

```
$ bash scripts/fact-health.sh | tail -1
fact-health: 2 failure(s), 2 warning(s), 34 citation(s), 13 foreign (not judged)   # exit 1
```

Both failures are `docs/governance/catch-log.md` citing `tr-56a8e36c` and
`tr-d0191e65`, diverged by two verdicts filed today and still uncommitted.
**Not caused by `AGENTS.md`** — at HEAD the sweep is green (verified in the
copy: `git show HEAD:.truth/claims.jsonl > .truth/claims.jsonl` then
`bash scripts/fact-health.sh` → `0 failure(s)`, exit 0). But `fact-health`
rides the battery, so a push blocks until `catch-log.md` is repaired.

---

## The nine documented defects, re-measured against this tree

| # | state | evidence |
|---|---|---|
| 1 | **the list's own false entry.** `AGENTS.md` never carried `--exit-ok`, in any revision | `git log -S '--exit-ok' --all -- '*AGENTS.md'` → nothing. See O1 |
| 2 | **PARTLY FIXED, NEW DEFECT.** Generalisation replaced by an enumeration; the enumeration and both counts are wrong | F2 |
| 3 | **FIXED.** Explicitly refuted at line 163 with the right split | of the five non-`.truth/` ids: 3 digest, 2 recipe — verified against each claim's `evidence.command` |
| 4 | **FIXED.** "no scan, no bot, and no NEW `invalidation` record… inert for status, not absent" | `grep -c '"kind": "invalidation"' .truth/claims.jsonl` → `1997`; the file's own command, and it runs |
| 5 | **FIXED.** The audit exists, and what it says is what the file says it says | `docs/reviews/agents-md-audit-and-review-2026-08-24.md:9` — "Four checkably false claims, and all four stale in the optimistic direction" |
| 6 | **FIXED, and improved.** Names sweep-to-gate, states the gate reads the scope file by definition, and discloses that the EXCLUSION list can still diverge | `sed -n '60,69p' AGENTS.md`; exclusion measured inert below |
| 7 | **FIXED.** No line number; a grep, and the reason | `grep -n load_citation_scope scripts/fact-health.sh` → `122,123` |
| 8 | **FIXED.** All three arm references are greps-by-assertion, and all three resolve | `grep -n 'retracted-figures sweep must block' …` → 559 (ARM 17); `'tag-check arm ahead of the battery'` → 364 (ARM 6); `'run THIS gate when the battery moves'` → 459 (ARM 14) |
| 9 | **FIXED, both halves.** No current-version stamp, and the file now carries ten ledger ids that `fact-health` holds | `grep -n 'v0\.[0-9]' AGENTS.md` → one line, a historical reference to the v0.9.15 release, not a version surface. Ten ids demonstrated held below |

---

## Verified sound

Checked and correct, with the commands, so a later reader knows the coverage
and not only the failures.

1. **The ten ledger ids in the file are real, all `live`, and the sweep does
   redden on this file if one dies.** Demonstrated: in a scratch copy, a
   forged `diverge` verdict on `tr-96351a43` turned the sweep red **on
   `AGENTS.md` specifically** —
   `FAIL  tr-96351a43  diverged -- live prose stands on a dead fact`.
   The status set the file names (`stale`, `diverged`, `retracted`,
   `disputed`) is exactly `truth vocab --json .citation_bad`; `unverified` and
   `cannot_verify` do WARN and leave `exit 0`
   (`sed -n '217,223p;233p' scripts/fact-health.sh`).
   This is a real strengthening: at HEAD the file carried **zero** ids and was
   invisible to its own tripwire (`24` citations swept at HEAD vs `34` now).

2. **`truth reproduce` exits 7 on an edited pin; the read verbs cannot go
   red.** Demonstrated in the copy by appending one line to
   `.truth/accept-allow`:
   `reproduce: 64 live claim(s) -- 63 reproduces, 1 capsule-stale`, `exit 7`;
   `truth list --live` → `exit 0`; `truth list --diverged` → `exit 0`.
   Restored and proven byte-identical:
   `ae9f68171fb43bf5952f0a367b6019684fe1daa15d57def9b8e6931592d73805`.
   The battery does invoke it exactly as the file says —
   `scripts/release-battery.sh:391: OUT=$(python3 template/scripts/truth reproduce 2>&1)`,
   with `7)` mapped to `bad` at line 399.

3. **`docs/archive/` is enforced twice, and both halves go red.** pre-commit
   refuses a staged path (exit 1, output in F5); the whisper hook returns
   `permissionDecision: "deny"` for `docs/archive/…` and for
   `.truth/claims.jsonl`. Wiring confirmed: `.claude/settings.json` →
   `PreToolUse` → `python3 scripts/truth-whisper.py`, matcher
   `Edit|Write|MultiEdit|NotebookEdit`; counter present at
   `.git/truth-whisper.seen`.

4. **`truth doctor` is the only thing that reports `core.hooksPath`, and it
   does.** `git config --get core.hooksPath` → `.githooks` today.
   Demonstrated in the copy: with it unset, doctor emits two FAILs naming both
   hooks and exits 1. Nothing else runs doctor —
   `grep -n doctor scripts/release-battery.sh .githooks/pre-*` → no output,
   so the file is right that you must run it yourself.

5. **The version paragraph is exact.** `scripts/truth` line 2 states
   `truth v0.10.0`; `TestCrossSurfaceVersions` pins **five** other surfaces —
   README title, loophole-map header, operations-guide header,
   `check-truth.sh`'s "current CLI:" line, `truthlib/cli.py` docstring line 1
   (`awk` over `template/scripts/test-truth-core.py:3136-3222`). The schema
   `$id` tests in the same class are a separate two-component contract
   version and are correctly not counted. The file adds no seventh surface.

6. **The three grep-by-assertion pointers all resolve** (row 8 above), and
   the honesty about ARM 17 is exact: the mutation half really does prove
   blocking, and the empty-policy half really is
   `grep -q 'no figure retracted yet' scripts/release-battery.sh` —
   the branch is written, not exercised.

7. **The fact-health exclusion list is inert today, exactly as claimed.**
   Expanding `.truth/citation-scope` through the CLI loader and applying the
   six `grep -v` lines: 39 files before, 39 after, zero removed. So
   "Add `docs/reviews/*.md` to the scope file and the divergence reopens
   silently" is a live, unguarded hazard, correctly disclosed.

8. **The canary sandbox guard is real and is genuinely UNGATED.** Both
   refusals present in `mkrepo()` (`cd "$1" || … exit 1`, then an outright
   refusal if `git rev-parse --show-toplevel` succeeds), landed in `441de48`
   (2026-08-21). And nothing tests it:
   `grep -rn 'cannot enter sandbox\|INSIDE an existing git repository\|mkrepo'`
   over `test-release-battery.sh`, `test-integrations.py`,
   `test-truth-core.py`, `release-battery.sh` → no output. "MECHANISM,
   UNGATED" is the correct marker.

9. **The intake refusals the file names all fire.** `--cause restated`
   without `--successor` refuses ("Nothing was filed."); `verdict retracted`
   with a valid successor and no `TRUTH_HUMAN` refuses on G12; the ADR-055
   freehand budget refuses a 6-path set and names all three exits
   (`--watch-policy`, `--paths-ok`, `path.json#/a/b`) — matching the file
   clause for clause.

10. **The flag census is right.** Six sentence-bearing, four bare booleans,
    one on a value; the six and the four are named correctly and match
    `waiver-index`'s `flag inventory 11`. `--single-run` really does leave no
    field (`NOT COUNTABLE`), while `--duplicate-ok` leaves
    `overridden_duplicates` (23 records), `--accept-unsafe-ok` leaves
    `accept.screened=false` (5) and `--evidence-unsafe-ok` leaves
    `evidence.screened=false` (0). "Flags are only one of six carriers"
    matches `docs/waivers.md`'s carrier table exactly (flag, env, file,
    syntax, config, code).

11. **The Python-floor rule is enforced and the gate is not inert on this
    machine.** `structural.py` guards `import tomllib` with
    `try/except ModuleNotFoundError` and degrades to a refusal naming the
    interpreter; the canary's tracker arms really do run under
    `PATH="/usr/bin:/bin"` (11 sites), and here
    `PATH="/usr/bin:/bin" python3 --version` → `Python 3.9.6`. Worth stating
    because a gate that pins "3.9" is worthless on a box whose `/usr/bin`
    ships 3.13; this one is live.
    *The "nine arms went CAUGHT → MISSED" figure is sourced from the code
    comment at `structural.py:46`, not re-measured — **TESTIMONY**.*

12. **The gate-metrics finding reproduces.** `grep -n '2026-08-08'
    docs/governance/gate-metrics.md` → six table rows (48, 49, 50, 52, 53,
    54) plus the prose line at 149 naming the R11 audit;
    `grep -rn 'Next review' scripts/ instruments/ template/ .githooks/` →
    nothing. Six dates in the past, no reader. The file's account is exact.

13. **Both git commands the file hands the reader work.**
    `git rev-list --count $(git merge-base main HEAD)..main` → `0`;
    `git log --format='%h %an' | grep test-actor` → exactly **four** commits
    (`a647b08 6711609 4198ed2 64f278c`), matching "the next FOUR commits by
    two different sessions".

14. **The remaining mechanism claims check out**: the ADR-045 flock is placed
    at `os.path.join(gd, …)` from `git rev-parse --git-dir` (`shellio.py:428-439`);
    `.truth/claims.jsonl merge=union` is in `.gitattributes`; `.venv/` is in
    `.gitignore:6`; `template/docs/**` is absent from `copier.yml`'s
    `_skip_if_exists` (which holds exactly `AGENTS.md`, `CHANGELOG.md`,
    `.truth/evidence-allow`, `.truth/accept-allow`, `.truth/generated-paths`);
    `test-integrations.py` names exactly the five classes listed and runs at
    `release-battery.sh:292`; the pre-push WARN branch carries no `exit` and
    the FAIL branch exits 1, with the battery `exec`'d after both. Every ADR
    status the file states — 055 ACCEPTED over an unmet condition, 056
    ACCEPTED without the adversarial pass, 057/058/059/061/062 PROPOSED,
    058 "deliberately NOT WIRED" with the 2026-08-23 operator ruling —
    matches the record's own status line. The ADR-062 role table is a
    faithful copy of the one in `062-multi-agent-roles.md:38-43`.

15. **The self-account of the previous round is accurate.** The audit did find
    four falsehoods, all optimistic (`…audit-and-review-2026-08-24.md:9`), and
    the fifth of the opposite kind is real and is where the file says it is
    (`…verification-2026-08-24.md:44` — the redraft's "Nothing prevents any of
    this today. It is prose." about a guard that had shipped three days
    earlier).

---

## What I could not reproduce with a command

- **F9** is a reading of the file against itself, not a measurement. The four
  quoted-number findings it generalises each carry their own command.
- The **"nine arms went CAUGHT → MISSED"** figure (line 547) and the
  **2026-08-18 diagnosis numbers** (line 559: `validate_events` 96.6%,
  173/179 mutants; 165 citation edges; 79%→47%) are **TESTIMONY**. They are
  historical, they have homes in a code comment and a dated review, and I did
  not re-run the mutation suite. I am not calling them defects; I am marking
  that this review did not check them.
- I did **not** run the release battery or the canary (forbidden by the
  handoff, and both write git state), so every claim about what happens *at
  push* is verified by reading the wiring and by running the individual
  sweeps, not by a push.

---

## Should this be committed as it stands

**No — but it is four sentence-edits away from yes.**

F1, F2, F3 and F4 are counted assertions that are false against this tree
right now. Three of the four are wrong in the **optimistic direction**, which
is the direction this file's own audit history says every previous falsehood
took. F1 is the one that matters most: it re-imports, into the file every
agent reads first, a totality claim that `docs/waivers.md` was retitled to
destroy one day earlier, and it is a claim about the *escape surface* — the
register of every way a gate can be lifted.

None of them require restructuring. F2 and F4 are deletions the file's own
doctrine already prescribes ("Do not maintain the membership here — ask the
ledger"). F3 and F1 are re-statements of what the two instruments already
print. F5 is a pre-existing contradiction worth fixing while the file is open.
F6 and F7 are one clause each.

The change itself is a substantial net improvement and I want that on the
record: it retires nine documented defects, replaces four brittle
line-number and arm-number references with greps that cannot rot, marks
which rules can go red, and — most importantly — takes `AGENTS.md` from
carrying **zero** ledger ids to carrying **ten**, all live, with the sweep
demonstrated reddening on this file. That last change is the one that makes
the next review cheaper, and it is the part of this change I would least want
to see delayed by the four sentences above.

**One caveat on the commit itself, independent of the file:** the working
tree's `fact-health` is currently red for an unrelated reason (O2), and it
rides the battery. Repair `docs/governance/catch-log.md` or the push will be
refused for someone else's finding.

---

## Session hygiene

No tracked file was modified. All destructive probing was done in a full copy
of the repository under this session's scratch directory. `AGENTS.md` closes
at the sha it opened at:
`61421cf165b84b254e45628ba7ca8a2494eb92a8c770b91da8629bdbcaf80e06`.
`.truth/claims.jsonl` was never written and never staged. No
`git checkout <path>`, `git restore`, `git stash` or `git reset` was run in
the tracked tree. This document is the only file added.
