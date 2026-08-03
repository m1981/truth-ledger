"""truthlib.kernel -- records, canon, the confluent folds, and the
validate mirror (C1).

Pure functions from plain data to plain data: no I/O, no clock reads, no
env, no subprocess.  Home of canon/fold_key (ADR-016), fold/fold_issues/
fold_supersedes, order_check (ADR-031), validate_events (the schema
mirror), the path matcher, and the pure git-output parsers
(parse_name_log, blast_forecast -- placed here, not in advisory, because
shellio.blast_history consumes them and shellio imports kernel only).
"""
import functools
import hashlib
import json
import re
from datetime import datetime

from truthlib.registry import *

# ------------------------------------------------------------ primitives

def canon(ev):
    """The canonical serialization of a record -- a deterministic
    function of content, identical for byte-identical records and
    distinct for any field difference. Records are appended with the
    same sort_keys=True dump, so this reproduces the on-disk bytes for a
    CLI-written line."""
    return json.dumps(ev, sort_keys=True)

def fold_key(ne):
    """ADR-016: the fold's TOTAL order. (ts, id) alone is not total --
    a duplicate id carrying a copied (equal) ts ties on both components,
    and a stable sort then breaks the tie by file position, the one
    thing the fold must ignore to be confluent (INV-I). The third key is
    canon(): distinct records never tie, so every event permutation --
    including the two file orders a union merge can produce -- folds to
    one state. Byte-identical records (git's union-merge duplicate, B2)
    tie on all three keys and coincide, so which wins is immaterial.
    order_check (a gate, not the fold) separately refuses ANY
    non-identical duplicate id (ADR-031), so an attacker cannot use this
    key to pick a substitution winner in a committed ledger."""
    ev = ne[1]
    return (ev.get("ts") or "", ev.get("id") or "", canon(ev))

def tokens(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))

def jaccard(a, b):
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)

@functools.lru_cache(maxsize=None)
def _glob_rx(pat):
    """Glob -> regex where `*`/`?` stop at `/` and `**` spans (v0.4:
    fnmatch's `*` crossed directory boundaries, over-invalidating).
    Cached (ADR-034): pure of its argument, and the scan/impact paths
    call it per (path, pattern) pair -- compiling once per pattern."""
    out, i = [], 0
    while i < len(pat):
        if pat[i:i + 2] == "**":
            out.append(".*"); i += 2
        elif pat[i] == "*":
            out.append("[^/]*"); i += 1
        elif pat[i] == "?":
            out.append("[^/]"); i += 1
        else:
            out.append(re.escape(pat[i])); i += 1
    return re.compile("^" + "".join(out) + "$")

def match_paths(path, patterns):
    for pat in patterns:
        if pat.endswith("/**"):
            base = pat[:-3]
            if path == base or path.startswith(base + "/"):
                return True
        if _glob_rx(pat).match(path):
            return True
    return False

def parse_ts(s):
    try:
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None

def split_csv(csv):
    """CSV flag values (--paths, --deps): split, strip, drop empties, so
    a trailing or doubled comma never surfaces as a refusal of ''."""
    if not csv:
        return []
    return [p.strip() for p in csv.split(",") if p.strip()]

# --------------------------------------------------- record construction

def make_id(payload, ts, actor_name, prefix="tr-"):
    blob = json.dumps(payload, sort_keys=True) + ts + actor_name
    return prefix + hashlib.sha256(blob.encode()).hexdigest()[:8]

def make_record(kind, payload, actor_name, session_name, ts, prefix="tr-"):
    return {"id": make_id(payload, ts, actor_name, prefix), "kind": kind,
            "actor": actor_name, "session": session_name, "ts": ts,
            "payload": payload}

# ----------------------------------------------------------------- fold

