"""truthlib.advisory -- advisory assembly and the pure report family (C6).

The CC-1 advisory block (ADR-034), the post-append intake advisories,
the commit-gate banner, and every pure fold consumer a read surface
renders: queue, impact, inverse, baseline, stats, half-life, vocab,
dispatch text, and the citation-scope helpers -- plus the Tier C report
family (override velocity, separation, blast, ADR-046), which stays
pure HERE and is driven by the meta-repo's instruments/*.py, no longer
by stats/doctor.  Pure: facts arrive as data; nothing here probes the
world.
"""
import hashlib
import json
import re
import statistics

from truthlib.registry import *
from truthlib.kernel import *
from truthlib.evidence import *
from truthlib.policy import *

# --- ADR-034: the CC-1 advisory assembler --------------------------------
# Every post-append intake advisory folds into ONE contiguous stderr
# block, each line carrying the stable prefix below (machine-greppable:
# the QB-011 class -- a warning swallowed by a `tail -1` capture -- must
# not recur across advisory classes). Silence on clean. The commit-gate
# banner is EXEMPT with reason: it must fire at dispatch even on refused
# filings (fail-open-with-noise is its documented property above).
ADVISORY_PREFIX = "truth: advisory:"

def _escape_ctrl(s):
    """SI-3: neutralize control bytes in claim-derived substrings before
    they reach a terminal. INV-M refuses only whitespace, so ESC survives
    intake; raw interpolation would allow terminal-escape injection into
    the advisory block and spoofing of injection-asserted canary strings.
    Pure; \\n and \\t survive (the renderer splits on newline; a tab is
    legitimate message content), everything else in C0, DEL, and C1
    renders escaped, repr-style (C1 included: \\x9b is a single-byte CSI
    on 8-bit terminals -- the R0 adversarial review's catch)."""
    return re.sub(r"[\x00-\x08\x0b-\x1f\x7f\x80-\x9f]",
                  lambda m: repr(m.group())[1:-1], s)

def render_advisory_block(messages):
    """CC-1 (ADR-034): fold advisory messages into one block, or None
    when every message is None/empty (silence on clean). Pure. Messages
    arrive WITHOUT the prefix; each physical line gets it here, so the
    block is contiguous and uniformly greppable."""
    lines = []
    for m in messages:
        if not m:
            continue
        for ln in _escape_ctrl(m).splitlines():
            lines.append(f"{ADVISORY_PREFIX} {ln}")
    return "\n".join(lines) if lines else None

# --- ADR-038: the dirty-watch advisory ------------------------------------
def parse_porcelain_z(out):
    """Pure: `git status --porcelain=v1 -z` fields -> [(xy, paths)].
    NUL-separated, UNQUOTED (SI-2: default quotepath would octal-quote
    non-ASCII names into match_paths-invisibility); a rename/copy entry
    (X or Y in RC) is followed by ONE extra NUL field, the source path
    -- both paths belong to the entry."""
    fields = [f for f in out.split("\x00")]
    entries, i = [], 0
    while i < len(fields):
        f = fields[i]
        i += 1
        if len(f) < 4 or f[2] != " ":
            continue
        xy, path = f[:2], f[3:]
        paths = [path]
        if ("R" in xy or "C" in xy) and i < len(fields) and fields[i]:
            paths.append(fields[i])
            i += 1
        entries.append((xy, paths))
    return entries

def dirty_watch(entries, watch_patterns):
    """Pure (ADR-038): the watched paths that are dirty in the working
    tree. Dirtiness is STRUCTURAL -- any XY other than clean ('  ') or
    ignored ('!!') counts, which covers the unmerged states (UU et al.:
    dirty precisely during conflict resolution, the pilot's QB-011
    scenario) that a letter whitelist would miss. Untracked entries
    ('??') count too: INV-M refuses untracked LITERAL watches, but a
    glob legitimately watches an empty-for-now namespace, and an
    untracked file under it is exactly the restale-at-birth vector.
    Renames match on either side. Returns sorted unique paths."""
    hits = set()
    for xy, paths in entries:
        if xy in ("  ", "!!"):
            continue
        for p in paths:
            if match_paths(p, watch_patterns):
                hits.add(p)
    return sorted(hits)

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

