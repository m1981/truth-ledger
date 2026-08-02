"""truthlib.gates -- the ADR-034 staged intake gate table (C4).

The INTAKE_GATES rows and their gate functions, plus run_intake_stage.
Documented exception to core purity: some gate fns gather their own
facts through shellio (tracked_files, load_generated_globs,
blast_history) exactly as they did inline before the split, and
run_intake_stage sys.exits the first refusal -- both are the documented
pre-P3 state, unchanged (ADR-044).
"""
import sys

from truthlib.registry import *
from truthlib.kernel import *
from truthlib.evidence import *
from truthlib.policy import *
from truthlib.shellio import *

# --- ADR-034: the staged intake gate table --------------------------------
# Order is data, not prose: rows are (stage, name, gate_fn); a gate_fn
# takes the shared ctx dict, may stash derived values in it, and returns
# a refusal string (the shell sys.exits it) or None. Stages:
#   pre-execution    -- text/path/policy checks; nothing has run yet;
#   [execution boundary] -- the ADR-009 evidence screen, then the G6
#     determinism double-run. DELIBERATELY NOT ROWS: the screen is a
#     gate on execution, not a peer refusal in a flat list (ADR-029
#     Decision 1; canary FAULT SD pins the non-flat contrast);
#   post-execution   -- gates reading the captured evidence (rc, output);
#     rows land here from ADR-035 (exit gate) on.
# GS canary arms assert the sequence end-to-end.

def _gate_text_nonempty(ctx):
    if not ctx["text"] or not ctx["text"].strip():
        return ("truth: claim text must be non-empty -- an assertion with "
                "no sentence cannot be verified, diverged from, or cited "
                "(schema: text minLength 1)")
    return None

def _gate_duplicate(ctx):
    # G8. Compute conflicts UNCONDITIONALLY (MEDIUM-1): a bare
    # --duplicate-ok used to skip the check and leave no trace, unlike
    # every other override (scope_basis, screened) which records itself.
    # The override stamps the ids it bypassed onto the record, so the
    # author's "these are genuinely distinct" judgment is attackable
    # ledger content a verifier can review -- not a silent flag.
    similar = duplicate_conflicts(ctx["text"], ctx["claims"])
    if similar and not ctx["duplicate_ok"]:
        lines = "\n".join(f"  {cid}: {t}" for cid, t in similar)
        return ("truth: refusing near-duplicate of active claim(s) (G8):\n"
                f"{lines}\nRe-file with --duplicate-ok if genuinely distinct.")
    ctx["overridden_duplicates"] = sorted(cid for cid, _ in similar) \
        if (similar and ctx["duplicate_ok"]) else []
    return None

def _gate_quantifier_scope(ctx):
    conflict = quantifier_scope_conflict(ctx["text"], ctx["evidence_cmd"])
    if conflict and not ctx["scope_basis"]:
        q, s = conflict
        return (f"truth: claim text quantifies universally ({q!r}) but the "
                f"evidence command is scoped ({s!r}) -- the exact shape of "
                "both pilot divergences (ADR-007). Either narrow the "
                "claim's sentence to the command's actual domain, or "
                "re-file with --scope-ok \"<one sentence: why this scope "
                "covers that quantifier>\".")
    return None

def _gate_scope_decay(ctx):
    # ADR-032 transform row -- never refuses. Stamps the default shelf
    # life BEFORE the class precheck reads ttl_days, so the effective
    # ttl rides the ordinary INV-B/ADR-019 machinery untouched; the
    # notice is voiced post-append through the CC-1 advisory block.
    # ADR-037 extends the decay to --generated-ok (decay INCLUDED, the
    # ADR-032 exclusions form: "this path is generated" rots as build
    # systems change, and the re-ask is exactly the scan->re-file loop).
    # Keyed on the STORED generated basis, never the raw flag: a
    # --generated-ok that matched nothing is dropped (and voiced), and
    # a dropped override must not decay -- ADR-032 re-asks a RECORDED
    # judgment (the R3 adversarial review's catch). This row therefore
    # runs AFTER the generated gate in the table.
    gen_stored = ctx.get("payload_generated_basis")
    flag = "--scope-ok" if ctx["scope_basis"] else "--generated-ok"
    ctx["ttl_days"], ctx["ttl_default"], _ = \
        override_decay(ctx["scope_basis"] or gen_stored,
                       ctx["ttl_days"], flag=flag)
    return None

