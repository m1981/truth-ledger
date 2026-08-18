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
# FAZA 3 step 3.2: the churn arm refuses at ADR-039's SELF-CALIBRATING
# floor, and effective_blast_floor is that floor's one implementation.
# Importing it is the alternative to copying a percentile into a second
# place, which is the F1/F5 drift this package keeps refusing. The edge
# is acyclic -- reports imports registry/kernel/evidence only, and never
# gates -- and it is drawn in docs/structure.md, whose diagram test
# compares the arrows against the real AST edges.
from truthlib.reports import *
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

def _gate_paths_budget(ctx):
    """FAZA 3 step 3.2: a freehand watch set wider than
    MAX_FREEHAND_WATCH_PATHS is REFUSED. Two exits, both of which leave a
    record; there is deliberately no silent third.

      --watch-policy <name>   the set was reviewed once and committed by
                              name. This is the whole bargain the policy
                              file offers, and it is why the gate has
                              teeth instead of being a counter.
      --paths-ok "<sentence>" the author states why THIS set is right.
                              Stored as paths_basis, decays at 30 days
                              (ADR-032) and counted in override_report,
                              so an unreviewed wide set is re-asked rather
                              than accumulated.

    Runs directly after paths-inv-m: INV-M asks whether each path could
    ever match, this asks whether the SET was chosen or accumulated. Both
    are about the same field and neither depends on the other's outcome.

    The symmetric refusals matter as much as the budget. A basis with
    nothing to excuse is schema noise (the ADR-035 --evidence-exit-ok
    precedent, verbatim reasoning): --paths-ok on a set inside the budget,
    or beside a --watch-policy that already exempts it, buys nothing and
    would decay a judgment nobody needed to make."""
    paths, basis = ctx["paths"], ctx.get("paths_basis")
    policy = ctx.get("watch_policy")
    # STRUCTURAL EXEMPTION (step 3.1). The budget counts targets that
    # were picked FREEHAND; a `#selector` target is not one of those, and
    # the difference is not a favour granted to a new feature.
    #
    # The budget exists because 75 claims held 60 distinct watch sets --
    # sets accumulated rather than chosen. You cannot accumulate
    # `/dependencies/stripe` by accident: the author had to name an exact
    # key path or heading, and INV-M has already read the file and
    # confirmed it resolves. That is a narrower review than --paths-ok
    # asks for, performed mechanically, one target at a time.
    #
    # And the cost the budget is denominated in does not apply. Each extra
    # freehand path costs a whisper line on every edit AND a false
    # "capsule-stale" whenever any byte of the file moves; a selector
    # target costs the whisper line but not the false stale, because
    # `truth reproduce` hashes the sub-tree (step 3.3). Charging both at
    # the same rate would price precision like breadth and push authors
    # back to the wide glob this file exists to discourage.
    freehand = [p for p in paths if not split_selector_target(p)[1]]
    over = len(freehand) > MAX_FREEHAND_WATCH_PATHS
    if basis and policy:
        return ("truth: --paths-ok beside --watch-policy -- the named "
                "policy already carries the review this basis would "
                "state, so the basis excuses nothing and would decay a "
                "judgment nobody needed to make (ADR-032). Drop it.")
    if basis and not over and not ctx.get("churn_over"):
        # NEITHER arm needed it. The churn row runs first and flags itself
        # when it would have refused, so a single-path claim excusing
        # BREADTH is not mistaken for a pointless basis.
        return (f"truth: --paths-ok with {len(paths)} watched path(s) and a "
                "watch set below the churn floor -- neither path budget "
                "objects, so there is nothing to excuse (a basis with "
                "nothing to excuse is schema noise; drop the flag).")
    if not over or policy or basis:
        return None
    return (f"truth: {len(freehand)} watched paths picked by hand -- the "
            f"freehand budget is {MAX_FREEHAND_WATCH_PATHS} "
            f"({WATCH_POLICIES_REL}). Measured on this ledger, 75 claims "
            "with a watch set held 60 DISTINCT sets: almost every set was "
            "re-invented rather than reviewed, and each extra path costs "
            "a whisper line on every edit (22.6 claims named per edit, "
            "J-040's recount). Either:\n"
            f"  --watch-policy <name>   a reviewed set from {WATCH_POLICIES_REL}\n"
            "  --paths-ok \"<sentence>\"  why THIS set is right (stored, "
            "decays at 30 days, counted)\n"
            "  path.json#/a/b          watch the SUB-TREE the recipe "
            "reads; selector targets are outside this budget\n"
            "Nothing was filed.")

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
    # Step 3.2 joins --paths-ok to the same decay, for the same reason
    # ADR-037 joined --generated-ok: "this wide watch set is the right one"
    # rots exactly as "this scope is covered" does, and the re-ask is the
    # point. Precedence in the flag label is filing order; only one of the
    # three can be the reason a given claim decays, and the notice must
    # name the flag the author actually passed.
    gen_stored = ctx.get("payload_generated_basis")
    paths_basis = ctx.get("paths_basis")
    if ctx["scope_basis"]:
        flag = "--scope-ok"
    elif paths_basis:
        flag = "--paths-ok"
    else:
        flag = "--generated-ok"
    ctx["ttl_days"], ctx["ttl_default"], _ = \
        override_decay(ctx["scope_basis"] or paths_basis or gen_stored,
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
    # --- step 3.1: the same INV-M question, asked of the SELECTOR ------
    # A `#selector` is a second way to build a tripwire that cannot fire,
    # and all three arms below are refused for the one reason the older
    # arms are: the author is standing here now, and in a week the claim
    # will look filed and healthy while watching nothing.
    on_glob = selector_on_glob_paths(paths)
    if on_glob:
        return ("truth: --paths entry puts a '#selector' on a GLOB "
                f"(INV-M): {on_glob!r} -- a selector names a sub-tree of "
                "ONE document, so there is no single file for the digest "
                "to be of. Worse than dead: the matcher reads the file "
                "half, so this would silently watch the whole glob while "
                "reading as if it were precise. Name the file, or drop "
                "the selector and watch the glob you actually mean.")
    unsupported = unsupported_selector_paths(paths)
    if unsupported:
        exts = ", ".join(sorted(SUPPORTED_STRUCTURED_EXTENSIONS))
        shown = [f"{t} ({e})" for t, e in unsupported]
        return ("truth: --paths entry selects a sub-tree of a format that "
                f"has none (INV-M): {shown!r} -- sub-tree selectors are "
                f"supported for: {exts}. For any other file the unit is "
                "the whole file, so drop the '#...' and watch the path "
                "(a selector here would raise on first read, days from "
                "now, on a claim that already looks filed).")
    # The LIVE arm: a selector that is well-formed and well-placed can
    # still name nothing in the document as it stands today, which is
    # dead_literal_paths' failure one level down. This is the only INV-M
    # arm that reads file CONTENT, and it costs one read per selector
    # target -- paid by selector-bearing claims only.
    for t in paths:
        if not split_selector_target(t)[1]:
            continue
        _digest, err = structural_hash(t)
        if not err:
            continue
        kind, detail = err
        if kind == "missing":
            continue        # dead_literal_paths already owns absent files
        if kind == "unsupported":
            # unsupported_selector_paths screens by EXTENSION and passed
            # this one, so the format is in the grammar and the parser is
            # missing HERE -- .toml on a pre-3.11 interpreter. A different
            # fact from a dead selector and it gets its own sentence: the
            # target may be perfectly correct on a colleague's machine.
            return (f"truth: --paths selector cannot be read on this "
                    f"interpreter (INV-M): {t!r} -- {detail}")
        return (f"truth: --paths selector resolves to nothing (INV-M): "
                f"{t!r} -- {detail}. A selector that names no sub-tree in "
                "the file as it stands is a dead tripwire from the moment "
                "it is filed: the digest can never change, so the claim "
                "would report 'unchanged' forever. Fix the key path or "
                "heading, or watch the whole file.")
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
    # Step 3.1: the FILE half is the subject. match_paths strips the
    # selector from its PATTERNS, but here evidence_paths are the thing
    # being matched and the generated globs are the patterns, so the
    # strip has to happen on this side too -- and the `p == g` equality
    # arm never strips anything at all. Without this line, appending
    # `#/a/b` to a generated path is a one-character bypass of ADR-037:
    # the watch still restales on every regeneration (match_paths ignores
    # the selector everywhere downstream) while this gate stops seeing it.
    hits = sorted(p for p in ctx["paths"]
                  if any(match_paths(watch_target_path(p), [g])
                         or watch_target_path(p) == g for g in globs))
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
    # ADR-039 advisory row -- never refuses, and since ADR-046 never
    # stamps the payload either: blast_forecast failed the envelope
    # admission rule (no fold or blocking gate reads it), so the
    # forecast is computed here LIVE for the post-append advisory only.
    # Shallow or unavailable history computes NOTHING (a floor is not a
    # bound); the advisory block voices why, post-append. The parsed
    # history is stashed so the advisory's floor calibration reuses the
    # one git log this probe already paid for (R6).
    if not ctx["paths"]:
        return None
    history, state = blast_history()
    ctx["blast_state"] = state  # R6: the advisory pass reuses this fact
    if state == "ok":
        ctx["blast_history"] = history
        ctx["blast_forecast"] = blast_forecast(ctx["paths"], history)
    return None

def _gate_paths_churn(ctx):
    """FAZA 3 step 3.2, SECOND ARM: the churn budget. `paths-budget-max`
    counts ENTRIES; this one measures BREADTH, and the measurement is why
    it exists.

    Ten of this repo's freehand claims produced 35% of all whisper lines,
    and entry count predicts that badly: the loudest carries eight paths,
    but a single `template/truthlib/**` glob outranked most two-path sets.
    A budget that counts commas measures the wrong thing.

    THE MOTIVATING NUMBERS WERE CORRECTED WHILE BUILDING THIS, and the
    correction is recorded because it changed the row's design. The three
    single-path globs that first argued for this arm scored 74 whisper
    lines each -- over 200 COMMITS. ADR-039's window is 30 DAYS, where the
    same globs score 24 against a calibrated floor of 54, comfortably
    legal. So this row does NOT catch the case that motivated it; what it
    catches is every broad set that is genuinely hot right now, and the
    highest single-path forecast on the ledger (48) sits close enough
    under the floor that one `**` would clear it. The arm guards a
    reachable case, not a hypothetical one -- but it is not the arm the
    first sketch promised, and pretending otherwise would leave a false
    rationale in the file.

    ADR-039 already measures the right thing and has since v0.9.25:
    blast_forecast is how many commits in the last BLAST_WINDOW_DAYS
    touched this watch set, and effective_blast_floor is the P90 of that
    over live path-claims (BLAST_ADVISORY_FLOOR is the cold-start
    fallback). Until now it only advised. This row raises it to a refusal
    with the SAME two exits the cardinality arm offers, so there is one
    bargain to learn rather than two.

    IT RUNS AFTER blast-forecast-adr039, not inside it. That row is a
    fact-gatherer whose docstring promises it never refuses, and a gate
    that quietly grew a refusal inside a row documented as advisory is the
    drift this table exists to prevent. Facts there, decision here.

    A SELF-TIGHTENING THRESHOLD, stated rather than discovered later: the
    floor is a PERCENTILE of the live population, so as broad watch sets
    are narrowed the floor falls and the bar rises. That is deliberate
    (ADR-039 chose a self-calibrating floor precisely so a constant could
    not go quietly cold), but it does mean a set that is legal today can
    be refused next month with no code change. The two exits are what
    keep that survivable: a reviewed policy is never re-litigated, and a
    stated basis is re-asked on the ADR-032 clock rather than at random.

    Abstains when the forecast is absent -- shallow or unavailable git
    history computes nothing, and a floor is not a bound (ADR-039). A
    refusal built on a truncated log would be the quietly-cold number
    that ADR forbids, pointing the wrong way."""
    forecast = ctx.get("blast_forecast")
    if forecast is None or not ctx["paths"]:
        return None
    # STRUCTURAL EXEMPTION (step 3.1): the refusal is decided over the
    # SELECTOR-FREE subset, and ctx["blast_forecast"] is deliberately left
    # alone -- ADR-039's advisory keeps reporting the file-level number.
    #
    # Two different questions, so two numbers. blast_forecast counts
    # commits that touched the FILE. For `package.json#/dependencies/
    # stripe` that is an upper bound so loose it is nearly noise: every
    # dependency bump in the repo is in it, and approximately none of
    # them move the sub-tree. Refusing on it would refuse precisely the
    # mechanism that fixes churn -- the author narrows a hot glob to the
    # key their recipe reads, and the gate that asked them to narrow it
    # then refuses the narrowed version, because the file underneath is
    # still hot. That is the gate teaching its own bypass (ADR-049), and
    # the bypass it teaches is "go back to the wide glob".
    #
    # The advisory keeps the wide number because it is still TRUE as an
    # upper bound, and a selector claim on a genuinely hot file is worth
    # a line of prose. It is not worth a refusal.
    plain = [p for p in ctx["paths"] if not split_selector_target(p)[1]]
    if not plain:
        return None
    if plain != ctx["paths"]:
        forecast = blast_forecast(plain, ctx.get("blast_history"))
    floor, source = effective_blast_floor(ctx["claims"],
                                          ctx.get("blast_history"))
    if forecast < floor:
        return None
    # Record that this arm WOULD have refused, before the exits clear it.
    # paths-budget-max runs next and owns the "a basis with nothing to
    # excuse is schema noise" check; without this flag it cannot tell a
    # pointless --paths-ok from one that is excusing BREADTH on a single
    # path -- and it refused exactly that legitimate case until this line
    # existed (caught by canary BF1b).
    ctx["churn_over"] = True
    if ctx.get("watch_policy") or ctx.get("paths_basis"):
        return None
    return (f"truth: this watch set matched {forecast} commits in the last "
            f"{BLAST_WINDOW_DAYS}d, at or above the churn floor of {floor} "
            f"({source}) -- ADR-039. Breadth, not entry count, is what "
            "costs attention: the pre-edit whisper names this claim on "
            "every one of those commits, and on this ledger ten claims "
            "produced 35% of all whisper lines. Either:\n"
            f"  --watch-policy <name>   a reviewed set from {WATCH_POLICIES_REL}\n"
            "  --paths-ok \"<sentence>\"  why this breadth is right "
            "(stored, decays at 30 days, counted)\n"
            "  path.json#/a/b          watch the SUB-TREE, not the file: "
            "a selector target is judged on whether ITS digest moved, so "
            "it is outside this floor entirely\n"
            "  ...or narrow the globs to the files the recipe actually reads.\n"
            "Nothing was filed.")

INTAKE_GATES = (
    ("pre-execution", "text-nonempty", _gate_text_nonempty),
    ("pre-execution", "near-duplicate-g8", _gate_duplicate),
    ("pre-execution", "quantifier-scope-adr007", _gate_quantifier_scope),
    ("pre-execution", "paths-inv-m", _gate_inv_m),
    # BREADTH BEFORE COUNT, and the order is load-bearing. Measured on
    # this ledger: all 17 freehand claims at or above the ADR-039 churn
    # floor carry 2+ paths, so with the cardinality row first the churn
    # row could never fire -- a gate whose population is empty by
    # construction, which is the dark-gate defect this repo refuses.
    # Reversed, the churn row fires on all 17 and the author gets the
    # ACTIONABLE message ("narrow these globs") instead of the merely
    # true one ("you have four paths"). blast-forecast-adr039 moves up
    # with it because it is the fact-gatherer the churn row reads; it
    # costs one `git log`, and paths-inv-m already pays a `git ls-files`
    # one row earlier, so no filing newly pays git that did not before.
    ("pre-execution", "blast-forecast-adr039", _gate_blast),
    ("pre-execution", "paths-churn-budget", _gate_paths_churn),
    ("pre-execution", "paths-budget-max", _gate_paths_budget),
    ("pre-execution", "generated-paths-adr037", _gate_generated),
    ("pre-execution", "scope-decay-adr032", _gate_scope_decay),
    ("pre-execution", "class-precheck", _gate_class_precheck),
    ("post-execution", "evidence-exit-adr035", _gate_evidence_exit),
    # further post-execution rows land with the linter and blast ADRs
)

def run_intake_stage(stage, ctx):
    """Iterate the table's rows for one stage, in table order; the first
    refusal wins. Returns that refusal STRING, or None when the stage
    passes. Any I/O lives inside individual gate fns exactly as it did
    inline before ADR-034.

    A1: this used to `sys.exit(err)`, and that was the table's own
    contract broken one frame up -- every row of INTAKE_GATES returns a
    refusal string and promises not to decide what happens to it, and
    then the function that runs the table decided. ADR-043's R14a had
    already made exactly this argument for two policy loaders ("they
    sys.exit-ed two frames below a gate table whose stated contract is
    'gate fns return a refusal string'") and the argument was never
    applied to the runner itself.

    The cost of the old shape was not style: nothing could compose. No
    batch intake, no embedding, no recover-and-continue, and testing a
    refusal meant spawning a subprocess instead of calling a function.
    The two callers in build_claim_payload now exit on a non-None
    return, so every refusal reaches the user through the same path with
    the same bytes."""
    for st, _name, fn in INTAKE_GATES:
        if st != stage:
            continue
        err = fn(ctx)
        if err:
            return err
    return None
