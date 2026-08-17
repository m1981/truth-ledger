"""truthlib.policy -- intake predicates and the ADR-001 matrix (C3).

Pure refusal decisions: premise_check/join_ready, the ADR-013 supersede
and issue-#4 contradicts intake ladders, the G8/ADR-007/INV-M/ADR-032
claim-intake predicates, and the invalidation strategies the scan
consults (decide_invalidation).  Returns refusal strings; only the cli
turns them into exits.
"""
import re

from truthlib.registry import *
from truthlib.kernel import *

# --- non-claim intake predicates (R14b) -----------------------------------
# ADR-013 supersede and issue #4 contradicts intakes decide in the CORE,
# the shell verbs gather and sys.exit -- the issue_event_error pattern,
# applied to the two intakes that had stayed inline under the shell's
# "makes no decisions" banner. Refusal strings are the exact bytes
# cmd_premise/cmd_contradicts used to exit with.

RETRACTED_NEEDS_ACK = "RETRACTED_NEEDS_ACK"
# ^ sentinel, never printed: the ADR-011/ADR-017 human-ack ceremony is
# I/O (env, tty), so it stays in the shell; the predicate only reports
# that the ceremony is required.

def supersede_error(issue, supersedes_id, claim_id, claims,
                    premises_for_issue):
    """ADR-013 intake gates: the fold is permissive (any recorded
    redirect applies, for confluence); intake is strict so a redirect
    that could never mean anything fails loudly. Rule ladder in filing
    order: id shape, self-supersede, replacement-exists,
    currently-a-premise (after redirects), still-passing, and the
    ADR-017 (C3) retracted case -- retraction is a HUMAN terminal veto,
    and redirecting a retracted premise out of an issue releases the
    work that veto was blocking, so it needs the same authority: the
    predicate returns RETRACTED_NEEDS_ACK and the shell runs
    human_ack_error. The mechanical dead states (stale/diverged/
    cannot_verify/missing) stay ungated: no human decided those, so a
    low-friction redirect to the corrected claim is the intended flow.
    Returns a refusal string, the sentinel, or None. Pure."""
    if not ID_RE.match(supersedes_id):
        return "truth: --supersedes must name a tr- claim id (ADR-013)"
    if supersedes_id == claim_id:
        return "truth: a claim cannot supersede itself (ADR-013)"
    if claim_id not in claims:
        return (f"truth: replacement claim {claim_id} is not in the "
                "ledger -- file the corrected fact first (ADR-013)")
    if supersedes_id not in premises_for_issue:
        return (f"truth: {supersedes_id} is not currently a premise of "
                f"{issue} (after redirects) -- nothing to supersede "
                "(ADR-013)")
    old = claims.get(supersedes_id)
    if old and old["status"] in ACTIVE_STATUSES:
        return (f"truth: premise {supersedes_id} is {old['status']} and "
                "passes ready as-is -- supersede is for dead premises "
                "(stale, diverged, retracted, cannot_verify, missing); "
                "re-verify or diverge it first (ADR-013)")
    if old and old["status"] == "retracted":
        return RETRACTED_NEEDS_ACK
    return None

RETRACTION_CAUSE_TREE = (
    "  --cause restated  the sentence is STILL TRUE; a successor states "
    "it better\n"
    "                    (requires --successor <tr-id>)\n"
    "  --cause expired   it WAS true and the world moved past it\n"
    "  --cause wrong     it was NEVER true, or its evidence never "
    "demonstrated it")