def _gate_inv_m(ctx):
    paths = ctx["paths"]
    if not paths:
        return None
    # INV-M applies to any claim carrying evidence_paths, not only
    # VERIFIED -- decide_invalidation doesn't gate on evidence_class
    # either, so an INFERRED/UNVERIFIED claim with paths is exposed to
    # the identical dead-tripwire failure.
    malformed = malformed_path_list(paths)
    if malformed:
        return ("truth: --paths entry contains whitespace with no comma "
                f"(INV-M): {malformed!r} -- did you forget a comma "
                "between paths? A space-joined literal can never match "
                "a real file.")
    dead = dead_literal_paths(paths, tracked_files())
    if dead:
        return (f"truth: --paths entry matches zero tracked files "
                f"(INV-M): {dead!r} -- a literal that matches nothing "
                "is a dead tripwire from the moment it's filed. Fix the "
                "path; use a glob ('*'/'?'/'**') if you're intentionally "
                "watching an empty-for-now pattern; or, for a fact about "
                "a file git does not track, use --ttl-days instead "
                "(untracked files never appear in diffs, so a path can "
                "never invalidate them).")
    dead_g = dead_glob_paths(paths)
    if dead_g:
        return ("truth: --paths glob can match no path git could emit "
                f"(INV-M, ADR-024): {dead_g!r} -- a glob that is "
                "absolute, ends in '/', or has a '.', '..', empty, or "
                "leading '.git' component never matches a repo-relative, "
                "normalized diff path, so it is a dead tripwire despite "
                "the glob exemption. Use a reachable repo-relative "
                "pattern like 'dir/**' or 'dir/*.py'.")
    return None

def _gate_generated(ctx):
    # ADR-037: a watch on a generated artifact restales on every
    # regeneration -- refused for ANY evidence class carrying paths
    # (an INFERRED claim restales identically; the INV-M stance).
    if not ctx["paths"]:
        return None
    globs, source, err = load_generated_globs()
    if err:
        return err  # R14a: the loader's refusal IS this gate's refusal
    ctx["generated_source"] = source
    if source != "file":
        return None
    hits = sorted(p for p in ctx["paths"]
                  if any(match_paths(p, [g]) or p == g for g in globs))
    if not hits:
        return None
    if ctx["generated_basis"]:
        ctx["payload_generated_basis"] = ctx["generated_basis"]
        return None
    return ("truth: --paths entry matches the committed generated-"
            f"artifact list ({GENERATED_PATHS_REL}): {hits!r} -- a watch "
            "on a generated file restales on every regeneration "
            "(ADR-037). Watch the SOURCE the generator reads, or state "
            "why the artifact itself is the fact: --generated-ok "
            "\"<sentence>\".")

def _gate_class_precheck(ctx):
    if ctx["evidence_class"] == "VERIFIED":
        return verified_intake_error(ctx["evidence_cmd"], ctx["paths"],
                                     ctx["ttl_days"], ctx["head"])
    if ctx["evidence_class"] == "INFERRED":
        return inferred_intake_error(ctx["basis"])
    return None

def _gate_evidence_exit(ctx):
    # ADR-035 (post-execution): reads the captured FIRST-run returncode
    # from the payload capsule -- never re-runs. Decay for the stored
    # basis is DECLINED with reason (ADR-032 exclusions form): a
    # legitimately-failing proof's non-zero exit is a permanent property
    # of the recipe, and re-verification re-runs the command anyway.
    rc = ctx["payload"]["evidence"].get("returncode")
    err = evidence_exit_error(ctx["text"], rc, ctx["evidence_exit_basis"])
    if err:
        return err
    if ctx["evidence_exit_basis"] and rc:
        ctx["payload"]["evidence_exit_basis"] = ctx["evidence_exit_basis"]
    return None

def _gate_blast(ctx):
    # ADR-039 transform row -- never refuses. Stamps the forecast so
    # the stats blast section can compare observed-vs-forecast later.
    # Shallow or unavailable history stores NOTHING (a floor is not a
    # bound); the advisory block voices why, post-append.
    if not ctx["paths"]:
        return None
    history, state = blast_history()
    ctx["blast_state"] = state  # R6: the advisory pass reuses this fact
    if state == "ok":
        ctx["blast_forecast"] = blast_forecast(ctx["paths"], history)
    return None

INTAKE_GATES = (
    ("pre-execution", "text-nonempty", _gate_text_nonempty),
    ("pre-execution", "near-duplicate-g8", _gate_duplicate),
    ("pre-execution", "quantifier-scope-adr007", _gate_quantifier_scope),
    ("pre-execution", "paths-inv-m", _gate_inv_m),
    ("pre-execution", "generated-paths-adr037", _gate_generated),
    ("pre-execution", "scope-decay-adr032", _gate_scope_decay),
    ("pre-execution", "blast-forecast-adr039", _gate_blast),
    ("pre-execution", "class-precheck", _gate_class_precheck),
    ("post-execution", "evidence-exit-adr035", _gate_evidence_exit),
    # further post-execution rows land with the linter and blast ADRs
)

def run_intake_stage(stage, ctx):
    """Iterate the table's rows for one stage, in table order; the first
    refusal wins (sys.exit). Any I/O lives inside individual gate fns
    exactly as it did inline before ADR-034."""
    for st, _name, fn in INTAKE_GATES:
        if st != stage:
            continue
        err = fn(ctx)
        if err:
            sys.exit(err)
