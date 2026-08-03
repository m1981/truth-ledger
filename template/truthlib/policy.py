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
    pilot ledger: tr-3591aae0)."""
    return [p for p in paths if re.search(r"\s", p)]

def dead_literal_paths(paths, tracked):
    """INV-M: a literal path (no glob metacharacters) matching zero
    tracked files can never invalidate anything -- the same dead-tripwire
    failure, reached a different way. Explicit globs ('*'/'?') are
    EXEMPT: watching a pattern that matches nothing yet is a legitimate
    intent (a not-yet-created file under a directory), unlike a plain
    literal, which has nothing else it could mean."""
    tracked_set = set(tracked)
    return [p for p in paths
            if "*" not in p and "?" not in p and p not in tracked_set]

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
    for p in paths:
        if "*" not in p and "?" not in p:
            continue                       # a literal: dead_literal_paths owns it
        comps = p.split("/")
        if comps[0] == ".git":             # under the git dir -- never tracked
            dead.append(p)
        elif any(c in ("", ".", "..") for c in comps):  # absolute, trailing
            dead.append(p)                 # slash, '//', or a '.'/'..' component
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
# was not gathered, and path/anchor strategies then abstain.
# Order matters and is part of the contract: TTL first, then anchor
# reachability, then path diffs (matches v0.2 semantics).

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

def _anchor_unreachable(entry, facts, now):
    if facts.get("anchor_reachable") is False:
        return {"payload": {"reason": "anchor unreachable (history rewritten)"},
                "label": "anchor unreachable"}
    return None

def _evidence_paths_touched(entry, facts, now):
    err = facts.get("diff_error")
    if err:
        return {"payload": {"reason": f"diff against anchor failed: {err[:120]}"},
                "label": "diff failed"}
    changed = facts.get("changed_files")
    if changed is None:
        return None
    paths = entry["claim"]["payload"].get("evidence_paths", [])
    touched = [f for f in changed if match_paths(f, paths)]
    if touched:
        return {"payload": {"touched": touched, "reason": "evidence paths changed"},
                "label": "paths changed"}
    return None

INVALIDATORS = (_ttl_expired, _anchor_unreachable, _evidence_paths_touched)

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