def fold(events):
    """Derive claim states (+ status timestamps) and the premise map.

    v0.4 semantics -- three hardenings, same shape:
      * CONFLUENCE: events are folded in (ts, id) order, a total order
        independent of file position, so union-merged branches derive the
        same status regardless of merge direction. "Last event wins" now
        means last in time, deterministically tie-broken by id.
      * FIRST CLAIM WINS: a duplicate claim id is ignored -- appending a
        second claim record with an existing id must not reset status
        (closes the tombstone-resurrection append attack on INV-G).
      * EFFECTIVE ANCHOR: an `agree` verdict carrying anchor_commit
        advances the claim's anchor, so re-verified claims stay live
        across subsequent invalidate-scans instead of re-staling forever.
    `retracted` remains terminal (G12).
    """
    ordered = sorted(events, key=fold_key)  # ADR-016: total, content-derived
    claims, premises, edges = {}, {}, []
    def set_status(cid, status, ts):
        if claims[cid]["status"] == "retracted":
            return
        claims[cid]["status"] = status
        claims[cid]["status_ts"] = ts
    for _, ev in ordered:
        kind, p = ev.get("kind"), ev.get("payload", {})
        if kind == "contradicts":
            edges.append((p.get("a"), p.get("b"), ev.get("ts")))
        elif kind == "claim":
            if ev["id"] in claims:
                continue  # first claim wins; duplicates cannot reset status
            claims[ev["id"]] = {"claim": ev, "status": "unverified",
                                "status_ts": ev.get("ts"),
                                "anchor": p.get("anchor_commit")}
        elif kind == "verdict":
            c = p.get("claim")
            if c in claims:
                # R13: VERDICT_STATUS by direct index -- an unknown
                # verdict raises KeyError exactly as the inline map did
                # (extraction only; the unknown-verdict split across
                # consumers is noted at the constant, not fixed here).
                set_status(c, VERDICT_STATUS[p["verdict"]], ev.get("ts"))
                if p["verdict"] == "agree" and p.get("anchor_commit") \
                        and claims[c]["status"] == "live":
                    claims[c]["anchor"] = p["anchor_commit"]
                # ADR-012: subtype is display metadata, never status --
                # a mechanically diverged claim still queues (the recipe
                # needs re-filing), it just says why.
                if claims[c]["status"] == "diverged":
                    claims[c]["subtype"] = (p.get("subtype")
                                            if p["verdict"] == "diverge"
                                            else None)
        elif kind == "invalidation":
            c = p.get("claim")
            if c in claims:
                set_status(c, "stale", ev.get("ts"))
        elif kind == "premise":
            premises.setdefault(p["issue"], []).append(p["claim"])
    # Issue #4 (v0.9.0): the DISPUTED post-pass. Every edge is judged
    # against the UNDERLYING statuses computed above -- never against
    # statuses this pass itself changes -- so the result is independent
    # of edge order and the fold stays confluent. An edge fires only
    # while BOTH endpoints would otherwise be live; anything else
    # (unverified, stale, diverged, dead, missing) leaves it dormant.
    # status_ts advances to the edge ts when later (ADR-015 fixed-width
    # timestamps make the string max well-ordered).
    fires = [(a, b, ts) for a, b, ts in edges
             if a != b  # hand-crafted self-edge: inert, never disputes
             and claims.get(a, {}).get("status") == "live"
             and claims.get(b, {}).get("status") == "live"]
    for a, b, ts in fires:
        for side, other in ((a, b), (b, a)):
            e = claims[side]
            e["status"] = "disputed"
            if ts and ts > (e.get("status_ts") or ""):
                e["status_ts"] = ts
            e.setdefault("disputed_with", []).append(other)
    for e in claims.values():
        if "disputed_with" in e:
            e["disputed_with"] = sorted(set(e["disputed_with"]))
    return claims, premises

def age_days(entry, now):
    ts = parse_ts(entry.get("status_ts") or "")
    if ts is None:
        return None
    return max(0, (now - ts).days)

# --------------------------------------------------- work kernel (ADR-002)

_ISSUE_EVENT_STATUS = {"claimed": "claimed", "released": "open",
                       "closed": "closed", "reopened": "open",
                       "cancelled": "cancelled"}

def fold_issues(events):
    """Derive issue states from the same event stream, in the same
    confluent (ts, id) total order as fold(). Duplicate issue ids are
    FIRST-WINS (ADR-006), identical to fold()'s claim handling -- closes
    the same class of attack F6 closed for claims: an appended duplicate
    wk- id could otherwise overwrite `premises` and silently strip an
    issue's ADR-001 protection. `cancelled` is terminal (G12 symmetry)
    while `closed` is not (work is cyclical; closing asserts completion,
    not falsity) -- that rule, unlike first-wins, does differ from claim
    folding and is decided in ADR-002."""
    ordered = sorted(events, key=fold_key)  # ADR-016: total, content-derived
    issues = {}
    for _, ev in ordered:
        kind, p = ev.get("kind"), ev.get("payload", {})
        if kind == "issue":
            if ev["id"] in issues:
                continue  # first issue payload wins; duplicates cannot alter it
            issues[ev["id"]] = {"issue": ev, "status": "open",
                                "status_ts": ev.get("ts")}
        elif kind == "issue_event":
            ref = p.get("issue")
            if ref in issues and issues[ref]["status"] != "cancelled":
                status = _ISSUE_EVENT_STATUS.get(p.get("event"))
                if status:
                    issues[ref]["status"] = status
                    issues[ref]["status_ts"] = ev.get("ts")
    return issues