def intake_advisories(events, tier, ttl_days_arg, scope_ok, evidence_class,
                      payload, generated_ok=None, claims=None, *,
                      generated_source, porcelain, shallow_state,
                      blast_forecast_live=None, blast_history=None):
    """The post-append advisory set shared by `claim` and `done --claim`
    (ADR-034): FS-1 half-life note (moved post-append -- it advises, so
    it rides the block), ADR-032 default-expiry notice, the ADR-037
    recipe lints and generated-list-absent notice, and the v0.9.11
    hollow-VERIFIED exit warning. Returns the non-None messages, table
    order; the renderer prefixes and escapes.

    PURE since P2 (R6): the shell gathers the three world-facts ONCE and
    passes them as keyword-only data -- generated_source is the ADR-037
    list state _gate_generated already stashed in ctx (None when the
    filing carried no paths, unread then), porcelain is the raw
    `git status --porcelain=v1 -z` text (or None), and shallow_state /
    blast_forecast_live / blast_history are _gate_blast's own probe
    results passed through as data (ADR-046: the forecast is computed
    live and NEVER stored -- the payload no longer carries it). No
    subprocess, file, clock, or env in here any more; the duplicate
    probes per filing are gone with them."""
    msgs = []
    if ttl_days_arg:
        # FS-1: suggestion only, beside the author's choice -- TTLs stay
        # author decisions, data-adjacent.
        obs, _ = half_life_observations(events)
        median = ttl_suggestion(obs, tier)
        if median is not None:
            msgs.append(f"ledger median half-life for {tier}: {median}d; "
                        f"you chose {ttl_days_arg}d (FS-1 suggestion, "
                        "not a gate)")
    stored_gen = payload.get("generated_ok_basis")
    flag = "--scope-ok" if scope_ok else "--generated-ok"
    _, _, decay_notice = override_decay(scope_ok or stored_gen,
                                        ttl_days_arg, flag=flag)
    msgs.append(decay_notice)
    if generated_ok and not stored_gen:
        # ADR-037: a stated override that matched nothing must not drop
        # silently (and it does not decay -- nothing was recorded).
        msgs.append("--generated-ok stated but the watch matched nothing "
                    f"on {GENERATED_PATHS_REL} -- the basis was NOT "
                    "stored (ADR-037); drop the flag or fix the list")
    # ADR-037: recipe lints on the recorded command (pure, screen-token
    # stream), and the generated-list-absent notice for path claims --
    # the check is dark until the consumer commits the list; a
    # committed-EMPTY list is conscious policy and stays silent (SI-4).
    msgs.extend(recipe_lints((payload.get("evidence") or {}).get("command")))
    if payload.get("evidence_paths") \
            and generated_source == "absent":
        msgs.append(f"no {GENERATED_PATHS_REL} -- the generated-artifact "
                    "check is dark; commit the list (empty is a conscious "
                    "'nothing is generated') to arm or silence this "
                    "(ADR-037)")
    # ADR-038: the dirty-watch advisory -- a claim filed before its
    # watched content lands restales at birth (the two-commit dance's
    # hazard, made visible at the only cheap moment). Advisory only:
    # filing ahead of the content commit is legitimate when the author
    # intends an immediate re-verify, and a refusal here would teach
    # `git stash` as its bypass.
    if payload.get("evidence_paths") and porcelain:
        for p in dirty_watch(parse_porcelain_z(porcelain),
                             payload["evidence_paths"]):
            msgs.append(f"dirty watch: {p} has uncommitted changes -- "
                        "this claim stales on the commit that lands "
                        "them (restale-at-birth, ADR-038). Commit the "
                        "content first, then file.")
    # ADR-039: the blast advisory -- an upper bound on stalings, voiced
    # only at or above the (self-calibrating) floor; shallow/unavailable
    # history is voiced loudly instead of quietly reading cold.
    if payload.get("evidence_paths"):
        f = blast_forecast_live
        if f is None:
            # R6: the shallow/unavailable fact is _gate_blast's own
            # blast_history state, passed through -- the duplicated
            # inline rev-parse probe is gone.
            msgs.append("blast: shallow history -- a forecast would be a "
                        "floor, not a bound; skipped (ADR-039)"
                        if shallow_state == "shallow"
                        else "blast: history unavailable -- forecast "
                             "skipped (ADR-039)")
        elif claims is not None:
            floor, src = effective_blast_floor(claims, blast_history)
            if f >= floor:
                msgs.append(f"blast: watch matched {f} commits in the "
                            f"last {BLAST_WINDOW_DAYS}d -- an upper bound "
                            "on stalings; narrower --paths cut "
                            f"re-verification load (ADR-039; floor {floor}"
                            f", {src})")
    # field-notes-batch-m item 2 remedy: the filing already succeeded and
    # its exit code stands; the captured intake returncode (first run --
    # already in the evidence capsule, never re-run) just gets a voice.
    # ADR-035: a stored --evidence-exit-ok basis IS the acknowledgment,
    # so the warning stays silent for it (the override row counts it).
    if not payload.get("evidence_exit_basis"):
        msgs.append(evidence_exit_warning(
            evidence_class, (payload.get("evidence") or {}).get("returncode")))
    return [m for m in msgs if m]