def retraction_cause_error(cause, successor, claim_id, claims):
    """ADR-049: a retraction records WHY, and the why carries an
    obligation. Two yes/no questions about the retracted SENTENCE fix
    the value (still true? ever true?), so the vocabulary is a truth
    table, not a survey -- see RETRACTION_CAUSES.

    The one blocking rule -- and the reason the field is admitted under
    ADR-046 at all -- is that `restated` MUST name a successor: a claim
    that still holds is a live belief, and killing it with nothing to
    carry the fact forward is the deletion this gate exists to refuse
    (it is exactly the operation the user-proposed `moved` cause would
    have blessed). The other two causes say the fact itself is gone, so
    a successor is optional there -- 10 of the meta-ledger's causal
    retractions are `wrong` WITH a corrected successor, and refusing
    that pattern would be a false refusal.

    No override flag exists, deliberately: unlike the ADR-036 sweep,
    which can be wrong about the world, this gate asks a question only
    the retracting human can answer and which is always answerable. An
    `--cause-ok` would be the invisible opt-out ADR-032 declined for
    `--no-ttl`. Rule ladder is filing order. Returns a refusal string
    or None. Pure -- `claims` arrives as data."""
    if not cause:
        return ("truth: a retraction must record WHY (ADR-049). Answer "
                "two questions about the sentence you are killing:\n"
                f"{RETRACTION_CAUSE_TREE}\n"
                "  Nothing was filed.")
    if cause not in RETRACTION_CAUSES:
        return (f"truth: unknown retraction cause {cause!r} -- one of "
                f"{'/'.join(RETRACTION_CAUSES)} (ADR-049)")
    if successor is not None:
        if not ID_RE.match(successor):
            return "truth: --successor must name a tr- claim id (ADR-049)"
        if successor == claim_id:
            return ("truth: a claim cannot be its own successor "
                    "(ADR-049)")
        if successor not in claims:
            return (f"truth: successor {successor} is not in the ledger "
                    "-- file the replacement fact FIRST, then retract "
                    "(ADR-049)")
        if claims[successor]["status"] == "retracted":
            return (f"truth: successor {successor} is itself retracted "
                    "-- a tombstone cannot carry a fact forward "
                    "(ADR-049)")
    elif cause == "restated":
        return ("truth: --cause restated says the fact still holds, so "
                "something must still state it -- name the replacement "
                "with --successor <tr-id>. If no claim carries the fact "
                "forward, either file one first, or the fact did NOT "
                "survive and the cause is `expired`/`wrong` (ADR-049). "
                "Nothing was filed.")
    return None

