"""truth v0.9.38 -- append-only claims ledger with a native work kernel.

truthlib.cli -- argparse and the cmd_* orchestration (the line above is
the argparse description, kept in lockstep with the entry docstring by
TestCrossSurfaceVersions).  The verbs gather via shellio, decide via the
pure modules, and exit refusals here; build_claim_payload drives the
ADR-034 gate table.  The only module argparse lives in.
"""
import argparse
import json
import os
import sys
import time

from truthlib.registry import *
from truthlib.kernel import *
from truthlib.evidence import *
from truthlib.policy import *
from truthlib.gates import *
from truthlib.reports import *
from truthlib.contract import *
from truthlib.advisory import *
from truthlib.shellio import *
from truthlib.advisory import _escape_ctrl
from truthlib.shellio import _short_sha

def build_claim_payload(text, evidence_class, evidence_cmd, paths_csv, tier,
                        ttl_days, basis, single_run, duplicate_ok, claims, *,
                        scope_basis=None, unsafe_ok=False,
                        evidence_exit_basis=None, generated_basis=None,
                        watch_policy=None, paths_basis=None):
    """Full claim intake, driven by the ADR-034 staged gate table --
    WITHOUT appending. Shared by `claim` and `done --claim` so
    claim-at-death goes through the identical intake, and so `done` can
    validate everything before it appends anything (ADR-002: both
    records or neither). The basis tail is KEYWORD-ONLY (R7: four
    adjacent sentence-or-None params -- a transposition type-checks and
    stores a basis under the wrong key with the wrong decay).

    Returns (payload, facts): facts exposes the ctx values the R6
    advisory pass needs (generated_source from _gate_generated,
    blast_state from _gate_blast) so the shell never re-probes what the
    gate rows already gathered."""
    # FAZA 3 (defect D-A): a named policy RESOLVES to the watch set, it
    # does not merely annotate one. Both refusals are pure and live in
    # policy.py; the shell loads the file and exits. Resolution happens
    # BEFORE the gate table so every downstream row -- INV-M's dead-glob
    # check, the ADR-039 blast forecast, the ADR-038 dirty-watch advisory
    # -- judges the resolved globs, exactly as it judges a hand-written
    # --paths list. A policy that ships an unreachable glob must be
    # refused by INV-M like any other.
    wp_policies, wp_state, wp_err = load_watch_policies()
    # ORDER IS SHORT-CIRCUIT, not cosmetic: a malformed policy file makes
    # load_watch_policies return policies=None, so the two predicates below
    # must not be EVALUATED before that exit -- putting all three in one
    # tuple looked tidier and raised TypeError on every bad file, which is
    # the crash-instead-of-refusal shape the refusal text exists to avoid.
    if wp_err:
        sys.exit(wp_err)
    for _e in (watch_policy_conflict_error(watch_policy, paths_csv),
               watch_policy_error(watch_policy, wp_policies, wp_state)):
        if _e:
            sys.exit(_e)
    resolved_paths = (list(wp_policies[watch_policy]) if watch_policy
                      else split_csv(paths_csv))
    ctx = {"text": text, "evidence_class": evidence_class,
           "evidence_cmd": evidence_cmd, "paths": resolved_paths,
           "tier": tier, "ttl_days": ttl_days, "basis": basis,
           "claims": claims, "duplicate_ok": duplicate_ok,
           "scope_basis": scope_basis,
           "evidence_exit_basis": evidence_exit_basis,
           "generated_basis": generated_basis,
           "watch_policy": watch_policy, "paths_basis": paths_basis,
           "head": head_commit() if evidence_class == "VERIFIED" else None,
           "overridden_duplicates": [], "ttl_default": False}
    # A1: the stage RETURNS its first refusal; exiting is the shell's job
    # and this is the shell. Same string, same exit, one frame further out.
    err = run_intake_stage("pre-execution", ctx)
    if err:
        sys.exit(err)
    payload = {"text": text, "evidence_class": evidence_class,
               "cost_tier": tier, "ttl_days": ctx["ttl_days"],
               "evidence_paths": ctx["paths"]}
    if paths_basis:
        # Step 3.2: the stated reason a freehand watch set wider than the
        # budget is the right one. Stored so it decays (ADR-032) and gets
        # counted (override_report) -- an override nobody re-asks is an
        # override that accumulates.
        payload["paths_basis"] = paths_basis
    if watch_policy:
        # PROVENANCE, beside the resolved globs -- never instead of them.
        # The ledger is append-only, so a claim must keep recording WHAT it
        # watched at filing time; storing only the name would let a later
        # edit to .truth/watch-policies silently rewrite what every past
        # claim is understood to have watched. The name records which
        # committed decision the author stood on, and stats_report counts
        # adoption from it (ADR-046: the field has a reader).
        payload["watch_policy"] = watch_policy
    if scope_basis:
        payload["scope_basis"] = scope_basis
    if ctx["ttl_default"]:
        # ADR-032: mark that this ttl_days was defaulted (not author-chosen)
        # so the override-velocity report (ADR-033) and any auditor can tell
        # a decay expiry from a real diverge.
        payload["ttl_default"] = True
    if ctx["overridden_duplicates"]:
        payload["overridden_duplicates"] = ctx["overridden_duplicates"]
    if ctx.get("payload_generated_basis"):
        payload["generated_ok_basis"] = ctx["payload_generated_basis"]
    # ADR-046: blast_forecast is NOT stamped -- it failed the envelope
    # admission rule (nothing in the fold or a blocking gate reads it).
    # The gate still computes it live; it rides `facts` to the advisory.

    if evidence_class == "VERIFIED":
        # -- execution boundary (ADR-029): screen, then double-run.
        # A missing allowlist fails closed even under --evidence-unsafe-ok
        # (the override targets a specific command, not absent machinery).
        allow = load_allowlist()
        screen_err = screen_evidence_command(evidence_cmd, allow,
                                             denylist=load_denylist())
        if screen_err and (allow is None or not unsafe_ok):
            sys.exit("truth: " + screen_err)
        digest, rc = run_evidence(evidence_cmd)
        if not single_run:
            err = determinism_error((digest, rc), run_evidence(evidence_cmd))
            if err:
                sys.exit(err)
        payload["evidence"] = {"command": evidence_cmd,
                               "output_hash": "sha256:" + digest,
                               "returncode": rc,
                               "screened": screen_err is None}
        payload["anchor_commit"] = ctx["head"]
        ctx["payload"] = payload
        # The SECOND of the two call sites, and the one I missed on the
        # first pass -- the fingerprint caught it in seconds: the ADR-035
        # exit gate lives in this stage, so a refusal became a silent
        # advisory and the hollow VERIFIED filed. Left as a comment
        # because "both call sites" is the whole of A1's shell half, and
        # one of two is the shape of the mistake.
        err = run_intake_stage("post-execution", ctx)
        if err:
            sys.exit(err)
    elif evidence_class == "INFERRED":
        payload["basis"] = basis
    facts = {"generated_source": ctx.get("generated_source"),
             "blast_state": ctx.get("blast_state"),
             "blast_forecast": ctx.get("blast_forecast"),
             "blast_history": ctx.get("blast_history")}
    return payload, facts

def cmd_claim(a):
    events = load_events()
    claims, _ = fold(events)
    payload, facts = build_claim_payload(
        a.text, a.evidence_class, a.evidence_cmd, a.paths, a.tier,
        a.ttl_days, a.basis, a.single_run, a.duplicate_ok, claims,
        scope_basis=a.scope_ok, unsafe_ok=a.evidence_unsafe_ok,
        evidence_exit_basis=a.evidence_exit_ok,
        generated_basis=a.generated_ok,
        watch_policy=getattr(a, "watch_policy", None),
        paths_basis=getattr(a, "paths_ok", None))
    rec = append_record("claim", payload)
    advisories = intake_advisories(events, a.tier, a.ttl_days, a.scope_ok,
                                   a.evidence_class, payload,
                                   generated_ok=a.generated_ok,
                                   claims=claims,
                                   generated_source=facts["generated_source"],
                                   porcelain=(working_tree_status()
                                              if payload.get("evidence_paths")
                                              else None),
                                   shallow_state=facts["blast_state"],
                                   blast_forecast_live=facts["blast_forecast"],
                                   blast_history=facts["blast_history"])
    if a.json:
        out = dict(rec)
        if advisories:
            # SI-3 (ADR-034): the machine-readable surface -- the echoed
            # record (NOT the ledger line) carries the advisory messages,
            # so a --json consumer never loses them to swallowed stderr
            # (the QB-011 class).
            out["advisories"] = advisories
        print(json.dumps(out))
    else:
        print(rec["id"])
    block = render_advisory_block(advisories)
    if block:
        print(block, file=sys.stderr)

def citation_sweep(cid, orphan_basis):
    """Shell orchestration shared by `verdict retracted` and `done
    --cancel`: voices the SI-4 notices, fails CLOSED on unavailable git
    (the one earned exception -- the verb is terminal and the human is
    already mid-ceremony), returns the blocking paths (possibly [])."""
    globs, source, err = load_citation_scope()
    if err:
        sys.exit(err)  # R14a: cli-level exit, loader message verbatim
    if source == "empty":
        return []
    if source == "default":
        print(f"truth: advisory: no {CITATION_SCOPE_REL} -- the citation "
              "sweep runs against the built-in default scope "
              f"({','.join(CITATION_SCOPE_DEFAULT)}); commit the file to "
              "declare this repo's own (ADR-036)", file=sys.stderr)
    else:
        notice = dead_scope_notice(globs, source, tracked_files())
        if notice:
            print(f"truth: advisory: {notice}", file=sys.stderr)
    hits, reason = citation_grep(cid)
    if reason is not None:
        if orphan_basis:
            return []
        sys.exit(f"truth: cannot verify citations -- {reason}. Retraction "
                 "is rare and human-gated: run it where the corpus is "
                 "greppable (ADR-036; fails CLOSED by design)")
    return citation_block_paths(hits, globs)

def cmd_citations(a):
    """ADR-036 preflight: read-only, no ceremony. A batch sweep runs one
    preflight pass, then per-id ceremonial verdicts on the clean set --
    a multi-id ack stays refused on principle (ADR-011: one typed id
    authorizes one tombstone). Exit 0 = nothing cited inside the scope;
    CITATIONS_EXIT_CITED = at least one id is."""
    # Input hygiene (ADR-036, no new decision): the sweep takes LEDGER
    # ids, so anything else is a question nobody asked -- `citations '#'`
    # used to grep the literal token across the whole corpus and answer
    # "clean" about it. Read-only, but it launders junk into a corpus
    # sweep and prints a verdict-shaped line about a non-id. Validated
    # BEFORE any sweep and for EVERY arg: a batch is one preflight pass,
    # so one bad token refuses the whole invocation -- nothing swept.
    # wk-hex8 is legitimate: `done --cancel` sweeps issue tombstones too.
    # fullmatch, not match: `$` also matches before a trailing newline,
    # and "tr-deadbeef\n<junk>" must not pass for a bare id.
    for cid in a.ids:
        if not (ID_RE.fullmatch(cid) or WK_ID_RE.fullmatch(cid)):
            # SI-3: a hostile arg is echoed control-escaped.
            sys.exit(f"truth: not a ledger id: '{_escape_ctrl(cid)}' -- "
                     "citations sweeps ledger ids only (tr-hex8, or "
                     "wk-hex8 for an issue tombstone); nothing was swept "
                     "(ADR-036)")
    globs, source, err = load_citation_scope()
    if err:
        sys.exit(err)  # R14a: cli-level exit, loader message verbatim
    if source == "default":
        print(f"truth: advisory: no {CITATION_SCOPE_REL} -- sweeping the "
              f"built-in default scope ({','.join(CITATION_SCOPE_DEFAULT)})",
              file=sys.stderr)
    elif source == "file":
        notice = dead_scope_notice(globs, source, tracked_files())
        if notice:
            print(f"truth: advisory: {notice}", file=sys.stderr)
    out, any_cited = {}, False
    for cid in a.ids:
        if source == "empty":
            out[cid] = []
            continue
        hits, reason = citation_grep(cid)
        if reason is not None:
            sys.exit(f"truth: cannot verify citations -- {reason}")
        blocking = citation_block_paths(hits, globs)
        out[cid] = blocking
        any_cited = any_cited or bool(blocking)
    if a.json:
        print(json.dumps(out))
    else:
        for cid in a.ids:
            print(f"{cid}: " + (", ".join(_escape_ctrl(p) for p in out[cid])
                                if out[cid] else "clean"))
    sys.exit(CITATIONS_EXIT_CITED if any_cited else 0)