def commit_gate_banner(verb, gate_wired):
    """R2 (roadmap-v3): ADR-025 made the commit gate decidable, but only
    `doctor` looked -- an unwired clone ran every verb silently ungated.
    Given the verb and the shell-gathered wiring fact, returns the loud
    banner (or None): write verbs only (a read verb changes nothing the
    gate screens, and `validate --stdin` runs inside the gate itself).
    Fail-open with noise -- the shell prints this to stderr and proceeds;
    it never refuses and never changes an exit code."""
    if gate_wired or verb not in WRITE_VERBS:
        return None
    return ("truth: WARNING -- no commit gate is wired (no active "
            "check-truth hook, no CI config naming it).\n"
            "  INV-A/INV-B and the ADR-008/016 detections are NOT "
            "enforced on commits in this clone.\n"
            "  Run `scripts/truth doctor` for the wiring check (ADR-025). "
            "This message does not block.")

# ------------------------------------------------------ stats (FS-1)

def half_life_observations(events):
    """FS-1: elapsed live-time for every claim that was live and later
    went stale -- the raw material for tier-calibrated TTL suggestions
    (paper section 6.2, made a number). This replays the same (ts, id)
    order and the same status rules as fold(); fold stays authoritative
    for status, and test-truth-core cross-checks the two never disagree
    on final state. Returns a list of (tier, days_live) tuples."""
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
            new = ("stale" if kind == "invalidation"
                   # R13: registry .get -- an unknown verdict still skips
                   # silently here, exactly as the local map did.
                   else VERDICT_STATUS.get(p.get("verdict")))
            if not new:
                continue
            ts = parse_ts(ev.get("ts") or "")
            # FS-1/ADR-032: a TTL expiry is administratively caused (the
            # ttl_days value itself, defaulted to 30 by ADR-032), not
            # observed drift, so it must NOT feed the half-life medians --
            # otherwise defaulted overrides industrialize observations that
            # cluster at the default and ttl_suggestion becomes circular
            # (suggests ~= the default that caused the data). Cut here, at
            # the single source of the tier streams both stats_report's
            # medians and ttl_suggestion read, so the exclusion covers both.
            # Prefer the v0.9.12+ structured `reason_code == "ttl"` stamp;
            # fall back to is_ttl_reason's prefix (the SAME two-arm rule as
            # ttl_staleness, reused not re-implemented) for pre-stamp
            # records. The claim still transitions to stale -- fold stays
            # authoritative on status, only the observation is withheld;
            # TTL expiries are counted in override_report's decay_expiries.
            is_ttl = kind == "invalidation" and (
                p.get("reason_code") == "ttl" or is_ttl_reason(p.get("reason")))
            if e["status"] == "live" and new == "stale" and not is_ttl \
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