def capsule_coherence_error(verdict, claim_payload, observed, refresh_basis,
                            capsule):
    """ADR-051: the agree-side twin of ADR-012's mechanical subtype.

    ADR-012 split `diverged` because it conflated two facts: reality
    changed, versus the measuring recipe changed while the fact held.
    `agree` carries the identical conflation and had no vocabulary for
    it: "the evidence reproduces AND supports the sentence" and "the
    evidence no longer reproduces but I judge the sentence still holds"
    file the same record. Measured on the pilot ledger, humans hit the
    second case and wrote the reason in prose -- "the recipe uses grep
    -n, so the line numbers shifted" -- which is exactly the unrecorded-
    judgment shape ADR-049 found in 65% of retraction bases.

    The cost of the missing vocabulary is not cosmetic. An agree on a
    path-carrying claim advances the effective anchor (F2); the capsule
    is immutable and stays behind. So that agree silently converts the
    claim into one that can NEVER be mechanically re-confirmed: every
    later `--recheck` compares against an unproducible hash and
    auto-diverges (and the verifier prompt says to stop there, before
    the step that would read the sentence), while reaffirm's hash-match
    arm can never take it back. 13 of 126 live claims sat in that state
    when this was measured, and 10 of 77 retractions had passed through
    it.

    So: refuse the agree that would advance the anchor past a capsule
    that no longer reproduces, unless the verifier states which case it
    is. `--refresh-evidence "<sentence>"` records the judgment AND the
    newly observed capsule, so anchor and capsule move together.

    Refusal, not advisory -- ADR-049's three-part test, applied:
      * volume is low (a mismatching manual agree, not every filing);
      * the question is perfectly decidable (two hashes) and can never
        produce a false refusal, so it cannot teach its own bypass --
        the ADR-014 confused-deputy objection that made ADR-037's lints
        warnings does not reach it;
      * the convention equivalent has been measured to fail: ADR-012's
        `--mechanical` exists on the diverge side and was used 6 times
        in 99 diverges, while the agree side recorded nothing at all.

    `observed` is (digest, returncode) from the shell's single run, or
    None when there was nothing to run or the screen refused it -- an
    unscreenable command can never be rechecked anyway, so there is no
    capsule freshness to protect and the gate abstains. `capsule` is the
    EFFECTIVE evidence (claim capsule + newest refresh), so a second
    drift after a refresh re-fires this gate. Returns a refusal string
    or None. Pure."""
    if verdict != "agree":
        if refresh_basis:
            return ("truth: --refresh-evidence only accompanies an agree "
                    "(ADR-051: it records that a changed output still "
                    "supports the sentence; a diverge says the opposite, "
                    "and cannot_verify says neither)")
        return None
    if not claim_payload.get("evidence_paths"):
        # No anchor advance (cmd_verdict re-anchors only for path
        # claims), so the capsule cannot be orphaned by this verdict.
        if refresh_basis:
            return ("truth: --refresh-evidence on a claim with no watched "
                    "paths -- this agree does not advance an anchor, so "
                    "no capsule can fall behind it (ADR-051)")
        return None
    if not (capsule or {}).get("command"):
        if refresh_basis:
            return ("truth: --refresh-evidence on a claim carrying no "
                    "evidence command -- there is no capsule to refresh "
                    "(ADR-051)")
        return None
    if observed is None:
        # Unscreenable or unrunnable: `--recheck` refuses to execute it
        # too (ADR-009/029), so the claim is manual-only either way.
        if refresh_basis:
            return ("truth: --refresh-evidence but the evidence command "
                    "was not executed here -- a refresh records an act, "
                    "never a wish (ADR-051). Nothing was filed.")
        return None
    digest, rc = observed
    matches = ("sha256:" + digest == capsule.get("output_hash")
               and rc == capsule.get("returncode", rc))
    if matches:
        if refresh_basis:
            return ("truth: --refresh-evidence with a capsule that still "
                    "reproduces -- there is nothing to refresh (ADR-051: "
                    "a basis with nothing to excuse is schema noise; drop "
                    "the flag)")
        return None
    if refresh_basis:
        return None
    return ("truth: this agree would advance the claim's anchor past a "
            "capsule that no longer reproduces (ADR-051). The recorded "
            "evidence hash can never be produced again, so every later "
            "--recheck on this claim would auto-diverge and reaffirm "
            "could never re-confirm it mechanically.\n"
            "  If the output changed but the SENTENCE still holds (a "
            "line-number shift, a count that grew), say so and carry the "
            "new capsule forward:\n"
            "    --refresh-evidence \"<one sentence: why the changed "
            "output still supports this claim>\"\n"
            "  If the change means the claim itself moved, file diverge "
            "instead (--mechanical if only the recipe drifted, ADR-012). "
            "Nothing was filed.")

def contradicts_intake_error(a, b, claims, events):
    """Issue #4 intake gates, filing order: self-edge, unknown id (a
    then b), retracted endpoint, duplicate edge either direction. The
    --basis requirement stays in the shell AFTER these checks (it reads
    the flag, not the fold) -- same order as before the extraction.
    Returns a refusal string or None. Pure."""
    if a == b:
        return "truth: a claim cannot contradict itself (issue #4)"
    for cid in (a, b):
        if cid not in claims:
            return (f"truth: unknown claim {cid} -- a contradiction is "
                    "declared between two EXISTING claims (issue #4)")
        if claims[cid]["status"] == "retracted":
            return (f"truth: {cid} is retracted -- the dispute is already "
                    "resolved; an edge to a tombstone can never fire "
                    "(issue #4)")
    pair = {a, b}
    for _, ev in events:
        if ev.get("kind") == "contradicts" \
                and {ev["payload"].get("a"), ev["payload"].get("b")} == pair:
            return (f"truth: this contradiction is already declared "
                    f"({ev['id']}) -- one edge per pair, either "
                    "direction (issue #4)")
    return None