def cmd_verdict(a):
    events = load_events()          # ADR-051: the refresh readers need it
    claims, _ = fold(events)
    if a.claim_id not in claims:
        sys.exit(f"truth: unknown claim {a.claim_id}")
    if claims[a.claim_id]["status"] == "retracted":
        sys.exit(f"truth: {a.claim_id} is retracted -- terminal state (G12). "
                 "File a new claim instead.")
    if a.mechanical and (a.recheck or a.verdict != "diverge"):
        sys.exit("truth: --mechanical only annotates a manual diverge "
                 "(ADR-012: it says the recipe changed, not reality)")
    observed = None   # ADR-051: set only on the manual-agree path below
    if getattr(a, "refresh_evidence", None) and a.recheck:
        # --recheck never files an agree (a matching hash is reported,
        # never filed), so there is no anchor advance for a refresh to
        # accompany. Refused rather than silently ignored -- the
        # --cause/--successor precedent (ADR-049).
        sys.exit("truth: --refresh-evidence does not accompany --recheck "
                 "(ADR-051: a recheck never files an agree, so no anchor "
                 "advances; run the recheck, then file your judgment)")
    if (a.cause or a.successor) and (a.recheck or a.verdict != "retracted"):
        # ADR-049: only the terminal verb kills a belief. `--recheck`
        # can never produce a retraction (recheck_verdict returns
        # diverge/cannot_verify only), so this covers it too rather
        # than letting the flags be silently ignored there.
        sys.exit("truth: --cause/--successor only accompany a manual "
                 "retraction (ADR-049: only the terminal verb kills a "
                 "belief; a diverge or cannot_verify says its own why "
                 "in --basis and stays recoverable)")
    if a.recheck:
        ev = claims[a.claim_id]["claim"]["payload"].get("evidence")
        if not ev:
            verdict, basis = NO_EVIDENCE_VERDICT
        else:
            # ADR-009: recheck executes the AUTHOR's command in THIS
            # session -- never run what the screen rejects. Records are
            # rescreened against the current allowlist (they may predate
            # the screen or have been appended raw); screened=false is
            # an author's own admission and is final.
            if ev.get("screened") is False:
                screen_err = ("filed with --evidence-unsafe-ok "
                              "(evidence.screened=false)")
            else:
                screen_err = screen_evidence_command(ev["command"],
                                                     load_allowlist(),
                                                     denylist=load_denylist())
            if screen_err:
                sys.exit(f"truth: {a.claim_id}: recheck will not execute "
                         f"this evidence command -- {screen_err}. If you "
                         "trust it, run it yourself and file a manual "
                         "verdict with a basis naming what you ran "
                         "(ADR-009). Nothing was filed.")
            digest, rc = run_evidence(ev["command"])
            # ADR-051: compare against the EFFECTIVE capsule -- the
            # claim's own, with output_hash/returncode overridden by the
            # newest evidence_refresh. Without this a refreshed claim
            # would keep auto-diverging against its original hash, which
            # is the very state the refresh exists to leave.
            verdict, basis = recheck_verdict(
                effective_evidence(ev, latest_evidence_refresh(events,
                                                               a.claim_id)),
                digest, rc)
        if verdict == "agree":
            # A matching hash is a report, not a judgment: filing agree here
            # would commit the verifier to a verdict before the
            # interpretation step, and force protocol-obedient verifiers to
            # double-file. Only the mechanical negative outcomes (diverge,
            # cannot_verify) are objective enough to auto-file.
            out = {"claim": a.claim_id, "recheck": "agree", "filed": False}
            print(json.dumps(out) if a.json else
                  f"{a.claim_id} recheck: hash matches -- nothing filed. If "
                  "the evidence also supports the claim's TEXT, file your "
                  f"judgment: truth verdict {a.claim_id} agree --basis "
                  "'<what you checked>'")
            return
    else:
        if not a.verdict or not a.basis:
            sys.exit("truth: manual verdicts require <verdict> and --basis")
        if a.verdict == "retracted":
            # ADR-049 FIRST -- deliberately BEFORE the ADR-011 ceremony.
            # It is a pure argument check (no I/O, no ledger read beyond
            # the fold already in hand), and a malformed invocation must
            # never consume a typed-id confirmation: making the human
            # re-type the id because a flag was missing would degrade
            # exactly the ceremony ADR-011 exists to make deliberate.
            # This is `verdict`'s own ordering rule, the one ADR-043's
            # L2-F6 propagated to `done`: cheap argument checks precede
            # the tombstone ceremony.
            err = retraction_cause_error(a.cause, a.successor,
                                         a.claim_id, claims)
            if err:
                sys.exit(err)
            err = human_ack_error(a.claim_id, "claim retraction")
            if err:
                sys.exit(err)
            # ADR-036: after the ADR-011 ceremony, before the append --
            # refuse while the id is cited inside the scope. The refusal
            # deliberately does NOT name its override (ADR-011's surface
            # rule: bypasses live in --help and the README, not in error
            # paths agents hit).
            blocking = citation_sweep(a.claim_id, a.orphan_ok)
            if blocking and not a.orphan_ok:
                # SI-3: git-emitted names render escaped (with -z they
                # arrive raw, so a hostile filename could otherwise
                # inject terminal escapes into this listing)
                listing = "\n".join(f"  {_escape_ctrl(p)}" for p in blocking)
                print(f"truth: retraction blocked -- {a.claim_id} is "
                      f"cited by {len(blocking)} scope-covered file(s) "
                      f"(ADR-036):\n{listing}\n  Swap each citation to "
                      "the successor claim first, then retract.",
                      file=sys.stderr)
                sys.exit(CITATIONS_EXIT_CITED)
        elif a.orphan_ok:
            sys.exit("truth: --orphan-ok only accompanies a retraction "
                     "(ADR-036: it excuses orphaned citations, which "
                     "only the terminal verb creates)")
        if a.verdict == "agree" \
                and claims[a.claim_id]["claim"].get("session") == session() \
                and os.environ.get("TRUTH_SELF_VERDICT") != "1":
            # ADR-010: asymmetric by design -- self-diverge and
            # self-cannot_verify run against interest and stay allowed.
            sys.exit(f"truth: agree on a claim this same session filed is "
                     "self-verification -- the independence seam (G11) "
                     "exists because authors share their own blind spots "
                     "(ADR-010). Dispatch it to a fresh session instead: "
                     f"scripts/truth dispatch {a.claim_id}")
        # ADR-051: the capsule-coherence gate. An agree on a path-claim
        # advances the effective anchor (F2) while the capsule stays in
        # the immutable claim record -- so an agree filed over a changed
        # output silently makes the claim permanently un-recheckable.
        # Run the command ONCE here (the shell gathers; the decision is
        # capsule_coherence_error's) and refuse the orphaning agree
        # unless the verifier states why the changed output still
        # supports the sentence. Placed AFTER the ADR-010 seam
        # deliberately: a self-verification must be refused before any
        # command runs on its behalf.
        cap = claims[a.claim_id]["claim"]["payload"].get("evidence") or {}
        refresh = latest_evidence_refresh(events, a.claim_id)
        eff_cap = effective_evidence(cap, refresh)
        observed = None
        if a.verdict == "agree" and cap.get("command") \
                and claims[a.claim_id]["claim"]["payload"].get(
                    "evidence_paths"):
            # Screened exactly as recheck screens it (ADR-009/029: the
            # screen gates execution, and a second screen implementation
            # is forbidden). A refusal leaves `observed` None and the
            # gate abstains -- an unscreenable command can never be
            # rechecked anyway, so there is no capsule to keep fresh.
            if cap.get("screened") is not False and not \
                    screen_evidence_command(cap["command"], load_allowlist(),
                                            denylist=load_denylist()):
                observed = run_evidence(cap["command"])
        err = capsule_coherence_error(
            a.verdict, claims[a.claim_id]["claim"]["payload"], observed,
            a.refresh_evidence, eff_cap)
        if err:
            sys.exit(err)
        verdict, basis = a.verdict, a.basis
    payload = {"claim": a.claim_id, "verdict": verdict, "basis": basis}
    if verdict == "agree" and getattr(a, "refresh_evidence", None) \
            and observed is not None:
        # ADR-051: the refresh records an ACT -- the capsule this
        # session actually observed, plus the judgment that it still
        # supports the sentence. effective_evidence() is its reader,
        # which is what admits the field under ADR-046's envelope rule.
        payload["evidence_refresh"] = {
            "output_hash": "sha256:" + observed[0],
            "returncode": observed[1],
            "basis": a.refresh_evidence}
    if verdict == "retracted" and a.cause:
        # ADR-049: the cause and its successor pointer. Not report-only
        # metadata -- retraction_cause_error BLOCKS on them, which is
        # what admits them under ADR-046's envelope rule.
        payload["cause"] = a.cause
        if a.successor:
            payload["successor"] = a.successor
    if verdict == "retracted" and a.orphan_ok:
        # ADR-036: deliberate orphaning, stored and counted (CC-2).
        # Decay: declined -- a tombstone is terminal, nothing re-asks.
        payload["orphan_basis"] = a.orphan_ok
    if a.mechanical:
        payload["subtype"] = "mechanical"
    if verdict == "agree" and \
            claims[a.claim_id]["claim"]["payload"].get("evidence_paths"):
        payload["anchor_commit"] = head_commit()  # re-anchor: durable re-verify
    rec = append_record("verdict", payload)
    print(json.dumps(rec) if a.json else f"{a.claim_id} -> {verdict}")

def cmd_ttl_scan(a):
    """ADR-019/G10: materialize TTL expiry, and nothing else.

    SUCCESSOR TO `invalidate-scan` (refactor step 2.6). The old
    verb read three signals -- TTL, anchor reachability, evidence-path
    diffs -- and the last two are exactly the proxy this refactor
    retires: 1997 records at a 3.6% positive predictive value, replaced
    by `truth reproduce`, which asks the semantic question (does the
    recorded capsule still produce its recorded output?) at ~8ms per
    capsule. Those two strategies are gone from INVALIDATORS, so this
    verb is what remained: the CLOCK.

    It has to remain, and could not be folded into `reproduce`. TTL
    expiry is the one thing reproduction provably cannot detect -- a
    claim whose TTL runs out today reproduces perfectly today -- and
    this is still the ONLY clock reader in the system: the fold stays
    pure and confluent by demoting to stale off the emitted record
    rather than evaluating a TTL itself. Retiring it would have left
    ADR-019 with a reader and no writer."""
    claims, _ = fold(load_events())
    head = head_commit() or "0000000"
    now = now_dt()
    hits = []
    for cid, entry in claims.items():
        if entry["status"] not in ACTIVE_STATUSES:
            continue
        # `facts` is vestigial for the clock arm (_ttl_expired reads only
        # the claim's own ts and ttl_days) and is kept as the seam the
        # strategy signature is built on. The per-claim git probes the old
        # verb ran to fill it -- commit_reachable plus a diff against the
        # anchor, once per active claim -- are gone with the strategies
        # that consumed them, which is most of this verb's former cost.
        decision = decide_invalidation(entry, {"head": head}, now)
        if decision:
            append_record("invalidation",
                          {"claim": cid, "commit": head, **decision["payload"]})
            hits.append((cid, decision["label"]))
    if not a.quiet:
        for cid, why in hits:
            print(f"stale: {cid} ({why})")
        print(f"ttl-scan: {len(hits)} claim(s) expired")

