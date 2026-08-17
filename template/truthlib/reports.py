"""truthlib.reports -- a pure derivation of ledger records into counts,
ranks and deltas: no refusal, no advice, no I/O.

That sentence is the criterion, and A2's falsifier is a function this
sentence does not admit. Every member turns records into a
machine-readable object and stops; nothing here decides whether a filing
is allowed, tells a user what to do about it, or reaches the world.

Split out of truthlib.advisory (A2), whose docstring said "advisory
assembly and the pure report FAMILY" -- and the word family was the
tell: a collection, not a criterion. Pure file moves, no logic edits.
"""
import statistics

from truthlib.registry import *
from truthlib.kernel import *
from truthlib.evidence import *

def effective_blast_floor(claims, history):
    """Pure (ADR-039, recast by ADR-046): the advisory floor,
    self-calibrated -- P90 of forecasts COMPUTED LIVE over live
    path-claims once >= BLAST_MIN_OBSERVATIONS exist; the constant is
    the cold-start fallback only. `history` is blast_history()'s parsed
    log passed as data (the shell gathers it ONCE -- same git cost as
    the retired stored-int read, one log, plus N pure matches); None
    (shallow/unavailable history) reads as fallback -- a floor computed
    from a truncated log would be the quietly-cold number ADR-039
    forbids. Returns (floor, source)."""
    if history is None:
        return BLAST_ADVISORY_FLOOR, "fallback"
    vals = sorted(
        blast_forecast(e["claim"]["payload"]["evidence_paths"], history)
        for e in claims.values()
        if e["status"] == "live"
        and e["claim"]["payload"].get("evidence_paths"))
    if len(vals) >= BLAST_MIN_OBSERVATIONS:
        # clamped to >= 1: an all-cold corpus must not calibrate the
        # floor to 0 and flag stone-cold watches as hot (R5 review, F2)
        return max(1, vals[max(0, int(len(vals) * 0.9) - 1)]), "calibrated"
    return BLAST_ADVISORY_FLOOR, "fallback"

def blast_report(events, folded=None, history=None):
    """ADR-039 (Tier C since ADR-046): the churn instrument -- observed
    invalidations vs forecast per path-claim (top 5 by observed), the
    per-path staler ranking read from invalidation `touched` lists (no
    git work), and the effective floor. Pure fold consumer; shares the
    fold. `history` is blast_history()'s parsed log as data: when
    present, forecasts are computed LIVE over the current window
    (ADR-046 -- intake no longer stamps them); when None, a stored
    legacy blast_forecast int is reported as-is (records admitted
    pre-ADR-046) and claims without one show forecast null. Driven by
    the meta-repo's instruments/blast-report.py, not by stats."""
    claims, _ = folded if folded is not None else fold(events)
    inval_counts, staler = {}, {}
    for _, ev in events:
        if ev.get("kind") != "invalidation":
            continue
        p = ev.get("payload") or {}
        cid = p.get("claim")
        inval_counts[cid] = inval_counts.get(cid, 0) + 1
        for t in p.get("touched") or []:
            staler[t] = staler.get(t, 0) + 1
    rows = []
    for cid, e in claims.items():
        paths = e["claim"]["payload"].get("evidence_paths")
        if not paths:
            continue
        pf = (blast_forecast(paths, history) if history is not None
              else e["claim"]["payload"].get("blast_forecast"))
        obs = inval_counts.get(cid, 0)
        if pf is not None or obs:
            rows.append({"claim": cid, "observed": obs, "forecast": pf})
    rows.sort(key=lambda r: (-r["observed"], r["claim"]))
    floor, src = effective_blast_floor(claims, history)
    return {"rows": rows[:5],
            "staler_ranking": [{"path": p, "invalidations": n} for p, n
                               in sorted(staler.items(),
                                         key=lambda kv: (-kv[1], kv[0]))[:5]],
            "effective_floor": floor, "floor_source": src}

# ------------------------------------------------------ stats (FS-1)

