#!/usr/bin/env python3
"""
test-tlr-fold.py — executable spec for the TLR-002/013/014 ordering primitive.

This is the acceptance oracle for the hash-linked (Merkle-tree) journal
described in truth-ledger-target-architecture-and-adrs.md (rev 2). The shipped
scripts/truth implements the OLD (ts,id) fold, NOT this; so a minimal, pure
REFERENCE implementation of the target primitives is embedded here and is the
thing under test. Any real CLI (or cross-language reimplementation) must satisfy
these properties.

stdlib only, deterministic (seeded, no wall clock). Run:  python3 test-tlr-fold.py
Exit 0 iff every property AND every negative-control canary passes.

Design decisions the ADRs left ambiguous, made explicit here (see report):
  D1. record_hash covers prev (tamper-evidence + tree links + fork tiebreak).
      content_hash EXCLUDES prev (TLR-013 identity + first-wins identity).
      The ADR says "byte-identical duplicate = one tree node"; that is
      record_hash grouping. But a fork that re-files the SAME claim content on
      a different prev is content-identical yet record_hash-distinct and must
      NOT trip TLR-013. So the dedup/first-wins key is content_hash, not
      record_hash. Flagged as a spec gap.
  D2. Linearization = DFS-contiguous, children visited in ascending record_hash.
  D3. TLR-014 "the two fork orders would derive different statuses" is
      implemented as: over ALL linear extensions of a claim's events consistent
      with tree ancestry, if >1 distinct status results, the claim is
      order-contested. (Exact for small event sets; a 2-order proxy is used
      above a cap. Flagged.)
  D4. Effective anchor lives in derive() (pure, = latest agree's commit);
      scan() (shell) diffs watched paths from it. Matches TLR-008 wording.
"""

import hashlib
import json
import random
import sys

# ---------------------------------------------------------------------------
# status constants
UNVERIFIED = "unverified"
LIVE = "live"
DIVERGED = "diverged"
CANNOT_VERIFY = "cannot_verify"
STALE = "stale"
RETRACTED = "retracted"

EFFECT_STATUS = {
    "agree": LIVE,
    "diverge": DIVERGED,
    "cannot_verify": CANNOT_VERIFY,
    "invalidation": STALE,
    "retract": RETRACTED,
}

# ===========================================================================
# REFERENCE IMPLEMENTATION (the thing under test)
# ===========================================================================

def _canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))

def _sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def content_hash(rec):
    """Hash of content-bearing fields, EXCLUDING prev/hash (D1)."""
    pre = {k: rec[k] for k in ("id", "kind", "actor", "session", "payload")}
    return _sha(_canon(pre))

def record_hash(rec):
    """Hash INCLUDING prev (D1): tamper-evidence, tree link, fork tiebreak."""
    pre = {k: rec[k] for k in ("id", "kind", "actor", "session", "payload")}
    pre["prev"] = rec["prev"]
    return _sha(_canon(pre))

def make_record(id, kind, actor, session, payload, prev):
    rec = {"id": id, "kind": kind, "actor": actor, "session": session,
           "payload": payload, "prev": prev}
    rec["hash"] = record_hash(rec)
    return rec

def _dedup_by_record_hash(records):
    """Set semantics: byte-identical duplicate lines collapse to one node (B2)."""
    seen = {}
    for r in records:
        seen[r["hash"]] = r
    return seen  # hash -> rec

# ---- tree / order ---------------------------------------------------------

def linearize(records):
    """DFS-contiguous linearization; children visited in ascending record_hash (D2).
    Pure function of the record SET => confluent for free."""
    by_hash = _dedup_by_record_hash(records)
    children = {}
    roots = []
    for h, r in by_hash.items():
        p = r["prev"]
        if p is None or p not in by_hash:
            roots.append(r)
        else:
            children.setdefault(p, []).append(r)
    order = []
    visited = set()

    def visit(r):
        if r["hash"] in visited:
            return
        visited.add(r["hash"])
        order.append(r)
        for c in sorted(children.get(r["hash"], []), key=lambda x: x["hash"]):
            visit(c)

    for r in sorted(roots, key=lambda x: x["hash"]):
        visit(r)
    return order

