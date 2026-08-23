# truth CLI — version history

Extracted verbatim from the `scripts/truth` module docstring at
v0.9.13 (roadmap-v3 R5): the history block had grown past 500 lines.
The CLI still states its CURRENT version on its own line 2
(`"""truth vX.Y.Z -- ...`) — the ADR-026 lockstep test
(`TestCrossSurfaceVersions` in scripts/test-truth-core.py) parses that
line and pins every other version surface to it. Newest first; a
release adds its entry here AND bumps the docstring version line.

v0.10.0 (the clock stops being an event; two verbs retired, one added.
  No schema change -- the record $id stays `truth-ledger-record.v0.18`.):

  -- WHAT THIS ENTRY RESTS ON ---------------------------------------------
  * `v0.9.38` was tagged before the Reproduce-on-Read refactor's later
    steps, FAZA 3 and FAZA 4 landed; 122 commits sit between that tag and
    this entry (`git rev-list --count v0.9.38..HEAD`). Of those, 23 touch
    code a consumer receives -- everything else is this repo's own ledger,
    governance and journals.
  * Every figure below is quoted from the commit that produced it or from
    the ADR it implements, not reconstructed by reading the code. Where a
    change is recorded only as code, it is named and left undescribed
    rather than guessed at.

  -- BEHAVIOUR CHANGES, read these first ----------------------------------
  * **Evidence commands no longer run through a shell (ADR-041, `4198ed2`;
    what shipped and what it does NOT close: the meta-repo's ADR-056).**
    The screen tokenized with `shlex` while the executor handed the same
    string to `subprocess.run(shell=True)`: two interpreters reading one
    string, and every divergence between them was a channel. ADR-021 closed
    the newline; the 2026-08-01 audit found three more (`uniq *` is one word
    to shlex and N to `/bin/sh`; `cat <>F` CREATES the file the `<` branch
    read as input; `>1` writes a file named `1` behind the fd-dup carve-out).
    Enumerating them does not terminate, because only `/bin/sh` implements
    `/bin/sh`. The screen's parse IS the execution now:
    `evidence.parse_evidence_command` emits argv arrays with resolved
    descriptors and glob patterns, and `shellio.run_evidence` runs them with
    `shell=False`, plumbing pipelines, and-or lists, `>/dev/null`, `2>&1`
    and `<FILE` itself. Below the parser there is no string, so "the
    screen's model diverges from the executor's" is inexpressible here, not
    merely false. Evidence: all 196 distinct evidence commands in this
    ledger yield an identical `(output_hash, returncode)` pair under
    `/bin/sh` and under the runner; `scripts/adr041-hash-stability.py`
    ships with the template so a consumer can re-run that comparison on
    their own corpus before upgrading.
  * **TTL expiry is derived at read time, not written (ADR-057, `68ef221`).**
    See the dedicated section below.

  -- SECURITY -------------------------------------------------------------
  * **A write channel the evidence screen accepted (SEC-0, `8970f5d`).**
    `tok.isdigit()`, present so `2>&1` could name descriptor `1`, also
    admitted `>2` -- a write to a file named `2`. Confirmed in a sandbox:
    `>2` and `>22` created files. The lexer had always distinguished them;
    the screener had not. Now a token ending in `&` is a dup redirect
    (target: a digit or `-`), and plain `>`/`>>` is an out redirect whose
    only legal target is `/dev/null`. The `>/dev/null 2>&1` convention is
    untouched. Two regression arms pin both sides.
  * **Two Tier A gates were DEAD, not degraded (step 0.1, `8970f5d`).**
    `truth list --json` is 145576 B against a `MAX_ARG_STRLEN` of 131072 B,
    so `execve` refused the whole environment and `fact-health.sh` and
    `spec-health.sh` -- both shipped to consumers -- never ran. The ledger
    JSON now travels by FILE (`CLAIMS_FILE`/`ISSUES_FILE`, mktemp + trap),
    not by environment variable. `spec-health`'s header had been measuring
    the wrong constant (`ARG_MAX` ~1 MB instead of `MAX_ARG_STRLEN` 128 KiB),
    which is why nobody reacted in time.

  -- NEW: WATCH SETS STOP BEING ASSEMBLED BY HAND -------------------------
  * **Named watch policies, `claim --watch-policy NAME` / `list
    --watch-policy NAME` (FAZA 3 step 3.1, `ee7902a`).** Measured on this
    ledger: 75 active claims carrying a watch set produced 60 DISTINCT sets
    -- reuse near zero. The file format is one `<name> -- <glob>[, <glob>]`
    line per policy, deliberately NOT YAML: the CLI is stdlib-only and a
    `.yml` extension would promise a generality the loader must refuse. A
    policy RESOLVES the set rather than annotating it, before the
    `INTAKE_GATES` table, so INV-M, the ADR-039 forecast and the ADR-038
    advisory judge its globs exactly like a hand-written list. The payload
    carries the name AND the resolved globs, because the ledger is
    append-only and editing the policy file must not rewrite what past
    claims consider themselves to be watching. An unknown name ENUMERATES
    the defined ones: a typo must not quietly file a claim watching
    nothing, which is the INV-M defect reached by a spelling mistake.
  * **The watch budget as a hard refusal (step 3.2, `79750ed` + `0dbfc87`).**
    Two rows in `INTAKE_GATES`. `paths-budget-max`
    (`MAX_FREEHAND_WATCH_PATHS=1`) asks whether a set was CHOSEN or
    accumulated; `paths-churn-budget` refuses a set whose ADR-039
    `blast_forecast` reaches the self-calibrating floor. Two exits, both
    leaving a trace, and no silent third: `--watch-policy <name>`, or
    `--paths-ok "<sentence>"` (stored as `paths_basis`, decaying at 30 days
    per ADR-032, counted in the override report). Refusals are symmetric
    with the ADR-035 precedent: `--paths-ok` beside a single path, or
    beside `--watch-policy`, is itself refused -- a basis that excuses
    nothing is schema noise. ORDER IS LOAD-BEARING and is pinned: all 17
    freehand claims at or above the churn threshold carry >=2 paths, so
    with the count row first the churn row would NEVER have fired -- a dead
    row impersonating coverage.
  * **Structural anchors: a watch target may name a sub-tree
    (`2822d8e` + `be0b4da`).** `package.json#/dependencies/stripe` is
    insensitive to a `version` bump; `pyproject.toml#tool.ruff.lint` to
    edits in `[tool.pytest]`; `docs/spec.md#2-jwt` to edits in other
    sections; a bare path is an ordinary whole-file digest. `.json`,
    `.toml` and `.md` only. SCOPE IS DELIBERATELY NARROW -- RFC 6901 and a
    dotted path, no wildcards, no array slices, no predicates: point
    addressing, not a query language. The hash is canonical (`sort_keys`,
    tight separators, `ensure_ascii=False`), and JSON and TOML share one
    domain, so equal values hash equally across formats and migrating a
    dependency between the two files keeps the anchor. Mutation score
    95.6% (129 of 135 killed; the surviving 6 are argued equivalent).
    Wired through exactly two seams -- `kernel.watch_target_path` for the
    file half, so all six readers of `evidence_paths` are selector-correct
    without knowing selectors exist, and `shellio.structural_hash` as the
    only place a file is read for a selector. A `package.json` that no
    longer parses reports `malformed`, never drift: it says nothing about
    `/dependencies/stripe`, and calling that drift would be the false
    alarm this feature exists to remove.

  -- NEW: `truth health` --------------------------------------------------
  * **`truth health [--json] [--reproduce]` (FAZA 4 steps 4.1/4.2,
    `0131a92`).** Reports, refuses nothing. The reason is not speed --
    measured, five instruments are five processes, five folds and 0.55s
    against 0.15s for one fold -- it is that `instruments/` IS NOT
    TEMPLATED. ADR-046 moved five pure ledger projections into meta-repo
    instruments, which left a generated consumer repo seeing `truth stats`
    and nothing else: no override velocity, no verifier-separation
    evidence, no churn report, no retraction causes, no staling breakdown.
    The measurements that say whether someone's ledger is being kept
    honestly existed only in the repo that publishes the tool. `health` is
    composition, not a rewrite: every section is an existing pure function
    called with one shared `folded`. The watch-adoption section lands here
    rather than in `stats`, which resolves the tension step 3.1 hit --
    ADR-046 ruled that `stats` carries the Tier B core, and `health` is the
    "elsewhere" that ships.

  -- INTERNAL: no behaviour change, stated because the shape moved --------
  * `truthlib` A-series (`fed4a1f` A1, `44f4ec8` A4, `37c0071` A2,
    `d76bda3` A3, `0dd321f` V1): refusals RETURN and the shell exits
    (`run_intake_stage` had broken its own table's contract one frame up);
    `main()` becomes a verb table instead of 370 lines of hand-copied
    argparse for 23 verbs; `advisory` is split BY CRITERION into
    `reports.py` and `contract.py` (932 lines -> 236) because a module
    defined negatively is where the next drift lands; and the ADR-044
    entry-point monkeypatch mirror -- a `_MirrorModule.__setattr__` plus a
    `gc.get_referrers()` walk in the production loading path -- is retired,
    its equivalence proof having been delivered. Every refusal byte and
    exit code is unchanged.
  * `doctor` resolves a delegated gate (ADR-054, `c84bfcd`). `find_gate_hook`
    stops testing the whole file and requires the needle at a CALL POSITION
    -- a non-comment line of the hook, or of a file the hook delegates to,
    one hop. ADR-054 had claimed "implementation lands with this record"
    since `39e1052`; until this commit that was untrue.
  * Recipe lint for fail-open shapes (`182f1fa`). WARNS, never refuses --
    a gate that refuses legal filings teaches its own workaround (the
    ADR-014 lesson). It fires when a `grep` recipe carries a flag making
    its output a SET OR ITS SIZE (`-c`, `-o`, `-l`, `-L`, long and bundled
    forms), because such a recipe counts what its pattern RECOGNIZES rather
    than what exists: a form invented later simply does not appear, the
    number stays plausible, and the capsule reproduces green after its fact
    has drifted.
  * The canary guards its own sandbox (`441de48`). `mkrepo()` did a bare
    `cd "$1"` with no `|| exit` under `set -u` and no `set -e`, so a failed
    cd let `git init -b main .` run wherever the shell was standing. The
    2026-08-20 answer to that was a SENTENCE in AGENTS.md; this repo has
    its own measurement that sentences do not hold, so it is a mechanism now.

  -- STILL UNWRITTEN ------------------------------------------------------
  * Reproduce-on-Read steps 0.1/1.x/2.1-2.3 and the FAZA 3 step 3.3 pilot
    migration have no entry here beyond what is quoted above. So does
    `f53ee93` (a dead flag choice removed from scope-decay, 5 mutants
    killed) and `a5aa4b7` (`arm-index` wired as a battery arm). None
    changes a shipped contract; all are recorded in `docs/refactor/`
    and in their commit messages.

  -- CLI SURFACE DELTA SINCE v0.9.38 (computed, not remembered) ------------
  * REMOVED: `invalidate-scan`, `reaffirm`. Both were write paths for a
    staling proxy that fired 1997 times against 71 judged divergences on
    this ledger -- a 3.6% positive predictive value. `truth reproduce`
    (v0.9.38) answers the same question semantically at read time.
    Nothing replaces `invalidate-scan`; `verdict --recheck` remains the
    per-claim re-confirmation. No aliases.
  * ADDED: `health`.
  * `ttl-scan` -- the interim verb step 2.6 narrowed `invalidate-scan`
    into -- was born and died between two unreleased commits and NEVER
    SHIPPED. A consumer upgrading from v0.9.38 has never been able to
    call it, so it needs no deprecation path.

  -- READ-TIME TTL (ADR-057, meta-repo docs/decisions/057-*.md) ------------
  * `fold(events, now_dt=None)`. The clock is a PARAMETER, so the fold
    stays a pure function of its two arguments and confluence is
    untouched: same events + same instant fold to the same state in any
    input order. `now_dt=None` (the default) evaluates no TTL at all,
    which is what keeps `baseline` byte-reproducible.
  * ADR-019's arithmetic is unchanged -- the shelf life counts from the
    claim's own `ts`, the boundary is strict -- and now lives in
    `kernel.ttl_expiry`, successor to `policy._ttl_expired`.
  * The `invalidation` record kind is WHOLLY INERT for status. Step 2.5
    had already retired the path arm; the TTL arm joins it. The ~1997
    records already written stay in the ledger and stay readable; a
    replayed or forged expiry record can no longer stale a claim the
    clock says is fresh.
  * `status_ts` for a derived `stale` is the EXPIRY INSTANT
    (`claim ts + ttl_days`), never the reader's `now` -- so two readers
    agree on it, and queue aging prices from when the fact expired
    instead of reporting a long-dead claim as zero days old.
  * REMOVED with the verb: `INVALIDATORS`, `decide_invalidation`,
    `_ttl_expired`, and the strategy seam itself. An empty tuple would
    have advertised a seat for exactly the design being retired.
  * The shipped `truth-scan.yml` drops to `permissions: contents: read`.
    Gone with the writer: the bot identity, its commit-back, its push,
    the `[skip ci]` marker, the actor loop-guard and the concurrency
    queue -- all of which existed only to contain that one write. An L1
    instrument no longer holds commit access to the branch it measures.
  * Consumers running `truth ttl-scan` in CI: you cannot be, see above.
    Consumers whose CI ran `invalidate-scan`: remove the step; expiry is
    visible in `truth list --stale`, `truth queue` and `truth health`.

  -- META-REPO ONLY, NOT SHIPPED TO CONSUMERS -----------------------------
  * `scripts/epistemic-isolate.sh` (ADR-058): restores the measuring
    apparatus from origin/main so a judging run cannot use an instrument
    it authored. Implemented, tested, and deliberately WIRED TO NOTHING --
    a local pre-push hook cannot isolate the very thing a local change is
    editing without blocking honest work. Operator ruling 2026-08-23:
    isolation belongs at the CI/CD boundary, which this repo does not yet
    have. Residual recorded in the ADR, not papered over.
  * `instruments/semantic-audit.py` (ADR-059): extracts the justification
    sentences that intake gates admit -- `--scope-ok`, `--paths-ok`,
    `--generated-ok`, `--exit-ok`, `--refresh-evidence` from ACTIVE
    claims, plus `--orphan-ok` from retracted ones -- as flat JSON for an
    external reader. The gates check a sentence EXISTS; nothing has ever
    checked it MEANS anything, and a model asked to rule on an argument
    is a judge, not a measurement (EPI-305), so the judging half lives at
    L2. NO NETWORK I/O, pinned structurally by the integration suite.

v0.9.38 (one new READ verb, one behaviour change to `doctor`, the
  structural view, and the acceptance instrument for the coming
  refactor; no schema change, fold untouched):

  -- BEHAVIOUR CHANGE, read this first ------------------------------------
  * **Evidence commands no longer run through a shell (ADR-041; what
    shipped, what it does NOT close, and the open questions answered: the
    meta-repo's ADR-056).** The
    screen used to tokenize with `shlex` while the executor ran
    `subprocess.run(cmd, shell=True)`: TWO interpreters reading one
    string, and every divergence between them was a channel. ADR-021
    closed the newline; the 2026-08-01 audit then found three more
    (`uniq *` is one word to shlex and N to `/bin/sh`, `cat <>F` CREATES
    the file the '<' branch read as input, `>1` writes a file named `1`
    behind the fd-dup carve-out). Enumerating them does not terminate,
    because only `/bin/sh` implements `/bin/sh`. The screen's parse is now
    the EXECUTION: `evidence.parse_evidence_command` emits argv arrays
    with resolved descriptors and glob patterns, and
    `shellio.run_evidence` runs them with `shell=False`, plumbing
    pipelines, `&&`/`||`/`;`, `>/dev/null`, `2>&1` and `<FILE` itself.
    **What this refuses that it used to accept**: `$VAR`/`${...}`
    expansion (a literal under the runner would silently change the
    recorded output -- an anchored `grep "a$"` still passes, because
    `$` only expands when what follows can name an expansion), `~`,
    `<>`, `&` backgrounding, `>&-`, a glob in program position, and
    `2>&1 >/dev/null` (the runner captures one stream). Nothing else
    moved: all 196 distinct evidence commands in the two ledgers produce
    a byte-identical output hash and exit code under the new runner
    (`TestShellFreeEvidenceRunner` pins the shapes; canary FAULT SF1-SF5
    pin the channels). The ADR-014 acceptance oracle is untouched -- it
    executes repository code on purpose and still runs through the shell.
    `scripts/adr041-hash-stability.py` ships with the template so you can
    run that same check against YOUR ledger before adopting this version;
    it exits non-zero on any command whose hash moves or that the new
    parser refuses.
  * `truth doctor` now FAILS on a committed-but-EMPTY policy file that
    carries no dated attestation (`.truth/generated-paths`,
    `.truth/citation-scope`). ADR-034's SI-4 reads committed-empty as
    "consciously configured" and stays silent; ADR-042 rule 2 says zero
    coverage is a failure. Both were on record and they contradict; SI-4
    won by being older, not on merit. An empty file must now SAY it is
    empty: `# attested YYYY-MM-DD: <reason>`. **Every existing consumer's
    doctor goes red until one line is written per empty policy file** --
    that is the intended and only effect on them. The template ships the
    instruction and an example, deliberately NOT the attestation line: an
    inherited attestation records nothing. Argued, with the case against
    (ADR-045 chose WARN in the same adoption shape), in ADR-053.
  * Cross-check, WARN never a refusal: `doctor` names tracked files under
    conventionally generated directories that the committed list does not
    cover. An attested "nothing here is generated" is a claim about the
    repository, and only the repository can contradict it. On the pilot
    consumer it names 25 files at once.

  -- NEW VERB -------------------------------------------------------------
  * `truth reproduce [--since] [--arm] [--json]` -- re-runs every LIVE
    claim's evidence capsule and classifies the outcome: `reproduces` /
    `capsule-stale` / `unexecutable` / `no-capsule`, with `capsule-stale`
    split four ways (`uncommitted`, `watched-moved`, `orphaned-capsule`,
    `unexplained`) because one count is four different repairs. Read verb:
    outside WRITE_VERBS, no ledger lock, files NOTHING -- a mismatching
    hash is ADR-012's judgment call and a batch verb has no judge.
    Exit 7 when any capsule no longer reproduces; exit 8 when the sweep
    examined ZERO claims (ADR-042 rule 2: measuring nothing is a failure,
    not a pass). Execution reuses the screened path `--recheck` and
    `reaffirm` use, against the ADR-051 effective capsule; the one
    addition is `cwd=repo_root()`. Argued in ADR-052, which ADR-051's own
    Non-goals section named and owed a record.
  * Measured on the pilot consumer: 126 live claims, 86 reproduce, 7
    capsule-stale (all orphaned-capsule), 11 unexecutable, 22 no-capsule --
    cross-checked against a reimplementation written from the ADR text
    rather than from truthlib, with zero per-claim disagreements. The same
    commit gave 78/13 in a Linux container and 82/9 in a clean macOS
    worktree: four claims depend on the machine, two more reproduce only
    on a tree carrying gitignored `__pycache__`.
  * Canary FAULT RP: five arms including a negative control, each seen RED
    against its own named mutation. RP2 is seeded as a RAW LEGACY RECORD,
    because since ADR-051 the CLI refuses to create an orphaned capsule --
    the only way to seed the population that still exists in deployed
    ledgers is to append the pre-ADR-051 shape directly.

  -- META-REPO INSTRUMENTS (not shipped to consumers) ----------------------
  * `instruments/field-consumers.py` fails any payload field with no
    reader, enumerating keys MECHANICALLY from the ledger. Detection is an
    AST walk, not a grep, and a PRESENCE TEST IS NOT A READER: it found
    `reaffirm_cleared`, riding 1072 records, whose only consumer asks
    whether it is there. The version that counted every read as a reader
    reported that field healthy.
  * `instruments/fingerprint.sh` (99 probes, all 23 verbs) + baseline +
    `reprove-fingerprint.sh` (four classes) + `reprove-verbs.sh` (28 rows,
    one per appended probe block): the acceptance instrument for the A1-A5
    refactor, with its sensitivity re-proved against seeded mutations in
    the reader's own tree. Its declared coverage limits are written down
    rather than implied -- including the ones that remain.
    It reached 99 the hard way. At 50 probes it claimed "every refusal
    path ... every intake gate ... every non-trivial exit code" while
    EIGHT verbs (`ready`, `baseline`, `dispatch`, `stats`, `queue`,
    `issues`, `invalidate-scan`, `reaffirm`) had no probe at all, `list`
    was used but never recorded, exit codes 4 and 7 were emitted by
    nothing, and the ADR-037 generated-artifact refusal was unreachable
    because the sandbox committed an EMPTY `.truth/generated-paths`
    (SI-4: consciously nothing generated). Worst: the tracker refusal
    that a refactor MOVED, whose commit certified "the refusal strings
    are unchanged" against this instrument, could have any word replaced
    with an empty diff. Per-probe stderr also went to a hardcoded
    `/tmp/fp.err`, so two concurrent runs -- `diff before.txt after.txt`
    is two runs -- clobbered each other into a garbage diff.

  -- THE STRUCTURAL VIEW --------------------------------------------------
  * NEW `docs/structure.md`: the decomposition the system never had. Nine
    drawn viewpoints existed and every one was behaviour or flow, so the
    module DAG (ADR-044), the tier boundary (ADR-046) and the intake-stage
    order (ADR-034) had to be reassembled from five ADRs by every reader.
    They are now one document, plus a stakeholder/concern table restoring
    the 42010 anchoring that `--concern` reached for and the envelope rule
    correctly evicted at v0.9.30 (it costs nothing in prose).
  * PINNED, relationally: `TestStructureDocMatchesDisk` derives BOTH sides
    at run time -- modules from `truthlib/`, edges from `ast`, the purity
    boundary from TestModulePurity -- and compares. No expected value is
    written down, so a count pinned to a literal cannot pass while a module
    is added. The drawn DAG is checked as a faithful transitive REDUCTION
    (every arrow real, same reachability), because drawing all 18 edges is
    a hairball nobody reads.
  * Stated in the test, because it is a real constraint: this cannot be a
    claim. Comparing two COMPUTED values needs command substitution, which
    the ADR-009 screen refuses by design. A claim could pin only one side,
    and `reaffirm` would auto-agree while the two drifted -- the shape
    measured on a consumer ledger as 13 orphaned capsules.
  * `docs/diagrams/asbuilt-architecture.md` marked SUPERSEDED for structure
    and kept as the v0.9.13 snapshot it is. Its running header -- ~3,000
    words of version deltas prepended over 20 releases, never once drawing
    `truthlib/` -- is the restatement-instead-of-citation failure (paper
    section 5) occurring in the architecture description of the artifact
    that mechanises citation.

v0.9.37 (ADR-013 redirects applied by every premise-map consumer;
  no schema change, no fold change, no gate semantics change):
  * `truth issues` now applies apply_supersedes(), matching `ready`,
    `impact` and `premise`. Four verbs build a premise map with
    merge_premises(); three followed it with the ADR-013 derivation and
    `issues` did not, so two verbs of one CLI answered differently about
    one fact. Observed on a real ledger: an issue listed both its
    successor premise and that premise's RETRACTED predecessor, while
    `ready` correctly honoured the redirect.
  * The property is now a test, not an instance: an AST arm walks cli.py
    and fails any function calling merge_premises() without
    apply_supersedes(), so a future verb that forgets reddens at once.
  * Display change only. The raw links stay permanent records in the
    ledger -- premise-at-birth payload, redirect record and replacement
    claim are three separate lines -- so history is not lost; this verb
    reports EFFECTIVE state, which is what governs readiness.

v0.9.36 (ADR-051 capsule coherence -- an agree carries the capsule with
  the anchor; schema $id v0.18, one new verdict field, no fold change):
  * `verdict <id> agree` on a path-claim now RUNS the screened evidence
    command once and REFUSES when the capsule no longer reproduces --
    that agree would advance the effective anchor (F2) past an immutable
    capsule, leaving the claim live and permanently un-recheckable
    (measured: 13 of 126 live claims, 10 of 77 retractions).
  * `--refresh-evidence "<sentence>"` files it, storing
    `evidence_refresh {output_hash, returncode, basis}` on the VERDICT.
    `--recheck` and `reaffirm` compare against the newest refresh
    (`effective_evidence`), so a refreshed claim RETURNS to reaffirm's
    hash-match arm.
  * BREAKING for scripted agrees: a plain `agree` over a changed output
    now exits non-zero. The refusal names both exits (refresh, diverge).
  * Counted as `evidence_refresh_filings` in the override report (CC-2).
  * Verifier prompt: the step-1 stop rule is qualified, and a new
    reproducible-by-whom step precedes the verdict rules.
  * Absent `evidence_refresh` stays valid forever (validate runs inside
    the commit gate; refusing history would wedge consumer repos).

v0.9.35 (ADR-050 staling breakdown -- report what the ledger's central
  rule costs; no schema change, no gate semantics change, fold untouched):
  * `truth staling [--since TS] [--append-order] [--json]` (new read verb):
    folds the event stream into staling EPISODES -- one opens at the first
    invalidation on a claim and closes at the next verdict on it, so repeat
    invalidations on an already-stale claim are re-stalings, not new
    episodes -- and buckets each resolution as auto-healed by `reaffirm`,
    hand-agreed, or genuinely changed. Also reports which kind of watched
    path triggered stalings, bucketed by file suffix; a semantic
    spec-vs-implementation split is deliberately NOT attempted, because the
    template cannot know a consumer's layout.
  * Walk order is the kernel's canonical `fold_key` (ts, id, canon; ADR-016)
    because statuses are DEFINED by that fold. `--append-order` walks the raw
    file, kept so measurements taken before this verb stay reproducible
    through the shipped surface; the walk is stamped on every output and two
    canary arms pin both walks against a fixture where they disagree.
  * Tier: an argued exception to ADR-046, stated as such in ADR-050's header.
    The report families left the CLI for meta-repo `instruments/`, which is
    not templated -- so Tier C would put this question permanently out of
    reach of the consumers who have it, and what is priced here is not a gate
    but the kernel's central rule.
  * 17 unit tests, 8 canary arms (FAULT ST), including two negative controls
    and a deletion control. Canary 261 -> 269.
  * No refusal, no advisory, no exit-code change. A high false-stale rate is
    not a defect to refuse: narrowing a watch trades false stalings for
    missed ones, and this report deliberately cannot see the second kind.

v0.9.34 (ADR-049 retraction cause -- entry written at v0.9.35; the release
  itself shipped without one, which is the gap this line closes):
  * `verdict <id> retracted` gains `--cause {restated,expired,wrong}` and
    `--successor TR_ID`: a retraction records WHY the fact died, and
    `restated` owes a successor that carries it forward. A bare tombstone
    left the reason to a free-text basis nobody could fold.
  * Registry constant `RETRACTION_CAUSES`; schema and canary arms alongside.

v0.9.33 (ADR-048 check reachability -- the audit remediation: a check no
  scheduled root invokes is prose, and four of ours were; no schema
  change, no gate semantics change, fold untouched):
  * `scripts/gate-reachability.sh` (meta-repo, new): enumerates every
    git-tracked executable check mechanically, enumerates the scheduled
    roots (`.githooks/*`, the harness hooks, and `install-hooks.sh` as a
    template root), and computes reachability as a transitive closure to
    fixpoint. Unreachable FAILS, excusable only by a committed reason in
    `.truth/reachability-opt-out` (ADR-037 policy semantics: absent =
    dark + loud, empty = conscious, populated = armed; a stale excuse
    also fails). It enumerates ITSELF and fails if it is unreachable or
    examined zero checks. First sweep found five dark checks.
  * The four orphaned suites are WIRED, not excused, so the opt-out file
    ships committed-empty: `test-fact-health` (10 arms), `test-instruments`
    (18), `test-whisper-hook` (5) and `test-session-digest` (3) now ride
    the battery through a `gate_arm` helper that judges each by its own
    "N caught, M missed" line -- no summary, zero caught, any missed, or
    a non-zero exit all FAIL (ADR-042 rules 1-2, enforced). Battery cost
    measured: ~9s -> ~17s on an ordinary push.
  * The battery's own mutation gate rides the battery (scoped to pushes
    touching it; ~6m19s there), re-entrancy guarded by a variable set at
    exactly one line and ANNOUNCED when it suppresses -- not an operator
    skip flag; `--no-verify` remains the one honest exit (ADR-011).
    `scripts/test-release-battery.sh` gains 6 arms (6 -> 12) covering the
    skip-awareness logic P0 shipped ungated.
  * `truth doctor --json` (the contract-layer surface the migration
    listed and never built): structured ok/warn/fail entries with
    `failures`/`warnings` derived from the same lists the exit code
    reads. Plain text and the exit-code contract are byte-unchanged.
  * ADR-044's module table said shellio was "the only subprocess
    importer" and cli.py contradicted it. The ADR-014 acceptance-oracle
    execution moved to `shellio.run_accept_command`, `import subprocess`
    is gone from cli.py, and `TestModulePurity` now ASSERTS it -- the row
    is mechanical instead of editorial. ADR-044 carries an amendment
    saying plainly that it was false when written.
  * `instruments/concern-tag.py` fetched its active-status set from a
    hand-copied tuple -- the contract-copy drift ADR-043 closed, reopened
    in the untemplated tier. It now reads `truth vocab --json` at runtime
    and fails loud, like the health satellites.
  * Canary 247 -> 251: doctor-JSON contract + text-unchanged arms, and
    GS7/GS7b closing the last hard gate with no end-to-end arm
    (`text-nonempty`: empty and whitespace-only refused, ledger
    unchanged, plus a negative control). Core suite 293 -> 296.
  * ADR-042 (check liveness) stays PROPOSED with a dated amendment: its
    acceptance preconditions are now met and rules 1/2/5 are enforced,
    but rules 3-4 are unshipped, and accepting on partial delivery is the
    defect this round exists to close. Registry rows for `text-nonempty`
    and `class-precheck` were missing (ADR-047 says "every"); added, so
    it carries 13 rows -- not the 11 the v0.9.31 entry states.
  * Provenance: everything above answers findings 1-5 and 7 of
    `docs/reviews/migration-audit-2026-08-02.md`. Finding 6 -- the
    migration's dropped per-phase ledger discipline -- is recorded OPEN
    and deliberately NOT retro-filed.

v0.9.32 (input hygiene on argument SHAPE -- no new ADR: both refusals
  enforce decisions already taken, ADR-036 for the citation sweep and
  ADR-013 for the premise refs; no schema change, no gate semantics
  change, fold untouched):
  * `truth citations` validates every positional arg as a ledger id
    (tr-hex8, or wk-hex8 -- `done --cancel` sweeps issue tombstones too)
    BEFORE any sweep runs, and refuses the WHOLE invocation on the first
    bad token, naming it control-escaped (SI-3) and stating the shapes.
    Found in a live operator transcript: `truth citations '#'` accepted
    `#` as an id, swept the literal token across the corpus, and
    reported it `clean` at exit 0 -- read-only, so nothing was
    corrupted, but the verb answered a question nobody asked and did it
    in verdict-shaped words. There is no bypass; a batch is one
    preflight pass, so one bad token refuses the batch.
  * `truth premise` refuses a claim id or `--supersedes` ref that is not
    tr-hex8 BEFORE it appends. Intake checked neither, while the
    validate mirror has always refused such a record: a normal verb
    could therefore write, to an APPEND-ONLY file, a line that `truth
    validate` and the commit gate then reject (`truth premise ISSUE-1
    '#'` filed, then `validate` exited 1 on it). SHAPE only -- an
    unknown-but-well-formed id stays legal, which is the deliberate
    treatment of dangling premises (doctor's `premise integrity` WARN,
    `issue --premise`'s warning, ADR-001); the issue ref stays free-form
    for external trackers (ADR-004).
  * Canary 245 -> 247 arms: TG12 (both junk shapes refused, nothing
    swept, negative control -- a well-formed unknown id still reports
    `clean` at rc 0, TG6's contract intact) and one R10-family arm (a
    malformed premise ref refuses, the ledger does not grow, `validate`
    still passes). Both red-proven: with the checks removed the arms
    MISS.

v0.9.31 (ADR-047: gate governance -- the P6 phase and close of the
  migration plan, decision D5; docs-only release, zero scripts/,
  truthlib/, or .truth/ contract changes -- the v0.9.16-0.9.19
  precedent):
  * ADR-047 (docs/adr/truth/047-gate-adoption-metrics.md): every
    Tier B blocking gate and counted override carries a named adoption
    metric, a data source (a Tier C instrument or stats key), and a
    next-review date; new gates enter PROPOSED with a metric or not at
    all (the growth-gate discipline applied to the gate table);
    reviews ride the existing R11 monthly hand-audit slot (zero new
    ceremony); the retirement test is three questions -- opportunity
    to fire, acted on when fired, failure still in the regime -- with
    ADR-032's decay as the precedent (re-ask a judgment on a
    schedule).
  * Gate-metric registry (meta-repo, never templated:
    docs/governance/gate-metrics.md): all 11 Tier B rows with live
    instrument values, plus the FIRST REVIEW's minutes (2026-08-02,
    applying D5): ADR-033's verbatim-repeat detector to DATED
    PROBATION (zero firing opportunity yet -- reviewable at >=5
    decay-expiry->re-file cycles, realistic 2026-10-08); G8 kept at
    0.6 Jaccard on data (11/198 = 5.6% override rate, one legitimate
    re-anchoring batch; re-review 2026-09-08); the 3650-day scope-TTL
    traced to one retracted 2026-07-21 claim (historical outlier,
    human re-justification queued).
  * Operator handoff (docs/governance/operator-actions-2026-08.md):
    the human-only actions with ready-to-run commands -- the TTL
    ruling, one stale blast-stamping retraction, the 31-claim
    superseded-predecessor pool (each preflighted clean via `truth
    citations`), the 27-claim pre-migration diverged pool, and the
    R11 audit's new first read.
  * Wire-in: ops guide sec 4 (the monthly hand-audit opens on the
    registry) + header stamps; loophole map header stamp (no loophole
    moved). Lockstep surfaces bumped; no CLI, schema, or gate change.

v0.9.30 (ADR-046: tiering and the envelope admission rule -- the P5
  phase of the migration plan, decision D4; the ONE migration phase
  that deliberately changes consumer-facing behavior: report surface is
  REMOVED from the template CLI and re-provided as meta-repo Tier C
  instruments; fold, statuses, refusals, and every gate unchanged):
  * Envelope admission rule, written down (schema `$id` v0.15 -> v0.16,
    the phase's single schema bump): a payload field is admitted only
    if the fold or a blocking gate reads it. Grandfathered as passing:
    the override bases (scope_basis, generated_ok_basis,
    evidence_exit_basis, orphan_basis, overridden_duplicates) and
    ttl_default. `concerns` and `blast_forecast` FAIL the rule and are
    legacy-admitted only: validate and the schema keep accepting them
    on records filed pre-ADR-046 (append-only history is never
    rewritten) and both carry deprecation notes; the fields are CLOSED
    to new records. The rule + grandfather list also land in
    docs/truth-ledger-machinery.md.
  * `concerns` -> Tier C (D4): REMOVED from the template CLI --
    `claim --concern`, `list --concern`, and the stats
    `concerns`/`concerns_untagged_active` section are gone, and
    `concerns_intake_error` left truthlib with its wiring. CONCERN_RE
    and the `claim_concerns` reader STAY (validate's legacy branch and
    the instrument need them). Replacement:
    `instruments/concern-tag.py`, a READER over
    `scripts/truth list --json` + the raw ledger (stdlib only) --
    filing-side tagging is gone, the field is closed, and hand-editing
    tags into the ledger is forbidden by the admission rule.
  * `blast_forecast` computed on read: intake stops stamping the
    payload (the `_gate_blast` row is advisory-only -- it computes the
    forecast live and passes it plus the parsed history through
    `facts`); `effective_blast_floor(claims, history)` now calibrates
    P90 from LIVE forecasts over live path-claims in one
    `blast_history()` log (same git cost as the retired stored-int
    read; >=1 clamp and fallback kept, None history NEVER calibrates);
    `blast_report(events, folded, history)` computes rows live and
    falls back to stored legacy ints only when history is unreadable.
    Replacement report surface: `instruments/blast-report.py`.
  * Reports out of `stats` and `doctor` (Tier C): `truth stats` keeps
    EXACTLY claims_by_status/claims_by_tier, verdicts, half_life (it
    feeds the FS-1 intake advisory -- Tier B), and queue_size/age; it
    LOSES the separation, overrides (+ repeats advisory lines +
    hollow), blast, and concerns sections in both plain and --json
    (TestStatsCLIShape pins the slimmed shape both ways). doctor LOSES
    the "verifier separation" check. The pure reports
    (separation_report, override_report, blast_report) STAY in
    truthlib/advisory.py; the new meta-repo drivers are
    `instruments/separation-report.py`,
    `instruments/override-velocity.py`, `instruments/blast-report.py`
    (each with --json; NOT templated -- consumers never receive them).
  * Retired arms, BY NAME (the ADR-046 canary-arm ledger): canary
    SEP1/SEP2/SEP3 (FAULT SEP), FAULT OV's two stats arms, and BF5 ->
    all moved to the NEW meta-repo gate `scripts/test-instruments.sh`
    (16 arms: real-ledger lane + a red-proof lane per instrument);
    canary BF4 FLIPPED to assert blast_forecast is NOT stored while
    the BF1 advisory still voices (canary 251 -> 245 arms). Core
    suite: TestConcernsCLI (6 tests) and
    TestOverrideReportCLI (2 tests) retired to the instruments gate;
    test_stats_report_concern_tally replaced by
    test_legacy_tagged_and_forecast_records_still_admitted;
    test_slug_hygiene re-pointed at CONCERN_RE
    (test_slug_shape_guards_the_legacy_validate_branch);
    TestStatsCLIShape (2) and a live-history TestBlastReport arm added
    (core 298 -> 293 tests).

v0.9.29 (ADR-045: write-path lock + merge gate -- the P4 phase of the
  migration plan, decisions D2/D3; no verb, flag, schema, or fold
  change; every existing refusal message and exit code byte-identical):
  * Ledger lock (D2, closes R10): every write verb now holds an
    EXCLUSIVE fcntl.flock around its ENTIRE load->gates->append call
    (main() wraps args.fn for WRITE_VERBS), so the intake gates that
    read a fold -- the G8 duplicate screen, the contradicts
    dormant/live decision, the issue_event transition check -- can no
    longer be raced by a concurrent same-machine append between fold
    and write (the R10 TOCTOU catalogue). Lock target:
    `<git-dir>/truth-ledger.lock` (registry LEDGER_LOCK_NAME), a
    separate file like .git/truth-whisper.seen -- never the ledger fd
    (the audited O_APPEND single-write path is untouched) and
    deliberately NOT a worktree sibling: the .truth/.claims.lock draft
    dirtied `git status` and red-flagged the session-close survival
    gate in its first canary contact. Blocking acquire, no timeout --
    flock state is kernel-owned and dies with a crashed holder's
    process. Read verbs (incl. `validate --stdin`, inside the commit
    gate) never touch the lock. Multi-machine concurrency unchanged
    (paper sec 8 item 4 stands); an acceptance oracle that itself runs
    a write verb against the SAME repo would self-deadlock -- disclosed
    in ADR-045, oracles are suites by design. Canary FAULT LK (2 arms:
    a held lock stalls a real `truth claim`, release lands it exactly
    once) + TestLedgerLock (git-dir target, exclusion while held,
    release on refusal exit).
  * pre-merge-commit hook (D3, closes R5's gate half): git runs
    pre-merge-commit -- never pre-commit -- when a merge auto-commits,
    which is exactly the commit class the union-merge sync story
    produces, previously ungated. install-hooks.sh now writes it as a
    third hook with the same `exec bash scripts/check-truth.sh` body
    (hooksPath-refusal guidance updated to name it); doctor gains an
    adoption-gated WARN (never FAIL) when a local pre-commit gate hook
    exists without a check-truth pre-merge-commit, naming
    install-hooks.sh -- CI-arm repos are exempt (their gate runs
    server-side on push/PR, where merge commits arrive like any other);
    the meta-repo's own .githooks/ gains pre-merge-commit (delegating
    to pre-commit so the archive freeze rides along). Canary UM5-UM7
    complete the P0 union-merge arm's deferred assertion: hooks
    installed via the real installer, the honest bidirectional union
    merge commits THROUGH the gate (a union-merged ledger is a prefix
    extension of ours), and a branch that rewrites an early committed
    ledger line, landed with --no-verify and merged back, is BLOCKED at
    the merge commit (non-prefix result, INV-A); plus 3 doctor arms
    (WARN fires, goes quiet once installed, CI-arm exempt).
  * Tail-seek + doctor fold-once (R15): _last_ledger_ts reads only the
    ledger's last 64KB (partial first window line dropped, junk tail
    lines walked past, full-scan fallback when the window holds nothing
    parseable -- correctness first; TestLastLedgerTsTailSeek pins every
    case against the old full scan inlined as the oracle), and
    cmd_doctor loads the ledger ONCE and folds once, sharing `folded=`
    with its consumers (it loaded 3x/folded 4x; ADR-034's fold-once
    convention applied to its last violator -- output byte-identical).
    The FS-3 scale-gate comment (registry) and the .truth/README FS-3
    line now name the write path and reaffirm the remaining linear
    scans (reaffirm, invalidate-scan) as watched-by-design residuals.
  * Canary 243 -> 251 arms (FAULT LK 2, UM5-UM7 3, doctor
    pre-merge-commit 3); core suite 290 -> 298 (TestLedgerLock 2,
    TestLastLedgerTsTailSeek 6); every new arm red-proven by mutation.
    ADR-045 records the decisions and the disclosed-not-solved
    residuals.

v0.9.28 (ADR-044: the package split -- truthlib/ modules behind the
  same single-file entry; zero behavior change; the unchanged 243-arm
  canary is the equivalence proof):
  * template/truthlib/: the 4.6k-line CLI carved into concern modules
    along the P2-shaped seams -- registry (vocabulary + lexicons),
    kernel (canon, folds, order_check, validate mirror), evidence
    (screens, recheck, reaffirm triage), policy (intake predicates,
    ADR-001 matrix, invalidation strategies), gates (the ADR-034 table),
    advisory (CC-1 assembly + the pure report family), shellio (ALL
    subprocess/files/clock/env), cli (argparse + cmd_*). Pure file
    moves and imports only: every refusal message, exit code, advisory
    line and derived status byte-identical.
  * scripts/truth stays the one loading surface: a thin entry that
    resolves its own real path (the meta-repo symlink resolves through),
    puts truthlib/'s parent on sys.path, and re-exports every module's
    namespace -- `python3 scripts/truth <verb>` and every
    SourceFileLoader consumer (core suite, v04 suite, canary snippets)
    see the exact pre-split surface, monkeypatch seam included
    (attribute assignments on the loaded module mirror into the
    truthlib modules that bind the name).
  * Purity is a theorem now: TestModulePurity parses each pure module
    (registry, kernel, evidence, policy, advisory) with ast and refuses
    subprocess imports, os.environ reads, open() calls (empty
    allowlist), clock reads, and any import edge outside the DAG
    (registry <- kernel <- evidence/policy <- advisory; shellio ->
    kernel/registry only; gates' shellio use is the documented
    exception; cli imports everything). Red-proven in the P3 run.
  * Layout consumers updated: canary mkrepo + BFSH/BFU sandboxes,
    test-fact-health/test-session-digest sandboxes, and the release
    battery's canary trigger copy/watch truthlib/ beside the entry;
    copier ships it automatically (template/ subdirectory).
  * ADR-044 records the one settled decision this reopens (single-file
    CLI) with the new evidence (measured hand-parity drift at 4.4k
    lines), what is retained (no install, no deps, copier-copyable,
    SourceFileLoader compat), and the zipapp escape hatch.

v0.9.27 (ADR-043: the P2 contract layer -- status registry + vocab
  contract; no schema change; every existing refusal message, exit code
  and derived status byte-identical -- the licensed additions are
  `truth vocab` and `done --json`, plus one licensed reorder in `done`):
  * Registry (R13): ACTIVE_STATUSES and VERDICT_STATUS module constants
    replace six hand-copied ("live", "unverified") tuples and three
    inline verdict->status maps; the stats verdict counters derive from
    VERDICTS (key order unchanged). Unknown-verdict behavior stays
    deliberately split per consumer (fold KeyError, half-life silent
    skip, stats uncounted) -- unifying it is a semantics change, not an
    extraction; noted at the constant.
  * `truth vocab [--json]` -- new READ verb (no commit-gate banner):
    exports statuses, active set, verdict map, premise_blocking /
    premise_warn DERIVED by evaluating premise_check over STATUSES x
    TIERS (the vocab IS the ADR-001 matrix, evaluated), and
    citation_bad = CITATION_BAD, the satellites' blocking contract,
    consumed by nothing else in the CLI. spec-health's CLAIM_BAD and
    fact-health's BAD now fetch it at runtime and fail LOUD (exit 2)
    when the call fails -- the R1 `disputed` hand-copy drift class is
    structurally closed: removing disputed from the constant reddened
    canary VC1, the S2D spec arm, and the fact-health disputed case
    together in the P2 red-run. That cascade is the contract.
  * Shared intake flags (R7): add_claim_intake_flags declares the seven
    flags `claim` and `done --claim` share verbatim; the four override
    flags whose done-side help reads "see `truth claim ...`" stay
    per-verb, and per decision D4 --concern is NOT added to done (its
    removal path is P5). `done` gains `--json`: one object {issue,
    event, claim, accept, advisories} -- the SI-3 guarantee extended to
    claim-at-death; advisories ride the echo, never the ledger line
    (canary GS6). build_claim_payload's four-sentence basis tail is
    keyword-only now, and it returns (payload, facts).
  * Loaders return, never exit (R14a): load_citation_scope and
    load_generated_globs return (globs, source, err); _gate_generated
    returns the error per the gate-table contract, the citation verbs
    sys.exit it at the cli level -- messages and exit codes verbatim
    (canary TG10/RC unchanged).
  * Non-claim intakes decide in the core (R14b): supersede_error (the
    ADR-013 rule ladder, with the RETRACTED_NEEDS_ACK sentinel -- the
    ADR-011/017 human ack itself is I/O and stays in the shell) and
    contradicts_intake_error; cmd_premise/cmd_contradicts are thin
    gather-call-exit shells. Refusal bytes identical.
  * intake_advisories is PURE (R6): generated_source, porcelain and
    shallow_state arrive as keyword-only data gathered ONCE by the
    shell, reusing what _gate_generated and _gate_blast already stashed
    in ctx; the duplicated inline shallow-probe subprocess is gone.
  * cmd_done check ordering (L2-F6, the licensed fix): a missing
    --basis or invalid transition now refuses BEFORE the human-ack
    prompt and citation sweep, matching cmd_verdict's order; the
    refusal strings are unchanged.
  * Core suite 257 -> 286 (TestStatusRegistry, TestSupersedeError,
    TestContradictsIntakeError, TestIntakeAdvisories, TestBlastReport,
    TestCitationBlockPaths, TestLoadersReturnErr, all red-proven);
    canary 240 -> 243 (FAULT VC 2 arms + GS6). Fold untouched.

v0.9.26 (ADR-040: an audited evidence-allowlist default; no schema
  change, no gate semantics change):
  * The shipped `.truth/evidence-allow` loses rg, file and date. A
    per-program audit of all 28 entries -- flags AND positionals, GNU
    and BSD, every channel demonstrated rather than inferred -- found
    `rg --pre PROG` / `--hostname-bin PROG` execute arbitrary programs,
    `file -C -m PATH` writes a compiled magic file anywhere, and `date`
    sets the clock from GNU -s/--set or a bare BSD POSITIONAL. The
    other 25 entries were confirmed read-only in both implementations;
    that negative coverage is what justifies the new default.
  * Empirical cost zero: of the 116 distinct commands this ledger has
    ever carried (114 evidence + 2 acceptance oracles), the programs
    used are grep, echo, test, ls, head and the deliberately-unlisted
    bash of the P0 canary claim. The three removed appear zero times.
  * DOCTOR_GREY_ZONE gains the same three -- the PROPAGATING half.
    Removal alone protects only new consumers, because the allowlist is
    consumer-owned and copier never reverts it; the grey zone is
    code-owned, so it warns every existing deployment still carrying
    them. Advisory, never a failure (ADR-022 part 2, unchanged).
    They are NOT added to the deny baseline: that file is for programs
    whose sole job is running other programs, where refusal costs
    nothing, and all three have ordinary read-only uses.
  * Canary FAULT AL (3 arms incl. negative control); core test
    test_grey_zone_covers_adr040_removals. FAULT G and R7 re-add `date`
    to their sandbox list on purpose -- they test the DETERMINISM gate,
    which an unlisted program would never reach.
  * ADR-040 records R1-R4, all still OPEN and measured: sort's denied
    long options are bypassable by getopt abbreviation (`--out=`,
    `--com=`) and by glued/clustered short forms (`-oFILE`,
    `-nroFILE`); `uniq IN OUT` reaches an output positional no flag
    table can see; and three SHELL-level channels -- `uniq *` (a glob
    is one word to shlex and N to /bin/sh), `cat <>f` (read-write
    open), `>1` (a digit target is a file, not an fd) -- which no
    allowlist can close. ADR-041 (PROPOSED, shell-free evidence
    execution) is drafted as their closure. Fold untouched.

v0.9.25 (ADR-039: blast forecast + churn report -- R5, the FINAL
  release of the 2026-07 gates adoption; schema $id v0.15):
  * A path filing stamps blast_forecast: distinct commits touching
    the watch in the trailing BLAST_WINDOW_DAYS (30), via one
    `git log --format=%x01%H --name-only --no-renames` with
    quotepath=off at the repo root (SI-2). An UPPER BOUND on
    stalings, stated as such (a claim stales only from live; the
    pilot's hottest claim showed 15 invalidations vs 14 re-agrees).
  * Advisory at/above the floor; the floor SELF-CALIBRATES (P90 of
    live stored forecasts once BLAST_MIN_OBSERVATIONS=20 exist,
    constant 15 as cold-start fallback -- the adoption review proved
    a fixed 15 would print on ~85% of this repo's own filings,
    tr-c3087292). Shallow history and unborn HEAD degrade LOUDLY
    with a notice and store nothing (a floor is not a bound).
  * `truth stats` gains the blast section: observed-vs-forecast
    (top 5), per-path staler ranking from invalidation `touched`
    lists (no git work), effective floor + source; also in --json.
  * The REFUSAL gate deliberately does not ship (the rev-1 proposal's
    BLAST_THRESHOLD was falsified at home): it returns only as its
    own ADR after >=30d of forecast-vs-observed data AND the
    ~2026-08-08 reaffirm-trial read, threshold derived from the
    measured distribution.
  * Canary FAULT BF (7 arms); core TestBlastForecast.

v0.9.24 (ADR-038: the dirty-watch advisory -- R4 of the 2026-07
  gates adoption; no schema change, per ADR-026 the $id stays v0.14):
  * Filing a claim with evidence_paths runs one
    `git status --porcelain=v1 -z --untracked-files=all` at the repo
    root (SI-2: NUL/unquoted -- quotepath cannot hide a non-ASCII
    dirty file; -uall expands untracked dirs so the exact file under
    a glob watch is named). Dirtiness is STRUCTURAL: any XY beyond
    clean/ignored, covering the UU merge-conflict state (the pilot's
    QB-011 scenario) that a letter whitelist would miss; untracked
    entries count (INV-M refuses untracked literals but exempts
    globs -- exactly the restale-at-birth vector); renames match on
    either NUL field.
  * One advisory line per dirty watched path in the CC-1 block --
    never a refusal (a gate would teach `git stash` as its bypass);
    mirrored in --json advisories. Measured demand at adoption:
    29/895 meta and 37/390 pilot invalidations landed within 30
    minutes of their claim's own birth (tr-5c2bd165).
  * Canary FAULT DW (7 arms); core TestDirtyWatch.

v0.9.23 (ADR-037: recipe lints + generated-paths -- R3 of the 2026-07
  gates adoption):
  * Recipe lints on the screen's OWN shlex token stream (a second
    screen-side parser stays forbidden; quote-splitting cannot evade):
    grep-family -n/--line-number (per-segment -- sort -n never fires),
    version- and date-shaped literals with three carve-outs
    (path-context tokens, the schema-$id shape, frozen-record dates).
    Warnings in the CC-1 advisory block, never refusals (ADR-014's
    confused-deputy lesson).
  * .truth/generated-paths (consumer policy, _skip_if_exists, ships
    EMPTY = conscious silence; absent = dark with one advisory line;
    pathspec-magic lines refused): a --paths entry matching it is
    REFUSED for every evidence class at the INV-M position;
    --generated-ok stores generated_ok_basis (schema $id v0.14,
    mirror rules, FS-2 fixtures), counted, and DECAYS per ADR-032
    (override_decay generalized; the notice names the actual flag).
  * override report: generated-ok row (CC-2 single home).
  * Canary FAULT RC (10 arms incl. the dropped-override arm: a
    --generated-ok matching nothing is voiced, not stored, and does
    not decay -- the decay row keys on the STORED basis, after the
    generated gate); core TestRecipeLints.

v0.9.22 (ADR-036: the tombstone citation gate -- R2 of the 2026-07
  gates adoption):
  * `verdict <id> retracted` and `done --cancel`, after the ADR-011
    ceremony and before the append, grep the exact id BARE at the
    repo root (SI-2: a subtree cwd truncates a sweep to rc=1 =
    'clean'; rc contract pinned 0=hits / 1=clean / else=unavailable
    -> fails CLOSED, the one earned exception) and refuse with EXIT 6
    (distinct, driver-usable -- the impact/baseline precedent) while
    a scope-covered file cites the id. The refusal does not name its
    override (ADR-011 surface rule); --orphan-ok "<sentence>" stores
    orphan_basis (schema $id v0.13 on verdict AND issue_event;
    validate mirror: non-empty, tombstone-only), counted in
    override_report (orphan-ok row; decay declined -- terminal).
  * Scope is consumer policy (.truth/citation-scope, SI-4): absent ->
    built-in default docs/specs/** + notice; committed-empty ->
    consciously silent; utf-8-sig; pathspec-magic lines (':'/'-'/'!')
    refused at load (SI-1 -- one ':(exclude)' idiom line would invert
    the sweep); dead scope (zero tracked matches) voices a loud
    notice. Filtering is core-side match_paths, never git pathspecs;
    .truth/claims.jsonl is structurally excluded (retraction bases
    cite predecessors).
  * New read-only verb `truth citations <id>...` -- the ceremony-free
    preflight (exit 0 clean / 6 cited, --json): a batch retraction
    runs one preflight, then per-id ceremonial verdicts; a multi-id
    ack stays refused on principle (ADR-011).
  * Canary FAULT TG (11 arms incl. fail-closed PATH-shim, subdir
    fixture, dead scope, ledger exclusion, magic-prefix refusal, and
    the unicode-quotepath arm: git grep -z emits raw names so a
    non-ASCII citing file cannot hide (SI-2, adversarial-review
    catch); listings render escaped (SI-3); '--' pins the id argument).

v0.9.21 (ADR-035: the positive-claim exit gate -- R1 of the 2026-07
  gates adoption):
  * NEGATION_TOKENS lexicon (copies of the five negation-shaped
    quantifier tokens plus the ordinary negation vocabulary; X6 core
    test pins the subset relation, one-directional by design).
  * First post-execution gate-table row: a VERIFIED filing whose text
    carries no negation token and whose recorded first-run exit is
    non-zero is REFUSED naming ADR-035 (the pilot's QB-011 hollow
    shape; simulated over 244 real filings pre-adoption: 5 refusals,
    all genuine, zero false -- tr-166c4616). Absence proofs keep the
    v0.9.11 advisory path. Applies identically to done --claim
    (both-or-neither preserved; FAULT X7).
  * --evidence-exit-ok "<sentence>" stores evidence_exit_basis
    (schema $id v0.11 -> v0.12; validate mirror refuses an empty
    basis, a basis beside exit 0, and tolerates legacy capsules
    lacking returncode). Decay for this basis: DECLINED with reason
    (ADR-032 exclusions form) -- a failing-by-design proof is a
    permanent property and re-verification re-runs the command.
  * override report: exit-ok filings counted (CC-2 single home);
    stats gains hollow-warned (recorded exit!=0, no basis) beside a
    pointer at the override row -- the refused class leaves no
    record, so it has no counter.
  * Canary FAULT X: 8 arms incl. negative control and the validate
    mirror pair; core TestExitGate.

v0.9.20 (ADR-034: the gate system -- staged intake table + CC-1
  advisory block; R0 of the 2026-07 gates adoption,
  docs/reviews/gates-2026-07/):
  * Intake gate ORDER becomes data: INTAKE_GATES rows
    (stage, name, gate_fn) drive build_claim_payload; the ADR-009
    evidence screen and the G6 double-run are stage boundaries, not
    rows (ADR-029 preserved; FAULT SD untouched). Refusal semantics
    are byte-identical to v0.9.19; canary FAULT GS1/GS2 pin the
    staged order, a core test pins the row sequence.
  * Post-append notices fold into ONE contiguous stderr block, every
    line prefixed `truth: advisory:` (the QB-011 swallowed-warning
    class): the v0.9.11 exit warning, the ADR-032 decay notice, and
    the FS-1 half-life note (moved post-append). Silence on clean;
    the commit-gate banner stays exempt (must fire on refused
    filings). `--json` mirrors the messages as an `advisories` array
    on the echoed record -- the ledger line never stores them.
    FAULT GS3-GS5 + TestAdvisoryAssembler gate it. Control bytes in
    advisory text render escaped (SI-3, terminal-escape injection).
  * `truth stats` folds ONCE and shares the result across
    stats_report/override_report (each used to re-fold and re-sort);
    _glob_rx gains lru_cache (pure; also speeds the invalidate-scan
    and impact paths). Parity pinned by a core test.
  * copier.yml: `.truth/accept-allow` joins _skip_if_exists -- it is
    consumer policy like evidence-allow and was clobber-exposed from
    v0.7.0 (tr-f49a00ee; the pilot carries local entries today).
  * evidence_exit_warning/override_decay now return bare messages
    (the renderer owns the prefix) -- any consumer grepping
    `truth: warning: evidence command exited` must switch to the
    `truth: advisory:` prefix.
  * One deliberate behavior ADDITION: `done --claim ... --ttl-days N`
    now prints the FS-1 half-life note (it never did) -- the shared
    intake_advisories means claim-at-death earns the identical
    advisory set as `claim`, which the cmd_done comment always
    promised in spirit.

v0.9.19 (the authoring loop -- docs-only release, zero scripts/ or
  .truth/ contract changes):
  * docs/truth-ledger-machinery.md sec 2 gains "The authoring loop":
    the four-role division of labor proven in consumer production --
    implementing worker (fresh context, never commits, never writes
    the ledger), adversarial reviewer (attacks BEFORE commit, armed
    with the CLI's own gate functions, scratch-copy two-state tests),
    orchestrator (alone runs suites, commits content before filing,
    scan+reaffirm in a fresh session), verifiers (one per dispatch,
    never the author, parallel-safe). Two mandatory triggers: an
    adversarial review per feature/release, and immediate verifier
    dispatch for freshly filed claims (reaffirm skips the
    never-agreed). Closes the routing gap the consumer's QB-010
    question caught: the choreography lived only in one agent's
    session memory.

v0.9.18 (ADR namespace + harness promotions -- docs-only release, zero
  scripts/ or .truth/ contract changes):
  * The 33 machinery ADRs move docs/adr/ -> docs/adr/truth/: the number
    space there belongs to the template alone, namespaced apart from
    the consumer's own docs/adr/ series. Born of a real collision in a
    consumer -- two ADR-001s (and more) in one directory, and immutable
    ledger citations made renumbering impossible; namespacing is the
    only fix that composes. Ships docs/adr/truth/README.md stating the
    convention; every template-shipped reference is rewritten (the
    archetype blanks' Decisions placeholders stay docs/adr/ -- those
    point at CONSUMER decisions). MIGRATION, consumers: `copier update`
    adds the docs/adr/truth/ copies but does not remove the old
    template-synced ADRs at docs/adr/ -- delete those stale root copies
    yourself, and update any citations (specs, docs, claim evidence
    paths) from docs/adr/NNN-*.md to docs/adr/truth/NNN-*.md.
  * docs/truth-ledger-machinery.md sec 2: the tail-variation paragraph
    grows into "Filing hygiene & aftermath -- rules earned in consumer
    production", promoting six more rules from consumer harness runs:
    pre-scan batch texts with the CLI's own quantifier/jaccard
    functions (ADR-007 matches phrases, ADR-018 measures against
    active claims); sweep the corpus for citations before any
    retraction (a retracted id cited by a spec blocks every spec
    commit); the doc<->claim two-commit dance (cite by title, file,
    then swap in the id); version-pin divergences are genuine, never
    --mechanical; consumer-local edits to copier-managed files must be
    upstreamed at the next release; batch filings go through
    argv-array drivers (never shell-interpolated loops) and
    post-union-merge reaffirm agrees are committed before pushing.
  * prompts/truth-verifier.md ADR-012 guidance: a divergence caused by
    a version pin superseded by a release is GENUINE (the fact
    changed) -- never softened with --mechanical.

v0.9.17 (machinery filing hygiene -- docs-only release, zero scripts/
  or .truth/ contract changes):
  * docs/truth-ledger-machinery.md sec 2 gains the tail-variation rule:
    claim families filed as a batch must vary their texts beyond the
    distinguishing token, or a shared boilerplate tail pushes sibling
    claims over the ADR-018 near-duplicate threshold and the gate
    refuses the batch midway (observed at jaccard 0.617 on a kuchnie
    symbol-pin pair, 2026-07-27). Upstreamed from the kuchnie consumer
    so the copier-managed copy and the template stay convergent.

v0.9.16 (V&V blank sections -- docs-only release, zero scripts/ or
  .truth/ contract changes):
  * Every archetype blank (docs/templates/archetype-*.md) gains a
    Verification & Validation section, pre-paired per archetype from
    the red-teamed pairing table: verification names the technique and
    cites the id that CARRIES the oracle (a wk- with --accept-cmd or a
    standing tr- sentinel) -- never the command text; validation is a
    human instrument recorded as an UNVERIFIED + --ttl-days
    attestation (expiry = re-walkthrough + re-file + edit the line);
    residuals are named by TITLE only, because an id in that section is
    a live tripwire, the opposite of "accepted". E's determinism check
    is confined to the ADR-014 accept-cmd lane; F's "the gate passes"
    is stated as session-close/session-gates.d enforcement, not a
    ledger oracle.
  * spec-archetypes.md gains "Appendix -- oracle recipes that survive
    the screen": the canonical layer-rule sentinel (the mandatory
    `tr -d ' '`; `!`-negation refused; filing over exit-1 = hollow
    VERIFIED), ADR-007/032 scope-override discipline, path-tripwired
    schema sentinels vs hash-pin divergence generators, the ADR-014
    lane for golden masters, the attestation pattern end-to-end with
    its disclosed costs, the consumer section-contract note, and a
    consumer-safe pointer at the spec-coverage traceability sibling.
  * prompts/truth-verifier.md: attestations have no recheck -- a claim
    with no evidence command files cannot_verify under --recheck; the
    verifier judges it manually and files agree/diverge on judgment.
  * Carries the archetype three-question-header fix (8137ce8): each
    blank's Reader/Enables/Update-trigger block sits inside the first
    15 lines, satisfying consumer new-doc gates.

v0.9.15 (stakeholder concerns -- ISO/IEC/IEEE 42010 triage metadata,
  red-teamed pre-release; spec-archetype satellite):
  * `claim --concern TAG` (repeatable) stamps 42010 stakeholder-concern
    tags on the claim payload (`concerns`: sorted, deduplicated). A tag
    is a slug, anchored \A[a-z0-9-]{1,32}\Z -- absolute anchors because
    Python's $ also matches before a trailing newline (red-team F1); a
    malformed tag is refused BEFORE intake runs any evidence command.
    That refusal is input hygiene like INV-M's path hygiene, NOT a
    concern-gate. TRIAGE METADATA ONLY, by doctrine: deciding whether a
    claim "touches security" needs a model, and the moment a gate needs
    a model to fire, it is a review, not a refusal -- tags never block
    filing, never enter the fold, never affect derived status or ready
    (fold blindness pinned by twin tests, including the bare-claim case).
  * `list --concern TAG` filters claims by tag; composes with the
    derived-status flags.
  * `stats` gains a `concerns` line (JSON: `concerns`,
    `concerns_untagged_active`): tag counts over non-retracted claims
    (only retraction kills a stakeholder's interest -- the impact
    --inverse convention), plus the count of active ({live, unverified},
    ADR-018 notion) claims carrying no tag. Read verbs consume the new
    pure `claim_concerns()`, which degrades a hand-appended malformed
    value to 'no tags' instead of crashing or substring-matching
    (red-team F2); `validate` still reports the malformation.
  * Schema AND stdlib mirror gain optional `concerns`: a non-empty,
    duplicate-free (uniqueItems, red-team F3 -- a duplicate would
    double-count in stats) list of slug strings; the schema pattern
    carries an ECMA-inert (?!\n) guard for the F1 trailing-newline case.
    Two independent surfaces, FS-2 corpus + generated-mutant lockstep;
    schema $id bumped v0.10->v0.11 for the field (ADR-026). A ledger
    written before the flag existed (no key anywhere) folds, lists,
    validates, and stats unchanged -- pinned in tests and smoke-checked
    against a 1143-record production-copy ledger.
  * spec-archetype satellite (docs-only): six component-archetype spec
    blanks + a field guide (docs/templates/) and the bootstrap interview
    prompt (prompts/spec-bootstrap.md), promoted from the pilot consumer
    repo -- closes the gap of shipping spec-health.sh (the gate) with no
    spec-authoring guide beside it. Template-owned like the evidence-deny
    baseline: updates ride `copier update`; per-project archetypes go in
    a separate local file (docs/templates/local-archetypes.md), never in
    edits to the shipped files. The guide's gate pseudo-code stays
    pseudo-code; scripts/spec-health.sh remains the authoritative gate.
  * invalidate-scan rename blindness fixed: changed_files_since now passes
    --no-renames, so a `git mv` of a watched path shows as delete+add and
    the tripwire fires on the old path. Found in the wild: retiring
    paper-v2 to docs/archive/ emitted only the destination path under
    rename detection, leaving three claims falsely live. Regression test
    with negative control (test fails on the pre-fix scan). On update,
    claims whose watched paths were renamed since their anchor will
    (correctly) stale at the next scan; `truth reaffirm` triages them.

v0.9.14 (batch-5 override decay + its instrument, roadmap-v3 R12/R13,
  ADR-032/033):
  * R12 (ADR-032) -- `--scope-ok` default expiry. A scope_basis claim
    (the ADR-007 quantifier-scope override) filed WITHOUT an explicit
    --ttl-days is stamped ttl_days=30 + `ttl_default: true` and prints a
    notice; it is never refused. Expiry then rides the UNCHANGED ADR-019
    scan path (counted from the claim ts, strict boundary, scan-
    materialized); ADR-030 arm 1 routes the stale claim to re-file, which
    re-fires the ADR-007 gate -- so the mechanism mechanically re-asks
    whether the scope judgment was ever real. Explicit --ttl-days (a
    large value is the visible opt-out) is kept unflagged. New pure core:
    `DEFAULT_OVERRIDE_TTL_DAYS`, `override_decay`. Schema AND stdlib
    mirror gain optional boolean `ttl_default` (two independent surfaces,
    FS-2 corpus + generated-mutant lockstep; schema $id bumped
    v0.9->v0.10 for the field). Canary FAULT SD-decay (4 arms incl.
    negative control). Deliberate exclusions: no decay for screened:false
    claims, no --no-ttl flag. ADR-032 carries its own adoption gate.
  * R13 (ADR-033) -- override-velocity report. `truth stats` gains an
    `overrides` section (pure `override_report`): scope-ok filings,
    override-decay expiries (reason_code=ttl on ttl_default claims),
    dup-overrides, unscreened filings, max scope TTL, and a NON-blocking
    advisory when a scope justification is re-filed verbatim (tokens()
    token-set-identical, reusing the existing tokenizer) after the prior
    claim died (stale/diverged/retracted) -- "review whether the scope
    judgment was ever real". `--json` carries the structured section. No
    threshold, no gate. Canary FAULT OV (2 arms incl. negative control).
  * Batch-5 red-team fixes (still v0.9.14, pre-release polish): (F1)
    `half_life_observations` now EXCLUDES TTL-reason invalidations
    (structured `reason_code=="ttl"`, `is_ttl_reason` prefix fallback --
    the same two-arm test as ttl_staleness, reused) so the FS-1 half-life
    medians and `ttl_suggestion` measure OBSERVED drift (path/anchor)
    only; a defaulted-TTL expiry no longer industrializes observations
    that cluster at the default and make the suggestion circular. The
    claim still transitions to stale (fold authoritative); TTL expiries
    stay counted in ADR-033's `decay_expiries`. ADR-032 Consequences +
    ADR-033 note the disjoint populations. (F2) plain-text lock: a
    CLI-level test asserts the PLAIN `truth stats` render carries
    `max scope ttl <N>d` (36500), not only the JSON field. (F3) ADR-033
    gains a "Residual false negatives" subsection: one synonym swap or
    appended junk token defeats the verbatim token-set advisory
    (reorder/case/punctuation do not), so the raw counters -- not the
    advisory -- are the evasion-proof volume signal the R11 audit reads;
    plus the cosmetic note that repeated advisories name the earliest
    dead prior and line count (no repeat counter) is the accumulation
    signal. New core tests: TestStats +3 (F1), TestOverrideReportCLI +1
    (F2).

v0.9.13 (batch-3 self-consistency, roadmap-v3 R4/R5/R6, ADR-031):
  * R6 (ADR-031, TLR-013 adoption) -- order_check's two duplicate-id
    detections (ADR-008 backdated, ADR-016 equal-ts) collapse to ONE
    rule: ANY duplicate id whose canonical content differs from the
    first-seen record is refused, regardless of ts relation. Only
    byte-identical union-merge duplicates may share an id. The fold's
    (ts, id, canon) total order, first-wins dedup, ADR-015 clock-push,
    and the clock-regression warning are all UNTOUCHED -- this is the
    detection gate only. Corrections file under fresh ids by design, so
    a content-distinct duplicate id has no legitimate use; the later-ts
    duplicate previously accepted (harmless under first-wins) was pure
    confusion attack surface serving nothing. Canary FAULT K gains a
    validate-refused arm; core tests TestOrderCheck updated (+2).
  * R4 (ADR-026 extension) -- TestCrossSurfaceVersions now also pins
    the `current: CLI vX.Y.Z` headers of the loophole map and the
    operations guide (meta-repo docs, skipped when absent in a consumer
    copy) and check-truth.sh's "current CLI:" comment line. The two
    docs' CONTENT still describes older CLIs (scope notes added);
    re-syncing them is roadmap Backlog work.
  * R5 -- the ~500-line version-history docstring moved to CHANGELOG.md
    (template root, shipped to consumers by copier); scripts/truth
    keeps a short header that still states its own version on line 2
    (the ADR-026 lockstep test parses exactly that line).

v0.9.12 (batch-2 churn fix, roadmap-v3 R3, ADR-030): `truth reaffirm` --
  batch re-confirmation of stale claims whose evidence COMMAND OUTPUT
  is UNCHANGED (precisely that -- see ADR-030's residuals), the
  measured bulk of re-verification churn (paper sec 8 item 2: ~10 agree
  verdicts per claim, half-life medians ~0.02d -- verification labor
  that overwhelmingly finds nothing). Walks every stale claim and
  triages it with ONE pure function (reaffirm_triage) into exactly one
  arm: TTL-staled -> skip, re-file required (ADR-019: TTL never resets
  by re-verification; TTL-staleness is read from the latest invalidation
  record's reason, never recomputed -- the fold reads no clock);
  mechanically unexecutable (evidence.screened=false, current-allowlist
  screen refusal, no evidence capsule, recheck exit 127, or never
  previously agreed -- first verification is a judgment, ADR-030) ->
  skip, manual verification only, the command is NEVER run; authored by
  the current session -> skip (ADR-010: reaffirm must not self-agree;
  TRUTH_SELF_VERDICT=1 stays the F4-class override); otherwise the
  evidence command re-runs through the SAME screened recheck path
  `verdict --recheck` uses (screen_evidence_command against the CURRENT
  allowlist gates execution, ADR-029; run_evidence + recheck_verdict --
  no second executor). Hash-match auto-files `agree` with basis
  "reaffirm: hash-match, no judgment re-run", anchor_commit=HEAD so the
  effective anchor advances (F2 semantics, fold unchanged). MISMATCH
  FILES NOTHING -- neither agree nor diverge: a batch verb cannot make
  the ADR-012 mechanical-vs-genuine call, so the claim is listed for the
  dispatch path (inverting `verdict --recheck`, whose single-claim
  auto-diverge feeds a verifier already looking). --dry-run triages and
  reports, files nothing; --json for harnesses. reaffirm joins
  WRITE_VERBS (it appends verdicts, so the R2 gate banner applies).
  Core tests TestReaffirmTriage / TestReaffirmCLI; canary FAULT RA.
  Red-team fixes (R3 review, ACCEPT-WITH-FIXES), same release: F2 --
  the match arm's anchor advance buries the watched-path change that
  staled the claim outside every future scan diff window, so the
  reaffirm agree now records `reaffirm_cleared: {prior_anchor,
  touched}` (the prior EFFECTIVE anchor -- the scan's diff base -- and
  the watched files changed since it, via changed_files_since +
  match_paths; prior anchor alone if the diff fails). Payloads are open
  in schema AND mirror, so no contract change. F3 hardening -- the scan
  stamps `reason_code: "ttl"` on TTL invalidations and triage prefers
  it (ttl_staleness: ANY scan-stamped ttl record is durable proof,
  ADR-019 monotonicity, so a later raw-appended free-text reason can no
  longer flip the claim into auto-agree; prefix match on the latest
  reason remains the pre-stamp fallback). F4 -- when TRUTH_SELF_VERDICT=1
  is active, reaffirm prints a loud stderr WARNING with the count of
  same-session claims auto-agreed under the override (the per-claim
  override amplifies to batch scale here). Plus a CLI test pinning that
  a command REMOVED from the current allowlist after filing is
  rescreened and never executed (marker-file proof).

v0.9.11 (batch-1 hardening, roadmap-v3 R1/R2): two loud-but-non-blocking
  warnings; no refusal, no exit-code, no record-format change. R1
  (field-notes-batch-m item 2): `claim --class VERIFIED` files on
  *determinism* (two intake runs hash-match), not exit 0, so a stably-
  failing probe filed clean and "rechecked" forever by stable failure --
  a hollow VERIFIED (two real instances). Intake now prints a stderr
  warning after the successful append when the captured evidence
  returncode is non-zero (pure predicate evidence_exit_warning; a
  non-zero-but-stable probe stays legal, so it never blocks). R2
  (ADR-025 follow-through): the commit gate became decidable but only
  `doctor` looked, so an unwired clone ran silently ungated. Every WRITE
  verb now prints a stderr banner when neither an active check-truth
  hook nor a CI config naming it exists -- fail-open with noise: probe
  runs at most once per invocation, any probe error stays silent, read
  verbs and `validate --stdin` (which runs inside the gate) are exempt.
  Doctor's hook detection factored into git_hooks_dir/find_gate_hook and
  shared with commit_gate_wired, no logic fork. Core tests
  TestEvidenceExitWarning / TestCommitGateBanner.

v0.9.10 (single-write append, independent review B-min7): append_record
  writes the record line with ONE os.write(2) call on an O_APPEND fd
  instead of the buffered text layer, whose stdio buffer could split an
  oversized record (long evidence command or claim text) across several
  write(2) calls -- voiding the single-write-call premise that the
  concurrent-append safety statement (paper sec 1) relies on. No record
  format change, no schema change. Core
  test_append_is_one_write_syscall_even_for_large_records.

v0.9.8 (INV-M glob scope + commit-gate decidability, batch-2 H5/H6): three
  spec-precision ADRs, one with a real gate. ADR-023 (H5): INV-M is a
  static-dead-tripwire gate, NOT a liveness guarantee -- a glob over a
  REACHABLE namespace is dormant (fires when it fills), refuting "an empty
  glob can never fire". ADR-024 (H5 follow-up, wk-dc763341): a glob over an
  UNREACHABLE namespace (`.git/*`, absolute, trailing-slash, `.`/`..`/empty
  component) is a dead tripwire despite the glob exemption, now REFUSED at
  intake (dead_glob_paths) -- sound, not complete; the tracked symlink is
  the undecidable residual. ADR-025 (H6, wk-4a7450d8): the README's one MUST
  (a `check-truth` commit gate via hook OR CI) is now DECIDABLE by `doctor`,
  which greps top-level CI configs for the gate script so a CI-only repo
  passes instead of false-failing; the invariant table + paper Sec 8 item 5
  disclose that INV-A/INV-G/INV-N + the ADR-008 detections are conditional
  on the commit gate running. Canary FAULTs T (dormant + unreachable glob),
  DG (doctor decides hook-or-CI, 4 arms).

v0.9.7 (evidence-deny baseline, wk-372de09c): ADR-022 adds an anti-footgun
  guardrail beneath the allowlist (which stays the boundary, ADR-021). A
  TEMPLATE-owned `.truth/evidence-deny` file lists programs whose sole job
  is to run other programs (shells + generic executors/exec-wrappers +
  privilege-then-run); the evidence screen refuses them in program
  position even if a consumer allowlisted one by accident (deny-wins),
  evidence screen only -- ADR-014 oracles still run `bash run.sh`. It is
  template-owned (NOT copier `_skip_if_exists`, unlike the consumer-owned
  allowlist), so `copier update` keeps the baseline current; absent it
  fails open, the allowlist still gating. `doctor` additionally warns
  (non-blocking) on grey-zone code-executors (git/python/curl/...) in the
  allowlist. An adversarial review found and closed one RCE gap (`time
  bash -c <cmd>`; time added to the baseline). NOT a completeness claim --
  the allowlist is the boundary. Core test_denylist_wins_over_allowlist /
  _deny_baseline_not_applied_to_oracles / _doctor_grey_zone_set; canary
  FAULT ED.


v0.9.6 (independent ledger-code review, H4 -- SECURITY): ADR-021
  (wk-5b2b724e) closes a live evidence-screen bypass. The screen tokenizes
  with shlex but run_evidence executes with subprocess shell=True
  (/bin/sh); shlex treats a newline as whitespace while /bin/sh treats it
  as a statement separator, so `grep x /dev/null\ntouch PWNED` put `touch`
  in ARGUMENT position (screen approves) while the shell RAN it --
  unscreened code execution in a verifier's recheck session. Fix: the
  screen refuses ASCII control characters except tab, so its token stream
  is a sound over-approximation of the shell's. An adversarial review
  could not break the fixed screen, but escalated H4's second half: the
  PROGRAM_ARG_DENY blocklist cannot bound a VCS (git filter-branch
  --tree-filter is RCE), so the security boundary is the bare-name
  ALLOWLIST, not the deny table -- docs corrected to stop implying the
  blocklist makes git safe, git kept out of the default allowlist by
  design, enumerable gaps closed (git -o, sort --compress-program). Core
  test_screen_rejects_control_chars / test_arg_deny_covers_h4_gaps; canary
  FAULT ES.


v0.9.5 (independent ledger-code review, H3 -- spec-precision, zero
  behavior change): ADR-020 (wk-b35d3849) pins the fold's status as ONE
  total function -- fold every event in (ts, id, canon) order, each
  verdict/invalidation sets status last-writer-wins, and `retracted` is
  absorbing (checked on the folded status, not ts). So `cannot_verify`,
  `diverged`, and `stale` are RECOVERABLE (a later `agree` returns them
  to live) while `retracted` is the sole terminal verdict. H3 also
  escalated this to "a verdict-path analogue of C1"; that was REJECTED
  with evidence (live sandbox + an adversarial 600-trial confluence
  fuzz): distinct verdict ids + the ADR-016 total order keep the verdict
  path confluent (C1 broke confluence), backdating only lowers a record's
  key so it is dominated by filing at ts=now, and the sole residual is the
  accepted section-8 forgery -- which even trips an ADR-008 warning. No
  runtime gate added. Core tests test_verdict_precedence_is_confluent /
  _negative_verdicts_are_recoverable / _retracted_absorbs_in_any_order;
  canary FAULT RV.


v0.9.4 (independent ledger-code review, H1/H2 -- spec-precision, zero
  behavior change): two conformance defects where the prose underdetermined
  the shipped code, so a clean-room second implementer would diverge.
  ADR-018 (H1, wk-c93f78bd): near-duplicate intake is symmetric Jaccard
  |A n B|/|A u B| over the SET of maximal [a-z0-9]+ runs of the lowercased
  text, against the active set {live, unverified} -- NOT the overlap
  coefficient a bare "token overlap" reading invites (they part ways on a
  strict token-subset, the elaboration case). ADR-019 (H2, wk-192107ef):
  TTL expiry counts from the claim's own ts with a STRICT boundary
  (now - ts > ttl_days), and the fold reads no clock -- expiry is
  materialized by invalidate-scan as an invalidation record, keeping the
  fold a pure confluent function of the log. Both ratify v0.4/v0.2
  behavior as normative and lock it: core tests + canary FAULT I
  metric-identity arm and FAULT D fold-clock-free arm.

v0.9.3 (ADR-017, wk-eaa42782): supersede authority. Source: independent
  review finding C3 (Critical), confirmed live -- retraction terminality
  was defended only at the status layer. `truth premise --supersedes`
  refused only live/unverified old premises and carried no human gate,
  so an agent (no TRUTH_HUMAN, a normal verb, no forgery) could redirect
  a HUMAN-retracted P0 premise to a fresh claim and release the work the
  retraction was blocking -- the paper's "cannot be undone" promise spent
  at the readiness layer. Fix: superseding a `retracted` premise now
  requires the ADR-011 human gate (TRUTH_HUMAN + typed-id ack); the
  mechanical dead states (stale/diverged/cannot_verify/missing) stay
  ungated -- no human decided those. Amends ADR-013. Canary FAULT R11.

v0.9.2 (independent spec review, MEDIUM-1/2/3): override auditability +
  cross-surface coherence. MEDIUM-1 (wk-00b8ee57): the --duplicate-ok
  override left no trace, unlike scope_basis/screened. The G8 gate now
  computes the near-duplicate conflict unconditionally and stamps
  `payload.overridden_duplicates` (the active claim ids the override
  declared distinct from) -- attackable ledger content, schema + mirror
  + corpus + canary FAULT I trace. MEDIUM-3 (wk-15335617): schema and
  mirror now forbid `accept.returncode` on an unexecuted acceptance
  (executed=false); README states the missing-allowlist fails-closed
  exception; ADR-002's superseded last-wins sentence gets an inline
  ADR-006 marker. MEDIUM-2 (wk-813b84d4) was doc-only (invariant-table
  rows INV-O/P/Q, INV-H broadened). No fold or gate-decision change.

v0.9.1 (ADR-016, wk-280e0b76): total fold order + equal-ts gate. Source:
  independent spec review finding C1 (Critical) -- the fold's (ts, id)
  order is NOT total: a duplicate id carrying a COPIED (equal) ts ties
  both components, and Python's stable sort then resolves the tie by
  file position -- the one thing section 1 promises the fold ignores.
  ADR-008's order_check keyed on strictly-earlier ts, so an equal-ts
  forgery passed validate, and a union merge could seat the tie in
  either file order -> two repositories, two fold results, content
  substitution on one side, validate green everywhere (INV-I falsified;
  ADR-008's own named falsifier reached with NO backdated ts). Two
  complementary fixes: (a) fold_key() appends canon() -- the canonical
  record serialization -- as a third, content-derived sort key, so
  distinct records never tie and every permutation folds identically;
  (b) order_check refuses a duplicate id with equal ts and non-identical
  content, the byte-identical union-merge shape (B2) still passing.
  Canary FAULTS B5-B6; permutation + validate core tests.

v0.9.0 (issue #4, wk-3a8a725f): `contradicts` -- 29148 set consistency
  made syntax (conformance rule R5). Near-dup intake catches
  restatement; nothing caught contradiction -- two incompatible live
  claims coexisted until a human diffed them (field: two back-panel
  formulas, two LEGRABOX width formulas). New record kind `contradicts`
  {a, b, basis}: a DECLARED edge, mirroring premise -- no NLP, the
  moment a gate needs a model to fire it is a review, not a refusal.
  Fold: a post-pass over the UNDERLYING statuses -- for every edge
  whose two endpoints would otherwise both be live, both derive
  DISPUTED. Evaluating edges against pre-edge statuses (never
  iteratively) keeps the fold confluent and makes multi-edge chains
  order-independent; disputed status_ts advances to the edge ts when
  later (safe as a string compare under ADR-015). DISPUTED behaves
  like diverged downstream: premise_check blocks, spec-health fails
  citers, queue lists BOTH sides naming the counterpart, impact stops
  whispering for it; inverse still counts it as watching (knowledge in
  dispute, not absence). Resolution needs no new verb: retract,
  supersede, or re-file one side -- the edge stops firing the moment
  either endpoint is not live, and a dormant edge (an endpoint
  unverified/stale/dead) fires nothing. Intake refusals: unknown ids,
  self-edge, duplicate edge (either direction), retracted endpoint
  (already resolved), empty basis. Canary FAULTS C1-C5.

v0.8.1 (ADR-015, wk-c7378976): canonical timestamp profile. Source: an
  independent spec-only review (pi, 2026-07-17; findings HIGH-1 and
  MEDIUM-4) -- the fold sorts the raw ts STRING, but nothing constrained
  the string's form: schema format:date-time is annotative in draft-07,
  and validate never looked. An honest non-CLI writer using `Z` or a
  non-UTC offset would silently misorder events and break INV-I
  confluence. Three moves, discharging ADR-008's deferred F5 check:
  (a) the profile now_iso() always emitted -- fixed-width UTC
  microseconds, YYYY-MM-DDTHH:MM:SS.ssssss+00:00 -- is mandated by
  schema `pattern` and validate-mirror TS_RE in lockstep (FS-2 mutants
  exercise both on every seed); (b) TRUTH_NOW overrides are normalized
  to aware-UTC so the test hook cannot mint a nonconforming record;
  (c) an HLC-degenerate clock-push at append bumps a real-clock record
  1 microsecond past a ledger tail it would otherwise sort before,
  bounded by ADR-008's skew tolerance (beyond it, the honest clock is
  kept and the regression warning fires). Canary FAULTS TS1-TS3; corpus
  fixtures for Z/offset/precision/naive forms.

v0.8.0 (issue #3, wk-16a3bff7): `baseline` -- set-level status
  accounting (ISO 10007). `baseline <ref>` reads the ledger at a git
  ref (`git show`), runs the SAME fold, and emits the frozen set:
  claims by status/tier, issues by state, with sorted id lists --
  deterministic JSON, no volatile timestamps, so redirect-and-commit
  gives an auditable artifact. `baseline <a> --diff <b>` folds both and
  prints the delta in release-notes shape: born records (with their
  b-status), status transitions grouped from->to, and DISAPPEARED
  records -- in an append-only ledger a record present at an ancestor
  and absent at a descendant means rewritten history, so disappearance
  is an omission alarm (the loophole map's named failure mode) with its
  own exit code 5, gateable. Exit 2 = unreadable ref (usage), 0
  otherwise. Read-only, no fold change, no new record kind, no
  persistence by the CLI (10007's baseline artifact is the caller's
  redirect). Canary FAULTS BL1-BL4.

v0.7.2 (issue #7, wk-75aa9735, owner decision 2026-07-17): path-form
  accept-allow entries. First-consumer dogfood found the gap the same
  day ADR-014 shipped: the repo's REAL suite interpreter is often
  repo-local (.venv/bin/python, ./gradlew, node_modules/.bin/*), and
  the screen's bare-name rule forced either a bash -c wrapper (which
  launders the path past the screen) or the broadest interpreter entry.
  Now an acceptance oracle's program may be a path IFF it exactly
  equals a committed .truth/accept-allow entry, is repo-relative (no
  leading /), and has no `..` segment -- an allowlisted exact path is
  the opposite of arbitrary, and STRONGER than an interpreter bare-name
  (it bounds which executable runs, not which language). The evidence
  screen (ADR-009) keeps its unconditional path refusal: recheck is a
  different trust seam and read-only stays the rule there. Canary
  FAULT AC8.

v0.7.1 (issue #5, wk-bd379821): `impact --inverse` -- the backward
  trace (ISO/IEC/IEEE 24765 bidirectional traceability). Forward impact
  answers "what knowledge does editing these paths endanger?"; inverse
  answers "which tracked files does the ledger know nothing about?" --
  the question a curation-only ledger cannot ask itself (field audit:
  8 of 9 sampled modules untraced, invisible by construction). Joins
  `git ls-files` against the union of evidence_paths globs of ACTIVE
  claims -- every status except retracted: a stale claim still names
  its paths (it needs re-verification, the file is not dark); only
  retraction kills the watch. Same match_paths matcher as the scan and
  forward impact (ADR-005: a second matcher implementation is
  forbidden). Read-only, no fold change, no new record kind. Scoping:
  --under <dir> plus repeatable --exclude <prefix>; anything smarter
  (inventories, verdict classes) is a downstream satellite's job. Exit
  0 when the scope is fully watched / 4 when dark files exist --
  distinct from forward impact's 3 so satellites can gate on each
  separately. Canary FAULTS W5-W8.

v0.7.0 (ADR-014, wk-eb59c649, upstream issues #1+#2): acceptance oracles.
  `truth issue --accept-cmd <cmd> [--accept-kind verification|validation]`
  stores an executable finish line on the issue record at birth (the
  author commits to it BEFORE doing the work, like scope_basis); `truth
  done` executes it from the repo root and refuses the close on non-zero
  exit -- "done" stops being the agent's word. Acceptance commands
  execute repository code BY PURPOSE (pytest, exercise runners), so they
  are screened against their own committed allowlist,
  .truth/accept-allow, never ADR-009's read-only evidence-allow --
  reusing that list would force an unsafe override on every real oracle,
  teaching the bypass. Same structural screen (bare allowlisted names
  per pipeline segment, no command substitution, no path-form programs),
  fail-closed when the allowlist is absent, re-screened at done time
  against the CURRENT allowlist. --accept-unsafe-ok at filing stamps
  accept.screened=false; at done it closes WITHOUT executing an oracle
  that CANNOT run (unscreened/unscreenable), stamped executed=false on
  the event -- it never overrides an oracle that ran and failed.
  --cancel and --reopen skip the oracle (killing failed work must not
  require its finish line to pass). The two kinds keep 12207's two V's
  distinct: verification = suite/gate ("built right"), validation =
  golden-diff ("built the right thing"). Fold impact: none -- acceptance
  is a gate at close, never a stored status. Canary FAULTS AC1-AC7.

v0.6.4 (ADR-013, wk-8d966a5b): premise supersede -- `truth premise
  <issue> <new-tr> --supersedes <old-tr>` appends an auditable redirect
  the ready/impact folds honor, releasing work HELD by a premise that
  died and was corrected under a new id (second-deployment finding:
  before this, the only exit was cancel-and-refile, breaking every
  reference to the old wk- id). Fold half is permissive and confluent
  (last-wins per (issue, old) in (ts, id) order, applied AFTER
  merge_premises so premise-at-birth links redirect too; chains follow
  to a fixed point, cycles stop at first repeat). Intake half is
  strict: replacement claim must exist, old must currently be a
  premise of the issue, and a live/unverified premise is refused
  (it passes ready as-is -- supersede is for dead premises). The
  redirect RE-TARGETS ADR-001 validity, never bypasses it: the
  replacement claim is judged by the same matrix. Canary R10.

v0.6.3 (wk-968bc087): `doctor` warns when the ledger holds work-kernel
  issue records but no discovery file names `truth ready` -- G2's
  invisibility failure, work-kernel edition, found when this template's
  own meta-repo documented the fact verbs but not the work verbs (the
  claim guarding against a recurrence is tr-f8d1d042 in that ledger).
  WARN, not FAIL: a facts-only ledger is legitimate; facts plus
  invisible work is not. Canary TL-2.

v0.6.2 (review findings F1-F5, independent Fable review of v0.6.0/v0.6.1):
  * F1 ADR-009: the evidence screen was bare-name only, so allowlisted
    programs with their own exec/write flags passed (find -exec, sort
    -o, git -c <k>=!cmd). PROGRAM_ARG_DENY screens those flags per
    program; git leaves the shipped default allowlist entirely (its exec
    surface is unbounded). Canary FAULT E5.
  * F2 ADR-008: order_check compared parsed timestamps and abstained
    on tz-naive/unparseable ts, but fold() sorts on the raw ts STRING --
    so a backdated duplicate with a naive or junk ts substituted content
    with validate green. order_check now compares the same string fold
    sorts on, closing the attack directly. Canary FAULTS B3, B4.
    (F5, a redundant validate-layer non-ISO-ts reject, is deferred: it
    would need the JSON-schema mirror's format:date-time enforced in
    lockstep or the FS-2 agreement generator flags drift -- a separate
    coordinated change, and F2 already closes the hole.)
  * F3 ADR-007: scope-signal narrowed vs the proposals doc -- added -t
    (ripgrep type filter) and glob-metacharacter positionals to the
    detector, and everywhere/always/each to the quantifier lexicon. A
    bare tracked-subdir name (no slash/glob) still evades: resolving it
    needs a git oracle the pure core has no access to (documented
    residual). Canary FAULTS Q5, Q6.

v0.6.0 (solo-regime hardening; docs/hardening-proposals-solo-regime.md):
  * ADR-007 quantifier-scope gate: intake refuses a universally
    quantified claim text backed by a scoped evidence command (the exact
    shape of both pilot divergences, paper section 2) unless
    --scope-ok "<why the scope covers the quantifier>" is given; the
    sentence is stored as payload scope_basis, attackable by verifiers.
  * ADR-008 order coherence: `validate` fails on a duplicate-id record
    whose ts sorts before the record it duplicates (the backdated
    substitution the fold accepts, paper section 1) and warns on clock
    regression beyond TRUTH-skew tolerance. File order is append order
    (INV-A), so backdating is visible; the commit gate now blocks it.
  * ADR-009 evidence screen: evidence commands are screened against
    .truth/evidence-allow at intake AND recheck (deferred execution in a
    verifier session is the threat). --evidence-unsafe-ok files anyway
    with evidence.screened=false, but recheck never executes an
    unscreened command. Missing allowlist fails closed for VERIFIED.
  * ADR-010 session separation: `verdict <id> agree` from the claim's
    own session is refused (self-verification); diverge/cannot_verify
    from the author stay allowed (self-incrimination runs against
    interest). Override: TRUTH_SELF_VERDICT=1 (self-attested, F4 class).
  * ADR-011 tombstones need a terminal: retraction and cancel require
    TRUTH_HUMAN=1 plus either an interactive typed-id confirmation or
    TRUTH_HUMAN_ACK=<exact-id> for headless human use. Refusal messages
    no longer teach the bypass ritual.
  * ADR-012 divergence subtype: `verdict <id> diverge --mechanical`
    records that the recipe changed rather than reality; fold and
    status unchanged, queue and stats display it.
  * FS-1 `truth stats`: status/tier/class counts, verdict rates, claim
    half-life per tier (live->stale), queue aging; intake prints the
    observed median half-life beside an author-chosen --ttl-days once
    >=5 observations exist for the tier (suggestion only, never set).
  * FS-3 gate only: `doctor` measures fold latency and warns above
    200ms (the trigger for the snapshot cache; unimplemented until it
    fires, per the growth-gate discipline).

v0.5.7 (ADR-005 trial, impact verb): `truth impact <path>...` -- the
  pre-edit whisper's template half. Pure fold query, read-only: for each
  repo-root-relative path, the live/unverified claims whose
  evidence_paths watch it (the SAME matcher invalidate-scan uses; a
  second matcher implementation is forbidden, ADR-005) and the
  open/claimed work premised on those claims; external premise-linked
  issue ids are listed unconditionally (their status lives
  tracker-side). Exit 0 silent / 3 watched; --json for harnesses.
  Output predicts what the machinery will do (STALES / HOLDs); the verb
  files nothing. Canary FAULTS W1-W4. The hook half (deny list,
  PreToolUse wiring, per-session dedup) is consumer-side per ADR-003
  rule 2; the trial venue is this template repo's own ledger (ADR-005
  status block, amended 2026-07-10).

v0.5.6 (review residuals): CSV parsing for --paths and --deps drops
  empty entries (a trailing comma used to surface as a refusal of the
  literal '' -- fails-closed but cryptic); the INV-M zero-match refusal
  now also names --ttl-days as the escape for facts about files git
  does not track; fold_issues' first-wins rule gains permutation
  confluence coverage matching the claims fold's.

v0.5.5 (audit parity): `validate` now rejects claim records with no
  `text` -- the stdlib mirror had drifted from claims.schema.json's
  required/minLength-1 rule (F1's defect class, caught by a fresh
  audit; the shared conformance corpus had no missing-text fixture).
  Intake refuses empty claim text for the same reason: `truth claim ""`
  used to file a record the schema rejects, which the INV-B commit gate
  would then block -- a CLI that contradicts its own gate. Canary FAULT
  S4 gates spec-health's issues-side degradation path (ADR-003 birth
  law: no satellite path exists ungated, including the graceful ones).

v0.5.4 (INV-M, dead-tripwire intake checks): `truth claim` and
  `done --claim` now refuse two shapes of evidence_path that can never
  invalidate anything -- a whitespace-containing entry with no comma
  (`--paths "a.sh b.sh"` silently storing as one nonexistent literal;
  found by inspection in the pilot ledger, tr-3591aae0) and any literal
  (non-glob) path matching zero files git currently tracks. Explicit
  globs (`*`/`?`) are exempt from the second check -- watching a pattern
  that's empty for now is legitimate intent, a bare typo'd literal is
  not. Applies to any evidence_class carrying paths, not only VERIFIED,
  since invalidation itself doesn't discriminate by class either.

v0.5.3 (ADR-006, issue-fold hardening): duplicate issue ids are now
  FIRST-WINS in fold_issues, matching fold()'s claim handling. v0.5's
  original last-wins choice described a verb the CLI never implements
  (`truth issue` always mints a fresh id from hash(payload, ts, actor);
  no command re-files an existing wk- id), so it was pure attack surface:
  an appended duplicate carrying `premises: []` silently stripped an
  issue's ADR-001 protection, needing no backdating and no terminal-state
  coincidence -- unlike the analogous claims-side gap (paper §8 item 6),
  which needs both. Closes it the way F6 closed it for claims.

v0.5 (ADR-002, work kernel): issues live in the same ledger as claims.
  Two new record kinds -- `issue` (wk- envelope id; payload title/text/
  deps/premises) and `issue_event` (claimed|released|closed|reopened|
  cancelled) -- folded in the same confluent (ts, id) order. Status is
  derived, never stored. `closed` is NOT terminal (work is cyclical);
  `cancelled` IS terminal and requires TRUTH_HUMAN=1 (G12 symmetry).
  Verbs: issue / start / done / issues. `done --claim` files the
  completion fact and the closing event atomically (claim-at-death);
  `issue --premise` links at creation (premise-at-birth; zero premises
  warns). `ready` source precedence: --stdin, TRUTH_TRACKER_CMD, native
  (when issue records exist), then `bd ready --json`. `issues
  --ready-json` emits the E1 adapter contract, so the kernel is itself a
  tracker source and the seam and kernel can never disagree. The ADR-002
  refusal list is binding: no assignees, priorities, dates, labels,
  hierarchy, comments, or compaction without a superseding ADR.

v0.4.1 (tracker adapter seam): `ready` no longer hardcodes Beads.
  Sources: --stdin pipe | TRUTH_TRACKER_CMD | default `bd ready --json`.
  Contract: a JSON array of issue objects with `id` (+ `title`).
  Missing/failing tracker degrades with guidance (previously: raw
  FileNotFoundError traceback, contradicting the "fails loudly with
  fallback" doc). Canary FAULT J now gates all three sources.

v0.4 (audit-driven; SEMANTIC changes, canary extended to 19 checks):
  * fold is CONFLUENT: (ts, id) total order replaces file order, so
    union-merged branches derive identical status either direction.
  * duplicate claim ids ignored (first wins): closes the tombstone-
    resurrection pure-append attack on INV-G.
  * `agree` verdicts re-anchor path-anchored claims: re-verified claims
    stay live across scans instead of re-staling on the frozen anchor.
  * retraction requires TRUTH_HUMAN=1: "humans only" is now a property,
    not a convention addressed to well-behaved verifiers.
  * evidence-path globs: `*`/`?` no longer cross `/` (use `**` to span).
  * claims.schema.json fixed to match behavior: verdict enum includes
    `retracted`; VERIFIED accepts paths OR ttl_days (anyOf).


Same behavior and CLI contract as v0.2 (all 14 canary checks must stay
green); internals reorganized as FUNCTIONAL CORE / IMPERATIVE SHELL:

  PURE CORE        decisions and derivations -- plain data in, plain data
                   out. No subprocess, no filesystem, no clock, no env.
                   Unit-tested in milliseconds by scripts/test-truth-core.py.
  IMPERATIVE SHELL git, files, evidence execution, argparse, printing.
                   Gathers facts, calls the core, applies effects.
                   Acceptance-tested by scripts/truth-canary.sh.

Open/closed seam: invalidation triggers live in the INVALIDATORS list --
adding a trigger (e.g. future attestation) is appending a pure function,
not editing the scan. Time is a parameter everywhere in the core; the
TRUTH_NOW test hook is honored only at the shell boundary (now_dt).

Event kinds, fold semantics, invariants, and gap fixes (G1 G6 G8 G10 G12
G13 G14 G15, ADR-001) are unchanged from v0.2 -- see .truth/README.md.
v0.3 also strengthens `validate` to match the JSON Schema on three points
the v0.2 mirror missed (INFERRED requires basis; id patterns on envelope
and payload references), caught by the schema-conformance test.