def issue_event_error(status, event):
    """Filing-time transition rules. The fold above is permissive (any
    recorded event moves status, for confluence across merged branches);
    the CLI is strict at intake so nonsense transitions fail loudly."""
    if status == "cancelled":
        return "issue is cancelled -- terminal state (ADR-002/G12)"
    allowed = {"claimed": ("open",), "released": ("claimed",),
               "closed": ("open", "claimed"), "reopened": ("closed",),
               "cancelled": ("open", "claimed", "closed")}
    if status not in allowed.get(event, ()):
        return f"cannot file '{event}' from status '{status}'"
    return None

def issue_event_ts_error(issue_record, now):
    """ADR-028: an issue_event must sort AFTER its issue record in the fold,
    or fold_issues drops it as a forward reference (`ref in issues` is false
    at the event's fold position) while intake -- which validates the
    transition against the FOLDED status -- reports success. A future-dated
    issue record (ts beyond skew of now) cannot be pushed past by
    append_record's bounded clock-push, so any event filed now sorts before
    it and is silently voided (`done`/`cancel` print '-> closed' yet the
    issue stays open). Refuse at intake so the transition is never a lie;
    order_check enforces the same coherence at the commit gate for records
    that bypass intake. Clock-based, so it lives at intake, not in the
    clock-free fold/validate path."""
    ts = parse_ts(issue_record.get("ts") or "")
    if ts is None or ts.tzinfo is None or now.tzinfo is None:
        return None  # unparseable/naive ts is the ADR-015 profile's concern
    if (ts - now).total_seconds() > SKEW_TOLERANCE_SECONDS:
        return (f"issue {issue_record.get('id')} is dated in the future "
                f"({issue_record.get('ts')}) -- an event filed now would sort "
                "before it in the fold and be silently dropped (ADR-028); the "
                "issue record's timestamp is invalid. Nothing was filed.")
    return None

def issue_premises(issues):
    """Premise links declared at creation (ADR-002 premise-at-birth)."""
    out = {}
    for wid, e in issues.items():
        for c in e["issue"]["payload"].get("premises", []):
            out.setdefault(wid, [])
            if c not in out[wid]:
                out[wid].append(c)
    return out

def merge_premises(a, b):
    out = {k: list(v) for k, v in a.items()}
    for k, links in b.items():
        for c in links:
            out.setdefault(k, [])
            if c not in out[k]:
                out[k].append(c)
    return out

def fold_supersedes(events):
    """ADR-013: premise redirects, (issue, old_claim) -> new_claim,
    last-wins in the same confluent (ts, id) total order every other
    fold uses. A redirect is scoped to ONE issue: superseding a claim
    for wk-A never touches wk-B's link to the same claim."""
    ordered = sorted(events, key=fold_key)  # ADR-016: total, content-derived
    out = {}
    for _, ev in ordered:
        p = ev.get("payload", {})
        if ev.get("kind") == "premise" and p.get("supersedes"):
            out[(p.get("issue"), p["supersedes"])] = p.get("claim")
    return out

def apply_supersedes(premises, supersedes):
    """ADR-013: rewrite each issue's premise list through its redirect
    chain (applied AFTER merge_premises, so premise-at-birth links in
    the issue payload redirect too). Chains follow to a fixed point; a
    cycle stops at the first repeat rather than looping. The result
    still goes through join_ready's ADR-001 matrix -- a redirect
    re-targets premise validity, it never bypasses it."""
    if not supersedes:
        return premises
    out = {}
    for iid, cs in premises.items():
        kept = []
        for c in cs:
            cur, seen = c, set()
            while (iid, cur) in supersedes and cur not in seen:
                seen.add(cur)
                cur = supersedes[(iid, cur)]
            if cur not in kept:
                kept.append(cur)
        out[iid] = kept
    return out