def _ancestors(records):
    """hash -> set of ancestor hashes (via prev chain). Memoized."""
    by_hash = _dedup_by_record_hash(records)
    memo = {}

    def anc(h):
        if h in memo:
            return memo[h]
        memo[h] = set()  # guard cycles
        r = by_hash.get(h)
        acc = set()
        if r and r["prev"] in by_hash:
            acc.add(r["prev"])
            acc |= anc(r["prev"])
        memo[h] = acc
        return acc

    for h in by_hash:
        anc(h)
    return memo

# ---- integrity: I1 / I2 / I3+TLR-013 --------------------------------------

def verify_hashes(records):
    for r in records:
        if r["hash"] != record_hash(r):
            return False, "hash mismatch (tampered field w/o rehash): %s" % r.get("id")
    return True, ""

def verify_tree(records):
    """I2: every prev resolves (or is genesis None); no dangling references."""
    by_hash = _dedup_by_record_hash(records)
    n_roots = 0
    for r in by_hash.values():
        p = r["prev"]
        if p is None:
            n_roots += 1
        elif p not in by_hash:
            return False, "dangling prev (reorder/drop): %s -> %s" % (r["id"], p)
    if n_roots == 0 and by_hash:
        return False, "no genesis root (all prev dangling)"
    return True, ""

def verify_dup_content(records):
    """I3 + TLR-013: an envelope id borne by two CONTENT-DISTINCT claim records fails.
    content_hash excludes prev, so a content-identical fork does NOT trip (D1)."""
    contents = {}
    for r in records:
        if r["kind"] != "claim":
            continue
        contents.setdefault(r["id"], set()).add(content_hash(r))
    for cid, hs in contents.items():
        if len(hs) > 1:
            return False, "TLR-013: id %s has %d content-distinct claim records" % (cid, len(hs))
    return True, ""

def verify_append_only(old_lines, new_lines):
    """I1: committed file is an append-only line-prefix extension of its first parent."""
    if new_lines[:len(old_lines)] != old_lines:
        return False, "I1: not a prefix-extension (reorder/drop/edit of committed lines)"
    return True, ""

def integrity_check(records, old_lines=None, new_lines=None, enable_013=True):
    reasons = []
    for fn in (verify_hashes, verify_tree):
        ok, why = fn(records)
        if not ok:
            reasons.append(why)
    if enable_013:
        ok, why = verify_dup_content(records)
        if not ok:
            reasons.append(why)
    if old_lines is not None and new_lines is not None:
        ok, why = verify_append_only(old_lines, new_lines)
        if not ok:
            reasons.append(why)
    return (len(reasons) == 0), reasons

# ---- fold / derive --------------------------------------------------------

def _fold_effects(effects):
    """Fold a sequence of effect strings; retract is absorbing (terminal)."""
    status = UNVERIFIED
    retracted = False
    for e in effects:
        if retracted:
            continue
        status = EFFECT_STATUS[e]
        if e == "retract":
            retracted = True
    return status

def _linear_extensions(events, before, cap=6):
    """All linear extensions of `events` under partial order `before(a,b)`.
    Returns None if above cap (caller falls back to a 2-order proxy) (D3)."""
    if len(events) > cap:
        return None
    result = []

    def rec(placed, remaining):
        if not remaining:
            result.append(placed)
            return
        for e in remaining:
            if any(before(o, e) for o in remaining if o is not e):
                continue
            rec(placed + [e], [x for x in remaining if x is not e])

    rec([], events)
    return result