def cmd_premise(a):
    # Input hygiene, mirror parity (same class as the citations check,
    # but this verb WRITES): validate_events refuses a premise whose
    # claim or supersedes ref is not tr-hex8, while intake checked
    # neither -- so a normal verb could append, to an APPEND-ONLY file,
    # a record that `truth validate` and the commit gate then reject.
    # Intake may not be weaker than the mirror. SHAPE only: an
    # unknown-but-well-formed id stays legal (doctor's dangling-premise
    # WARN and `issue --premise`'s warning are the deliberate treatment
    # of that case, ADR-001). The issue ref stays free-form -- external
    # tracker ids are the point of the adapter seam (ADR-004).
    for label, val in (("claim id", a.claim_id),
                       ("--supersedes", a.supersedes)):
        if val is not None and not ID_RE.fullmatch(val):
            sys.exit(f"truth: not a claim id: '{_escape_ctrl(val)}' -- "
                     f"premise {label} takes tr-hex8; validate refuses "
                     "the record this would append (ADR-013). Nothing "
                     "was filed.")
    payload = {"issue": a.issue, "claim": a.claim_id}
    if a.supersedes:
        # R14b: the ADR-013 rule ladder lives in supersede_error (core);
        # this shell gathers the folds, applies the one I/O effect (the
        # ADR-017/C3 human ack for a retracted premise -- without it,
        # any agent could spend a human's P0 block via a normal CLI
        # verb, no forgery needed), and exits the refusal.
        events = load_events()
        claims, premises = fold(events)
        issues = fold_issues(events)
        premises = merge_premises(premises, issue_premises(issues))
        premises = apply_supersedes(premises, fold_supersedes(events))
        err = supersede_error(a.issue, a.supersedes, a.claim_id, claims,
                              premises.get(a.issue, []))
        if err == RETRACTED_NEEDS_ACK:
            err = human_ack_error(a.supersedes,
                                  "superseding a retracted premise")
        if err:
            sys.exit(err)
        payload["supersedes"] = a.supersedes
    rec = append_record("premise", payload)
    print(json.dumps(rec) if a.json else rec["id"])

def cmd_contradicts(a):
    events = load_events()
    claims, _ = fold(events)
    # R14b: the issue #4 checks live in contradicts_intake_error (core).
    err = contradicts_intake_error(a.claim_a, a.claim_b, claims, events)
    if err:
        sys.exit(err)
    if not (a.basis or "").strip():
        sys.exit("truth: --basis is required: state WHY these cannot both "
                 "hold; the sentence is the attackable record (issue #4)")
    rec = append_record("contradicts", {"a": a.claim_a, "b": a.claim_b,
                                        "basis": a.basis})
    both_live = all(claims[c]["status"] == "live"
                    for c in (a.claim_a, a.claim_b))
    state = ("both claims now derive DISPUTED (premised work HOLDs, "
             "specs citing either side fail)" if both_live else
             "edge filed DORMANT (fires only while both sides are live)")
    print(f"{rec['id']}: {a.claim_a} <-x-> {a.claim_b} -- {state}")

def cmd_list(a):
    """FAZA 3 adds `--watch-policy <name>`: which claims stand on a named
    policy. It is the operational question the migration (step 3.3) asks
    on every pass -- "what is on this policy, and what is still freehand?"
    -- and it is also the ADR-046 READER that earns `watch_policy` its
    place in the payload envelope: a field nothing reads is precisely the
    defect instruments/field-consumers.py exists to find, and provenance
    alone would have been exactly that. `--watch-policy -` selects the
    complement: path-carrying claims on NO policy, i.e. the migration
    backlog."""
    claims, _ = fold(load_events())
    now = now_dt()
    want = {f for f in STATUSES if getattr(a, f)}
    wp = getattr(a, "watch_policy", None)
    def _wp_match(payload):
        if wp is None:
            return True
        if wp == "-":            # the backlog: watches paths, names no policy
            return bool(payload.get("evidence_paths")) \
                and not payload.get("watch_policy")
        return payload.get("watch_policy") == wp
    rows = [{"id": cid, "status": e["status"], "age_days": age_days(e, now),
             "tier": e["claim"]["payload"].get("cost_tier"),
             "class": e["claim"]["payload"].get("evidence_class"),
             "watch_policy": e["claim"]["payload"].get("watch_policy"),
             "text": e["claim"]["payload"].get("text")}
            for cid, e in claims.items()
            if (not want or e["status"] in want)
            and _wp_match(e["claim"]["payload"])]
    if a.json:
        print(json.dumps(rows, indent=2))
    else:
        for r in rows:
            print(f"{r['id']}  {r['status']:<13} {r['tier']:<3} "
                  f"{r['class']:<10} {r['text']}")

def cmd_queue(a):
    claims, _ = fold(load_events())
    rows = queue_rows(claims, now_dt())
    if a.json:
        print(json.dumps(rows, indent=2))
    elif not rows:
        print("queue empty: no divergence, no stale P0/P1, no unverifiable P0")
    else:
        for r in rows:
            age = f"{r['age_days']}d" if r["age_days"] is not None else "?"
            print(f"{r['id']}  {r['tier']:<3} {r['status']:<13} age {age:<5} "
                  f"{r['reason']}: {r['text']}")

# ------------------------------------------------ work kernel commands (ADR-002)

def cmd_issue(a):
    events = load_events()
    issues = fold_issues(events)
    claims, _ = fold(events)
    deps = split_csv(a.deps)
    unknown_deps = [d for d in deps if d not in issues]
    if unknown_deps:
        # Deps must reference existing wk- issues. Because an issue cannot
        # name an id that does not exist yet, CLI-filed dep graphs are
        # acyclic by construction -- this rejection IS the filing-time
        # cycle defense (ADR-002).
        sys.exit(f"truth: unknown dep(s): {', '.join(unknown_deps)} -- deps "
                 "must reference existing wk- issues")
    premises = list(dict.fromkeys(a.premise or []))
    unknown_prem = [c for c in premises if c not in claims]
    if unknown_prem:
        print(f"warning: premise claim(s) not in ledger: "
              f"{', '.join(unknown_prem)} -- this issue will be HELD until "
              "they exist (ADR-001: missing blocks)", file=sys.stderr)
    if not premises:
        print("warning: no --premise given -- this issue is not protected "
              "by the ledger; if it stands on any repository fact, link it "
              "(premise-at-birth, ADR-002)", file=sys.stderr)
    payload = {"title": a.title, "text": a.text or "",
               "deps": deps, "premises": premises}
    # ADR-014: the finish line is declared BEFORE the work happens
    # (accept-at-birth, the completion mirror of premise-at-birth) --
    # attackable at review time, like scope_basis.
    if a.accept_kind and not a.accept_cmd:
        sys.exit("truth: --accept-kind names an oracle shape with no "
                 "oracle -- give --accept-cmd too (ADR-014)")
    if a.accept_cmd:
        err = screen_accept_command(a.accept_cmd,
                                    load_allowlist(ACCEPT_ALLOW_REL))
        if err and not a.accept_unsafe_ok:
            sys.exit("truth: " + err)
        if err:
            print("warning: acceptance oracle filed unscreened "
                  "(accept.screened=false) -- `done` will refuse to "
                  "execute it, and closing will need --accept-unsafe-ok, "
                  "stamped on the close event (ADR-014)", file=sys.stderr)
        payload["accept"] = {"command": a.accept_cmd,
                             "kind": a.accept_kind or "verification",
                             "screened": err is None}
    rec = append_record("issue", payload, prefix="wk-")
    print(json.dumps(rec) if a.json else rec["id"])

def _issue_or_exit(issues, wid):
    if wid not in issues:
        sys.exit(f"truth: unknown issue {wid}")
    return issues[wid]["status"]

def cmd_start(a):
    issues = fold_issues(load_events())
    status = _issue_or_exit(issues, a.issue_id)
    tserr = issue_event_ts_error(issues[a.issue_id]["issue"], now_dt())
    if tserr:
        sys.exit(f"truth: {tserr}")
    event = "released" if a.release else "claimed"
    err = issue_event_error(status, event)
    if err:
        sys.exit(f"truth: {err}")
    append_record("issue_event", {"issue": a.issue_id, "event": event,
                                  "basis": a.basis or ""})
    print(f"{a.issue_id} -> {event}")

def cmd_done(a):
    events = load_events()
    issues = fold_issues(events)
    status = _issue_or_exit(issues, a.issue_id)
    tserr = issue_event_ts_error(issues[a.issue_id]["issue"], now_dt())
    if tserr:
        sys.exit(f"truth: {tserr}")
    if a.cancel and a.reopen:
        sys.exit("truth: --cancel and --reopen are mutually exclusive")
    event = "cancelled" if a.cancel else "reopened" if a.reopen else "closed"
    if event != "cancelled" and getattr(a, "orphan_ok", None):
        sys.exit("truth: --orphan-ok only accompanies --cancel "
                 "(ADR-036: the issue tombstone)")
    # L2-F6 (licensed reorder): the --basis requirement and the
    # transition check are pure of the tombstone ceremony, so they run
    # BEFORE the human-ack prompt / citation sweep -- cmd_verdict's
    # order, applied to its twin. Refusal strings unchanged.
    if not a.basis:
        sys.exit(f"truth: '{event}' requires --basis (cite what you did, "
                 "never a vibe)")
    err = issue_event_error(status, event)
    if err:
        sys.exit(f"truth: {err}")
    if event == "cancelled":
        err = human_ack_error(a.issue_id, "issue cancellation")
        if err:
            sys.exit(err)
        # ADR-036: the issue tombstone runs the identical citation sweep.
        blocking = citation_sweep(a.issue_id, a.orphan_ok)
        if blocking and not a.orphan_ok:
            listing = "\n".join(f"  {_escape_ctrl(p)}" for p in blocking)  # SI-3
            print(f"truth: cancellation blocked -- {a.issue_id} is cited "
                  f"by {len(blocking)} scope-covered file(s) (ADR-036):\n"
                  f"{listing}\n  Swap each citation first, then cancel.",
                  file=sys.stderr)
            sys.exit(CITATIONS_EXIT_CITED)
    claim_payload, claim_facts = None, None
    if a.claim_text:
        if event != "closed":
            sys.exit("truth: --claim only accompanies a plain close "
                     "(claim-at-death records what the finished work made true)")
        claims, _ = fold(events)
        # Validate and run evidence BEFORE any append: both records or
        # neither (ADR-002). build_claim_payload sys.exits on any failure.
        claim_payload, claim_facts = build_claim_payload(
            a.claim_text, a.evidence_class, a.evidence_cmd, a.paths,
            a.tier, a.ttl_days, a.claim_basis, a.single_run,
            a.duplicate_ok, claims, scope_basis=a.scope_ok,
            unsafe_ok=a.evidence_unsafe_ok,
            evidence_exit_basis=a.evidence_exit_ok,
            generated_basis=a.generated_ok,
            watch_policy=getattr(a, "watch_policy", None),
            paths_basis=getattr(a, "paths_ok", None))
    # ADR-014: the acceptance oracle gates a plain close -- it runs after
    # the cheap intake checks and before ANY append (both-or-neither
    # extends to the oracle). --cancel/--reopen skip it: killing or
    # reviving work must not require its finish line to pass.
    accept_note = None
    accept = issues[a.issue_id]["issue"]["payload"].get("accept")
    if event == "closed" and accept:
        err = (None if accept.get("screened")
               else "the oracle was filed unscreened (accept.screened=false)")
        if err is None:
            # Re-screen against the CURRENT allowlist: it is the committed
            # policy NOW, not at filing time (the ADR-009 intake-AND-
            # recheck posture).
            err = screen_accept_command(accept.get("command", ""),
                                        load_allowlist(ACCEPT_ALLOW_REL))
        if err:
            if not a.accept_unsafe_ok:
                sys.exit(f"truth: refusing to execute the acceptance "
                         f"oracle -- {err}\n  Fix {ACCEPT_ALLOW_REL} (or "
                         "the oracle) and re-run; --accept-unsafe-ok "
                         "closes WITHOUT running it and stamps "
                         "executed=false on the event (ADR-014)")
            accept_note = {"command": accept.get("command"),
                           "kind": accept.get("kind", "verification"),
                           "executed": False, "screened": False}
        else:
            # ADR-044 (P4): the execution itself is shellio's -- cli holds
            # the decision and the refusal text, not the subprocess.
            rc, combined = run_accept_command(accept["command"], repo_root())
            if rc != 0:
                tail = "\n".join(combined.splitlines()[-15:])
                sys.exit(f"truth: acceptance oracle failed (exit "
                         f"{rc}) -- {a.issue_id} stays {status}; "
                         "the finish line is the command, not the "
                         f"narrative (ADR-014)\n  $ {accept['command']}\n"
                         f"{tail}")
            accept_note = {"command": accept["command"],
                           "kind": accept.get("kind", "verification"),
                           "executed": True, "returncode": 0}
    event_payload = {"issue": a.issue_id, "event": event, "basis": a.basis}
    if event == "cancelled" and a.orphan_ok:
        event_payload["orphan_basis"] = a.orphan_ok  # ADR-036, CC-2
    if accept_note:
        event_payload["accept"] = accept_note
    # "Both records or neither" (ADR-002/ADR-014) is LITERAL: the claim
    # and the close event land in one write(2) via append_records, so no
    # crash window can orphan a completion claim against an open issue.
    batch = ([("claim", claim_payload, "tr-")] if claim_payload else []) \
        + [("issue_event", event_payload, "tr-")]
    recs = append_records(batch)
    claim_rec = recs[0] if claim_payload else None
    advisories = []
    if claim_payload:
        # ADR-034: claim-at-death shares build_claim_payload, so it earns
        # the identical post-append advisory block (ADR-032 decay notice,
        # hollow-VERIFIED warning, FS-1 note) -- one CC-1 block, stderr.
        advisories = intake_advisories(
            events, a.tier, a.ttl_days, a.scope_ok, a.evidence_class,
            claim_payload, generated_ok=a.generated_ok, claims=claims,
            generated_source=claim_facts["generated_source"],
            porcelain=(working_tree_status()
                       if claim_payload.get("evidence_paths") else None),
            shallow_state=claim_facts["blast_state"],
            blast_forecast_live=claim_facts["blast_forecast"],
            blast_history=claim_facts["blast_history"])
    if a.json:
        # SI-3, extended to claim-at-death (P2): one machine-readable
        # object -- the echoed claim record (NOT the ledger line) plus
        # the advisory messages, so a --json consumer never loses them
        # to swallowed stderr (the QB-011 class; cmd_claim's convention).
        out_obj = {"issue": a.issue_id, "event": event,
                   "claim": claim_rec, "accept": accept_note}
        if advisories:
            out_obj["advisories"] = advisories
        print(json.dumps(out_obj))
    else:
        out = f"{a.issue_id} -> {event}"
        if accept_note:
            out += (" (acceptance passed)" if accept_note["executed"]
                    else " (acceptance NOT executed -- unscreened oracle)")
        if claim_rec:
            out += f"; filed {claim_rec['id']}"
        print(out)
    block = render_advisory_block(advisories)
    if block:
        print(block, file=sys.stderr)