def half_life_observations(events):
    """FS-1: elapsed live-time for every claim that was live and later
    DIVERGED -- the raw material for tier-calibrated TTL suggestions
    (paper section 6.2, made a number). This replays the same (ts, id)
    order and the same status rules as fold(); fold stays authoritative
    for status, and test-truth-core cross-checks the two never disagree
    on final state. Returns a list of (tier, days_live) tuples.

    THE MEASURED TRANSITION CHANGED IN THE REFACTOR (step 2.5,
    operator decision on J-034 option 2), and the number it publishes
    changed meaning with it. It used to be `live -> stale`: how long a
    claim lasted before a WATCHED PATH WAS TOUCHED. Step 2.5 makes a
    path invalidation inert, so that transition no longer exists -- but
    the honest reason to move is what the old number was:

        half-life P0: median 0.02d (n=77)     <- ~30 minutes
        half-life P1: median 0.04d (n=1441)
        half-life P2: median 0.06d (n=445)

    A TTL calibrated on 1963 observations of "somebody edited a watched
    file within the hour" is calibrated on the proxy's firing rate, not
    on how long a fact stays true. The replacement is `live -> diverged`:
    elapsed live-time until a JUDGE recorded that the evidence actually
    moved. Semantic where the old one was syntactic, and per J-034
    roughly an order of magnitude scarcer (71 diverge verdicts against
    1997 invalidations) -- which is the point: HALF_LIFE_MIN_OBS still
    guards the suggestion, so a tier without enough judged divergence
    now suggests NOTHING rather than suggesting a number built from
    noise.

    A retraction is deliberately NOT an observation. `retracted` says
    the claim should never have been filed; `diverged` says it was true
    and stopped being true, which is the only transition a time-to-live
    can be calibrated on."""
    ordered = sorted(events, key=fold_key)  # ADR-016: total, content-derived
    state = {}   # cid -> {"tier", "status", "since": datetime|None}
    obs = []
    for _, ev in ordered:
        kind, p = ev.get("kind"), ev.get("payload", {})
        if kind == "claim":
            if ev["id"] not in state:
                state[ev["id"]] = {"tier": p.get("cost_tier"),
                                   "status": "unverified", "since": None}
        elif kind in ("verdict", "invalidation"):
            cid = p.get("claim")
            e = state.get(cid)
            if not e or e["status"] == "retracted":
                continue
            if kind == "invalidation":
                # PARITY WITH fold(), through the SAME discriminator it
                # calls (kernel.ttl_invalidation). This replay used to
                # carry its own rule -- `new = "stale" if kind ==
                # "invalidation"` -- and step 2.5 proved why that is the
                # dangerous shape: the moment fold's algebra changed, the
                # replay went on describing a ledger nobody has. It was
                # test_half_life_replay_matches_fold that caught it, which
                # is exactly the arm's job; the fix is to delete the second
                # opinion rather than re-sync it.
                if not ttl_invalidation(p):
                    continue  # path invalidation: inert in fold, inert here
                new = "stale"
            else:
                # R13: registry .get -- an unknown verdict still skips
                # silently here, exactly as the local map did.
                new = VERDICT_STATUS.get(p.get("verdict"))
            if not new:
                continue
            ts = parse_ts(ev.get("ts") or "")
            # THE OBSERVATION: live -> diverged, a judge's finding that the
            # evidence moved. FS-1/ADR-032's exclusion of TTL expiries from
            # the medians is now STRUCTURAL rather than a special case: a
            # TTL expiry produces `stale`, never `diverged`, so it cannot
            # reach this branch at all and the circularity it guarded
            # against (suggesting ~= the ttl_days default that caused the
            # data) cannot re-form. TTL expiries are still counted, in
            # override_report's decay_expiries.
            if e["status"] == "live" and new == "diverged" \
                    and e["since"] and ts \
                    and (ts.tzinfo is None) == (e["since"].tzinfo is None):
                obs.append((e["tier"],
                            (ts - e["since"]).total_seconds() / 86400.0))
            e["status"] = new
            e["since"] = ts if new == "live" else None
    return obs, {cid: e["status"] for cid, e in state.items()}

def claim_concerns(payload):
    """The claim's LEGACY 42010 concern tags as READ-side data: the
    string items of a well-formed list, else []. Kept after ADR-046
    demoted the concerns surface to Tier C because two readers remain:
    validate's legacy branch (records admitted pre-ADR-046) and the
    meta-repo's instruments/concern-tag.py. Readers must degrade to 'no
    tags', never crash on an unhashable item or fall into substring
    matching on a bare string (red-team F2). Pure."""
    cs = payload.get("concerns")
    if not isinstance(cs, list):
        return []
    return [t for t in cs if isinstance(t, str)]