def derive(records, git_facts=None, now=None):
    """(records, git_facts, now) -> {id -> info}. Pure, deterministic, total.
    info = {status, content, eff_anchor, contested}. git_facts/now unused for
    status: TLR-012 makes TTL an event and TLR-008 puts eff-anchor here; the
    actual path-diff lives in scan()."""
    order = linearize(records)
    pos = {r["hash"]: i for i, r in enumerate(order)}
    anc = _ancestors(records)

    # first-wins content by content-identity (D1): first claim per id in canonical order
    content = {}
    for r in order:
        if r["kind"] == "claim" and r["id"] not in content:
            content[r["id"]] = r["payload"].get("text")

    # gather status-affecting events per target claim id
    events_by_target = {}
    anchors = {}
    for r in order:
        if r["kind"] == "claim":
            anchors[r["id"]] = r["payload"].get("anchor", 0)
        eff = r["payload"].get("effect")
        if eff in EFFECT_STATUS:
            events_by_target.setdefault(r["payload"]["target"], []).append(r)

    out = {}
    for cid in content:
        evs = events_by_target.get(cid, [])
        # effective anchor = latest agree commit (TLR-008 / D4)
        agree_commits = [e["payload"].get("commit", anchors[cid])
                         for e in evs if e["payload"].get("effect") == "agree"]
        eff_anchor = max([anchors[cid]] + agree_commits)

        contested = False
        if evs:
            def before(a, b):
                return a["hash"] in anc.get(b["hash"], set())
            exts = _linear_extensions(evs, before)
            if exts is None:
                # proxy: canonical (asc-hash tiebreak) vs reversed tiebreak
                canon = sorted(evs, key=lambda e: pos[e["hash"]])
                rev = sorted(evs, key=lambda e: (-_rank(e, anc, evs), e["hash"]))
                statuses = {_fold_effects([e["payload"]["effect"] for e in canon]),
                            _fold_effects([e["payload"]["effect"] for e in rev])}
            else:
                statuses = {_fold_effects([e["payload"]["effect"] for e in ext])
                            for ext in exts}
            contested = len(statuses) > 1
            canon_seq = sorted(evs, key=lambda e: pos[e["hash"]])
            status = _fold_effects([e["payload"]["effect"] for e in canon_seq])
        else:
            status = UNVERIFIED

        if contested:
            status = STALE  # TLR-014: demote, queue "order-contested"
        out[cid] = {"status": status, "content": content[cid],
                    "eff_anchor": eff_anchor, "contested": contested}
    return out

def _rank(e, anc, evs):
    return sum(1 for o in evs if o["hash"] in anc.get(e["hash"], set()))

# ---- scan (shell side; TLR-008 + TLR-012) ---------------------------------

def scan(records, git_facts, use_eff_anchor=True):
    """Return NEW invalidation records for claims whose watched path changed
    after the effective anchor. git_facts = {claim_id: {'watched':[p],
    'changes': {p:[commit_ints]}}}. Models the mechanical invalidator."""
    d = derive(records)
    order = linearize(records)
    tip = order[-1]["hash"] if order else None
    new = []
    seq = 0
    for cid, info in d.items():
        if info["status"] not in (LIVE, UNVERIFIED):
            continue
        gf = git_facts.get(cid)
        if not gf:
            continue
        anchor = info["eff_anchor"] if use_eff_anchor else _birth_anchor(records, cid)
        fired = False
        for p in gf.get("watched", []):
            for c in gf.get("changes", {}).get(p, []):
                if c > anchor:
                    fired = True
        if fired:
            new.append(make_record("ev-scan-%s-%d" % (cid, seq), "invalidation",
                                    "scanner", "scan",
                                    {"target": cid, "effect": "invalidation",
                                     "reason": "path"}, tip))
            seq += 1
    return new

def _birth_anchor(records, cid):
    for r in records:
        if r["kind"] == "claim" and r["id"] == cid:
            return r["payload"].get("anchor", 0)
    return 0

# ---- freshness stamp (TLR-001) --------------------------------------------