def cmd_issues(a):
    events = load_events()
    issues = fold_issues(events)
    if a.ready_json:
        # The E1 adapter contract, emitted by the kernel itself: pipe into
        # `truth ready --stdin` and the join must equal the native path.
        print(json.dumps(native_ready_issues(issues)))
        return
    claims, premises = fold(events)
    premises = merge_premises(premises, issue_premises(issues))
    # ADR-013: apply the redirects, exactly as `ready` and `impact` do. The
    # effective premise list is DERIVED, like every status in this system,
    # and three consumers of merge_premises() applying the derivation while
    # a fourth did not is the drift shape ADR-043 named -- two verbs of one
    # CLI answering differently about one fact. Observed on the kuchnie
    # ledger: wk-cc0daf81 listed both tr-bd0ba211 (the successor) and
    # tr-8ed0a7ff (its RETRACTED predecessor) here, while `ready` correctly
    # honoured the redirect, so an operator reading `issues` saw a dead
    # premise the machinery had already re-targeted.
    # The raw links are not lost: they are permanent records in the ledger
    # (the premise-at-birth payload, the redirect record, and the
    # replacement claim are three separate lines), so `git log` and the
    # ledger itself remain the history. This verb reports EFFECTIVE state,
    # which is what governs readiness.
    premises = apply_supersedes(premises, fold_supersedes(events))
    rows = []
    for wid, e in sorted(issues.items()):
        p = e["issue"]["payload"]
        rows.append({"id": wid, "status": e["status"],
                     "title": p.get("title"), "deps": p.get("deps", []),
                     "premises": premises.get(wid, []),
                     "accept": p.get("accept")})
    if a.json:
        print(json.dumps(rows, indent=2))
    else:
        for r in rows:
            extra = ""
            if r["deps"]:
                extra += f"  deps: {','.join(r['deps'])}"
            if r["premises"]:
                extra += f"  premises: {','.join(r['premises'])}"
            if r["accept"]:
                extra += f"  accept: {r['accept'].get('kind')}"
            print(f"{r['id']}  {r['status']:<9} {r['title']}{extra}")

def cmd_ready(a):
    events = load_events()
    claims, premises = fold(events)
    issues_fold = fold_issues(events)
    native = native_ready_issues(issues_fold) if issues_fold else None
    # A1: the loader returns its refusal; the shell exits it, unchanged.
    issues, err = tracker_issues(a, native)
    if err:
        sys.exit(err)
    # premise-at-birth links apply whichever source delivered the issues,
    # so native, --stdin, and adapter paths join identically (ADR-002);
    # redirects apply after the merge so payload links redirect too (ADR-013)
    premises = merge_premises(premises, issue_premises(issues_fold))
    premises = apply_supersedes(premises, fold_supersedes(events))
    ready, annotated = join_ready(issues, claims, premises)
    if a.json:
        print(json.dumps(ready, indent=2))
    else:
        for i in ready:
            w = (f"  [warn: {'; '.join(i['_truth']['warnings'])}]"
                 if i["_truth"]["warnings"] else "")
            print(f"{i.get('id')}  {i.get('title', i.get('text', ''))}{w}")
        for i in annotated:
            if not i["_truth"]["ready"]:
                print(f"HELD {i.get('id')}  broken premises: "
                      f"{', '.join(i['_truth']['broken_premises'])}")

def _events_at_ref_or_exit(ref):
    """A1: events_at_ref returns (events, err); the exit-2 usage contract
    is `baseline`'s own (it is in the verb's --help), so it is enforced
    here. Both call sites go through this, because two hand-written
    copies of one exit rule is how the copies drift."""
    events, err = events_at_ref(ref)
    if err:
        print(err, file=sys.stderr)
        sys.exit(2)
    return events

def cmd_baseline(a):
    snap_a = baseline_snapshot(_events_at_ref_or_exit(a.ref))
    if not a.diff:
        snap_a["ref"] = a.ref
        snap_a["commit"] = _short_sha(a.ref)
        if a.json:
            print(json.dumps(snap_a, indent=2, sort_keys=True))
        else:
            c, i = snap_a["claims"], snap_a["issues"]
            fmt = lambda d: ", ".join(f"{v} {k}" for k, v in d.items()) or "none"
            print(f"baseline {a.ref} ({snap_a['commit']}): "
                  f"{snap_a['records']} records")
            print(f"claims: {fmt(c['by_status'])}  "
                  f"[{' / '.join(f'{k} {v}' for k, v in c['by_tier'].items())}]")
            print(f"issues: {fmt(i['by_status'])}")
        return
    snap_b = baseline_snapshot(_events_at_ref_or_exit(a.diff))
    delta = baseline_diff(snap_a, snap_b)
    delta["from"], delta["to"] = a.ref, a.diff
    disappeared = any(delta[k]["disappeared"] for k in ("claims", "issues"))
    if a.json:
        print(json.dumps(delta, indent=2, sort_keys=True))
    else:
        print(f"baseline diff {a.ref} -> {a.diff} "
              f"({delta['records_delta']:+d} records)")
        for kind in ("claims", "issues"):
            d = delta[kind]
            if d["born"]:
                by = {}
                for _, st in d["born"].items():
                    by[st] = by.get(st, 0) + 1
                print(f"{kind} born: {len(d['born'])} "
                      f"({', '.join(f'{v} {k}' for k, v in sorted(by.items()))})")
                for i_, st in d["born"].items():
                    print(f"  + {i_}  {st}")
            for pair, ids in d["transitions"].items():
                print(f"{kind} {pair}: {len(ids)}")
                for i_ in ids:
                    print(f"  ~ {i_}")
            for i_, st in d["disappeared"].items():
                print(f"{kind} DISAPPEARED (was {st}): {i_} -- a record "
                      "present at the older ref is gone: history was "
                      "rewritten or the refs diverge (10007 omission)")
    sys.exit(5 if disappeared else 0)

def cmd_impact(a):
    if a.inverse:
        # Issue #5: the backward slice. Positional paths make no sense
        # here -- the verb enumerates the whole tracked universe; --under
        # is the scoping surface.
        if a.paths:
            sys.exit("truth: --inverse takes no positional paths (it "
                     "enumerates every tracked file; scope with --under)")
        claims, _ = fold(load_events())
        rep = inverse_report(tracked_files(), claims, a.under,
                             a.exclude or [])
        if rep["considered"] == 0:
            # An audit over an empty universe is a misconfiguration
            # (typo'd --under, over-broad --exclude), not a clean pass --
            # exit 0 here would be a permanent false green for any
            # satellite gating on this verb.
            print("truth: --inverse scope matched no tracked files -- "
                  "check --under/--exclude (exit 2: usage, not a clean "
                  "audit)", file=sys.stderr)
            sys.exit(2)
        if a.json:
            print(json.dumps(rep, indent=2))
        else:
            for p in rep["dark"]:
                print(p)
            print(f"impact --inverse: {len(rep['dark'])} of "
                  f"{rep['considered']} tracked file(s) watched by no "
                  "active claim", file=sys.stderr)
        sys.exit(4 if rep["dark"] else 0)
    if a.under or a.exclude:
        sys.exit("truth: --under/--exclude only accompany --inverse")
    if not a.paths:
        sys.exit("truth: give paths to query, or --inverse for the "
                 "backward slice")
    events = load_events()
    claims, premises = fold(events)
    issues = fold_issues(events)
    premises = merge_premises(premises, issue_premises(issues))
    premises = apply_supersedes(premises, fold_supersedes(events))
    rows = impact_report(a.paths, claims, issues, premises)
    if a.json:
        print(json.dumps(rows, indent=2))
    else:
        for r in rows:
            # Refactor step 2.5 changed this line's VERB, because it had
            # become a false prediction. It read "next commit STALES
            # <claim>", and that was true while a path invalidation demoted
            # the claim -- a proxy that was right about 1 time in 8. Nothing
            # stales on a path touch now, so the honest report is what the
            # tool actually knows: this claim WATCHES what you are editing.
            # Whether the fact moved is decided downstream, by `truth
            # reproduce` at the push boundary or by a judge -- and saying so
            # is the point, since the old wording taught readers to treat a
            # 3.6%-precision guess as a verdict.
            line = (f"editing {', '.join(r['touched'])} -> WATCHED BY "
                    f"{r['claim']} ({r['tier']}, {r['status']}): "
                    f"{r['text']}")
            if r["holds"]:
                line += (" -- if that fact moved, ready HOLDs "
                         + ", ".join(r["holds"]))
            print(line)
    sys.exit(3 if rows else 0)

def cmd_dispatch(a):
    claims, _ = fold(load_events())
    if a.claim_id not in claims:
        sys.exit(f"truth: unknown claim {a.claim_id}")
    prompt_path = os.path.join(repo_root(), PROMPT_REL)
    if not os.path.exists(prompt_path):
        sys.exit(f"truth: verifier prompt missing at {PROMPT_REL}")
    with open(prompt_path, encoding="utf-8") as f:
        content = f.read()
    print(dispatch_text(content, claims[a.claim_id]["claim"]))

def cmd_validate(a):
    stream = sys.stdin if a.stdin else None
    events = load_events(stream)
    errors = validate_events(events)
    order_errors, order_warnings = order_check(events)
    errors += order_errors
    for w in order_warnings:
        print("warning: " + w, file=sys.stderr)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        sys.exit(1)
    print(f"validate: {len(events)} record(s) OK")