# ------------------------------------------------- intake decisions (G1/6/8)

def duplicate_conflicts(text, claims):
    """G8 / ADR-018: near-duplicates among ACTIVE claims only. "Active" is
    exactly {live, unverified} (positive form -- stays correct as the
    status vocabulary grows); every other status (stale, diverged,
    cannot_verify, retracted, disputed) is dead-for-intake, so a
    correcting refile against it is legitimate (UC-4). Metric is jaccard()
    -- symmetric |A n B|/|A u B|, NOT the overlap coefficient -- so a
    strict elaboration (subset) is not a duplicate. Threshold >= 0.6."""
    return [(cid, e["claim"]["payload"].get("text", ""))
            for cid, e in claims.items()
            if e["status"] in ACTIVE_STATUSES
            and jaccard(text, e["claim"]["payload"].get("text", ""))
            >= DUPLICATE_THRESHOLD]

def malformed_path_list(paths):
    """INV-M: a path token containing internal whitespace almost always
    means the caller forgot a comma -- '--paths "a.sh b.sh"' stores as
    ONE literal ('a.sh b.sh') matching nothing, a dead invalidation
    tripwire from the moment it's filed (found by inspection in the
    pilot ledger: tr-3591aae0).

    THE FILE HALF ONLY, since step 3.1. A Markdown selector is a heading
    query and headings have spaces in them: `docs/spec.md#2. Session
    Management` is the ordinary spelling, and the slug form is an
    alternative the author may not know. Screening the whole target
    would refuse the documented syntax (spec §2.2) as a missing comma --
    the reverse of this check's purpose, which is to catch a token that
    can never match, not to forbid one that reads oddly."""
    return [p for p in paths if re.search(r"\s", watch_target_path(p))]

def dead_literal_paths(paths, tracked):
    """INV-M: a literal path (no glob metacharacters) matching zero
    tracked files can never invalidate anything -- the same dead-tripwire
    failure, reached a different way. Explicit globs ('*'/'?') are
    EXEMPT: watching a pattern that matches nothing yet is a legitimate
    intent (a not-yet-created file under a directory), unlike a plain
    literal, which has nothing else it could mean.

    Compared on the FILE half (step 3.1): `package.json#/dependencies/
    stripe` is tracked as `package.json`, and comparing the whole target
    against the tracked set would make every selector a dead literal --
    refusing the feature at its own intake."""
    tracked_set = set(tracked)
    return [p for p in paths
            if "*" not in (q := watch_target_path(p)) and "?" not in q
            and q not in tracked_set]

def selector_on_glob_paths(paths):
    """INV-M, step 3.1: a `#selector` on a GLOB is refused. A selector
    resolves against one document -- `extract_structural_hash` takes the
    bytes of a single file -- so `template/**#/a/b` names no fact: there
    is no one sub-tree for the digest to be OF, and nothing downstream
    could pick a file to read. Left unrefused it would be worse than
    dead: match_paths strips the selector, so the target would quietly
    behave as the bare glob and watch far more than the author wrote.

    Sound and complete on its own terms -- a selector is present or it
    is not, the pattern has a metacharacter or it does not."""
    return [p for p in paths
            if split_selector_target(p)[1]
            and any(c in watch_target_path(p) for c in "*?")]