def freshness_stamp(journal_file_bytes, head):
    """Working-tree file contents + HEAD (NOT git-blob-at-HEAD): an uncommitted
    append changes the stamp so the cache is invalidated (Round-2 F5)."""
    body = hashlib.sha256(journal_file_bytes).hexdigest()
    return _sha(body + "|" + str(head))

def head_only_stamp(head):
    """The BROKEN stamp: HEAD only. Used only by a canary."""
    return _sha(str(head))

# ===========================================================================
# GENERATORS
# ===========================================================================

def gen_history(rng, n):
    """Random valid Merkle-tree history (forks anywhere)."""
    root = make_record("tr-0", "claim", "a0", "s0",
                       {"target": "tr-0", "text": "claim 0", "anchor": 0}, None)
    records = [root]
    claim_ids = ["tr-0"]
    for i in range(1, n):
        prev = rng.choice(records)["hash"]
        if rng.random() < 0.4:
            cid = "tr-%d" % i
            records.append(make_record(cid, "claim", "a%d" % i, "s%d" % i,
                                       {"target": cid, "text": "claim %d" % i,
                                        "anchor": i}, prev))
            claim_ids.append(cid)
        else:
            target = rng.choice(claim_ids)
            eff = rng.choice(["agree", "diverge", "cannot_verify",
                              "invalidation", "retract"])
            kind = {"invalidation": "invalidation", "retract": "retract"}.get(eff, "verdict")
            records.append(make_record("ev-%d" % i, kind, "a%d" % i, "s%d" % i,
                                       {"target": target, "effect": eff}, prev))
    return records

# ===========================================================================
# TEST RUNNER
# ===========================================================================

RESULTS = []

def check(name, passed, detail=""):
    RESULTS.append((name, passed, detail))

# --- Property 1: convergence ------------------------------------------------

def prop_convergence():
    ok = True
    detail = ""
    for seed in range(40):
        rng = random.Random(seed)
        recs = gen_history(rng, rng.randint(6, 40))
        base = {k: v["status"] for k, v in derive(recs).items()}
        # simulate different merge directions = different file line orders,
        # incl. an identical-duplicate line (union-merge shape).
        for s2 in range(4):
            r2 = random.Random(seed * 100 + s2)
            shuffled = list(recs)
            r2.shuffle(shuffled)
            shuffled.append(recs[r2.randrange(len(recs))])  # dup line
            got = {k: v["status"] for k, v in derive(shuffled).items()}
            if got != base:
                ok = False
                detail = "seed %d order %d diverged" % (seed, s2)
                break
        if not ok:
            break
    # octopus: three branches off one fork, explicit
    root = make_record("tr-0", "claim", "a", "s", {"target": "tr-0", "text": "x", "anchor": 0}, None)
    kids = [make_record("ev-%d" % i, "verdict", "a%d" % i, "s%d" % i,
                        {"target": "tr-0", "effect": e}, root["hash"])
            for i, e in enumerate(["agree", "diverge", "cannot_verify"])]
    oct_recs = [root] + kids
    o1 = {k: v["status"] for k, v in derive(oct_recs).items()}
    o2 = {k: v["status"] for k, v in derive(list(reversed(oct_recs))).items()}
    if o1 != o2:
        ok = False
        detail = "octopus merge-direction dependent"
    check("P1 convergence (both directions, 3-way/octopus)", ok, detail)

def canary_convergence():
    # Reintroduce the bug: order by FILE POSITION (input list order) not by set.
    def buggy_derive(records):
        # fold in given list order, ignoring the tree
        events = {}
        content = {}
        for r in records:
            if r["kind"] == "claim":
                content.setdefault(r["id"], True)
            eff = r["payload"].get("effect")
            if eff:
                events.setdefault(r["payload"]["target"], []).append(eff)
        return {cid: _fold_effects(events.get(cid, [])) for cid in content}
    root = make_record("tr-0", "claim", "a", "s", {"target": "tr-0", "text": "x", "anchor": 0}, None)
    a = make_record("ev-1", "verdict", "a1", "s1", {"target": "tr-0", "effect": "agree"}, root["hash"])
    b = make_record("ev-2", "invalidation", "a2", "s2", {"target": "tr-0", "effect": "invalidation"}, root["hash"])
    recs = [root, a, b]
    caught = buggy_derive(recs) != buggy_derive([root, b, a])
    check("  canary P1 (file-order fold => merge-direction dependent)", caught)

