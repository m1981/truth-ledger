"""truth v0.9.33 -- append-only claims ledger with a native work kernel.

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
from truthlib.advisory import *
from truthlib.shellio import *
from truthlib.advisory import _escape_ctrl
from truthlib.shellio import _short_sha

def build_claim_payload(text, evidence_class, evidence_cmd, paths_csv, tier,
                        ttl_days, basis, single_run, duplicate_ok, claims, *,
                        scope_basis=None, unsafe_ok=False,
                        evidence_exit_basis=None, generated_basis=None):
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
    ctx = {"text": text, "evidence_class": evidence_class,
           "evidence_cmd": evidence_cmd, "paths": split_csv(paths_csv),
           "tier": tier, "ttl_days": ttl_days, "basis": basis,
           "claims": claims, "duplicate_ok": duplicate_ok,
           "scope_basis": scope_basis,
           "evidence_exit_basis": evidence_exit_basis,
           "generated_basis": generated_basis,
           "head": head_commit() if evidence_class == "VERIFIED" else None,
           "overridden_duplicates": [], "ttl_default": False}
    run_intake_stage("pre-execution", ctx)
    payload = {"text": text, "evidence_class": evidence_class,
               "cost_tier": tier, "ttl_days": ctx["ttl_days"],
               "evidence_paths": ctx["paths"]}
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
        run_intake_stage("post-execution", ctx)
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
        generated_basis=a.generated_ok)
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
    claims, _ = fold(load_events())
    if a.claim_id not in claims:
        sys.exit(f"truth: unknown claim {a.claim_id}")
    if claims[a.claim_id]["status"] == "retracted":
        sys.exit(f"truth: {a.claim_id} is retracted -- terminal state (G12). "
                 "File a new claim instead.")
    if a.mechanical and (a.recheck or a.verdict != "diverge"):
        sys.exit("truth: --mechanical only annotates a manual diverge "
                 "(ADR-012: it says the recipe changed, not reality)")
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
            verdict, basis = recheck_verdict(ev, digest, rc)
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
        verdict, basis = a.verdict, a.basis
    payload = {"claim": a.claim_id, "verdict": verdict, "basis": basis}
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

def cmd_invalidate_scan(a):
    claims, _ = fold(load_events())
    head = head_commit() or "0000000"
    now = now_dt()
    hits = []
    for cid, entry in claims.items():
        if entry["status"] not in ACTIVE_STATUSES:
            continue
        p = entry["claim"]["payload"]
        facts = {"head": head}
        anchor = entry.get("anchor") or p.get("anchor_commit")  # effective
        paths = p.get("evidence_paths", [])
        if anchor and paths and anchor != head:
            reachable = commit_reachable(anchor)
            facts["anchor_reachable"] = reachable
            if reachable:
                changed, err = changed_files_since(anchor)
                facts["changed_files"], facts["diff_error"] = changed, err
        decision = decide_invalidation(entry, facts, now)
        if decision:
            append_record("invalidation",
                          {"claim": cid, "commit": head, **decision["payload"]})
            hits.append((cid, decision["label"]))
    if not a.quiet:
        for cid, why in hits:
            print(f"stale: {cid} ({why})")
        print(f"invalidate-scan: {len(hits)} claim(s) marked stale")

def cmd_reaffirm(a):
    """R3 / ADR-030: batch re-confirmation of stale claims whose evidence
    COMMAND OUTPUT is unchanged (only that -- a watched-but-unread path
    may have changed; the filed agree records what the anchor advance
    cleared, see ADR-030). The shell only walks, gathers, executes, and
    appends;
    every decision is reaffirm_triage's. Execution goes through the SAME
    screened path `verdict --recheck` uses -- screen_evidence_command
    against the CURRENT allowlist (the screen gates execution, ADR-029),
    then run_evidence + recheck_verdict; a second executor is forbidden
    for the same reason a second matcher is (ADR-005's drift lesson)."""
    events = load_events()
    claims, _ = fold(events)
    # ADR-010, reused verbatim from `verdict agree`: the comparison is
    # claim-session == current session; TRUTH_SELF_VERDICT=1 (the F4-class
    # self-attested override) disables it by making the comparison
    # unmatchable, exactly as loud and deliberate as on a manual agree.
    cur = (None if os.environ.get("TRUTH_SELF_VERDICT") == "1"
           else session())
    allow, deny = load_allowlist(), load_denylist()
    rows, counts = [], {arm: 0 for arm in REAFFIRM_ARMS}
    self_agreed = 0  # F4: agrees filed on this session's own claims
    for cid, entry in sorted(claims.items()):
        if entry["status"] != "stale":
            continue
        reason = latest_invalidation_reason(events, cid)
        ttl_staled = ttl_staleness(events, cid)  # red-team F3: structured
        was_agreed = previously_agreed(events, cid)
        d = reaffirm_triage(entry, reason, cur, was_agreed,
                            ttl_staled=ttl_staled)
        if d["arm"] == "execute":
            ev = entry["claim"]["payload"]["evidence"]
            # Rescreen against the CURRENT allowlist -- committed policy
            # NOW, not at filing time (the ADR-009 intake-AND-recheck
            # posture); a refusal means the command never runs here.
            screen_err = screen_evidence_command(ev["command"], allow,
                                                 denylist=deny)
            if screen_err:
                d = reaffirm_triage(entry, reason, cur, was_agreed,
                                    screen_err=screen_err,
                                    ttl_staled=ttl_staled)
            else:
                digest, rc = run_evidence(ev["command"])
                d = reaffirm_triage(entry, reason, cur, was_agreed,
                                    recheck=recheck_verdict(ev, digest, rc),
                                    ttl_staled=ttl_staled)
        action, filed = d["action"], None
        if d["arm"] == "match":
            if cur is None and entry["claim"].get("session") == session():
                self_agreed += 1  # F4: the override let this through
            if a.dry_run:
                action = "hash-match -- would file agree (dry-run: " \
                         "nothing filed)"
            else:
                payload = {"claim": cid, "verdict": "agree",
                           "basis": REAFFIRM_BASIS}
                cp = entry["claim"]["payload"]
                if cp.get("evidence_paths"):
                    # F2 semantics, same rule as cmd_verdict: the agree
                    # carries HEAD so the EFFECTIVE anchor advances and
                    # the next scan diffs from here, not the old anchor.
                    payload["anchor_commit"] = head_commit()
                    # ...which also buries whatever watched-path change
                    # staled the claim outside every future scan window
                    # (the command's OUTPUT matched; the watched universe
                    # may be wider than what it reads). Red-team F2:
                    # record what the advance auto-cleared so the burial
                    # is auditable -- the prior EFFECTIVE anchor (the
                    # scan's diff base) and the watched files changed in
                    # that range, via the scan's own helpers (a second
                    # differ/matcher is forbidden, the F1/F5 lesson). If
                    # the diff fails, the prior anchor alone still lands.
                    prior = entry.get("anchor") or cp.get("anchor_commit")
                    if prior:
                        cleared = {"prior_anchor": prior}
                        changed, _err = changed_files_since(prior)
                        if changed is not None:
                            cleared["touched"] = [
                                f for f in changed
                                if match_paths(f, cp.get("evidence_paths",
                                                         []))]
                        payload["reaffirm_cleared"] = cleared
                filed = append_record("verdict", payload)["id"]
                action = f"filed agree ({filed}): {REAFFIRM_BASIS}"
        counts[d["arm"]] += 1
        rows.append({"id": cid, "arm": d["arm"], "action": action,
                     "filed": filed})
    if cur is None:
        # F4 (red-team): the manual-agree override is per-claim and loud;
        # here one env var amplifies across the whole sweep. Same
        # loudness, batch edition -- count what it actually let through.
        print("truth: WARNING: TRUTH_SELF_VERDICT=1 override active -- "
              f"reaffirm {'would auto-agree' if a.dry_run else 'auto-agreed'} "
              f"{self_agreed} claim(s) THIS SESSION authored (batch "
              "self-verification: the G11/ADR-010 independence seam is off "
              "for this sweep)", file=sys.stderr)
    summary = (f"reaffirm: {len(rows)} stale claim(s) -- "
               f"{counts['match']} reaffirmed, {counts['mismatch']} "
               f"diverged (dispatch), {counts['ttl']} ttl (re-file), "
               f"{counts['manual']} manual, {counts['same_session']} "
               "same-session"
               + (" [dry-run: nothing filed]" if a.dry_run else ""))
    if a.json:
        print(json.dumps({"dry_run": a.dry_run, "claims": rows,
                          "counts": counts}, indent=2))
        return
    for r in rows:
        print(f"{r['id']}  {r['arm']:<12} {r['action']}")
    print(summary)

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
    claims, _ = fold(load_events())
    now = now_dt()
    want = {f for f in STATUSES if getattr(a, f)}
    rows = [{"id": cid, "status": e["status"], "age_days": age_days(e, now),
             "tier": e["claim"]["payload"].get("cost_tier"),
             "class": e["claim"]["payload"].get("evidence_class"),
             "text": e["claim"]["payload"].get("text")}
            for cid, e in claims.items()
            if not want or e["status"] in want]
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
            generated_basis=a.generated_ok)
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
    issues = tracker_issues(a, native)
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