def unsupported_selector_paths(paths):
    """INV-M, step 3.1: a `#selector` on a file type with no sub-trees
    (`.py`, `.ts`, `.sh`) is refused AT INTAKE rather than at first read.

    extract_structural_hash raises UnsupportedFormatError for these, and
    the raise would land in `truth reproduce` -- days later, on a claim
    that already looks filed and healthy. The whole INV-M stance is that
    a tripwire which cannot fire must be caught while the author is
    still standing there, and this is the same defect with a new cause.

    Returns [(target, ext), ...]; the caller names the supported set.
    Pure: the decision is the extension, never the file."""
    bad = []
    for p in paths:
        path, selector = split_selector_target(p)
        if not selector:
            continue
        base = path.rsplit("/", 1)[-1]
        ext = base.rsplit(".", 1)[-1].lower() if "." in base[1:] else ""
        if ext not in SUPPORTED_STRUCTURED_EXTENSIONS:
            bad.append((p, "." + ext if ext else "<none>"))
    return bad

def dead_glob_paths(paths):
    """INV-M / ADR-024 (H5 follow-up): a glob is EXEMPT from
    dead_literal_paths, but a glob whose pattern can match no path
    `git diff --name-only` could ever emit is a dead tripwire all the same.
    git-diff paths are repo-relative, '/'-separated and normalized: never
    absolute, never under '.git/', with no '.'/'..'/empty component and no
    trailing '/'. So a glob is statically dead when a path COMPONENT is
    empty (absolute path, trailing slash, or '//'), is '.' or '..', or the
    leading component is exactly '.git'. Unlike the tracked-symlink
    residual (which needs link resolution) this is decidable from the
    pattern alone. SOUND, not complete: every pattern returned is provably
    unreachable -- no false refusals, since a wildcard component ('*',
    'a*', '.git*', '.github/**') still matches real names -- but exotic
    dead globs (e.g. a nested-submodule '.git') may still slip through;
    that is INV-M's residual class, not a boundary claim (cf. ADR-021)."""
    dead = []
    for target in paths:
        # Step 3.1: the FILE half decides reachability -- git emits paths,
        # never selectors -- but the ORIGINAL target is what gets reported,
        # so the refusal quotes the string the author actually typed.
        p = watch_target_path(target)
        if "*" not in p and "?" not in p:
            continue                       # a literal: dead_literal_paths owns it
        comps = p.split("/")
        if comps[0] == ".git":             # under the git dir -- never tracked
            dead.append(target)
        elif any(c in ("", ".", "..") for c in comps):  # absolute, trailing
            dead.append(target)            # slash, '//', or a '.'/'..' component
    return dead

def verified_intake_error(evidence_cmd, evidence_paths, ttl_days, head):
    if not evidence_cmd:
        return "truth: VERIFIED claims require --evidence-cmd (INV-B)"
    if not evidence_paths and not ttl_days:
        return ("truth: VERIFIED claims require --paths (INV-C) or "
                "--ttl-days for facts outside the repo (G10)")
    if head is None:
        return ("truth: repository has no commits -- the anchor requires "
                "at least one commit before VERIFIED claims can be filed (G1)")
    return None

def inferred_intake_error(basis):
    return None if basis else "truth: INFERRED claims require --basis"

def quantifier_scope_conflict(text, evidence_cmd):
    """ADR-007: a universally quantified sentence over a scoped command
    is the exact shape of both pilot divergences -- a repo-wide clause
    backed by a package-scoped grep whose filters do invisible work.
    Returns (q_signal, s_signal) when both sides fire, else None. Token
    matching only; the gate forces the mismatch to be *stated*
    (--scope-ok), never judges whether the scope covers the quantifier
    -- that stays the verifier's job."""
    if not evidence_cmd:
        return None
    low = text.lower()
    q = next((ph for ph in QUANTIFIER_PHRASES
              if re.search(r"\b" + re.escape(ph) + r"\b", low)), None)
    if q is None:
        q = next((t for t in sorted(QUANTIFIER_TOKENS) if t in tokens(text)),
                 None)
    if q is None:
        return None
    parts = evidence_cmd.split()
    s = next((p for p in parts
              if p in SCOPE_OPTION_TOKENS
              or p.split("=", 1)[0] in SCOPE_OPTION_TOKENS), None)
    if s is None and evidence_cmd.strip().startswith("cd "):
        s = "cd"
    if s is None:
        # a positional that narrows the domain: a path (slash) or a glob
        # metacharacter (F3/v0.6.2 -- 'grep foo src/*.py' is scoped). A
        # bare tracked-subdir name with no slash or glob ('grep foo src')
        # still evades: resolving it needs a git oracle, which this pure
        # core deliberately has no access to (residual, ADR-007 comment).
        s = next((p for p in parts[1:]
                  if not p.startswith("-")
                  and ("/" in p or any(c in p for c in "*?["))), None)
    if s is None:
        return None
    return (q, s)