def cmd_vocab(a):
    """P2 contract layer: emit the machine vocabulary (vocab_report).
    Read verb -- deliberately NOT in WRITE_VERBS, so no commit-gate
    banner: the satellites call this on every sweep, and banner noise
    there would train `2>/dev/null`, hiding real advisories."""
    rep = vocab_report()
    if a.json:
        print(json.dumps(rep))
        return
    for key, val in rep.items():
        body = (",".join(f"{k}->{v}" for k, v in val.items())
                if isinstance(val, dict) else ",".join(val))
        print(f"{key}: {body}")

def cmd_stats(a):
    events = load_events()
    if a.since:
        events = [(n, ev) for n, ev in events
                  if (ev.get("ts") or "") >= a.since]
    # ADR-034: fold ONCE and share. ADR-046 (Tier C): the separation,
    # override-velocity, blast, and concerns sections moved OUT of this
    # verb -- their pure reports stay in truthlib.advisory, driven by the
    # meta-repo's instruments/*.py over `truth ... --json` + the raw
    # ledger. stats keeps exactly what Tier B reads: counts, verdicts,
    # half-life (feeds the FS-1 intake advisory), and queue aging.
    folded = fold(events)
    report = stats_report(events, now_dt(), folded=folded)
    if a.json:
        print(json.dumps(report, indent=2))
        return
    print("claims by status: " + (", ".join(
        f"{k}={v}" for k, v in sorted(report["claims_by_status"].items()))
        or "none"))
    v = report["verdicts"]
    print(f"verdicts: agree={v['agree']} diverge_genuine="
          f"{v['diverge_genuine']} diverge_mechanical="
          f"{v['diverge_mechanical']} cannot_verify={v['cannot_verify']} "
          f"retracted={v['retracted']}")
    if report["half_life"]:
        for tier, h in sorted(report["half_life"].items()):
            print(f"half-life {tier}: median {h['median_days']}d "
                  f"(n={h['n']})")
    else:
        print("half-life: no live->stale observations yet")
    age = report["queue_max_age_days"]
    print(f"queue: {report['queue_size']} item(s)"
          + (f", oldest {age}d" if age is not None else ""))

def cmd_health(a):
    """FAZA 4 step 4.2: one command, one fold, every health section.

    A READ verb -- deliberately NOT in WRITE_VERBS: it files nothing,
    takes no ledger lock, and prints no commit-gate banner.

    IT REPORTS AND REFUSES NOTHING, and that is the design rather than
    timidity. This repository already has surfaces that block -- the
    commit gate, the intake table, `reproduce`'s exit 7/8, the release
    battery -- and each owns a question. A second blocking surface over
    the same facts would be a second place to disagree about them.
    `health` answers "how is this ledger doing", which is not a gate's
    question. Exit is 0 unless the ledger cannot be read.

    --reproduce runs the capsule sweep and folds its counts in. It is
    OPT-IN because it EXECUTES author-recorded commands: a read verb that
    silently ran the repository's own recipes would be a surprising thing
    for `health` to do, and the ADR-009 screen is a boundary a reader
    should cross knowingly. Without it the reproduce section is null and
    the signal says so, rather than implying a clean sweep nobody ran."""
    events = load_events()
    folded = fold(events)
    history, hstate = blast_history()
    policies, _pstate, perr = load_watch_policies()
    reproduce = None
    if a.reproduce:
        sweep = reproduce_sweep(events)
        reproduce = dict(sweep["counts"], examined=sweep["examined"])
    report = health_report(events, now_dt(), folded=folded,
                           history=history if hstate == "ok" else None,
                           history_state=hstate, reproduce=reproduce,
                           watch_policies=None if perr else policies)
    if a.json:
        print(json.dumps(report, indent=2))
        return
    for s in report["signals"]:
        print(f"{'ok  ' if s['level'] == 'ok' else 'WARN'}  {s['code']}: "
              f"{s['detail']}")
    print()
    led = report["ledger"]
    print("claims by status: " + (", ".join(
        f"{k}={v}" for k, v in sorted(led["claims_by_status"].items()))
        or "none"))
    v = led["verdicts"]
    print(f"verdicts: agree={v['agree']} diverge_genuine={v['diverge_genuine']} "
          f"diverge_mechanical={v['diverge_mechanical']} "
          f"cannot_verify={v['cannot_verify']} retracted={v['retracted']}")
    for tier, h in sorted(led["half_life"].items()):
        print(f"half-life {tier}: median {h['median_days']}d (n={h['n']})")
    ov = report["overrides"]
    print(f"overrides: scope={ov['scope_basis_filings']} "
          f"paths={ov['paths_basis_filings']} "
          f"exit={ov.get('exit_overrides', 0)} "
          f"duplicate={ov.get('overridden_duplicates', 0)} "
          f"screened-false={ov.get('screened_false_filings', 0)}")
    rc = report["retractions"]
    print("retraction causes: " + (", ".join(
        f"{k}={v}" for k, v in sorted(rc.get("by_cause", {}).items()))
        or "none"))
    sep = report["separation"]
    print(f"verifier separation: {sep.get('unevidenced', 0)} unevidenced, "
          f"median {sep.get('median_seconds')}s")
    b = report["blast"]
    print(f"churn: floor {b['effective_floor']} ({b['floor_source']}, "
          f"history {b['history_state']})")

def cmd_staling(a):
    """ADR-050: the staling breakdown -- how much of this ledger's
    invalidation traffic was a false alarm, and which kind of watched
    path caused it. Read verb (not in WRITE_VERBS): it derives nothing
    the fold owns and files nothing. Same `--since` window convention as
    `stats` -- the shell filters, the pure report counts what it is
    given."""
    events = load_events()
    if a.since:
        events = [(n, ev) for n, ev in events
                  if (ev.get("ts") or "") >= a.since]
    # ADR-050/ADR-016: a staling is a STATUS transition, and status is
    # defined by the fold's total order -- so the shell sorts before the
    # pure fold counts. --append-order walks the raw file instead, the
    # only supported use being reproduction of a measurement taken that
    # way before this verb existed. The order is stamped on the output:
    # two orders can disagree, so a number that does not say which one
    # produced it is not a result.
    order = "append" if a.append_order else "fold"
    if order == "fold":
        events = sorted(events, key=fold_key)
    report = staling_report(events)
    report["order"] = order
    if a.json:
        print(json.dumps(report, indent=2))
        return
    if not report["stalings"]:
        print("staling: no invalidations in range -- nothing to break down")
        return
    print(f"stalings: {report['stalings']} "
          f"({report['invalidations']} invalidation record(s), "
          f"{report['restaled']} re-staled an already-stale claim) "
          f"[{order} order]")
    print(f"resolved: {report['resolved']}, "
          f"unresolved: {report['unresolved']}")
    print(f"the fact had NOT changed: {report['false_stale']} "
          f"(mechanical {report['mechanical_agree']}, "
          f"human {report['human_agree']})")
    print(f"the fact HAD changed: {report['true_stale']}")
    kinds = ", ".join(f"{r['kind']}={r['stalings']}"
                      for r in report["by_path_kind"]) or "none"
    print(f"triggered by: {kinds}"
          + (f" (+{report['pathless']} with no watched path)"
             if report["pathless"] else ""))

def _capsule_stale_facts(entry, diff_cache, dirty_entries):
    """Gather (SHELL) what capsule_stale_shape decides on: the claim's own
    watched paths changed over effective-anchor..HEAD. Uses the scan's own
    differ and matcher -- changed_files_since + match_paths -- because a
    second differ is exactly the drift ADR-005 catalogued. The per-anchor
    cache matters: a sweep of a repo where many claims share one anchor
    would otherwise fork one `git diff` per claim."""
    cp = entry["claim"]["payload"]
    own = cp.get("anchor_commit")
    effective = entry.get("anchor") or own
    paths = cp.get("evidence_paths", [])
    # ADR-038's own matcher, reused: a watched path dirty in the working
    # tree explains the mismatch outright, and it must be decided even
    # when there is no anchor to diff from.
    dirty = dirty_watch(dirty_entries, paths) if dirty_entries else []
    if not effective:
        return {"shape": "uncommitted" if dirty else None,
                "shape_error": (None if dirty else
                                "the claim carries no anchor to diff from"),
                "watched_dirty": dirty}

    def window(a, b):
        if (a, b) not in diff_cache:
            diff_cache[(a, b)] = changed_files_between(a, b)
        changed, err = diff_cache[(a, b)]
        if changed is None:
            return None, (f"diff {_short_sha(a)}..{_short_sha(b)} failed: "
                          f"{(err or 'unknown')[:120]}")
        return [f for f in changed if match_paths(f, paths)], None

    ahead, err = window(effective, "HEAD")
    if err:
        return {"shape": "uncommitted" if dirty else None,
                "shape_error": err, "watched_dirty": dirty}
    buried = []
    if own and own != effective:
        buried, err = window(own, effective)
        if err:
            # A rewritten or unreachable own-anchor is not a reason to
            # report nothing: the forward window already decides
            # watched-moved, and the remaining two shapes collapse to
            # "cannot tell" rather than to a wrong label.
            return {"shape": ("uncommitted" if dirty
                              else "watched-moved" if ahead else None),
                    "shape_error": err, "watched_touched": ahead,
                    "watched_buried": [], "watched_dirty": dirty}
    return capsule_stale_shape(entry, ahead, buried, dirty)

def reproduce_sweep(events, since=None):
    """The capsule sweep as a FUNCTION, extracted in FAZA 4 step 4.2 so
    `truth health --reproduce` can fold its counts in without owning a
    second copy of it. The body below is `cmd_reproduce`'s, moved
    unchanged; that verb now calls this and keeps every byte of its
    rendering, its --arm filter and its 0/7/8 exit contract.

    Extracted rather than re-implemented for the reason this package
    repeats: a second sweep would answer the same question with its own
    screen, its own triage and its own drift. Returns the report dict."""
    class _A:                       # the two fields the body reads
        pass
    a = _A()
    a.since = since
    if a.since:
        # Same window convention as `stats` and `staling`: the shell
        # filters, and the fold then derives status from what is left --
        # so --since narrows WHICH claims are live, not just the report.
        events = [(n, ev) for n, ev in events
                  if (ev.get("ts") or "") >= a.since]
    claims, _ = fold(events)
    allow, deny = load_allowlist(), load_denylist()
    # F1.1: pin execution to the repo root. Capsules were recorded by
    # `claim` running there; a sweep from a subdirectory would otherwise
    # report drift that is really the caller's cwd.
    root = repo_root()
    rows, counts = [], {arm: 0 for arm in REPRODUCE_ARMS}
    shapes, diff_cache = {}, {}
    # Gathered ONCE, before the loop: the diff windows are
    # commit-to-commit, so without this an uncommitted edit to a watched
    # file lands in `unexplained` -- the arm that is supposed to mean
    # "reads something outside its own watch". Found by running the sweep
    # on the tree that was implementing it.
    porcelain = working_tree_status()
    dirty_entries = parse_porcelain_z(porcelain) if porcelain else []
    for cid, entry in sorted(claims.items()):
        if entry["status"] != "live":
            continue
        d = reproduce_triage(entry)
        if d["arm"] == "execute":
            ev = entry["claim"]["payload"]["evidence"]
            screen_err = screen_evidence_command(ev["command"], allow,
                                                 denylist=deny)
            if screen_err:
                d = reproduce_triage(entry, screen_err=screen_err)
            else:
                digest, rc = run_evidence(ev["command"], cwd=root)
                d = reproduce_triage(entry, recheck=recheck_verdict(
                    effective_evidence(
                        ev, latest_evidence_refresh(events, cid)),
                    digest, rc))
        cp = entry["claim"]["payload"]
        row = {"id": cid, "arm": d["arm"], "detail": d["detail"],
               "tier": cp.get("cost_tier"), "text": cp.get("text"),
               "command": (cp.get("evidence") or {}).get("command")}
        if d["arm"] == "capsule-stale":
            row.update(_capsule_stale_facts(entry, diff_cache,
                                            dirty_entries))
            shapes[row.get("shape")] = shapes.get(row.get("shape"), 0) + 1
        counts[d["arm"]] += 1
        rows.append(row)
    stale_rows = [r for r in rows if r["arm"] == "capsule-stale"]
    # `head` and `dirty` are the reproducibility provenance: two sweeps
    # that disagree are only comparable if they say which tree they ran
    # against (the `staling --append-order` precedent -- a number that
    # does not say how it was produced is not a result).
    return {"examined": len(rows), "counts": counts,
            "capsule_stale_shapes": shapes,
            "head": head_commit(),
            "dirty": (None if porcelain is None else bool(porcelain)),
            "claims": rows}