def cmd_baseline(a):
    snap_a = baseline_snapshot(events_at_ref(a.ref))
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
    snap_b = baseline_snapshot(events_at_ref(a.diff))
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
            line = (f"editing {', '.join(r['touched'])} -> next commit "
                    f"STALES {r['claim']} ({r['tier']}, {r['status']}): "
                    f"{r['text']}")
            if r["holds"]:
                line += (" -- if that premise dies, ready HOLDs "
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

    for names, needle, purpose in ((("pre-commit",), "check-truth", "INV-A/INV-B"),
                                   (("post-merge", "post-commit"),
                                    "invalidate-scan", "INV-C")):
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

def add_claim_intake_flags(p):
    """R7: the claim-intake flags `claim` and `done --claim` share
    verbatim, declared once so the two surfaces cannot drift (done had
    already lost --json by hand-copy). Deliberately per-verb, NOT here:
    claim's `text` positional; --basis vs --claim-basis (done's claim
    basis must not shadow the close's own --basis); --json; and the four
    override flags whose done-side help deliberately reads 'see `truth
    claim ...`' (--scope-ok, --evidence-unsafe-ok, --generated-ok,
    --evidence-exit-ok). --concern is GONE from both (D4/ADR-046: the
    concerns surface is Tier C; the field is closed to new records)."""
    p.add_argument("--class", dest="evidence_class", default="UNVERIFIED",
                   choices=EVIDENCE_CLASSES)
    p.add_argument("--evidence-cmd", help="re-runnable command whose output is the evidence")
    p.add_argument("--paths", help="comma-separated globs the evidence depends on")
    p.add_argument("--tier", default="P2", choices=TIERS)
    p.add_argument("--ttl-days", type=int, default=None,
                   help="expiry for facts the repo cannot invalidate (G10)")
    p.add_argument("--single-run", action="store_true",
                   help="skip the determinism double-run (expensive commands; "
                        "accepts false-divergence risk, G6)")
    p.add_argument("--duplicate-ok", action="store_true",
                   help="file despite similarity to an active claim (G8)")

def main():
    ap = argparse.ArgumentParser(prog="truth", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("claim", help="file a claim (one command, end to end)")
    c.add_argument("text")
    add_claim_intake_flags(c)  # R7: shared verbatim with `done --claim`
    c.add_argument("--basis", help="reasoning basis (required for INFERRED)")
    c.add_argument("--scope-ok", metavar="SENTENCE",
                   help="one sentence: why the evidence command's scope "
                        "covers the claim's universal quantifier (ADR-007; "
                        "stored as scope_basis, attackable by verifiers)")
    c.add_argument("--evidence-unsafe-ok", action="store_true",
                   help="file despite a failed evidence-command safety "
                        "screen (ADR-009); recheck will refuse to execute "
                        "the command, so verification becomes manual")
    c.add_argument("--generated-ok", metavar="SENTENCE",
                   help="watch a path on the committed generated-artifact "
                        "list anyway (ADR-037): one sentence why the "
                        "artifact itself is the fact; stored as "
                        "generated_ok_basis, counted, and decays like "
                        "--scope-ok (ADR-032 default expiry)")
    c.add_argument("--evidence-exit-ok", metavar="SENTENCE",
                   help="one sentence: why a FAILING evidence command "
                        "proves this positive sentence (ADR-035; stored "
                        "as evidence_exit_basis, attackable by verifiers; "
                        "refused when the evidence exits 0 -- nothing to "
                        "excuse)")
    c.add_argument("--json", action="store_true")
    c.set_defaults(fn=cmd_claim)

    v = sub.add_parser("verdict", help="record a verification verdict; "
                       "retraction is human-only (TRUTH_HUMAN=1 plus an "
                       "interactive typed-id confirmation, or "
                       "TRUTH_HUMAN_ACK=<id> for headless human use)")
    v.add_argument("claim_id")
    v.add_argument("verdict", nargs="?", choices=VERDICTS)
    v.add_argument("--basis")
    v.add_argument("--recheck", action="store_true",
                   help="re-run the claim's evidence command and compare hashes")
    v.add_argument("--mechanical", action="store_true",
                   help="annotate a diverge: the measuring recipe changed, "
                        "not necessarily the fact (ADR-012)")
    v.add_argument("--orphan-ok", metavar="SENTENCE",
                   help="retract despite scope-covered citations of the id "
                        "(ADR-036): one sentence why deliberate orphaning "
                        "is right; stored as orphan_basis, counted in the "
                        "override report")
    v.add_argument("--json", action="store_true")
    v.set_defaults(fn=cmd_verdict)

    ci = sub.add_parser("citations", help="ADR-036 preflight: which "
                        "scope-covered files cite these ledger ids "
                        "(read-only, no ceremony; exit 0 = clean, "
                        f"{CITATIONS_EXIT_CITED} = cited -- sweep before "
                        "a batch retraction)")
    ci.add_argument("ids", nargs="+")
    ci.add_argument("--json", action="store_true")
    ci.set_defaults(fn=cmd_citations)

    s = sub.add_parser("invalidate-scan",
                       help="mark claims stale: paths changed, TTL expired, or anchor lost")
    s.add_argument("--quiet", action="store_true")
    s.set_defaults(fn=cmd_invalidate_scan)

    ra = sub.add_parser("reaffirm", help="batch re-confirm stale claims "
                        "whose evidence is unchanged (ADR-030): re-run "
                        "each claim's evidence through the screened "
                        "recheck path; hash-match auto-files agree "
                        "(anchor advances), mismatch is listed for "
                        "dispatch and files NOTHING; TTL-staled, "
                        "unscreened, never-agreed, and same-session "
                        "claims are skipped with the reason")
    ra.add_argument("--dry-run", dest="dry_run", action="store_true",
                    help="triage and report every arm; file nothing")
    ra.add_argument("--json", action="store_true")
    ra.set_defaults(fn=cmd_reaffirm)

    p = sub.add_parser("premise", help="link a tracker issue (external or wk-) "
                       "to a claim it depends on; --supersedes redirects a "
                       "dead premise to its corrected claim (ADR-013)")
    p.add_argument("issue")
    p.add_argument("claim_id")
    p.add_argument("--supersedes", metavar="OLD_TR",
                   help="dead premise claim this link replaces for the issue "
                        "-- an auditable redirect the ready-fold honors; "
                        "refused while the old premise still passes ready "
                        "(ADR-013)")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_premise)

    ct = sub.add_parser("contradicts", help="declare two claims cannot both "
                        "hold (issue #4): while both would otherwise be "
                        "live, both derive DISPUTED -- premised work HOLDs "
                        "and specs citing either side fail; resolve by "
                        "retract/supersede/re-file, no new verb")
    ct.add_argument("claim_a")
    ct.add_argument("claim_b")
    ct.add_argument("--basis", required=True,
                    help="why these cannot both hold -- the attackable "
                         "record of the accusation")
    ct.set_defaults(fn=cmd_contradicts)

    i = sub.add_parser("issue", help="file a work item in the ledger (ADR-002); "
                       "link the facts it stands on with --premise")
    i.add_argument("title")
    i.add_argument("--text", help="longer description")
    i.add_argument("--deps", help="comma-separated wk- ids this issue depends on")
    i.add_argument("--premise", action="append",
                   help="claim id this work stands on (repeatable; "
                        "premise-at-birth)")
    i.add_argument("--accept-cmd", dest="accept_cmd",
                   help="executable finish line: `done` runs this from the "
                        "repo root and refuses the close on non-zero exit; "
                        "screened against .truth/accept-allow (ADR-014)")
    i.add_argument("--accept-kind", dest="accept_kind",
                   choices=ACCEPT_KINDS,
                   help="which of 12207's two V's the oracle is: "
                        "verification = suite/gate ('built right'), "
                        "validation = golden-diff ('built the right "
                        "thing'); default verification (ADR-014)")
    i.add_argument("--accept-unsafe-ok", dest="accept_unsafe_ok",
                   action="store_true",
                   help="file despite a failed acceptance-command screen "
                        "(ADR-014); `done` will refuse to execute the "
                        "oracle, so the close will need this flag again")
    i.add_argument("--json", action="store_true")
    i.set_defaults(fn=cmd_issue)

    st = sub.add_parser("start", help="claim a work item (files 'claimed')")
    st.add_argument("issue_id")
    st.add_argument("--release", action="store_true",
                    help="file 'released' instead: give the item back")
    st.add_argument("--basis")
    st.set_defaults(fn=cmd_start)

    dn = sub.add_parser("done", help="close a work item; --claim files what "
                        "the finished work made true (claim-at-death)")
    dn.add_argument("issue_id")
    dn.add_argument("--basis", help="required: what was done / why it dies")
    dn.add_argument("--cancel", action="store_true",
                    help="terminal tombstone (G12): TRUTH_HUMAN=1 plus an "
                         "interactive typed-id confirmation, or "
                         "TRUTH_HUMAN_ACK=<id> for headless human use")
    dn.add_argument("--reopen", action="store_true",
                    help="reopen a closed item (work is cyclical)")
    dn.add_argument("--orphan-ok", metavar="SENTENCE",
                    help="cancel despite scope-covered citations of the "
                         "wk- id (ADR-036); stored as orphan_basis on the "
                         "event, counted in the override report")
    dn.add_argument("--claim", dest="claim_text",
                    help="text of the completion fact to file atomically")
    add_claim_intake_flags(dn)  # R7: shared verbatim with `claim`
    dn.add_argument("--claim-basis", help="basis for an INFERRED completion claim")
    dn.add_argument("--scope-ok", metavar="SENTENCE",
                    help="see `truth claim --scope-ok` (ADR-007)")
    dn.add_argument("--evidence-unsafe-ok", action="store_true",
                    help="see `truth claim --evidence-unsafe-ok` (ADR-009)")
    dn.add_argument("--generated-ok", metavar="SENTENCE",
                    help="see `truth claim --generated-ok` (ADR-037)")
    dn.add_argument("--evidence-exit-ok", metavar="SENTENCE",
                    help="see `truth claim --evidence-exit-ok` (ADR-035)")
    dn.add_argument("--accept-unsafe-ok", dest="accept_unsafe_ok",
                    action="store_true",
                    help="close WITHOUT executing an acceptance oracle that "
                         "CANNOT run (unscreened or unscreenable); stamped "
                         "executed=false on the event. Never overrides an "
                         "oracle that ran and failed (ADR-014)")
    dn.add_argument("--json", action="store_true",
                    help="print one JSON object {issue, event, claim, "
                         "accept, advisories} -- the SI-3 machine surface "
                         "extended to claim-at-death (advisories ride the "
                         "echo, never the ledger line)")
    dn.set_defaults(fn=cmd_done)

    iss = sub.add_parser("issues", help="list work items with derived status; "
                         "--ready-json emits the E1 adapter contract")
    iss.add_argument("--json", action="store_true")
    iss.add_argument("--ready-json", dest="ready_json", action="store_true",
                     help="JSON array of {id,title} for open, dep-satisfied "
                          "items (pipe into `truth ready --stdin`)")
    iss.set_defaults(fn=cmd_issues)

    l = sub.add_parser("list", help="list claims by derived status")
    for flag in STATUSES:
        l.add_argument("--" + flag.replace("_", "-"), dest=flag, action="store_true")
    l.add_argument("--json", action="store_true")
    l.set_defaults(fn=cmd_list)

    q = sub.add_parser("queue",
                       help="human review queue: diverged + stale P0/P1 + unverifiable P0")
    q.add_argument("--json", action="store_true")
    q.set_defaults(fn=cmd_queue)

    stt = sub.add_parser("stats", help="ledger metrics (FS-1): status/tier "
                         "counts, verdict rates, claim half-life, queue "
                         "aging -- the monthly audit's mechanical half")
    stt.add_argument("--since", metavar="ISO_TS",
                     help="only count events with ts >= this ISO timestamp")
    stt.add_argument("--json", action="store_true")
    stt.set_defaults(fn=cmd_stats)

    r = sub.add_parser("ready", help="unblocked issues filtered by premise "
                       "validity (ADR-001); source: --stdin, TRUTH_TRACKER_CMD, "
                       "native work kernel if issue records exist, else "
                       "`bd ready --json` (ADR-002 precedence)")
    r.add_argument("--json", action="store_true")
    r.add_argument("--stdin", dest="stdin_issues", action="store_true",
                   help="read the issues JSON array from stdin instead of "
                        "invoking a tracker command")
    r.set_defaults(fn=cmd_ready)

    im = sub.add_parser("impact", help="what knowledge does editing these "
                        "paths endanger? (ADR-005; read-only prediction; "
                        "exit 0 silent / 3 watched). --inverse flips the "
                        "question: which tracked files does no active "
                        "claim watch? (issue #5; exit 0 clean / 4 dark)")
    im.add_argument("paths", nargs="*",
                    help="repo-root-relative paths about to be edited "
                         "(forward mode; forbidden with --inverse)")
    im.add_argument("--inverse", action="store_true",
                    help="list tracked files watched by NO active "
                         "(non-retracted) claim -- the 24765 backward "
                         "trace; exit 4 when dark files exist")
    im.add_argument("--under", metavar="DIR",
                    help="restrict --inverse to files under this "
                         "repo-root-relative directory")
    im.add_argument("--exclude", metavar="PREFIX", action="append",
                    help="drop files under this path prefix from "
                         "--inverse (repeatable; lockfiles, assets)")
    im.add_argument("--json", action="store_true")
    im.set_defaults(fn=cmd_impact)

    bl = sub.add_parser("baseline", help="fold the ledger at a git ref: "
                        "the frozen status account (10007, issue #3); "
                        "--diff folds a second ref and prints the delta "
                        "(exit 5 if any record DISAPPEARED -- rewritten "
                        "history; exit 2 unreadable ref)")
    bl.add_argument("ref", help="git ref to fold the ledger at (tag, sha, HEAD)")
    bl.add_argument("--diff", metavar="REF_B",
                    help="second (newer) ref: print born/transitions/"
                         "disappeared between ref and REF_B")
    bl.add_argument("--json", action="store_true",
                    help="deterministic JSON (sorted; redirect to a file "
                         "and commit it if you want a persisted baseline)")
    bl.set_defaults(fn=cmd_baseline)

    d = sub.add_parser("dispatch",
                       help="print the verifier context (prompt + claim only) for a fresh session")
    d.add_argument("claim_id")
    d.set_defaults(fn=cmd_dispatch)

    doc = sub.add_parser("doctor", help="check the installation, not just the scripts (G4)")
    doc.add_argument("--json", action="store_true",
                     help="the same run as one object: {ok, warn, fail} "
                          "lists of {check, detail} plus failures/warnings "
                          "counts; the exit code is unchanged (1 on "
                          "failures)")
    doc.set_defaults(fn=cmd_doctor)

    val = sub.add_parser("validate", help="schema-check every ledger record")
    val.add_argument("--stdin", action="store_true", help="read ledger from stdin")
    val.set_defaults(fn=cmd_validate)

    vb = sub.add_parser("vocab", help="the machine vocabulary (P2 "
                        "contract): statuses, active set, verdict->status "
                        "map, ADR-001 premise derivations, and the "
                        "satellites' citation-blocking set -- one "
                        "greppable line per key, or --json")
    vb.add_argument("--json", action="store_true")
    vb.set_defaults(fn=cmd_vocab)

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