def stats_report(events, now, folded=None):
    """FS-1: everything the monthly hand-audit (paper section 8 item 2)
    needs that a machine can compute. Pure fold consumer; pass `folded`
    (a fold(events) result) to share one fold across the stats
    consumers (ADR-034 -- each consumer used to re-fold and re-sort)."""
    claims, _ = folded if folded is not None else fold(events)
    by_status, by_tier = {}, {}
    for e in claims.values():
        by_status[e["status"]] = by_status.get(e["status"], 0) + 1
        t = e["claim"]["payload"].get("cost_tier")
        by_tier.setdefault(t, {})[e["status"]] = \
            by_tier.setdefault(t, {}).get(e["status"], 0) + 1
    # R13: counter keys derive from VERDICTS (diverge splits by ADR-012
    # subtype), in VERDICTS order -- the rendered key order is unchanged.
    verdicts = {}
    for v in VERDICTS:
        if v == "diverge":
            verdicts["diverge_genuine"] = 0
            verdicts["diverge_mechanical"] = 0
        else:
            verdicts[v] = 0
    for _, ev in events:
        if ev.get("kind") != "verdict":
            continue
        v = ev.get("payload", {}).get("verdict")
        if v == "diverge":
            key = ("diverge_mechanical"
                   if ev["payload"].get("subtype") == "mechanical"
                   else "diverge_genuine")
            verdicts[key] += 1
        elif v in verdicts:
            verdicts[v] += 1
    obs, _ = half_life_observations(events)
    half_life = {}
    for tier in TIERS:
        days = sorted(d for t, d in obs if t == tier)
        if days:
            half_life[tier] = {"n": len(days),
                               "median_days": round(statistics.median(days), 2)}
    # FAZA 3 note, recorded rather than acted on: watch-policy ADOPTION is
    # the number that phase exists to move, and it is NOT added here. The
    # ADR-046 tiering ruling says `truth stats` carries the Tier B core --
    # counts, verdicts, half-life (which feeds the FS-1 intake advisory),
    # queue aging -- and TestStatsCLIShape pins that key set precisely so a
    # new section cannot regrow it by habit. An adoption ratio is an
    # analysis metric of the override-velocity family, which ADR-046 moved
    # OUT to instruments/. Amending that ruling is an operator decision,
    # not a side effect of shipping the feature; `truth list
    # --watch-policy <name>` answers the operational question meanwhile.
    queue = queue_rows(claims, now)
    ages = sorted(r["age_days"] for r in queue if r["age_days"] is not None)
    # ADR-046: the 42010 concern tally moved OUT (Tier C -- the meta-repo's
    # instruments/concern-tag.py reads legacy tags over the raw ledger).
    return {"claims_by_status": by_status, "claims_by_tier": by_tier,
            "verdicts": verdicts, "half_life": half_life,
            "queue_size": len(queue),
            "queue_max_age_days": ages[-1] if ages else None}