def cmd_reproduce(a):
    """F1.1: re-run every LIVE claim's evidence capsule and classify what
    came back. Read verb -- deliberately NOT in WRITE_VERBS: it executes
    author-recorded commands and files NOTHING, so it takes no ledger lock
    and prints no commit-gate banner.

    The measurement this verb exists for: `invalidate-scan`'s rule -- a
    watched path moved, so the claim is suspect -- is wrong about seven
    times in eight in this repo, and over half of those false alarms still
    cost a human a read (`truth staling`, ADR-050). Nothing so far
    measures the OTHER error: a claim that is live and whose capsule
    quietly stopped being producible. Every arm below is a population the
    ledger could not previously name.

    Execution goes through the SAME screened path `verdict --recheck` and
    `reaffirm` use -- screen_evidence_command against the CURRENT
    allowlist (committed policy now, not at filing time), then
    run_evidence + recheck_verdict against the ADR-051 effective capsule.
    A second executor or a second matcher is forbidden.

    WHAT THIS MEASURES IS THE WORKING TREE, NOT THE COMMIT. Measured on
    kuchnie: two live claims (`ls kitchen-cam/src/kitchen_cam | sort`,
    `grep -rln recipe kuchnie-core/src/kuchnie_core`) reproduce in a tree
    that carries gitignored __pycache__ directories and do NOT reproduce
    in a clean checkout of the same commit -- their capsules are hostage
    to build artifacts no tripwire watches. No warning is emitted for
    this: an "ignored files present" banner would fire in every repo and
    train `2>/dev/null` (the ADR-046 noise lesson). The report carries
    `head` and `dirty` instead, and F1.3's CI lane -- a clean checkout on
    another machine -- is the mechanism that surfaces it."""
    events = load_events()
    report = reproduce_sweep(events, since=a.since)
    rows = report["claims"]
    # The renderer below reads these three as locals, exactly as it did
    # when the sweep was inline. Rebinding them here (rather than editing
    # ~40 lines of rendering) keeps the extraction a pure MOVE: every byte
    # this verb prints, and its 0/7/8 exit contract, are untouched.
    counts, shapes = report["counts"], report["capsule_stale_shapes"]
    stale_rows = [r for r in rows if r["arm"] == "capsule-stale"]
    if a.json:
        print(json.dumps(report, indent=2))
    else:
        for r in rows:
            if a.arm and r["arm"] != a.arm:
                continue
            print(f"{r['id']}  {r['arm']:<14} {r['detail']}")
            if r["arm"] == "capsule-stale":
                extra = (f"shape={r['shape']}" if r.get("shape")
                         else f"shape=UNKNOWN ({r.get('shape_error')})")
                for label, key in (("watched touched", "watched_touched"),
                                   ("buried", "watched_buried"),
                                   ("dirty", "watched_dirty")):
                    if r.get(key):
                        extra += f", {label}: " + ", ".join(r[key][:5])
                print(f"{'':<16}{extra}")
        print(f"reproduce: {len(rows)} live claim(s) -- "
              + ", ".join(f"{counts[arm]} {arm}" for arm in REPRODUCE_ARMS))
        if shapes:
            print("capsule-stale shapes: "
                  + ", ".join(f"{k or 'unknown'}={v}"
                              for k, v in sorted(shapes.items(),
                                                 key=lambda kv: str(kv[0]))))
    if not rows:
        # ADR-042 rule 2, the reason this verb has an exit code of its
        # own: an instrument that examined nothing has NOT passed. A
        # sweep that silently exits 0 over an empty population is the
        # green-because-it-never-ran failure, and it is indistinguishable
        # from a healthy repo at the CI summary line.
        print("truth: reproduce examined ZERO live claims -- the sweep "
              "measured nothing, which is a failure, not a pass (ADR-042 "
              "rule 2). Check --since, the ledger path, and that this "
              "repo has live claims at all.", file=sys.stderr)
        sys.exit(REPRODUCE_EXIT_EMPTY)
    if stale_rows:
        sys.exit(REPRODUCE_EXIT_STALE)

def cmd_doctor(a):
    """G4: check the INSTALLATION, which the sandboxed canary cannot."""
    root = repo_root()
    fails, warns = [], []
    # --json is a REPORTING layer only (the contract-layer machine
    # surface: one question, one surface). The checks below, their
    # order, their semantics and the exit code are untouched; the three
    # accumulators additionally record {check, detail} so the same run
    # can be rendered as text OR as one object. Text mode prints exactly
    # what it always printed, byte for byte.
    report = {"ok": [], "warn": [], "fail": []}
    as_json = getattr(a, "json", False)
    def ok(name, detail=""):
        report["ok"].append({"check": name, "detail": detail})
        if not as_json:
            print(f"OK    {name}" + (f" -- {detail}" if detail else ""))
    def fail(name, detail):
        fails.append(name); report["fail"].append({"check": name,
                                                   "detail": detail})
        if not as_json:
            print(f"FAIL  {name} -- {detail}")
    def warn(name, detail):
        warns.append(name); report["warn"].append({"check": name,
                                                   "detail": detail})
        if not as_json:
            print(f"WARN  {name} -- {detail}")

    if head_commit():
        ok("repo has commits (anchors resolvable)")
    else:
        fail("repo has commits", "no HEAD -- VERIFIED claims cannot anchor (G1)")

    # ADR-034 fold-once, applied to its last violator (R15): doctor used
    # to load the ledger three times and fold four; the timed block below
    # is now the ONE load and fold, shared by every consumer down-file.
    lp = ledger_path()
    events_d, folded = [], None
    if os.path.exists(lp):
        t0 = time.perf_counter()
        events_d = load_events()
        folded = fold(events_d)
        fold_issues(events_d)
        fold_ms = (time.perf_counter() - t0) * 1000
        errs = validate_events(events_d)
        errs += order_check(events_d)[0]
        if errs:
            fail("ledger validates", f"{len(errs)} schema error(s); run truth validate")
        else:
            ok("ledger validates")
        if fold_ms > FOLD_LATENCY_WARN_MS:
            warn("fold latency", f"{fold_ms:.0f}ms -- the FS-3 scale gate "
                 "tripped: time to implement the fold snapshot cache")
        else:
            ok("fold latency", f"{fold_ms:.0f}ms")
    else:
        fail("ledger exists", f"{LEDGER_REL} missing -- touch it")

    allow = load_allowlist()
    if allow is not None:
        ok("evidence allowlist present")
    else:
        fail("evidence allowlist present",
             f"{EVIDENCE_ALLOW_REL} missing -- VERIFIED intake and recheck "
             "fail closed without it (ADR-009); the template ships a "
             "read-only default")

    # ADR-022: hard-deny baseline catches shells/executors; doctor
    # additionally advises (non-blocking) on grey-zone programs that can
    # execute code or write files but have plausible read-only uses -- the
    # policy stays the consumer's, but an accidental `git`/`python`/`curl`
    # in the allowlist (the H4 class) is surfaced, not silently trusted.
    grey = sorted(set(allow or []) & DOCTOR_GREY_ZONE)
    if grey:
        warn("evidence allowlist grey-zone",
             f"{', '.join(grey)} in {EVIDENCE_ALLOW_REL} can execute code or "
             "write files; confirm each is intended and used read-only, or "
             "move deliberate execution to an acceptance oracle (ADR-014/022)")
    else:
        ok("evidence allowlist grey-zone", "no code-executing programs listed")

    # F3.1: every attestable policy file, and the cross-check that an
    # attested empty list can still be wrong. Runs here rather than at
    # intake because it is a property of the INSTALLATION, which is
    # exactly what doctor is for (G4) -- and because a refusal at filing
    # time would punish the filer for a policy decision that is not
    # theirs to make.
    for rel in ATTESTABLE_POLICY_FILES:
        state = policy_file_state(read_policy_file(rel))
        err = policy_attestation_error(rel, state)
        if err:
            fail(f"policy file attested ({rel})", err)
        elif state == "absent":
            warn(f"policy file attested ({rel})",
                 "not committed -- the check it drives runs dark, and an "
                 "absent file records no decision either way")
        else:
            ok(f"policy file attested ({rel})", state)
    # The cross-check. An attested "nothing here is generated" is a
    # statement about the repository, and the repository can contradict
    # it -- this is the only surface that asks.
    gen_globs, _gen_src, _gen_err = load_generated_globs()
    blind = generated_blind_spot(gen_globs or [], tracked_files())
    if blind:
        warn("generated-paths covers what looks generated",
             f"{len(blind)} tracked file(s) sit under a conventionally "
             f"generated directory that {GENERATED_PATHS_REL} does not "
             f"cover: {', '.join(blind[:5])}"
             + (f" (+{len(blind) - 5} more)" if len(blind) > 5 else "")
             + " -- either list them (ADR-037 then refuses watches on "
               "them) or accept that claims watching them restale on "
               "every regeneration")
    else:
        ok("generated-paths covers what looks generated")

    ga = os.path.join(root, ".gitattributes")
    if os.path.exists(ga) and "claims.jsonl merge=union" in open(ga, encoding="utf-8").read():
        ok("union merge rule present")
    else:
        fail("union merge rule present",
             "add '.truth/claims.jsonl merge=union' to .gitattributes (E3)")

    # Hook detection lives in git_hooks_dir/find_gate_hook (factored for
    # the R2 write-verb banner): core.hooksPath honored, husky `_` shim
    # delegation, directory-named-hook hardening -- one detection, shared.
    hooks_dir, hp_cfg = git_hooks_dir(root)

    # Refactor step 2.6: the second row USED to grep post-merge and
    # post-commit for `invalidate-scan`. That verb is retired, and the row had already
    # gone dark one step earlier: step 2.4 emptied both hooks to `exit 0`
    # under a comment EXPLAINING the removal -- and the comment contains the
    # word `invalidate-scan`, so this one-hop grep kept reporting "post-merge
    # hook enforces INV-C" over a hook that enforces nothing. A check that
    # passes on its own retirement notice is the dark gate this repo exists
    # to refuse. Re-aimed at the successor guarantee: `truth reproduce` at
    # the push boundary, which is what install-hooks.sh now writes.
    for names, needle, purpose in ((("pre-commit",), "check-truth", "INV-A/INV-B"),
                                   (("pre-push",), "reproduce",
                                    "reproduce-on-read (INV-C successor)")):
        hit = find_gate_hook(hooks_dir, names, needle)
        if hit:
            ok(f"{names[0]} hook enforces {purpose}",
               os.path.relpath(hit, root))
            continue
        # ADR-025 (H6): no local hook -- the README allows CI as the other
        # arm of the MUST, so decide it before failing. A CI config naming
        # the gate script passes (self-certified: doctor cannot run the
        # pipeline, only see that it references the gate).
        ci = ci_gate_names(needle, root)
        if ci:
            ok(f"{names[0]} gate enforces {purpose} via CI",
               f"{ci} names {needle} -- CI arm, not locally verifiable")
        else:
            where = os.path.relpath(hooks_dir, root)
            fail(f"{names[0]} hook enforces {purpose}",
                 f"no executable hook invoking {needle} under {where}"
                 + (" -- core.hooksPath is set, so .git/hooks is IGNORED by git"
                    if hp_cfg else "")
                 + f", and no top-level CI config (.github/workflows/*.yml, "
                 f".gitlab-ci.yml, Jenkinsfile, …) names {needle} -- a hook "
                 "OR CI MUST exist, see README Install")

    # ADR-045 (D3): a merge that auto-commits runs pre-merge-commit,
    # NEVER pre-commit -- the exact commit class the union-merge sync
    # story produces, so a locally hook-gated repo without the third
    # hook lands merged ledgers ungated. WARN, not FAIL: consumers who
    # installed hooks before v0.9.29 lack it through no fault
    # (adoption-gated). The check runs only when a pre-commit gate hook
    # is wired LOCALLY: a CI-arm repo (no local hook, gate named in CI)
    # is exempt because its gate runs server-side on push/PR, where a
    # merge commit arrives like any other.
    if find_gate_hook(hooks_dir, ("pre-commit",), "check-truth"):
        pmc = find_gate_hook(hooks_dir, ("pre-merge-commit",),
                             "check-truth")
        if pmc:
            ok("pre-merge-commit hook gates merge commits",
               os.path.relpath(pmc, root))
        else:
            warn("pre-merge-commit hook gates merge commits",
                 "pre-commit is wired but git runs pre-merge-commit "
                 "(not pre-commit) when a merge auto-commits, so a "
                 "union-merged ledger would land ungated -- re-run "
                 "scripts/install-hooks.sh to add the third hook "
                 "(ADR-045)")

    found = [f for f in DISCOVERY_FILES
             if os.path.exists(os.path.join(root, f))
             and "scripts/truth" in open(os.path.join(root, f),
                                         encoding="utf-8", errors="replace").read()]
    if found:
        ok("discovery", f"snippet found in {', '.join(found)}")
    else:
        fail("discovery", "no instruction file mentions scripts/truth -- the "
             f"layer is invisible to agents (G2). Checked: {', '.join(DISCOVERY_FILES)}")

    claims, premises = folded if folded is not None else fold(events_d)
    dangling = [f"{i}->{c}" for i, cs in premises.items() for c in cs if c not in claims]
    if dangling:
        warn("premise integrity", f"dangling premise(s): {', '.join(dangling)}")
    elif premises:
        ok("premise integrity")

    # wk-968bc087: G2's invisibility failure, work-kernel edition. A
    # facts-only ledger is legitimate, so this is a WARN, not a FAIL --
    # but wk- records with no instruction file naming `truth ready`
    # means agents can discover the facts and never the work standing
    # on them.
    if any(ev.get("kind") == "issue" for _, ev in events_d):
        names_ready = [f for f in DISCOVERY_FILES
                       if os.path.exists(os.path.join(root, f))
                       and "truth ready" in open(os.path.join(root, f),
                                                 encoding="utf-8",
                                                 errors="replace").read()]
        if names_ready:
            ok("work-kernel discovery",
               f"`truth ready` named in {', '.join(names_ready)}")
        else:
            warn("work-kernel discovery",
                 "wk- issue records exist but no instruction file names "
                 "`truth ready` -- the work kernel is invisible to agents "
                 f"(G2). Checked: {', '.join(DISCOVERY_FILES)}")

    old = [r_ for r_ in queue_rows(claims, now_dt())
           if r_["age_days"] is not None and r_["age_days"] > QUEUE_AGE_WARN_DAYS]
    if old:
        warn("queue aging", f"{len(old)} item(s) older than "
             f"{QUEUE_AGE_WARN_DAYS}d -- attention debt accruing")
    else:
        ok("queue aging")

    # ADR-046: the ADR-010 "verifier separation" check moved OUT of
    # doctor -- it is a Tier C instrument (the meta-repo's
    # instruments/separation-report.py), not an installation check.

    if as_json:
        # The counts are derived from the SAME lists the exit code reads,
        # so a consumer can trust failures>0 <=> exit 1 without parsing
        # the human summary line (which --json replaces, not augments).
        report["failures"] = len(fails)
        report["warnings"] = len(warns)
        print(json.dumps(report, indent=2))
    else:
        print(f"\ndoctor: {len(fails)} failure(s), {len(warns)} warning(s)")
    sys.exit(1 if fails else 0)

