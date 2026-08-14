"""truthlib.advisory -- what the CLI prints BESIDE a result and never
instead of one: the CC-1 block, the facts it needs to decide, and its
rendering.

That sentence is the criterion (A2). Before the split this module said
"advisory assembly and the pure report family", and `family` was the
tell -- a collection, not a criterion, and a module defined negatively
is where the next drift lands. One already had: reaffirm_cleared is
written in cli and read here as a bare presence boolean, with its
contents read by nothing.

Left this module in the split: the pure report family -> truthlib.reports,
the two exact machine surfaces -> truthlib.contract, and
citation_block_paths -> truthlib.policy, because deciding which citation
BLOCKS a tombstone is a refusal, not advice.

Pure: facts arrive as data; nothing here probes the world.
"""
import re
import statistics

from truthlib.registry import *
from truthlib.kernel import *
from truthlib.evidence import *
from truthlib.policy import *
from truthlib.reports import *

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

def ttl_suggestion(observations, tier):
    """FS-1: observed median half-life for the tier, or None below the
    observation threshold (suggestions from noise are worse than none).
    Suggestion only -- TTLs stay author decisions."""
    days = [d for t, d in observations if t == tier]
    if len(days) < HALF_LIFE_MIN_OBS:
        return None
    return round(statistics.median(days), 1)

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
