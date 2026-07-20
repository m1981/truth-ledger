# truth CLI — version history

Extracted verbatim from the `scripts/truth` module docstring at
v0.9.13 (roadmap-v3 R5): the history block had grown past 500 lines.
The CLI still states its CURRENT version on its own line 2
(`"""truth vX.Y.Z -- ...`) — the ADR-026 lockstep test
(`TestCrossSurfaceVersions` in scripts/test-truth-core.py) parses that
line and pins every other version surface to it. Newest first; a
release adds its entry here AND bumps the docstring version line.

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