def override_decay(scope_basis, ttl_days, flag="--scope-ok"):
    """ADR-032: a --scope-ok override (scope_basis, ADR-007) filed WITHOUT
    an explicit --ttl-days decays -- it is stamped a default shelf life so
    the scope judgment cannot rot silently: when the default TTL lapses the
    unchanged ADR-019 scan materializes the expiry, ADR-030 arm 1 routes
    the stale claim to re-file, and re-filing re-fires the ADR-007 gate,
    mechanically re-asking whether the scope judgment was ever real.

    Returns (ttl_days, ttl_default_flag, notice_or_None):
      * scope_basis present AND ttl_days is None -> (DEFAULT_OVERRIDE_TTL_
        DAYS, True, a one-line stderr notice explaining the default and how
        to opt out);
      * an explicit ttl_days -> (ttl_days, False, None) -- the visible
        opt-out (a large --ttl-days is the deliberate long life), unchanged
        even when a scope_basis is present;
      * no scope_basis -> (ttl_days, False, None), unchanged.

    Pure -- reads no clock; the expiry itself is counted from the claim's
    ts by the scan (ADR-019), never here. Deliberately no decay for
    screened:false claims and no --no-ttl flag: an explicit large
    --ttl-days is the visible opt-out (ADR-032 exclusions)."""
    if scope_basis and ttl_days is None:
        return (DEFAULT_OVERRIDE_TTL_DAYS, True,
                f"{flag} override filed with no --ttl-days -- "
                f"stamped a default {DEFAULT_OVERRIDE_TTL_DAYS}-day expiry "
                "(ADR-032) so the override judgment is re-asked when it "
                "lapses. Pass an explicit --ttl-days (a large value is the "
                "visible opt-out) to choose a different shelf life.")
    return (ttl_days, False, None)

# ------------------------------- invalidation strategies (OCP seam, G10/14)
# Each strategy: (entry, facts, now) -> None, or
#   {"payload": <fields merged into the invalidation record>,
#    "label":   <short reason for scan output>}
# `facts` is gathered by the shell per claim; missing keys mean the fact
# was not gathered, and a strategy needing them abstains.
# the Reproduce-on-Read refactor (step 2.6) narrowed this to the CLOCK arm alone -- see the note
# where the two path/anchor strategies used to live.

def _ttl_expired(entry, facts, now):
    """ADR-019: TTL counts from the claim's own ts (not the anchor, not
    the agree verdict) and the boundary is STRICT -- expired only when
    (now - ts) > ttl_days, so at exactly ts + ttl_days it survives. Runs
    inside the scan (an INVALIDATOR), which is the only clock reader; it
    emits an invalidation record, and the fold demotes to stale off that
    record. The fold never evaluates TTL itself -- purity/confluence."""
    p = entry["claim"]["payload"]
    ttl = p.get("ttl_days")
    claim_ts = parse_ts(entry["claim"].get("ts") or "")
    if ttl and claim_ts and (now - claim_ts).total_seconds() > ttl * 86400:
        # reason_code (v0.9.12 red-team F3): the STRUCTURED twin of the
        # human reason, so consumers (reaffirm's TTL arm) need not parse
        # free text. Schema/mirror payloads are open; older records
        # simply lack it and readers fall back to the reason prefix.
        return {"payload": {"reason": f"ttl expired ({ttl} days)",
                            "reason_code": "ttl"},
                "label": "ttl expired"}
    return None