def native_ready_issues(issues):
    """Tracker-side readiness only: open AND every dep closed. Premise
    validity is deliberately NOT applied here -- it is applied by
    join_ready, identically for every tracker source, which is what makes
    the kernel and the E1 seam incapable of disagreeing (ADR-002). A dep
    on a cancelled or unknown issue never satisfies, so such work stays
    blocked and visible in `issues` rather than silently ready."""
    out = []
    for wid, e in sorted(issues.items()):
        if e["status"] != "open":
            continue
        deps = e["issue"]["payload"].get("deps", [])
        if all(issues.get(d, {}).get("status") == "closed" for d in deps):
            out.append({"id": wid,
                        "title": e["issue"]["payload"].get("title", wid)})
    return out

# --- ADR-039: blast forecast (pure half) ----------------------------------
def parse_name_log(out):
    """Pure: `git log --format=%x01%H --name-only` output -> a list of
    (commit, frozenset(files)). Chunks are split on the \\x01 marker;
    quotepath=off at the shell edge keeps names raw (SI-2). A newline
    inside a filename breaks the line parse -- accepted residual,
    disclosed in ADR-039."""
    hist = []
    for chunk in out.split("\x01"):
        lines = [ln for ln in chunk.splitlines() if ln.strip()]
        if not lines:
            continue
        hist.append((lines[0], frozenset(lines[1:])))
    return hist

def blast_forecast(paths, history):
    """Pure (ADR-039): distinct commits in the window touching any
    watched path -- an UPPER BOUND on stalings, not an expectation (a
    claim stales only from live, so N commits between re-verifications
    produce ONE staling; the pilot's hottest claim showed 15
    invalidations against 14 re-agrees). Matches the deduplicated
    distinct-file set once, then counts commits by set intersection."""
    if not paths or not history:
        return 0
    all_files = set().union(*(files for _, files in history))
    watched = {f for f in all_files if match_paths(f, paths)}
    if not watched:
        return 0
    return sum(1 for _, files in history if files & watched)

def order_check(events):
    """ADR-031 (unifying ADR-008/ADR-016's detection halves): within one
    repository's history, file order is append order (INV-A prefix
    gate), so every duplicate id is *visible* -- both lines are in the
    file. Returns (errors, warnings). Error: ANY duplicate id whose
    canonical content differs from the first-seen record, regardless of
    ts relation. Corrections file under fresh ids by design, so a
    content-distinct duplicate id has no legitimate use: backdated
    (ADR-008) and equal-ts (ADR-016) duplicates were substitution
    forgeries, and the later-ts duplicate formerly accepted -- harmless
    to the first-wins fold -- was pure confusion attack surface serving
    nothing. Only the byte-identical line duplicated by git union merge
    legitimately shares an id and passes. The fold's (ts, id, canon)
    total order and the ADR-015 clock-push are UNTOUCHED by this gate.
    Warnings only for clock regression beyond tolerance -- a branch
    ledger union-merged into main legitimately places older records
    after newer ones, and failing there would punish the exact merge
    path the confluent fold was built for. NOTE: unlike the fold, this
    check is deliberately order-SENSITIVE -- validating a re-sorted
    stream is not equivalent to validating the file."""
    errors, warnings = [], []
    first_seen = {}
    max_ts, max_line = None, None
    # ADR-028: an issue_event must sort AFTER the issue record it references,
    # or fold_issues drops it as a forward reference (its referent has not
    # folded yet). Collect each issue's fold-winning key (first-wins = the
    # smallest fold_key) so an honest-clock event on a future-dated issue
    # record -- which sorts before it -- is refused here, not silently voided.
    issue_keys = {}
    for ne in events:
        e = ne[1]
        if e.get("kind") == "issue" and e.get("id"):
            k = fold_key(ne)
            if e["id"] not in issue_keys or k < issue_keys[e["id"]]:
                issue_keys[e["id"]] = k
    def cmp_ok(a, b):
        return (a.tzinfo is None) == (b.tzinfo is None)
    for n, ev in events:
        eid = ev.get("id")
        ts_raw = ev.get("ts") or ""
        ts = parse_ts(ts_raw)
        if eid in first_seen:
            f_ts_raw, f_line, f_canon = first_seen[eid]
            # ADR-031: content-distinct duplicate ids are refused
            # WHATEVER the ts relation. canon() equality is the
            # byte-identity test the union-merge shape passes; the
            # comparison never parses a ts, so no forged-ts shape
            # (tz-naive, junk, copied, future) can route around it (the
            # F2 lesson, kept). Subsumes ADR-008 (backdated: ts_raw <
            # f_ts_raw) and ADR-016/C1 (equal-ts: ts_raw == f_ts_raw);
            # newly refuses the later-ts distinct duplicate that
            # first-wins folding rendered harmless but nothing
            # legitimate ever produces.
            if canon(ev) != f_canon:
                errors.append(
                    f"line {n}: duplicate id {eid} with content differing "
                    f"from line {f_line}'s -- duplicate-id substitution "
                    "(ADR-031): corrections file under fresh ids, so only "
                    "a byte-identical union-merge duplicate may share an "
                    "id")
        elif eid:
            first_seen[eid] = (ts_raw, n, canon(ev))
        if ev.get("kind") == "issue_event":
            ref = (ev.get("payload") or {}).get("issue")
            if ref in issue_keys and fold_key((n, ev)) < issue_keys[ref]:
                errors.append(
                    f"line {n}: issue_event references {ref} but sorts before "
                    "its issue record in fold order -- a forward reference the "
                    "fold silently drops (ADR-028), so the transition would be "
                    "inert. The issue record is dated after this event; fix "
                    "its timestamp.")
        if ts and max_ts and cmp_ok(ts, max_ts) \
                and (max_ts - ts).total_seconds() > SKEW_TOLERANCE_SECONDS:
            warnings.append(
                f"line {n}: ts precedes line {max_line}'s by more than "
                f"{SKEW_TOLERANCE_SECONDS}s (ADR-008) -- legitimate after "
                "a union merge, a clock regression otherwise")
        if ts and (max_ts is None or (cmp_ok(ts, max_ts) and ts > max_ts)):
            max_ts, max_line = ts, n
    return errors, warnings