# --- Property 2: anti-grinding (TLR-013) -----------------------------------

def _grind_pair(nonce):
    """Genuine + forged duplicate-id claim, both forked off r0. `nonce` perturbs
    the forged record so its record_hash sweeps ordering positions."""
    root = make_record("tr-root", "claim", "op", "s0", {"target": "tr-root", "text": "root", "anchor": 0}, None)
    genuine = make_record("tr-x", "claim", "michal", "s1",
                          {"target": "tr-x", "text": "db safe to drop", "anchor": 1}, root["hash"])
    agree = make_record("ev-a", "verdict", "verifier", "s2",
                        {"target": "tr-x", "effect": "agree", "commit": 2}, genuine["hash"])
    forged = make_record("tr-x", "claim", "evil", "s9",
                         {"target": "tr-x", "text": "DROP DATABASE prod", "nonce": nonce, "anchor": 1},
                         root["hash"])
    return [root, genuine, agree, forged], genuine, forged

def prop_anti_grinding():
    all_fail = True
    saw_forged_first = False
    substituted_when_first = False
    for nonce in range(400):
        recs, genuine, forged = _grind_pair(nonce)
        ok, _ = integrity_check(recs, enable_013=True)
        if ok:
            all_fail = False
            break
        # observe that grinding DOES move the forged record ahead sometimes,
        # and that WITHOUT the gate that would substitute content
        if forged["hash"] < genuine["hash"]:
            saw_forged_first = True
            cont = derive(recs)["tr-x"]["content"]
            if cont == "DROP DATABASE prod":
                substituted_when_first = True
    check("P2 anti-grinding: TLR-013 fails the pair in EVERY grind position", all_fail)
    check("  (sanity: grinding really can seat forged first, and would substitute)",
          saw_forged_first and substituted_when_first)

def canary_anti_grinding():
    # Gate OFF: there EXISTS a grind position that is 'green' with substituted content.
    found_green_substitution = False
    for nonce in range(400):
        recs, genuine, forged = _grind_pair(nonce)
        ok, _ = integrity_check(recs, enable_013=False)
        if ok and derive(recs)["tr-x"]["content"] == "DROP DATABASE prod":
            found_green_substitution = True
            break
    check("  canary P2 (gate OFF => green ledger w/ substituted content exists)",
          found_green_substitution)

# --- Property 3: identical union-merge duplicate passes (B2) ----------------

def prop_b2_identical_dup():
    root = make_record("tr-0", "claim", "a", "s", {"target": "tr-0", "text": "hi", "anchor": 0}, None)
    c = make_record("tr-1", "claim", "a", "s", {"target": "tr-1", "text": "fact", "anchor": 1}, root["hash"])
    dup = dict(c)  # byte-identical line duplicated by union merge
    base = derive([root, c])
    withdup = derive([root, c, dup])
    ok_integrity, _ = integrity_check([root, c, dup], enable_013=True)
    passed = ok_integrity and ({k: v["status"] for k, v in base.items()} ==
                               {k: v["status"] for k, v in withdup.items()})
    check("P3 identical union-merge duplicate: integrity green, status unchanged (B2)", passed)

def canary_b2():
    # Make the 'duplicate' content-distinct => must FAIL (proving P3 isn't vacuous)
    root = make_record("tr-0", "claim", "a", "s", {"target": "tr-0", "text": "hi", "anchor": 0}, None)
    c = make_record("tr-1", "claim", "a", "s", {"target": "tr-1", "text": "fact", "anchor": 1}, root["hash"])
    evil = make_record("tr-1", "claim", "a", "s", {"target": "tr-1", "text": "LIE", "anchor": 1}, root["hash"])
    ok, _ = integrity_check([root, c, evil], enable_013=True)
    check("  canary P3 (content-distinct dup under same id => integrity FAILS)", not ok)