# _anchor_unreachable and _evidence_paths_touched were RETIRED in the Reproduce-on-Read refactor
# (refactor step 2.6). Both answered the SYNTACTIC question -- did git
# touch something -- that `truth reproduce` now answers directly and
# semantically at read time (~8ms per capsule, 0.53s for the whole live
# ledger). On this ledger they wrote 1997 records at a 3.6% positive
# predictive value; keeping a writer at that precision, for a status the
# fold no longer derives from it (the double-invalidation rule), would be
# storing noise nobody reads. The 1997 records they already wrote stay in
# the ledger and stay readable forever -- retiring a WRITER is not
# breaking a READER (J-012).

# --- FAZA 3: named watch policies (defect D-A) ---------------------------

def watch_policy_error(name, policies, state):
    """Intake decision for `--watch-policy <name>`: a refusal string, or
    None when the filing may proceed. Pure -- the shell loads the file
    (shellio.load_watch_policies) and this decides.

    The whole point of the feature is that a watch set stops being
    re-invented per filing, so the ONE thing this must never do is guess.
    An unknown name is refused with the available names listed, rather
    than falling back to 'watch nothing' -- a claim that silently watched
    nothing would be the dead tripwire INV-M exists to refuse, arrived at
    by a typo.

    `name is None` is the ordinary case and passes: policies are opt-in,
    and a repo that names none is not misconfigured (WATCH_POLICIES_REL)."""
    if name is None:
        return None
    if state == "absent":
        return (f"truth: --watch-policy {name!r} but {WATCH_POLICIES_REL} "
                "does not exist -- there is no policy set to name. Create "
                "it with one `<name> -- <glob>[, <glob>...]` line per "
                "policy, or pass --paths directly.")
    if name not in policies:
        known = ", ".join(sorted(policies)) or "(none defined)"
        return (f"truth: unknown watch policy {name!r} -- "
                f"{WATCH_POLICIES_REL} defines: {known}. A typo must not "
                "quietly file a claim that watches nothing (INV-M).")
    return None

def watch_policy_conflict_error(name, paths_csv):
    """G-class refusal: --watch-policy and --paths both given. Two
    sources for one field is the drift shape this feature exists to
    close, and 'the flag wins' would make the recorded evidence_paths
    depend on argument order rather than on a committed decision. Pure."""
    if name is not None and paths_csv:
        return (f"truth: --watch-policy {name!r} and --paths cannot be "
                "combined -- a claim's watch set comes from ONE source, "
                "either the named policy or the explicit list. Drop one.")
    return None

# --- F3.1: a conscious empty is not the same as an untouched default -----

def policy_file_state(text):
    """F3.1: classify a policy file's CONTENT (SI-4, made decidable).
    Pure -- `text` is the file's content, or None when the file is
    absent; the shell does the reading.

      absent      the file is not there. A different state with its own
                  voice (the check runs dark and says so); never an
                  attestation problem.
      populated   at least one non-comment, non-blank line. The entries
                  ARE the statement; nothing to attest.
      attested    no entries, and a `# attested YYYY-MM-DD: <reason>`
                  line. Emptiness was chosen, dated, and justified.
      unattested  no entries and no such line -- byte-for-byte what the
                  template ships, which is a decision NOBODY MADE. This
                  is the state F3.1 exists to separate out; before it,
                  SI-4 read it as identical to `attested` and went
                  silent."""
    if text is None:
        return "absent"
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return "populated"
    for line in text.splitlines():
        if POLICY_ATTESTATION_RE.match(line):
            return "attested"
    return "unattested"