# --------------------------------------------------------- validation

def validate_events(events):
    """Stdlib mirror of .truth/schema/claims.schema.json. Kept in
    conformance by scripts/test-truth-core.py's shared fixture corpus."""
    errors = []
    for n, ev in events:
        for field in ("id", "kind", "actor", "session", "ts", "payload"):
            if field not in ev:
                errors.append(f"line {n}: missing envelope field '{field}'")
        for field in ("actor", "session"):
            if field in ev and not ev[field]:
                errors.append(f"line {n}: empty envelope field '{field}' "
                              "(schema requires minLength 1)")
        if "ts" in ev and not TS_RE.match(str(ev.get("ts") or "")):
            errors.append(f"line {n}: ts not in the canonical profile "
                          "YYYY-MM-DDTHH:MM:SS.ssssss+00:00 (ADR-015: the "
                          "fold sorts the raw string, so any other offset, "
                          "Z-suffix, or precision breaks order coherence)")
        kind, p = ev.get("kind"), ev.get("payload", {})
        # issue records carry wk- envelope ids (ADR-002); everything else tr-
        id_re, id_name = ((WK_ID_RE, "wk-hex8") if kind == "issue"
                          else (ID_RE, "tr-hex8"))
        if "id" in ev and not id_re.match(str(ev["id"])):
            errors.append(f"line {n}: envelope id does not match {id_name}")
        if kind not in KINDS:
            errors.append(f"line {n}: unknown kind '{kind}'")
        elif kind == "claim":
            if not p.get("text"):
                errors.append(f"line {n}: claim missing text (schema requires "
                              "minLength 1)")
            if p.get("evidence_class") not in EVIDENCE_CLASSES:
                errors.append(f"line {n}: bad evidence_class")
            if p.get("cost_tier") not in TIERS:
                errors.append(f"line {n}: bad cost_tier")
            ttl = p.get("ttl_days")
            if ttl is not None and "ttl_days" in p and \
                    (isinstance(ttl, bool) or not isinstance(ttl, int)
                     or ttl < 1):
                errors.append(f"line {n}: ttl_days must be a positive "
                              "integer or null")
            if "scope_basis" in p and not p["scope_basis"]:
                errors.append(f"line {n}: empty scope_basis (ADR-007: the "
                              "override carries a sentence, not a boolean)")
            # ADR-039/ADR-046: blast_forecast -- LEGACY, admitted
            # pre-ADR-046 (intake stamped it v0.9.25-v0.9.29; since
            # ADR-046 the forecast is computed on read and never
            # stored). Append-only history is never rewritten, so
            # validate KEEPS shape-checking stored values; new records
            # never carry the field.
            if "blast_forecast" in p:
                bf = p["blast_forecast"]
                if isinstance(bf, bool) or not isinstance(bf, int) or bf < 0:
                    errors.append(f"line {n}: blast_forecast must be a "
                                  "non-negative integer (ADR-039)")
            # ADR-037: generated_ok_basis is a sentence and only path
            # claims can carry it. Present-but-EMPTY paths beside a basis
            # is refused; an absent key is tolerated (the FS-2 mutant
            # generator dels fields, and the two contract surfaces must
            # agree on every derived mutant -- the ADR-035 returncode
            # tolerance pattern).
            if "generated_ok_basis" in p:
                if not p["generated_ok_basis"]:
                    errors.append(f"line {n}: empty generated_ok_basis "
                                  "(ADR-037)")
                elif "evidence_paths" in p and not p["evidence_paths"]:
                    errors.append(f"line {n}: generated_ok_basis beside "
                                  "empty evidence_paths -- nothing was "
                                  "watched, nothing to excuse (ADR-037)")
            # ADR-035: only a failing command has anything to excuse. A
            # basis beside a recorded exit of 0 is schema noise (X5); a
            # legacy capsule lacking returncode is tolerated (recheck
            # already tolerates it via .get).
            if "evidence_exit_basis" in p:
                if not p["evidence_exit_basis"]:
                    errors.append(f"line {n}: empty evidence_exit_basis "
                                  "(ADR-035: the override carries a "
                                  "sentence, not a boolean)")
                elif p.get("evidence", {}).get("returncode") == 0:
                    errors.append(f"line {n}: evidence_exit_basis beside a "
                                  "recorded exit of 0 -- a basis with "
                                  "nothing to excuse (ADR-035, X5)")
            # ADR-032: ttl_default marks a --scope-ok override that took the
            # default 30-day expiry. Optional; a boolean when present. Two
            # INDEPENDENT contract surfaces (this mirror + the schema), held
            # in lockstep by the FS-2 corpus.
            if "ttl_default" in p and not isinstance(p["ttl_default"], bool):
                errors.append(f"line {n}: ttl_default must be a boolean "
                              "(ADR-032: it flags a defaulted override TTL)")
            if "overridden_duplicates" in p:
                od = p["overridden_duplicates"]
                if (not isinstance(od, list) or not od
                        or any(not ID_RE.match(str(c)) for c in od)):
                    errors.append(f"line {n}: overridden_duplicates must be a "
                                  "non-empty list of tr-hex8 ids (MEDIUM-1: "
                                  "the --duplicate-ok trace records which "
                                  "active claims it declared distinct from)")
            # 42010 concerns -- LEGACY, admitted pre-ADR-046 (the filing
            # surface is gone and the field is closed to new records;
            # this repo's ledger holds records that carry it, and
            # append-only history is never rewritten). When present, a
            # non-empty duplicate-free list of slug strings. Two
            # INDEPENDENT contract surfaces (this mirror + the schema's
            # uniqueItems/pattern), held in lockstep by the FS-2 corpus.
            # Shape hygiene only -- no tag value gates anything. The dup
            # check runs only after every item proved a hashable string
            # (`or` short-circuit): set() on a junk item must not raise.
            if "concerns" in p:
                cs = p["concerns"]
                if (not isinstance(cs, list) or not cs
                        or any(not isinstance(t, str)
                               or not CONCERN_RE.match(t) for t in cs)
                        or len(set(cs)) != len(cs)):
                    errors.append(f"line {n}: concerns must be a non-empty "
                                  "duplicate-free list of slug strings "
                                  "([a-z0-9-]{1,32}) -- 42010 triage "
                                  "metadata, shape-checked only (never a "
                                  "concern-gate; a duplicate would double-"
                                  "count in stats)")
            if "screened" in p.get("evidence", {}) \
                    and not isinstance(p["evidence"]["screened"], bool):
                errors.append(f"line {n}: evidence.screened must be a "
                              "boolean (ADR-009)")
            if p.get("evidence_class") == "VERIFIED":
                ev_ = p.get("evidence", {})
                if not (ev_.get("command") and ev_.get("output_hash")
                        and p.get("anchor_commit")
                        and (p.get("evidence_paths") or p.get("ttl_days"))):
                    errors.append(f"line {n}: VERIFIED claim missing evidence "
                                  "provenance (INV-B)")
            if p.get("evidence_class") == "INFERRED" and not p.get("basis"):
                errors.append(f"line {n}: INFERRED claim missing basis")
            # ADR-027: a git SHA prefix is >=7 everywhere the system emits
            # one. The schema floors anchor_commit's string branch at 7
            # (null still allowed for non-VERIFIED); mirror the floor for
            # ANY claim, not just the VERIFIED branch -- the FS-2 mutant
            # generator cannot reach this (it emits no null and its junk
            # literal is 7 chars), so an explicit check and corpus fixture
            # carry it. VERIFIED-null is already an INV-B error above.
            anc = p.get("anchor_commit")
            if isinstance(anc, str) and len(anc) < 7:
                errors.append(f"line {n}: claim anchor_commit must be a git "
                              "SHA prefix of at least 7 chars when present "
                              "(ADR-027, schema minLength 7)")
        elif kind == "verdict":
            # ADR-036: orphan_basis is a sentence, and only the terminal
            # verb creates orphans -- a basis on any other verdict is
            # schema noise (mirror-only cross-field rule; the schema
            # stays necessary-not-sufficient, ADR-027).
            if "orphan_basis" in p:
                if not p["orphan_basis"]:
                    errors.append(f"line {n}: empty orphan_basis (ADR-036: "
                                  "the override carries a sentence)")
                elif p.get("verdict") != "retracted":
                    errors.append(f"line {n}: orphan_basis on a "
                                  f"{p.get('verdict')!r} verdict -- only a "
                                  "retraction orphans citations (ADR-036)")
            if p.get("verdict") not in VERDICTS or not p.get("claim") \
                    or not p.get("basis"):
                errors.append(f"line {n}: malformed verdict")
            elif not ID_RE.match(str(p.get("claim"))):
                errors.append(f"line {n}: verdict claim ref not tr-hex8")
            if "subtype" in p and p["subtype"] != "mechanical":
                errors.append(f"line {n}: verdict subtype must be "
                              "'mechanical' when present (ADR-012)")
            # ADR-049: the retraction cause. ABSENT IS TOLERATED, FOREVER
            # -- pre-ADR-049 retractions carry no cause, the ledger is
            # append-only, and `validate` runs INSIDE the commit gate, so
            # a mirror that refused history would brick every consumer
            # repo that already holds one. Required at INTAKE, optional
            # here: intake stricter than validate is the SAFE direction
            # (v0.9.32 fixed the unsafe one -- validate stricter than
            # intake let a normal verb wedge the gate). The enum and the
            # successor shape are shared with the schema and ride the
            # FS-2 corpus; the cross-field rules below are mirror-only
            # (ADR-027, the orphan_basis precedent) and are canary-held.
            if "cause" in p:
                if p["cause"] not in RETRACTION_CAUSES:
                    errors.append(
                        f"line {n}: verdict cause must be one of "
                        f"{'/'.join(RETRACTION_CAUSES)} when present "
                        "(ADR-049)")
                elif p.get("verdict") != "retracted":
                    errors.append(f"line {n}: cause on a "
                                  f"{p.get('verdict')!r} verdict -- only a "
                                  "retraction kills a belief (ADR-049)")
                elif p["cause"] == "restated" and not p.get("successor"):
                    errors.append(f"line {n}: cause 'restated' without a "
                                  "successor -- the fact is said to still "
                                  "hold, so a claim must carry it forward "
                                  "(ADR-049)")
            if "successor" in p:
                if not ID_RE.match(str(p["successor"])):
                    errors.append(f"line {n}: verdict successor ref not "
                                  "tr-hex8 (ADR-049)")
                elif p.get("verdict") != "retracted":
                    errors.append(f"line {n}: successor on a "
                                  f"{p.get('verdict')!r} verdict -- only a "
                                  "retraction hands a fact on (ADR-049)")
            # ADR-027: schema requires verdict.anchor_commit be a string
            # >=7; the mirror had no length check (was weaker than schema).
            if "anchor_commit" in p and (not isinstance(p["anchor_commit"], str)
                                         or len(p["anchor_commit"]) < 7):
                errors.append(f"line {n}: verdict anchor_commit must be a "
                              "string of at least 7 chars (ADR-027, schema "
                              "minLength 7)")
        elif kind == "invalidation":
            if not p.get("claim") or not p.get("commit"):
                errors.append(f"line {n}: malformed invalidation")
            elif not ID_RE.match(str(p.get("claim"))):
                errors.append(f"line {n}: invalidation claim ref not tr-hex8")
            # ADR-027: schema floors invalidation.commit at 7; mirror had
            # only the truthiness check above (was weaker than schema).
            elif isinstance(p.get("commit"), str) and len(p["commit"]) < 7:
                errors.append(f"line {n}: invalidation commit must be a git "
                              "SHA of at least 7 chars (ADR-027, schema "
                              "minLength 7)")
        elif kind == "contradicts":
            if not p.get("a") or not p.get("b") \
                    or not (p.get("basis") or "").strip():
                errors.append(f"line {n}: malformed contradicts (needs "
                              "a, b, basis) (issue #4)")
            elif not ID_RE.match(str(p["a"])) or not ID_RE.match(str(p["b"])):
                errors.append(f"line {n}: contradicts refs not tr-hex8")
            # a==b is refused at INTAKE and inert in the fold, but not a
            # validate error: draft-07 cannot express property inequality,
            # and the mirror may not be stricter than the schema (FS-2)
        elif kind == "premise":
            if not p.get("issue") or not p.get("claim"):
                errors.append(f"line {n}: malformed premise")
            elif not ID_RE.match(str(p.get("claim"))):
                errors.append(f"line {n}: premise claim ref not tr-hex8")
            if "supersedes" in p and not ID_RE.match(str(p["supersedes"])):
                errors.append(f"line {n}: premise supersedes ref not tr-hex8 "
                              "(ADR-013)")
        elif kind == "issue":
            if not p.get("title"):
                errors.append(f"line {n}: issue missing title")
            if any(not WK_ID_RE.match(str(d)) for d in p.get("deps", [])):
                errors.append(f"line {n}: issue dep ref not wk-hex8")
            if any(not ID_RE.match(str(c)) for c in p.get("premises", [])):
                errors.append(f"line {n}: issue premise ref not tr-hex8")
            if "accept" in p:
                acc = p["accept"]
                if not isinstance(acc, dict) or not acc.get("command"):
                    errors.append(f"line {n}: issue accept missing command "
                                  "(ADR-014)")
                elif acc.get("kind") not in ACCEPT_KINDS:
                    errors.append(f"line {n}: issue accept kind must be one "
                                  f"of {'/'.join(ACCEPT_KINDS)} (ADR-014)")
                elif not isinstance(acc.get("screened"), bool):
                    errors.append(f"line {n}: issue accept.screened must be "
                                  "a boolean (ADR-014)")
        elif kind == "issue_event":
            if p.get("event") not in ISSUE_EVENTS or not p.get("issue"):
                errors.append(f"line {n}: malformed issue_event")
            elif not WK_ID_RE.match(str(p.get("issue"))):
                errors.append(f"line {n}: issue_event ref not wk-hex8")
            elif p.get("event") in ("closed", "cancelled") and not p.get("basis"):
                errors.append(f"line {n}: {p['event']} issue_event missing basis")
            # ADR-036: orphan_basis only on the issue tombstone
            # (mirror-only cross-field rule, like the verdict side).
            if "orphan_basis" in p:
                if not p["orphan_basis"]:
                    errors.append(f"line {n}: empty orphan_basis (ADR-036)")
                elif p.get("event") != "cancelled":
                    errors.append(f"line {n}: orphan_basis on a "
                                  f"{p.get('event')!r} issue_event -- only "
                                  "a cancellation orphans citations "
                                  "(ADR-036)")
            # ADR-049 is scoped to CLAIM retraction: a cancelled issue is
            # work abandoned, not a belief killed, and "was the sentence
            # ever true" has no referent there. Refused in the mirror so
            # the field cannot creep onto the other tombstone verb
            # without an ADR (mirror-only, ADR-027).
            for k in ("cause", "successor"):
                if k in p:
                    errors.append(f"line {n}: {k} on an issue_event -- "
                                  "ADR-049 records why a CLAIM died; a "
                                  "cancelled issue says why in its basis")
            if "accept" in p:
                acc = p["accept"]
                if not isinstance(acc, dict) \
                        or not isinstance(acc.get("executed"), bool):
                    errors.append(f"line {n}: issue_event accept.executed "
                                  "must be a boolean (ADR-014)")
                elif acc["executed"] and acc.get("returncode") != 0:
                    errors.append(f"line {n}: an executed acceptance on a "
                                  "close must record returncode 0 -- a "
                                  "failing oracle never closes (ADR-014)")
                elif not acc["executed"] and "returncode" in acc:
                    errors.append(f"line {n}: an unexecuted acceptance "
                                  "(executed=false) must not carry a "
                                  "returncode -- there was no run to have an "
                                  "exit code (ADR-014, MEDIUM-3)")
                elif "kind" in acc and acc["kind"] not in ACCEPT_KINDS:
                    errors.append(f"line {n}: issue_event accept kind must "
                                  f"be one of {'/'.join(ACCEPT_KINDS)} "
                                  "(ADR-014)")
    return errors