# --- Property 4: order-contested demotion (TLR-014) -------------------------

def _contested_fixture():
    root = make_record("tr-0", "claim", "a", "s", {"target": "tr-0", "text": "x", "anchor": 0}, None)
    claim = make_record("tr-x", "claim", "a", "s", {"target": "tr-x", "text": "y", "anchor": 1}, root["hash"])
    # two concurrent siblings off `claim`: agree vs invalidation
    agree = make_record("ev-ok", "verdict", "v", "sv", {"target": "tr-x", "effect": "agree", "commit": 3}, claim["hash"])
    inval = make_record("ev-inv", "invalidation", "sc", "ss", {"target": "tr-x", "effect": "invalidation"}, claim["hash"])
    return [root, claim, agree, inval]

def prop_order_contested():
    recs = _contested_fixture()
    info = derive(recs)["tr-x"]
    passed = info["contested"] and info["status"] == STALE
    check("P4 order-contested (concurrent agree|invalidation) => demote to stale", passed)
    # retract vs agree is NOT contested: retract absorbs in both orders => terminal
    root = make_record("tr-0", "claim", "a", "s", {"target": "tr-0", "text": "x", "anchor": 0}, None)
    claim = make_record("tr-y", "claim", "a", "s", {"target": "tr-y", "text": "y", "anchor": 1}, root["hash"])
    agree = make_record("ev-a", "verdict", "v", "sv", {"target": "tr-y", "effect": "agree"}, claim["hash"])
    retr = make_record("ev-r", "retract", "h", "sh", {"target": "tr-y", "effect": "retract"}, claim["hash"])
    info2 = derive([root, claim, agree, retr])["tr-y"]
    check("  (retract|agree concurrent => NOT contested, stays retracted)",
          (not info2["contested"]) and info2["status"] == RETRACTED)

def canary_order_contested():
    # Bug: trust the tiebreak silently (no contested detection). Then a
    # merge-direction change would flip status live<->stale with no queue entry.
    recs = _contested_fixture()
    order = linearize(recs)
    pos = {r["hash"]: i for i, r in enumerate(order)}
    evs = [r for r in recs if r["payload"].get("effect")]
    canon = _fold_effects([e["payload"]["effect"] for e in sorted(evs, key=lambda e: pos[e["hash"]])])
    other = _fold_effects([e["payload"]["effect"] for e in sorted(evs, key=lambda e: e["hash"], reverse=True)])
    # the two tiebreak orders genuinely disagree -> silent-trust would be a coin flip
    check("  canary P4 (untrusted tiebreak really yields two different statuses)",
          canon != other)

# --- Property 5: tamper-evidence (I1/I2) ------------------------------------

def prop_tamper():
    rng = random.Random(7)
    recs = gen_history(rng, 12)
    lines = [_canon(r) for r in recs]
    # legit append passes
    extra = make_record("tr-99", "claim", "z", "sz", {"target": "tr-99", "text": "new", "anchor": 99}, recs[-1]["hash"])
    ok_append, _ = integrity_check(recs + [extra], old_lines=lines, new_lines=lines + [_canon(extra)])
    # drop an interior committed record => dangling prev (I2) AND prefix break (I1)
    dropped = recs[:5] + recs[6:]
    ok_drop, _ = integrity_check(dropped, old_lines=lines, new_lines=[_canon(r) for r in dropped])
    # reorder committed lines => I1 prefix break
    reordered = [lines[1], lines[0]] + lines[2:]
    ok_reorder, _ = integrity_check(recs, old_lines=lines, new_lines=reordered)
    # silent field edit without rehash => verify_hashes catches
    tampered = [dict(r) for r in recs]
    tampered[3]["payload"] = dict(tampered[3]["payload"]); tampered[3]["payload"]["text"] = "EDITED"
    ok_edit, _ = integrity_check(tampered)
    passed = ok_append and (not ok_drop) and (not ok_reorder) and (not ok_edit)
    check("P5 tamper-evidence: legit append passes; drop/reorder/edit FAIL", passed)