def separation_report(events, now, folded=None):
    """The evidence-of-separation instrument for ADR-010. Pure consumer of
    the fold, beside override_report/blast_report; NO schema change -- every
    figure below is derivable from records already written.

    ADR-010 refuses a SAME-SESSION agree, so the gate compares two session
    strings. `session()` returns whatever TRUTH_SESSION says, which means
    the gate can only ever see the name, never the separation. This report
    is what the records CAN prove: how long a claim existed before its
    first agree. Returns a dict:
      * pairs -- claims whose first agree exists;
      * same_session -- agrees whose session equals the author's (the gate
        should keep this at 0; a non-zero value is a gate regression);
      * unevidenced -- first agrees inside SEPARATION_FLOOR_SECONDS;
      * live_unevidenced -- ids of those whose claim is LIVE today, i.e.
        currently-trusted state resting on a verdict that cannot have
        involved reading;
      * fastest -- (seconds, claim id) or None;
      * median_seconds -- the corpus middle, for context.
    Pure: no clock read (`now` unused -- every timestamp is read from the
    records, never recomputed; kept for signature parity)."""
    del now  # signature parity; the report reads records, not the clock
    claims, _ = folded if folded is not None else fold(events)
    authored = {}
    for cid, e in claims.items():
        c = e["claim"]
        authored[cid] = (c.get("ts"), c.get("session"))
    firsts, same = {}, 0
    for _n, ev in sorted(events, key=fold_key):
        if ev.get("kind") != "verdict":
            continue
        p = ev.get("payload") or {}
        cid = p.get("claim")
        if p.get("verdict") != "agree" or cid not in authored:
            continue
        # ADR-010 governs EVERY agree, not just the first: a regressed gate
        # letting an author self-agree a claim that already carries an
        # independent first agree would be invisible to a firsts-only scan.
        if ev.get("session") and ev.get("session") == authored[cid][1]:
            same += 1
        if cid not in firsts:
            firsts[cid] = ev
    # Latency is measured on FIRST agrees only, deliberately: later agrees
    # are dominated by hash-match reaffirms answering an invalidation, which
    # are legitimately fast and would swamp the signal.
    lat, unevidenced, live_un = [], [], []
    for cid, v in firsts.items():
        cts, _csess = authored[cid]
        try:
            d = (parse_ts(v.get("ts")) - parse_ts(cts)).total_seconds()
        except Exception:
            continue
        lat.append((d, cid))
        if d < SEPARATION_FLOOR_SECONDS:
            unevidenced.append(cid)
            if claims[cid]["status"] == "live":
                live_un.append(cid)
    lat.sort()
    return {
        "pairs": len(lat),
        "same_session": same,
        "floor_seconds": SEPARATION_FLOOR_SECONDS,
        "unevidenced": len(unevidenced),
        "live_unevidenced": sorted(live_un),
        "fastest": ([round(lat[0][0], 3), lat[0][1]] if lat else None),
        "median_seconds": (round(lat[len(lat) // 2][0], 1) if lat else None),
    }

def override_report(events, now, folded=None):
    """ADR-033: the override-velocity instrument that supplies ADR-007's
    adoption gate its data. A pure fold consumer beside stats_report,
    counting over the given events (the shell applies any --since window
    before calling -- stats_report's overall-count convention, no
    per-window split of its own). Returns a dict:
      * scope_basis_filings -- ADR-007 --scope-ok overrides;
      * decay_expiries -- ADR-032 override-decay invalidations
        (reason_code=='ttl' on a ttl_default claim);
      * overridden_duplicates -- G8/--duplicate-ok filings;
      * screened_false_filings -- --evidence-unsafe-ok filings;
      * max_scope_ttl_days -- the largest ttl among scope_basis claims
        (None if none), so an operator can see the visible opt-out in use;
      * repeats -- verbatim re-justification after expiry: a scope_basis
        claim whose tokens() token set EQUALS that of an EARLIER claim now
        DEAD (stale/diverged/retracted). A prior claim still live/unverified
        is NOT flagged (that is ADR-018 near-duplicate territory). tokens()
        is REUSED, never re-implemented -- the ADR-018/021 parity lesson.
    Pure: no clock read (now is unused -- expiries are read from records,
    not recomputed; kept for signature parity with stats_report)."""
    del now  # signature parity; the report reads records, not the clock
    claims, _ = folded if folded is not None else fold(events)
    scope_filings = overridden_dupes = screened_false = 0
    exit_overrides = hollow_warned = generated_overrides = 0
    max_scope_ttl = None
    for e in claims.values():
        p = e["claim"]["payload"]
        # ADR-035: exit-override count (CC-2 single home) plus the
        # warned-population denominator -- a recorded non-zero exit with
        # no stated basis is the negation-path/pre-R1 warned class.
        if p.get("generated_ok_basis"):
            generated_overrides += 1
        if p.get("evidence_exit_basis"):
            exit_overrides += 1
        elif (p.get("evidence") or {}).get("returncode"):
            hollow_warned += 1
        if p.get("scope_basis"):
            scope_filings += 1
            t = p.get("ttl_days")
            if isinstance(t, int) and not isinstance(t, bool):
                max_scope_ttl = t if max_scope_ttl is None \
                    else max(max_scope_ttl, t)
        if p.get("overridden_duplicates"):
            overridden_dupes += 1
        if (p.get("evidence") or {}).get("screened") is False:
            screened_false += 1
    # ADR-036: deliberate-orphaning count (CC-2 single home) -- verdict
    # and issue-tombstone sides together; read from raw events (a
    # retracted claim's verdict is what carries it).
    orphan_filings = sum(
        1 for _, ev in events
        if ev.get("kind") in ("verdict", "issue_event")
        and (ev.get("payload") or {}).get("orphan_basis"))
    # ADR-051 (CC-2): capsule refreshes -- an agree filed over a changed
    # output. This is the gate's OWN health metric: a rising count means
    # evidence recipes are drifting faster than the facts they measure
    # (the ADR-012 mechanical class, agree side), which is a signal to
    # re-file recipes, not to widen the gate.
    evidence_refresh_filings = sum(
        1 for _, ev in events
        if ev.get("kind") == "verdict"
        and (ev.get("payload") or {}).get("evidence_refresh"))
    decay_expiries = 0
    for _, ev in events:
        if ev.get("kind") != "invalidation":
            continue
        p = ev.get("payload") or {}
        if p.get("reason_code") != "ttl":
            continue
        c = claims.get(p.get("claim"))
        if c and c["claim"]["payload"].get("ttl_default"):
            decay_expiries += 1
    # verbatim-repeat: walk claims in fold (ts, id) order, flagging a
    # scope_basis claim whose token set matches an EARLIER dead one.
    ordered = sorted(claims.values(),
                     key=lambda e: (e["claim"].get("ts") or "",
                                    e["claim"].get("id") or ""))
    repeats, seen = [], []
    for e in ordered:
        sb = e["claim"]["payload"].get("scope_basis")
        if not sb:
            continue
        toks, cid = frozenset(tokens(sb)), e["claim"].get("id")
        for ptoks, pcid, pstatus in seen:
            if ptoks == toks and pstatus in DEAD_CLAIM_STATUSES:
                repeats.append({"claim": cid, "prior": pcid,
                                "prior_status": pstatus})
                break
        seen.append((toks, cid, e["status"]))
    return {"scope_basis_filings": scope_filings,
            "decay_expiries": decay_expiries,
            "overridden_duplicates": overridden_dupes,
            "screened_false_filings": screened_false,
            "evidence_exit_filings": exit_overrides,
            "hollow_warned": hollow_warned,
            "orphan_filings": orphan_filings,
            "evidence_refresh_filings": evidence_refresh_filings,
            "generated_ok_filings": generated_overrides,
            "max_scope_ttl_days": max_scope_ttl,
            "repeats": repeats}

# --------------------------------------------------------- consumers (E5)

def queue_rows(claims, now):
    rows = []
    for cid, e in claims.items():
        tier = e["claim"]["payload"].get("cost_tier")
        status = e["status"]
        reason = None
        if status == "diverged":
            reason = "author/verifier diverged"
            if e.get("subtype") == "mechanical":
                reason += " (mechanical: recipe changed, fact may hold)"
        elif status == "disputed":
            reason = ("declared contradiction with "
                      + ", ".join(e.get("disputed_with", []))
                      + " -- retract, supersede, or re-file one side")
        elif status == "stale" and tier in ("P0", "P1"):
            # Since step 2.5 `stale` has exactly ONE cause -- TTL expiry
            # (ADR-019) -- so the reason can name it instead of the vague
            # "evidence invalidated" it inherited from the path proxy. The
            # exit is a re-file: re-verification never resets a TTL.
            reason = "ttl expired -- re-file required (ADR-019)"
        elif status == "cannot_verify" and tier == "P0":
            reason = "P0 claim unverifiable: fix evidence or retract"
        if reason:
            rows.append({"id": cid, "status": status, "tier": tier,
                         "age_days": age_days(e, now), "reason": reason,
                         "text": e["claim"]["payload"].get("text")})
    return rows

def impact_report(query_paths, claims, issues, premises):
    """ADR-005: the whisper's mechanics. For each queried path, the
    live/unverified claims whose evidence_paths watch it, and the work
    premised on those claims. Files nothing, judges nothing.

    It reports ATTENTION, not consequence, since refactor step 2.5. It
    used to be a prediction -- "invalidate-scan STALES this, ready HOLDs
    that" -- and the first half stopped being true when a path
    invalidation became inert. The rows are unchanged; what they mean is
    narrower and more honest: these claims read the path you are about to
    edit, so if your edit moves the FACT, `truth reproduce` will say so at
    the push boundary and the premised work is what is downstream of it. Reuses match_paths: a second matcher implementation is
    forbidden (two copies of the matching contract will drift, the F1/F5
    lesson). wk- holds are listed only while open/claimed; non-wk ids
    (external tracker premises) are listed unconditionally, since their
    status lives tracker-side where this fold cannot see it."""
    holders = {}
    for wid, cids in premises.items():
        for c in cids:
            holders.setdefault(c, []).append(wid)
    rows = []
    for cid, e in sorted(claims.items()):
        if e["status"] not in ACTIVE_STATUSES:
            continue
        watched = e["claim"]["payload"].get("evidence_paths", [])
        touched = sorted({q for q in query_paths if match_paths(q, watched)})
        if not touched:
            continue
        holds = sorted(w for w in holders.get(cid, [])
                       if not w.startswith("wk-")
                       or issues.get(w, {}).get("status") in ("open", "claimed"))
        rows.append({"claim": cid,
                     "tier": e["claim"]["payload"].get("cost_tier"),
                     "status": e["status"],
                     "text": e["claim"]["payload"].get("text"),
                     "touched": touched, "watched": watched,
                     "holds": holds})
    rows.sort(key=lambda r: (r["tier"] or "P9", r["claim"]))
    return rows

def baseline_snapshot(events):
    """Issue #3 (10007): the frozen status account of one fold. Counts
    AND sorted id lists -- ids make diffs exact and give auditors the
    drill-down; sorting plus sort_keys serialization makes the artifact
    deterministic, so identical ledgers yield byte-identical baselines."""
    claims, _ = fold(events)
    issues = fold_issues(events)
    c_ids, tiers = {}, {}
    for cid, e in sorted(claims.items()):
        c_ids.setdefault(e["status"], []).append(cid)
        if e["status"] != "retracted":
            t = e["claim"]["payload"].get("cost_tier") or "?"
            tiers[t] = tiers.get(t, 0) + 1
    i_ids = {}
    for wid, e in sorted(issues.items()):
        i_ids.setdefault(e["status"], []).append(wid)
    return {"records": len(events),
            "claims": {"by_status": {k: len(v) for k, v in sorted(c_ids.items())},
                       "by_tier": dict(sorted(tiers.items())),
                       "ids": dict(sorted(c_ids.items()))},
            "issues": {"by_status": {k: len(v) for k, v in sorted(i_ids.items())},
                       "ids": dict(sorted(i_ids.items()))}}

def baseline_diff(a, b):
    """Issue #3: the delta between two snapshots, release-notes shape.
    Three classes per kind: born (in b only, with b-status), transitions
    (both, status changed; grouped 'from->to'), and DISAPPEARED (in a
    only) -- impossible between ancestor and descendant of an
    append-only file, so its presence means rewritten or divergent
    history: 10007's omission, caught by exactly the comparison the
    standard prescribes. The caller escalates it (exit 5)."""
    out = {}
    for kind in ("claims", "issues"):
        sa = {i: st for st, ids in a[kind]["ids"].items() for i in ids}
        sb = {i: st for st, ids in b[kind]["ids"].items() for i in ids}
        trans = {}
        for i in sorted(sa.keys() & sb.keys()):
            if sa[i] != sb[i]:
                trans.setdefault(f"{sa[i]}->{sb[i]}", []).append(i)
        out[kind] = {"born": {i: sb[i] for i in sorted(sb.keys() - sa.keys())},
                     "transitions": dict(sorted(trans.items())),
                     "disappeared": {i: sa[i]
                                     for i in sorted(sa.keys() - sb.keys())}}
    out["records_delta"] = b["records"] - a["records"]
    return out

def inverse_report(tracked, claims, under=None, excludes=()):
    """Issue #5: the backward trace (24765). Returns {"dark": [paths],
    "considered": n} -- the tracked files (optionally scoped to --under,
    minus --exclude prefixes) matched by NO evidence_path glob of any
    active claim. Active = every status except retracted: stale and
    diverged claims still name their paths (knowledge needing re-check,
    not absence of knowledge); a retracted claim's watch died with it.
    Reuses match_paths -- the scan, forward impact, and this verb must
    agree on what "watched" means or the three will drift apart
    (ADR-005). Enumeration only: no module awareness, no auto-filing --
    what to DO about a dark file (adopt/attic/delete) is a human verb
    downstream."""
    def scoped(path):
        if under:
            u = under.rstrip("/")
            if path != u and not path.startswith(u + "/"):
                return False
        for ex in excludes:
            e = ex.rstrip("/")
            if path == e or path.startswith(e + "/"):
                return False
        return True
    patterns = sorted({p for e in claims.values()
                       if e["status"] != "retracted"
                       for p in (e["claim"]["payload"].get("evidence_paths")
                                 or [])})
    considered = [p for p in tracked if scoped(p)]
    dark = [p for p in considered if not match_paths(p, patterns)]
    return {"dark": sorted(dark), "considered": len(considered)}

def retraction_cause_report(events):
    """ADR-049's adoption metric (ADR-047: metric or it doesn't ship),
    Tier C -- a pure report, driven by instruments/retraction-causes.py,
    NOT a stats section (ADR-046 sent the instrument family out of the
    template CLI).

    Tallies every retraction verdict by its recorded `cause`, plus:
      * `unrecorded` -- pre-ADR-049 records carrying no cause. NOT a
        stored value and never stamped: the legacy population stays
        VISIBLE in the denominator instead of being silently dropped
        (the F1 fail-loud rule). It is what makes the metric readable
        during the crossover: the number that must stop growing.
      * successors_named / successors_missing -- how often a retraction
        leaves a followable pointer at all. This is the number the
        prose regime could not produce: at adoption 39 of the meta
        ledger's 75 retraction bases claimed a successor in words
        ("successor in verdict trail") and named no id.
    Pure: reads records, no clock, no fold."""
    counts = {c: 0 for c in RETRACTION_CAUSES}
    counts["unrecorded"] = 0
    named = missing = 0
    for _, ev in events:
        if ev.get("kind") != "verdict":
            continue
        p = ev.get("payload") or {}
        if p.get("verdict") != "retracted":
            continue
        cause = p.get("cause")
        counts[cause if cause in counts else "unrecorded"] += 1
        if p.get("successor"):
            named += 1
        else:
            missing += 1
    return {"by_cause": counts,
            "total": named + missing,
            "successors_named": named,
            "successors_missing": missing}

# --- ADR-050: the staling breakdown --------------------------------------
# Derived from the ONE home of the reaffirm basis string (evidence.py), so
# the marker this report keys on cannot drift from the one `reaffirm`
# writes -- the ADR-018/021 hand-copy lesson applied to a literal.
REAFFIRM_BASIS_PREFIX = REAFFIRM_BASIS.split(":", 1)[0] + ":"

def watched_path_kind(path):
    """ADR-050: the structural KIND of a watched path -- its lowercased
    file suffix, or `<none>` for a suffix-less basename (`Makefile`,
    `scripts/truth`, `.gitignore`: a LEADING dot names a dotfile, it is
    not a suffix, hence the `base[1:]` scan). Deliberately structural:
    the template cannot know which directories a consumer calls
    "specification" and which "implementation", and a shipped guess
    would be wrong in most repos. The suffix is the language-agnostic
    proxy the Estler reading needs (prose vs code) and it is derivable
    from the record alone. Pure."""
    base = path.rsplit("/", 1)[-1]
    if "." in base[1:]:
        return "." + base.rsplit(".", 1)[-1].lower()
    return "<none>"

def _staling_bucket(payload):
    """ADR-050: which of the three arms a staling's resolving verdict
    lands in. `agree` says the fact had NOT changed -- the staling was a
    false alarm -- and splits by WHO paid for that answer: a machine
    (the `reaffirm:` basis, or a `reaffirm_cleared` record; ADR-030's
    mechanical half) or a human re-reading the evidence. Every other
    verdict -- diverge, cannot_verify, retracted -- says the fact moved.
    Pure."""
    if payload.get("verdict") != "agree":
        return "true_stale"
    if (payload.get("basis") or "").startswith(REAFFIRM_BASIS_PREFIX) \
            or payload.get("reaffirm_cleared") is not None:
        return "mechanical_agree"
    return "human_agree"

def staling_report(events):
    """ADR-050: what a path-touched-means-stale rule actually cost --
    the false/true split of every resolved staling, and which KIND of
    watched path triggered them. Pure: reads records, no clock, no fold,
    no I/O (retraction_cause_report's shape).

    One staling is one EPISODE, not one invalidation record: a claim
    already stale that is invalidated again did not stale twice, and
    counting the repeat would inflate the denominator with re-scans of
    an unanswered question. Those repeats are reported separately as
    `restaled`. An episode opens at the first invalidation and closes at
    the NEXT verdict on that claim; episodes still open when the stream
    ends are `unresolved` and are counted in NEITHER numerator (their
    answer is not in yet -- assigning them would be inventing it).

    ORDER: the events are read in the ORDER GIVEN and never re-sorted
    here -- the shell owns the order, as it owns every other fact this
    core is handed (ADR-043). The shipped caller (`truth staling`) sorts
    by fold_key first, because a staling IS a status transition and
    ADR-016's (ts, id, canon) order is what DEFINES status; walking the
    raw file instead measures append order, which on a union-merged
    ledger interleaves branch blocks whose wall-clock order differs.
    That is not hypothetical: the pilot's first staling measurement was
    self-diverged for exactly this (kuchnie tr-0e4c30d7, superseding
    tr-13d16cc0 with tr-e1225a78) after the two orders disagreed on
    ~3.5% of its stalings. `truth staling --append-order` keeps the
    file-order walk reachable so those pre-ADR-050 numbers stay
    reproducible; nothing else should use it. fold() remains the sole
    authority on status.

    Returns a dict:
      * invalidations / restaled / stalings -- raw records, repeats
        inside an open episode, and episodes (resolved + unresolved);
      * mechanical_agree / human_agree / true_stale -- the three arms;
      * false_stale -- mechanical + human, the alarm that cost work and
        found nothing;
      * resolved / unresolved -- the denominator and the remainder;
      * by_path_kind -- stalings per watched_path_kind of the OPENING
        invalidation's `touched` list, descending. An episode touching
        two kinds counts under both, so the column sums to >= stalings;
      * pathless -- episodes whose opening invalidation named no touched
        path at all (TTL expiry, unreachable anchor), which is why the
        by_path_kind column can also sum to LESS than stalings.
    """
    pending, kinds = {}, {}
    counts = {"mechanical_agree": 0, "human_agree": 0, "true_stale": 0}
    invalidations = restaled = pathless = 0
    for _, ev in events:
        kind = ev.get("kind")
        if kind not in ("invalidation", "verdict"):
            continue
        p = ev.get("payload") or {}
        cid = p.get("claim")
        if not isinstance(cid, str):
            continue  # a malformed record is not a staling either way
        if kind == "invalidation":
            invalidations += 1
            if cid in pending:
                restaled += 1
                continue
            pending[cid] = True
            ks = {watched_path_kind(t) for t in (p.get("touched") or [])
                  if isinstance(t, str)}
            if not ks:
                pathless += 1
            for k in ks:
                kinds[k] = kinds.get(k, 0) + 1
        elif cid in pending:
            # the NEXT verdict on a stale claim answers the staling; a
            # verdict on a claim with no open episode answers nothing
            # and must not be counted (the negative controls, ST4/ST5).
            del pending[cid]
            counts[_staling_bucket(p)] += 1
    resolved = sum(counts.values())
    return {"invalidations": invalidations,
            "restaled": restaled,
            "stalings": resolved + len(pending),
            "resolved": resolved,
            "unresolved": len(pending),
            "mechanical_agree": counts["mechanical_agree"],
            "human_agree": counts["human_agree"],
            "true_stale": counts["true_stale"],
            "false_stale": (counts["mechanical_agree"]
                            + counts["human_agree"]),
            "pathless": pathless,
            "by_path_kind": [{"kind": k, "stalings": n} for k, n in
                             sorted(kinds.items(),
                                    key=lambda kv: (-kv[1], kv[0]))]}