# ---------------------------------------------------------------- main
#
# The verb surface is declared as DATA -- the same trick INTAKE_GATES
# already uses for the gate surface.  One row per verb, `(name, help,
# flags, fn)`, where a flag is the `(args, kwargs)` of a single deferred
# add_argument call.  main() below is the interpreter of that table and
# nothing else.
#
# Order is load-bearing: argparse renders `truth <verb> --help` in
# declaration order and that help is a user-facing surface, so a shared
# group is SPLICED at the position its flags occupied, never appended.
#
# The shared groups are the whole point.  R7 found that `done --claim`
# had silently lost `--json` to a hand-copy, declared exactly ONE group
# once (the claim-intake flags below), and left the other twenty verbs
# hand-copied -- after which `--refresh-evidence` was added by hand.  A
# flag declared once cannot drift between the surfaces that share it; a
# flag copied cannot help but.


def _flag(*args, **kwargs):
    """One deferred `parser.add_argument(*args, **kwargs)`, as data."""
    return (args, kwargs)


# The bare machine-output flag, shared by every verb that emits one.
JSON_FLAG = _flag("--json", action="store_true")

# The event-window flag `stats` and `staling` share verbatim.  NOT
# `reproduce --since`, whose help says a different thing (it narrows
# which claims are live, not just the report), so it stays per-verb.
WINDOW_FLAG = _flag("--since", metavar="ISO_TS",
                    help="only count events with ts >= this ISO timestamp")

# R7: the claim-intake flags `claim` and `done --claim` share verbatim,
# declared once so the two surfaces cannot drift (done had already lost
# --json by hand-copy).  Deliberately per-verb, NOT here: claim's `text`
# positional; --basis vs --claim-basis (done's claim basis must not
# shadow the close's own --basis); --json; and the four override flags
# whose done-side help deliberately reads 'see `truth claim ...`'
# (--scope-ok, --evidence-unsafe-ok, --generated-ok,
# --evidence-exit-ok).  --concern is GONE from both (D4/ADR-046: the
# concerns surface is Tier C; the field is closed to new records).
CLAIM_INTAKE_FLAGS = [
    _flag("--class", dest="evidence_class", default="UNVERIFIED",
          choices=EVIDENCE_CLASSES),
    _flag("--evidence-cmd",
          help="re-runnable command whose output is the evidence"),
    _flag("--paths", help="comma-separated globs the evidence depends on"),
        _flag("--watch-policy", dest="watch_policy", metavar="NAME",
              help="take the watch set from a named policy in "
                   ".truth/watch-policies instead of --paths (FAZA 3): the "
                   "set is reviewed once and reused, rather than "
                   "re-invented per filing"),
        _flag("--paths-ok", dest="paths_ok", metavar="SENTENCE",
              help="why THIS freehand watch set is right, when it exceeds "
                   "the one-path budget and no named policy fits: stored "
                   "as paths_basis, decays at 30 days (ADR-032) and "
                   "counted in the override report"),
    _flag("--tier", default="P2", choices=TIERS),
    _flag("--ttl-days", type=int, default=None,
          help="expiry for facts the repo cannot invalidate (G10)"),
    _flag("--single-run", action="store_true",
          help="skip the determinism double-run (expensive commands; "
               "accepts false-divergence risk, G6)"),
    _flag("--duplicate-ok", action="store_true",
          help="file despite similarity to an active claim (G8)"),
]