def canary_tamper():
    # Bug: append-only check that only compares LENGTH would miss a reorder.
    lines = ["a", "b", "c"]
    reordered = ["b", "a", "c"]
    def buggy(old, new):
        return len(new) >= len(old)  # length-only: WRONG
    caught = buggy(lines, reordered) and not verify_append_only(lines, reordered)[0]
    check("  canary P5 (length-only append check would miss a reorder)", caught)

# --- Property 6: cache purity + freshness stamp -----------------------------

def prop_cache_purity():
    rng = random.Random(11)
    recs = gen_history(rng, 20)
    a = {k: v["status"] for k, v in derive(recs).items()}
    shuffled = list(recs)
    random.Random(999).shuffle(shuffled)
    b = {k: v["status"] for k, v in derive(shuffled).items()}
    pure = (a == b)
    # freshness stamp: an uncommitted append (HEAD unchanged) must change stamp
    before = b"".join(_canon(r).encode() + b"\n" for r in recs)
    extra = make_record("tr-new", "claim", "z", "sz", {"target": "tr-new", "text": "n", "anchor": 5}, recs[-1]["hash"])
    after = before + (_canon(extra).encode() + b"\n")
    HEAD = "commit-abc"  # unchanged across the uncommitted append
    stamp_moved = freshness_stamp(before, HEAD) != freshness_stamp(after, HEAD)
    check("P6 cache purity (order-invariant) + freshness stamp moves on uncommitted append",
          pure and stamp_moved)

def canary_cache():
    # Bug: HEAD-only stamp does NOT move across a real uncommitted append (HEAD
    # unchanged) => cache serves a stale snapshot; content stamp WOULD move.
    HEAD = "commit-abc"
    root = make_record("tr-0", "claim", "a", "s", {"target": "tr-0", "text": "r", "anchor": 0}, None)
    before = _canon(root).encode() + b"\n"
    extra = make_record("tr-1", "claim", "a", "s", {"target": "tr-1", "text": "n", "anchor": 1}, root["hash"])
    after = before + _canon(extra).encode() + b"\n"
    head_only_blind = head_only_stamp(HEAD) == head_only_stamp(HEAD)          # unchanged (bug)
    content_sees_it = freshness_stamp(before, HEAD) != freshness_stamp(after, HEAD)  # changed (fix)
    check("  canary P6 (HEAD-only stamp blind to append while content stamp sees it)",
          head_only_blind and content_sees_it)

# --- Property 7: effective-anchor durability (TLR-008) ----------------------

def _anchor_fixture():
    root = make_record("tr-0", "claim", "a", "s", {"target": "tr-0", "text": "r", "anchor": 0}, None)
    claim = make_record("tr-p", "claim", "a", "s",
                        {"target": "tr-p", "text": "watched fact", "anchor": 1, "watched": ["P"]}, root["hash"])
    return [root, claim]

def prop_effective_anchor():
    recs = _anchor_fixture()
    gf = {"tr-p": {"watched": ["P"], "changes": {"P": [2]}}}  # P changed at commit 2 (> anchor 1)
    # scan 1: stale
    inv = scan(recs, gf)
    recs2 = recs + [make_record(r["id"], r["kind"], r["actor"], r["session"], r["payload"], r["prev"]) for r in inv]
    staled = derive(recs2)["tr-p"]["status"] == STALE
    # re-verify at commit 3 (verifying commit) -> agree; eff anchor -> 3
    agree = make_record("ev-a", "verdict", "v", "sv", {"target": "tr-p", "effect": "agree", "commit": 3}, recs2[-1]["hash"])
    recs3 = recs2 + [agree]
    relived = derive(recs3)["tr-p"]["status"] == LIVE
    # scan 2: P last changed at 2, eff anchor now 3 -> NO new invalidation -> stays live (no flap)
    inv2 = scan(recs3, gf, use_eff_anchor=True)
    no_flap = (len(inv2) == 0) and derive(recs3)["tr-p"]["status"] == LIVE
    check("P7 effective-anchor durability: stale->agree->scan stays live (no flap)",
          staled and relived and no_flap)