def ttl_suggestion(observations, tier):
    """FS-1: observed median half-life for the tier, or None below the
    observation threshold (suggestions from noise are worse than none).
    Suggestion only -- TTLs stay author decisions."""
    days = [d for t, d in observations if t == tier]
    if len(days) < HALF_LIFE_MIN_OBS:
        return None
    return round(statistics.median(days), 1)

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
            reason = "evidence invalidated"
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
    premised on those claims. Pure PREDICTION of what the machinery will
    do (invalidate-scan STALES, ready HOLDs) -- files nothing, judges
    nothing. Reuses match_paths: a second matcher implementation is
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

def vocab_report():
    """P2 contract layer: the machine vocabulary -- every named set a
    satellite or instrument would otherwise hand-copy, exported once.
    premise_blocking / premise_warn are DERIVED by evaluating
    premise_check over STATUSES x TIERS (blocking = refused for at least
    one tier; warn = warned for at least one), so the vocab can never
    drift from the ADR-001 matrix: it IS the matrix, evaluated.
    citation_bad is the satellites' blocking contract (CITATION_BAD),
    consumed by nothing else in this CLI. Pure."""
    blocking, warn = [], []
    for status in STATUSES:
        results = [premise_check(status, tier) for tier in TIERS]
        if any(not passes for passes, _ in results):
            blocking.append(status)
        if any(w for _, w in results):
            warn.append(status)
    return {"statuses": list(STATUSES),
            "active": sorted(ACTIVE_STATUSES),
            "verdicts": dict(VERDICT_STATUS),
            "premise_blocking": blocking,
            "premise_warn": warn,
            "citation_bad": sorted(CITATION_BAD),
            "tiers": list(TIERS),
            "kinds": list(KINDS)}

def dispatch_text(prompt_content, claim_record):
    """G11: the exact verifier context -- prompt body + claim, nothing else.
    The envelope self-describes its own integrity: G11 scripts what the
    verifier is SENT, but proxies and context trimmers can lossily compress
    what ARRIVES (observed in the wild: a compression layer dropped an
    entire numbered rule). The header states what a complete copy contains;
    the terminator carries the prompt-file hash so a verifier can compare
    against the file on disk."""
    body = prompt_content.split("\n---\n", 1)[-1].strip()
    rules = sum(1 for ln in body.splitlines() if re.match(r"\d+\. ", ln))
    digest = hashlib.sha256(prompt_content.encode("utf-8")).hexdigest()
    header = (f"INTEGRITY (check before following): a complete copy of this "
              f"dispatch contains {rules} numbered rules and ends with the "
              f"line 'END-OF-DISPATCH sha256:{digest}'. If any rule number "
              "is missing or that terminator is absent, your copy was "
              "altered in transit -- do not proceed from it; read "
              f"{PROMPT_REL} from disk instead and compare its hash "
              f"(shasum -a 256 {PROMPT_REL}).")
    return (header + "\n\n" + body
            + "\n\n\nCLAIM RECORD (verify exactly what is written):\n\n"
            + json.dumps(claim_record, indent=2, sort_keys=True)
            + f"\n\nEND-OF-DISPATCH sha256:{digest}")

def citation_block_paths(hits, scope_globs):
    """Pure (ADR-036): which grep hits actually block -- inside the
    scope and never the ledger itself (retraction bases legitimately
    cite predecessors/successors, so an unexcluded ledger would make
    every second retraction self-blocking). TG4/TG9 pin this."""
    return sorted(h for h in hits
                  if h != LEDGER_REL and match_paths(h, scope_globs))

def dead_scope_notice(scope_globs, source, tracked):
    """Pure (SI-4): a non-empty scope FILE matching zero tracked files
    is dead policy -- loud, never a silent clean sweep."""
    if source != "file":
        return None
    if any(match_paths(t, scope_globs) for t in tracked):
        return None
    return (f"{CITATION_SCOPE_REL} matches zero tracked files -- the "
            "citation sweep runs against dead scope; fix the globs or "
            "commit an empty file to consciously disable (ADR-036)")