def policy_attestation_error(rel, state):
    """F3.1: the refusal text for an unattested empty policy file, or
    None. Pure. The message has to teach the fix, because the fix is one
    line and the failure otherwise reads as bureaucracy."""
    if state != "unattested":
        return None
    return (f"{rel} is committed but EMPTY with no attestation -- which is "
            "byte-identical to the untouched default, so nothing here "
            "records that the emptiness was ever decided (ADR-042 rule 2: "
            "zero coverage is a failure until someone says otherwise). Add "
            "one line: '# attested YYYY-MM-DD: <why nothing belongs here>' "
            "-- or add the entries that do belong.")

def generated_blind_spot(globs, tracked, probes=GENERATED_DIR_PROBES):
    """F3.1 cross-check: tracked files sitting under a conventionally
    generated directory that the committed list does NOT cover. Pure;
    the shell supplies the committed globs and `git ls-files`.

    Naming is evidence, not proof -- a directory called `generated/` can
    hold hand-written files -- so a hit is a WARN that NAMES the files
    and lets a human decide, never a refusal. It exists because the
    expensive failure is silent: an empty generated-paths list plus a
    tracked `exercises/*/generated/rozrys.csv` means the ADR-037 gate is
    switched off exactly where it was needed, and the attestation check
    alone cannot see that -- an attested empty file is still wrong if
    the repo demonstrably generates something."""
    return sorted(f for f in tracked
                  if match_paths(f, probes) and not match_paths(f, globs))

# ONE strategy since refactor step 2.6. The cascade's order used to be part of the
# contract (TTL, then anchor, then paths); with the other two retired
# there is nothing left to order, and the tuple stays a tuple so a future
# clock-shaped invalidator has an obvious seat rather than a rewrite.
INVALIDATORS = (_ttl_expired,)

def decide_invalidation(entry, facts, now):
    if entry["status"] not in ACTIVE_STATUSES:
        return None
    for strategy in INVALIDATORS:
        decision = strategy(entry, facts, now)
        if decision:
            return decision
    return None

def premise_check(status, tier):
    """ADR-001 matrix. Returns (passes, warning-or-None)."""
    if status == "live":
        return True, None
    if status == "unverified":
        return True, "premise not yet independently verified"
    if status == "cannot_verify":
        if tier == "P0":
            return False, None
        return True, "premise is cannot_verify (non-P0, passes per ADR-001)"
    return False, None  # stale | diverged | disputed | retracted | missing

def join_ready(issues, claims, premises):
    """Annotate bd issues with premise validity; return (ready, all)."""
    annotated, ready = [], []
    for issue in issues:
        iid = issue.get("id", "")
        deps = premises.get(iid, [])
        broken, warnings = [], []
        for c in deps:
            if c not in claims:
                broken.append(c + " (missing)")
                continue
            passes, warn = premise_check(
                claims[c]["status"],
                claims[c]["claim"]["payload"].get("cost_tier"))
            if not passes:
                broken.append(f"{c} ({claims[c]['status']})")
            elif warn:
                warnings.append(f"{c}: {warn}")
        if broken:
            issue = {**issue, "_truth": {"ready": False,
                                         "broken_premises": broken}}
        else:
            issue = {**issue, "_truth": {"ready": True, "premises": deps,
                                         "warnings": warnings}}
            ready.append(issue)
        annotated.append(issue)
    return ready, annotated

# --- moved here by A2 -----------------------------------------------------
# citation_block_paths decides which grep hits BLOCK a tombstone. That is a
# refusal decision, and policy's criterion is "it is a refusal"; advisory's
# is "what the CLI prints beside a result". It was in the wrong module.
def citation_block_paths(hits, scope_globs):
    """Pure (ADR-036): which grep hits actually block -- inside the
    scope and never the ledger itself (retraction bases legitimately
    cite predecessors/successors, so an unexcluded ledger would make
    every second retraction self-blocking). TG4/TG9 pin this."""
    return sorted(h for h in hits
                  if h != LEDGER_REL and match_paths(h, scope_globs))