def canary_effective_anchor():
    # Bug: scan diffs from BIRTH anchor (ignores agree). Then re-verified claim re-stales -> flap.
    recs = _anchor_fixture()
    gf = {"tr-p": {"watched": ["P"], "changes": {"P": [2]}}}
    agree = make_record("ev-a", "verdict", "v", "sv", {"target": "tr-p", "effect": "agree", "commit": 3}, recs[-1]["hash"])
    recs3 = recs + [agree]
    inv2 = scan(recs3, gf, use_eff_anchor=False)  # birth-anchor bug
    flaps = len(inv2) > 0
    check("  canary P7 (birth-anchor scan re-stales a re-verified claim => flap)", flaps)

# --- Property 8: retraction terminality (TLR-006) ---------------------------

def prop_retraction_terminal():
    root = make_record("tr-0", "claim", "a", "s", {"target": "tr-0", "text": "r", "anchor": 0}, None)
    claim = make_record("tr-k", "claim", "a", "s", {"target": "tr-k", "text": "k", "anchor": 1}, root["hash"])
    retr = make_record("ev-r", "retract", "h", "sh", {"target": "tr-k", "effect": "retract"}, claim["hash"])
    # pile later events on the retracted id: agree, invalidation, diverge
    later = []
    prev = retr["hash"]
    for i, e in enumerate(["agree", "invalidation", "diverge", "agree"]):
        kind = {"invalidation": "invalidation"}.get(e, "verdict")
        r = make_record("ev-l%d" % i, kind, "x", "sx", {"target": "tr-k", "effect": e}, prev)
        later.append(r); prev = r["hash"]
    recs = [root, claim, retr] + later
    stays = derive(recs)["tr-k"]["status"] == RETRACTED
    # and confluent: any input order still retracted
    stays2 = derive(list(reversed(recs)))["tr-k"]["status"] == RETRACTED
    check("P8 retraction terminality: retract absorbs all later events (any order)", stays and stays2)

def canary_retraction():
    # Bug: non-absorbing fold (plain LWW) => a later agree resurrects a retracted claim.
    def lww(effects):
        s = UNVERIFIED
        for e in effects:
            s = EFFECT_STATUS[e]
        return s
    resurrected = lww(["retract", "agree"]) == LIVE
    check("  canary P8 (plain LWW without absorption resurrects a retracted claim)", resurrected)

# ---------------------------------------------------------------------------

def main():
    prop_convergence();       canary_convergence()
    prop_anti_grinding();     canary_anti_grinding()
    prop_b2_identical_dup();  canary_b2()
    prop_order_contested();   canary_order_contested()
    prop_tamper();            canary_tamper()
    prop_cache_purity();      canary_cache()
    prop_effective_anchor();  canary_effective_anchor()
    prop_retraction_terminal(); canary_retraction()

    print("TLR ordering-primitive acceptance oracle (TLR-002/013/014 + deps)\n")
    npass = 0
    for name, passed, detail in RESULTS:
        tag = "PASS" if passed else "FAIL"
        line = "  [%s] %s" % (tag, name)
        if detail and not passed:
            line += "  -- " + detail
        print(line)
        npass += 1 if passed else 0
    total = len(RESULTS)
    print("\n%d/%d checks passed" % (npass, total))
    sys.exit(0 if npass == total else 1)

if __name__ == "__main__":
    main()