VERB_TABLE = [
    ("claim", "file a claim (one command, end to end)", [
        _flag("text"),
        *CLAIM_INTAKE_FLAGS,  # R7: shared verbatim with `done --claim`
        _flag("--basis", help="reasoning basis (required for INFERRED)"),
        _flag("--scope-ok", metavar="SENTENCE",
              help="one sentence: why the evidence command's scope "
                   "covers the claim's universal quantifier (ADR-007; "
                   "stored as scope_basis, attackable by verifiers)"),
        _flag("--evidence-unsafe-ok", action="store_true",
              help="file despite a failed evidence-command safety "
                   "screen (ADR-009); recheck will refuse to execute "
                   "the command, so verification becomes manual"),
        _flag("--generated-ok", metavar="SENTENCE",
              help="watch a path on the committed generated-artifact "
                   "list anyway (ADR-037): one sentence why the "
                   "artifact itself is the fact; stored as "
                   "generated_ok_basis, counted, and decays like "
                   "--scope-ok (ADR-032 default expiry)"),
        _flag("--evidence-exit-ok", metavar="SENTENCE",
              help="one sentence: why a FAILING evidence command "
                   "proves this positive sentence (ADR-035; stored "
                   "as evidence_exit_basis, attackable by verifiers; "
                   "refused when the evidence exits 0 -- nothing to "
                   "excuse)"),
        JSON_FLAG,
    ], cmd_claim),

    ("verdict", "record a verification verdict; "
                "retraction is human-only (TRUTH_HUMAN=1 plus an "
                "interactive typed-id confirmation, or "
                "TRUTH_HUMAN_ACK=<id> for headless human use) and "
                "records WHY (--cause, ADR-049)", [
        _flag("claim_id"),
        _flag("verdict", nargs="?", choices=VERDICTS),
        _flag("--basis"),
        _flag("--recheck", action="store_true",
              help="re-run the claim's evidence command and compare hashes"),
        _flag("--mechanical", action="store_true",
              help="annotate a diverge: the measuring recipe changed, "
                   "not necessarily the fact (ADR-012)"),
        _flag("--cause", choices=RETRACTION_CAUSES,
              help="REQUIRED on a retraction (ADR-049): why the belief "
                   "dies. Two questions about the sentence -- restated "
                   "= still true, a successor states it better "
                   "(--successor required); expired = was true, the "
                   "world moved past it; wrong = never true, or its "
                   "evidence never demonstrated it. There is no "
                   "override flag: the question is always answerable "
                   "by the human retracting"),
        _flag("--successor", metavar="TR_ID",
              help="the claim that carries the fact forward (ADR-049): "
                   "must exist and not itself be retracted. Required "
                   "with --cause restated, optional with "
                   "expired/wrong (a corrected re-file is a normal "
                   "`wrong` retraction). A CLAIM-level pointer -- "
                   "ADR-013's --supersedes is per-ISSUE premise "
                   "redirection and stays separate"),
        _flag("--refresh-evidence", dest="refresh_evidence",
              metavar="SENTENCE",
              help="REQUIRED on an agree whose evidence no longer "
                   "reproduces (ADR-051): one sentence why the "
                   "changed output still supports the claim's "
                   "sentence -- a line-number shift, a count that "
                   "grew. Stores the newly observed capsule on the "
                   "verdict so the anchor and the capsule advance "
                   "TOGETHER; without it the agree would leave the "
                   "claim live and permanently un-recheckable. If "
                   "the fact itself moved, file diverge instead "
                   "(--mechanical if only the recipe drifted)"),
        _flag("--orphan-ok", metavar="SENTENCE",
              help="retract despite scope-covered citations of the id "
                   "(ADR-036): one sentence why deliberate orphaning "
                   "is right; stored as orphan_basis, counted in the "
                   "override report"),
        JSON_FLAG,
    ], cmd_verdict),

    ("citations", "ADR-036 preflight: which "
                  "scope-covered files cite these ledger ids "
                  "(read-only, no ceremony; exit 0 = clean, "
                  f"{CITATIONS_EXIT_CITED} = cited -- sweep before "
                  "a batch retraction)", [
        _flag("ids", nargs="+"),
        JSON_FLAG,
    ], cmd_citations),

    # Refactor step 2.6: `invalidate-scan` was NARROWED to `ttl-scan`
    # and `reaffirm` was RETIRED outright. Both were write paths for the
    # staling proxy; `truth reproduce` is the read-time replacement, and
    # `verdict --recheck` remains the per-claim re-confirmation. The READ
    # side of both is untouched -- the fold still parses all 1997
    # `invalidation` records and reports still classify the 1283
    # `reaffirm_cleared` ones (ADR-046 legacy-admitted, closed to new
    # records).
    ("ttl-scan",
     "mark claims stale whose ttl_days has elapsed (ADR-019); the only "
     "clock reader in the system. Successor to invalidate-scan, whose "
     "path and anchor arms were retired in favour of `truth reproduce`", [
        _flag("--quiet", action="store_true"),
    ], cmd_ttl_scan),

    ("premise", "link a tracker issue (external or wk-) "
                "to a claim it depends on; --supersedes redirects a "
                "dead premise to its corrected claim (ADR-013)", [
        _flag("issue"),
        _flag("claim_id"),
        _flag("--supersedes", metavar="OLD_TR",
              help="dead premise claim this link replaces for the issue "
                   "-- an auditable redirect the ready-fold honors; "
                   "refused while the old premise still passes ready "
                   "(ADR-013)"),
        JSON_FLAG,
    ], cmd_premise),

    ("contradicts", "declare two claims cannot both "
                    "hold (issue #4): while both would otherwise be "
                    "live, both derive DISPUTED -- premised work HOLDs "
                    "and specs citing either side fail; resolve by "
                    "retract/supersede/re-file, no new verb", [
        _flag("claim_a"),
        _flag("claim_b"),
        _flag("--basis", required=True,
              help="why these cannot both hold -- the attackable "
                   "record of the accusation"),
    ], cmd_contradicts),

    ("issue", "file a work item in the ledger (ADR-002); "
              "link the facts it stands on with --premise", [
        _flag("title"),
        _flag("--text", help="longer description"),
        _flag("--deps", help="comma-separated wk- ids this issue depends on"),
        _flag("--premise", action="append",
              help="claim id this work stands on (repeatable; "
                   "premise-at-birth)"),
        _flag("--accept-cmd", dest="accept_cmd",
              help="executable finish line: `done` runs this from the "
                   "repo root and refuses the close on non-zero exit; "
                   "screened against .truth/accept-allow (ADR-014)"),
        _flag("--accept-kind", dest="accept_kind",
              choices=ACCEPT_KINDS,
              help="which of 12207's two V's the oracle is: "
                   "verification = suite/gate ('built right'), "
                   "validation = golden-diff ('built the right "
                   "thing'); default verification (ADR-014)"),
        _flag("--accept-unsafe-ok", dest="accept_unsafe_ok",
              action="store_true",
              help="file despite a failed acceptance-command screen "
                   "(ADR-014); `done` will refuse to execute the "
                   "oracle, so the close will need this flag again"),
        JSON_FLAG,
    ], cmd_issue),

    ("start", "claim a work item (files 'claimed')", [
        _flag("issue_id"),
        _flag("--release", action="store_true",
              help="file 'released' instead: give the item back"),
        _flag("--basis"),
    ], cmd_start),

    ("done", "close a work item; --claim files what "
             "the finished work made true (claim-at-death)", [
        _flag("issue_id"),
        _flag("--basis", help="required: what was done / why it dies"),
        _flag("--cancel", action="store_true",
              help="terminal tombstone (G12): TRUTH_HUMAN=1 plus an "
                   "interactive typed-id confirmation, or "
                   "TRUTH_HUMAN_ACK=<id> for headless human use"),
        _flag("--reopen", action="store_true",
              help="reopen a closed item (work is cyclical)"),
        _flag("--orphan-ok", metavar="SENTENCE",
              help="cancel despite scope-covered citations of the "
                   "wk- id (ADR-036); stored as orphan_basis on the "
                   "event, counted in the override report"),
        _flag("--claim", dest="claim_text",
              help="text of the completion fact to file atomically"),
        *CLAIM_INTAKE_FLAGS,  # R7: shared verbatim with `claim`
        _flag("--claim-basis", help="basis for an INFERRED completion claim"),
        _flag("--scope-ok", metavar="SENTENCE",
              help="see `truth claim --scope-ok` (ADR-007)"),
        _flag("--evidence-unsafe-ok", action="store_true",
              help="see `truth claim --evidence-unsafe-ok` (ADR-009)"),
        _flag("--generated-ok", metavar="SENTENCE",
              help="see `truth claim --generated-ok` (ADR-037)"),
        _flag("--evidence-exit-ok", metavar="SENTENCE",
              help="see `truth claim --evidence-exit-ok` (ADR-035)"),
        _flag("--accept-unsafe-ok", dest="accept_unsafe_ok",
              action="store_true",
              help="close WITHOUT executing an acceptance oracle that "
                   "CANNOT run (unscreened or unscreenable); stamped "
                   "executed=false on the event. Never overrides an "
                   "oracle that ran and failed (ADR-014)"),
        _flag("--json", action="store_true",
              help="print one JSON object {issue, event, claim, "
                   "accept, advisories} -- the SI-3 machine surface "
                   "extended to claim-at-death (advisories ride the "
                   "echo, never the ledger line)"),
    ], cmd_done),

    ("issues", "list work items with derived status; "
               "--ready-json emits the E1 adapter contract", [
        JSON_FLAG,
        _flag("--ready-json", dest="ready_json", action="store_true",
              help="JSON array of {id,title} for open, dep-satisfied "
                   "items (pipe into `truth ready --stdin`)"),
    ], cmd_issues),

    ("list", "list claims by derived status", [
        *[_flag("--" + flag.replace("_", "-"), dest=flag,
                action="store_true") for flag in STATUSES],
        _flag("--watch-policy", dest="watch_policy", metavar="NAME",
              help="only claims standing on this named watch policy; "
                   "'-' selects path-carrying claims on NO policy (the "
                   "FAZA 3 migration backlog)"),
        JSON_FLAG,
    ], cmd_list),

    ("queue",
     "human review queue: diverged + stale P0/P1 + unverifiable P0", [
        JSON_FLAG,
    ], cmd_queue),

    ("stats", "ledger metrics (FS-1): status/tier "
              "counts, verdict rates, claim half-life, queue "
              "aging -- the monthly audit's mechanical half", [
        WINDOW_FLAG,
        JSON_FLAG,
    ], cmd_stats),

    ("health", "one fold, every health section (FAZA 4): the "
               "signals first, then ledger counts, overrides, retraction "
               "causes, verifier separation and churn. A READ verb -- it "
               "reports and refuses nothing; the gates that block already "
               "exist. --reproduce additionally runs the capsule sweep "
               "(opt-in: it EXECUTES recorded commands)", [
        _flag("--reproduce", action="store_true",
              help="also run the capsule sweep and fold its counts in"),
        JSON_FLAG,
    ], cmd_health),

    ("staling", "what the path-touched-means-"
                "stale rule cost (ADR-050): every resolved "
                "staling split into the fact had NOT changed "
                "(mechanically re-confirmed / re-read by a "
                "human) vs it HAD, plus which kind of watched "
                "path triggered them", [
        WINDOW_FLAG,
        _flag("--append-order", dest="append_order",
              action="store_true",
              help="walk the raw FILE (append) order instead of the "
                   "fold's (ts, id, canon) order -- reproduction "
                   "only, for measurements taken that way before "
                   "this verb existed (ADR-050); the two disagree "
                   "on union-merged ledgers"),
        JSON_FLAG,
    ], cmd_staling),

    ("reproduce", "re-run every LIVE claim's "
                  "evidence capsule here and now (F1.1): reproduces "
                  "/ capsule-stale / unexecutable / no-capsule. The "
                  "question no other verb asks -- invalidate-scan "
                  "watches PATHS, recheck and reaffirm only reach "
                  "claims already knocked out of live. Files "
                  "nothing. Exit 7 when any capsule no longer "
                  "reproduces; exit 8 when the sweep examined zero "
                  "claims (ADR-042 rule 2: measuring nothing is a "
                  "failure, not a pass)", [
        _flag("--since", metavar="ISO_TS",
              help="only fold events with ts >= this ISO timestamp "
                   "(same window convention as `stats`/`staling`; it "
                   "narrows which claims are live, not just the "
                   "report)"),
        _flag("--arm", choices=REPRODUCE_ARMS,
              help="print only this arm's rows (the summary line and "
                   "the exit code still cover the whole sweep)"),
        JSON_FLAG,
    ], cmd_reproduce),

    ("ready", "unblocked issues filtered by premise "
              "validity (ADR-001); source: --stdin, TRUTH_TRACKER_CMD, "
              "native work kernel if issue records exist, else "
              "`bd ready --json` (ADR-002 precedence)", [
        JSON_FLAG,
        _flag("--stdin", dest="stdin_issues", action="store_true",
              help="read the issues JSON array from stdin instead of "
                   "invoking a tracker command"),
    ], cmd_ready),

    ("impact", "what knowledge does editing these "
               "paths endanger? (ADR-005; read-only prediction; "
               "exit 0 silent / 3 watched). --inverse flips the "
               "question: which tracked files does no active "
               "claim watch? (issue #5; exit 0 clean / 4 dark)", [
        _flag("paths", nargs="*",
              help="repo-root-relative paths about to be edited "
                   "(forward mode; forbidden with --inverse)"),
        _flag("--inverse", action="store_true",
              help="list tracked files watched by NO active "
                   "(non-retracted) claim -- the 24765 backward "
                   "trace; exit 4 when dark files exist"),
        _flag("--under", metavar="DIR",
              help="restrict --inverse to files under this "
                   "repo-root-relative directory"),
        _flag("--exclude", metavar="PREFIX", action="append",
              help="drop files under this path prefix from "
                   "--inverse (repeatable; lockfiles, assets)"),
        JSON_FLAG,
    ], cmd_impact),

    ("baseline", "fold the ledger at a git ref: "
                 "the frozen status account (10007, issue #3); "
                 "--diff folds a second ref and prints the delta "
                 "(exit 5 if any record DISAPPEARED -- rewritten "
                 "history; exit 2 unreadable ref)", [
        _flag("ref", help="git ref to fold the ledger at (tag, sha, HEAD)"),
        _flag("--diff", metavar="REF_B",
              help="second (newer) ref: print born/transitions/"
                   "disappeared between ref and REF_B"),
        _flag("--json", action="store_true",
              help="deterministic JSON (sorted; redirect to a file "
                   "and commit it if you want a persisted baseline)"),
    ], cmd_baseline),

    ("dispatch",
     "print the verifier context (prompt + claim only) for a fresh session", [
        _flag("claim_id"),
    ], cmd_dispatch),

    ("doctor", "check the installation, not just the scripts (G4)", [
        _flag("--json", action="store_true",
              help="the same run as one object: {ok, warn, fail} "
                   "lists of {check, detail} plus failures/warnings "
                   "counts; the exit code is unchanged (1 on "
                   "failures)"),
    ], cmd_doctor),

    ("validate", "schema-check every ledger record", [
        _flag("--stdin", action="store_true", help="read ledger from stdin"),
    ], cmd_validate),

    ("vocab", "the machine vocabulary (P2 "
              "contract): statuses, active set, verdict->status "
              "map, ADR-001 premise derivations, and the "
              "satellites' citation-blocking set -- one "
              "greppable line per key, or --json", [
        JSON_FLAG,
    ], cmd_vocab),
]

def main():
    ap = argparse.ArgumentParser(prog="truth", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    for name, help_text, flags, fn in VERB_TABLE:
        p = sub.add_parser(name, help=help_text)
        for args_, kwargs_ in flags:
            p.add_argument(*args_, **kwargs_)
        p.set_defaults(fn=fn)

    args = ap.parse_args()
    # R2 (roadmap-v3): loud fail-open. An unwired commit gate means INV-A/
    # INV-B and the ADR-008/016 detections silently don't run, and until
    # now only `doctor` said so. Probed at most once per invocation, and
    # only for write verbs -- read verbs (notably `validate --stdin`,
    # which runs inside the gate itself) skip even the probe.
    if args.cmd in WRITE_VERBS:
        banner = commit_gate_banner(args.cmd, commit_gate_wired())
        if banner:
            print(banner, file=sys.stderr)
    try:
        if args.cmd in WRITE_VERBS:
            # ADR-045 (D2): the ENTIRE verb -- load, gates, append -- is
            # one critical section under the ledger lock, so every fold a
            # gate decision reads is still current when the append lands
            # (the R10 TOCTOU class). Read verbs (incl. `validate
            # --stdin`, which runs inside the commit gate) never touch
            # the lock. Blocking acquire, no timeout: flock(2) state dies
            # with a crashed holder's process, so waiting is safe.
            with ledger_lock():
                args.fn(args)
        else:
            args.fn(args)
    except BrokenPipeError:
        try:
            sys.stdout.close()
        except Exception:
            pass
        sys.exit(0)
