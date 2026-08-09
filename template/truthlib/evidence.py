"""truthlib.evidence -- the evidence discipline (C2): command screens,
recipe lints, determinism, recheck, and the reaffirm triage.

Pure: the shell gathers (allowlists, run output, sessions) and this
module decides.  One screen implementation (ADR-009/014), one screen-side
tokenizer (_evidence_toks), the ADR-035 exit gate, and the R3/ADR-030
triage that owns every reaffirm decision.
"""
import re
import shlex

from truthlib.registry import *
from truthlib.kernel import *

# ADR-009 (v0.6.2, F1) / ADR-021 (H4): allowlisted programs whose own
# options open an exec or file-write channel the bare-name screen cannot
# see. Keyed by program; an argument whose '='-prefix is listed is refused
# even though the program is allowlisted. THIS IS A BLOCKLIST AND A
# BLOCKLIST CANNOT BOUND AN INTERPRETER OR VCS: it is defense-in-depth for
# a few shipped programs' KNOWN write channels (find's -exec/-fprint*,
# sort's -o/--output/--compress-program), NOT a safety guarantee. `git` is
# the standing example -- its exec/write surface is unbounded by flags
# (filter-branch --tree-filter, bundle, archive -o, config --file,
# worktree, format-patch -o, checkout-index, bisect run, submodule
# foreach, -c <k>=!cmd aliases, ...), no enumerable deny set closes it, so
# git is NOT in the shipped default allowlist and MUST NOT be added for
# evidence use (ADR-021). The git entry below only blunts a few top-level
# flags for a consumer who re-adds it against that advice; it does not
# make git safe.
PROGRAM_ARG_DENY = {
    "find": frozenset(("-exec", "-execdir", "-ok", "-okdir", "-delete",
                       "-fprintf", "-fprint", "-fprint0", "-fls")),
    "sort": frozenset(("-o", "--output", "--compress-program")),
    "git": frozenset(("-c", "--exec-path", "-p", "--paginate", "-O", "-o",
                      "--output")),
}

def determinism_error(run1, run2):
    """G6: two intake executions must agree, else recheck will lie later."""
    if run1 != run2:
        return ("truth: evidence command is nondeterministic -- two "
                "runs produced different output (G6). Make it "
                "deterministic (sort, strip timestamps) or accept the "
                "false-divergence risk explicitly with --single-run.")
    return None

def evidence_exit_warning(evidence_class, returncode):
    """field-notes-batch-m item 2 remedy: `claim --class VERIFIED` files
    on *determinism* (the G6 double-run hash-matches), not on exit 0, so
    a stably-failing probe used to file clean and "recheck" forever by
    stable failure -- a hollow VERIFIED, an INV-M dead tripwire one
    level up (two real instances caught by a verifier, never by
    filing). Since ADR-035 the positive-sentence slice is REFUSED at
    intake (evidence_exit_error); this advisory voices the remaining
    absence-proof/legacy population.
    Non-blocking by design: a non-zero-but-stable probe can be a
    legitimate fact to record, so this returns a warning line (or None)
    for the shell to print on stderr AFTER the successful append --
    never a refusal, and the filing's exit code is untouched."""
    if evidence_class != "VERIFIED" or not returncode:
        return None
    return (f"evidence command exited {returncode} -- a "
            "VERIFIED claim usually demonstrates its fact with a passing "
            "command; a stably-failing probe verifies nothing (consider "
            "`... && echo OK` or a positive assertion)")

def evidence_exit_error(text, returncode, exit_basis):
    """ADR-035: the positive-claim exit gate. A VERIFIED filing whose
    sentence carries no NEGATION_TOKENS token asserts presence -- a
    failing evidence command demonstrates nothing it says (the pilot's
    QB-011 hollow shape; simulated over 244 real filings: 5 refusals,
    all genuine, zero false). Absence proofs -- a negation token in the
    text -- keep the v0.9.11 warning path: grep proving absence exits 1,
    and that exit IS the demonstration. The token test proxies the
    SENTENCE's polarity, not the recipe's: an inverted recipe (! grep)
    exits 0 and passes silently; a differential proof (diff exiting 1)
    pays a --evidence-exit-ok basis, counted in override_report. Pure;
    the recorded first-run returncode is passed in. Returns a refusal
    string or None."""
    if not returncode:
        if exit_basis:
            return ("truth: --evidence-exit-ok with a passing command -- "
                    "the evidence exited 0, so there is nothing to excuse "
                    "(ADR-035: a basis with nothing to excuse is schema "
                    "noise; drop the flag)")
        return None
    if tokens(text) & NEGATION_TOKENS:
        return None
    if exit_basis:
        return None
    return (f"truth: a positive claim's evidence exited {returncode} -- "
            "the command demonstrates nothing the sentence asserts (a "
            "hollow VERIFIED, ADR-035). Fix the recipe, or state why a "
            "failing command proves this sentence: "
            "--evidence-exit-ok \"<basis>\".")

_SCREEN_SEPARATORS = frozenset((";", "|", "||", "&&", "&"))
_SCREEN_PUNCT = frozenset("();<>|&")

def _evidence_toks(cmd):
    """The ONE screen-side tokenization of an evidence command (shlex
    posix + punctuation mode, whitespace_split) -- shared by the ADR-009
    screen and the ADR-037 recipe lints. A second screen-side parser is
    forbidden (the F1/F5 drift lesson; a whitespace splitter would be
    gameable by quote-splitting, 'v0.9''.8'). Returns (toks, err)."""
    lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    try:
        return list(lex), None
    except ValueError as e:
        return None, f"unparseable command ({e}) (ADR-009)"

# ADR-037: recipe-lint lexicons. Shapes and carve-outs change only with
# the RC-canary faults (the ADR-007 constants-with-faults precedent).
GREP_FAMILY = frozenset(("grep", "rg", "egrep", "fgrep", "zgrep"))
VERSION_SHAPE_RE = re.compile(r"\bv?\d+\.\d+(?:\.\d+)?\b")
DATE_SHAPE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
SCHEMA_ID_RE = re.compile(r"truth-ledger-record\.v\d")
FROZEN_DATE_RE = re.compile(r"(?:Accepted|Amended|Date:)\s*\(?\d{4}-")

def recipe_lints(cmd):
    """ADR-037: warnings, never refusals (a gate refusing legitimate
    filings teaches its own bypass -- ADR-014's confused-deputy lesson)
    about evidence recipes with a known expiry. Three carve-outs, each a
    measured legitimate-invariant class: a token containing '/' is
    path-context (filenames legitimately carry versions and dates), the
    schema-$id shape is a deliberately release-independent anchor (the
    very fix of the tr-22853f21 defect), and a frozen-record date
    (Accepted/Amended/Date headers) never changes. Pure; consumes the
    screen's own token stream."""
    if not cmd:
        return []
    toks, err = _evidence_toks(cmd)
    if not toks or err:
        return []
    msgs = []
    program, expecting, n_flagged = None, True, False
    for t in toks:
        if t in _SCREEN_SEPARATORS:
            expecting, program = True, None
            continue
        if t and set(t) <= _SCREEN_PUNCT:
            continue
        if expecting:
            program, expecting = t, False
            continue
        # Per-token: a literal '-n' PATTERN (grep -e -n) false-fires;
        # warning-only, accepted (arg-value parsing is the screen's own
        # stated non-goal).
        if program in GREP_FAMILY and t in ("-n", "--line-number") \
                and not n_flagged:
            n_flagged = True
            msgs.append("recipe: -n makes the output shift under "
                        "unrelated edits -- mechanical divergence on the "
                        "first insertion above the match (ADR-012/"
                        "ADR-037). Drop -n unless the line number is the "
                        "fact.")
            continue
        if "/" in t or SCHEMA_ID_RE.search(t):
            continue
        m = VERSION_SHAPE_RE.search(t)
        if m:
            msgs.append(f"recipe: {m.group(0)!r} is a volatile literal "
                        "with a release-shaped expiry (ADR-037) -- anchor "
                        "to an invariant (a def/test name, an ADR id, a "
                        "FAULT tag) or file with --ttl-days. A deliberate "
                        "version pin is legitimate; its divergence at the "
                        "next bump is genuine, successor material.")
            continue
        d = DATE_SHAPE_RE.search(t)
        if d and not FROZEN_DATE_RE.search(t):
            msgs.append(f"recipe: {d.group(0)!r} is a date-shaped "
                        "literal with a calendar expiry (ADR-037) -- "
                        "anchor to an invariant unless the date names a "
                        "frozen record.")
    return msgs

def screen_evidence_command(cmd, allowlist, allow_rel=EVIDENCE_ALLOW_REL,
                            missing_tail=None, unlisted_hint=None,
                            allow_paths=False, denylist=None):
    """ADR-009: evidence commands re-execute later in a *verifier's*
    session (recheck) -- deferred code execution across the trust seam
    G11 protects. Static screen over a QUOTE-AWARE token stream (shlex
    punctuation mode -- a '|' inside a quoted grep regex is an argument,
    not a pipe; the first real ledger command proved the naive split
    wrong): every segment's program must be a bare name on the
    allowlist; no command substitution; output redirection only to the
    bit bucket ('>/dev/null') or an fd dup ('2>&1') -- the pin-the-
    output convention depends on those. Input redirection (<) is
    read-only and allowed. Returns an error string or None.

    ADR-014 reuses this screen verbatim for acceptance oracles via
    screen_accept_command (a second screen implementation is forbidden
    -- the F1/F5 drift lesson); only the allowlist and the two
    list-naming messages differ."""
    if allowlist is None:
        return ("no command allowlist at " + allow_rel +
                " -- the safety screen fails closed. " +
                (missing_tail or "Create it (one command name per line; "
                 "the template ships a read-only default) before filing "
                 "VERIFIED claims (ADR-009)."))
    if "$(" in cmd or "`" in cmd:
        return ("command substitution ('$(' or backtick) is not "
                "screenable (ADR-009)")
    # ADR-021 (H4): the screen tokenizes with shlex but run_evidence
    # executes with /bin/sh (shell=True). shlex's whitespace set includes
    # newline and CR, so it drops a post-newline program into ARGUMENT
    # position while /bin/sh treats a newline as a statement separator and
    # runs it -- a screen/executor tokenizer mismatch that smuggles an
    # unscreened command into a verifier's recheck session. Refuse every
    # ASCII control character except tab (tab is word-whitespace to both):
    # evidence commands must be a single printable line.
    ctrl = next((c for c in cmd
                 if (ord(c) < 0x20 and c != "\t") or ord(c) == 0x7f), None)
    if ctrl is not None:
        return (f"control character {ctrl!r} is not screenable -- it is "
                "word-whitespace to the screen's lexer but a command "
                "separator to the executing shell (a newline is /bin/sh's "
                "statement terminator); evidence commands must be a single "
                "printable line (ADR-021)")
    toks, tok_err = _evidence_toks(cmd)
    if tok_err:
        return tok_err
    if not toks:
        return "empty command (ADR-009)"
    expecting_program = True
    program = None  # the current segment's program, for arg-level screening
    redir = None  # 'in' | 'out' when the next token is a redirection target
    for tok in toks:
        if redir:
            if redir == "out" and tok != "/dev/null" and not tok.isdigit():
                return (f"output redirection to {tok!r} is refused -- "
                        "evidence commands must be read-only; '/dev/null' "
                        "and fd dups ('2>&1') are the only allowed sinks "
                        "(ADR-009)")
            redir = None
            continue
        if tok in _SCREEN_SEPARATORS:
            expecting_program = True
            program = None
            continue
        if tok and set(tok) <= _SCREEN_PUNCT:
            if tok.startswith("<"):
                redir = "in"    # reads are fine, any source
            elif tok.startswith(">"):
                redir = "out"   # writes only to /dev/null or an fd
            else:
                return f"unscreenable shell construct {tok!r} (ADR-009)"
            continue
        if expecting_program:
            if denylist and tok in denylist:
                # ADR-022: deny-wins over the allowlist. Shells/executors
                # are never read-only evidence; refuse even if a consumer
                # allowlisted one by accident (the H4 footgun).
                return (f"'{tok}' is on the template-owned evidence deny "
                        f"baseline ({EVIDENCE_DENY_REL}) -- shells and "
                        "generic executors turn the read-only screen into "
                        "arbitrary execution and are never valid evidence, "
                        "even if allowlisted (ADR-022). To run repository "
                        "code on purpose, use an acceptance oracle (ADR-014).")
            if "/" in tok:
                # Issue #7 (v0.7.2, accept screen only): an ALLOWLISTED
                # exact repo-relative path may run as an oracle -- the
                # committed entry bounds precisely which executable, which
                # is stronger than an interpreter bare-name. Absolute
                # paths and `..` segments never pass; the evidence screen
                # (allow_paths=False) keeps ADR-009's blanket refusal.
                if allow_paths and tok in allowlist \
                        and not tok.startswith("/") \
                        and ".." not in tok.split("/"):
                    expecting_program = False
                    program = tok
                    continue
                return (f"program {tok!r} is a path, not a bare command "
                        "name -- " +
                        ("add the exact repo-relative path to "
                         f"{allow_rel} to admit it as an oracle; absolute "
                         "paths and '..' never pass (issue #7, ADR-014)"
                         if allow_paths else
                         "repo-local executables are not screenable "
                         "(ADR-009)"))
            if tok not in allowlist:
                return (f"'{tok}' is not in {allow_rel}. " +
                        (unlisted_hint or "Add it there if it is read-only "
                         "and you accept it re-running inside verifier "
                         "sessions, or file with --evidence-unsafe-ok "
                         "(recheck will then refuse to execute it) "
                         "(ADR-009)."))
            expecting_program = False
            program = tok
        else:
            # F1/v0.6.2: an allowlisted program can still open an exec or
            # file-write channel through its own flags (find -exec, sort
            # -o, git -c alias=!cmd). The bare-name check above cannot see
            # this; the per-program deny table can.
            denied = PROGRAM_ARG_DENY.get(program)
            if denied and tok.split("=", 1)[0] in denied:
                return (f"{program} {tok.split('=', 1)[0]!r} opens an exec "
                        "or file-write channel -- evidence commands must be "
                        "read-only, and this one would re-run inside a "
                        "verifier session (ADR-009)")
    if expecting_program or redir:
        return "dangling operator at end of command (ADR-009)"
    return None

def screen_accept_command(cmd, allowlist):
    """ADR-014: acceptance oracles execute REPOSITORY CODE at `done`
    time inside the closing session -- that is their purpose, so
    ADR-009's read-only rationale does not apply, but its structural
    screen does: the committed .truth/accept-allow bounds WHICH programs
    a work item filed in one session may cause a later session to run.
    Same screen function, different allowlist (one implementation)."""
    return screen_evidence_command(
        cmd, allowlist, allow_rel=ACCEPT_ALLOW_REL,
        missing_tail=("Create it (one command name per line; entries "
                      "execute repository code at `done` time -- that is "
                      "their purpose) before filing an --accept-cmd "
                      "(ADR-014)."),
        unlisted_hint=("Add it there if you accept it executing at `done` "
                       "time inside the closing session, or file the issue "
                       "with --accept-unsafe-ok (`done` will then refuse "
                       "to execute the oracle) (ADR-014)."),
        allow_paths=True)

# --------------------------------------------------- verdict decisions

def recheck_verdict(evidence, digest, returncode):
    """Deterministic recheck rules. exit 127 = environment, not reality."""
    if returncode == 127:
        return "cannot_verify", "recheck: evidence command not found (exit 127)"
    ok = ("sha256:" + digest == evidence["output_hash"]) \
        and returncode == evidence.get("returncode", returncode)
    return ("agree" if ok else "diverge",
            f"recheck: output hash {'matches' if ok else 'MISMATCH'} recorded evidence")

NO_EVIDENCE_VERDICT = ("cannot_verify",
                       "recheck requested but claim carries no evidence command")

# ------------------------------------------ reaffirm triage (R3, ADR-030)

REAFFIRM_BASIS = "reaffirm: hash-match, no judgment re-run"
REAFFIRM_ARMS = ("ttl", "manual", "same_session", "match", "mismatch")

def latest_invalidation_reason(events, cid):
    """The reason of the claim's LATEST invalidation record, latest by
    fold_key (the ADR-016 total order), never by file position -- the
    triage must key off the same order the fold's status does. ADR-019:
    TTL expiry is materialized by the scan as an invalidation record and
    the fold reads no clock, so TTL-staleness is a property of this
    record's reason, not something reaffirm may recompute. Returns the
    reason string, or None when no invalidation names the claim."""
    best_key, reason = None, None
    for ne in events:
        ev = ne[1]
        p = ev.get("payload") or {}
        if ev.get("kind") != "invalidation" or p.get("claim") != cid:
            continue
        k = fold_key(ne)
        if best_key is None or k > best_key:
            best_key, reason = k, p.get("reason")
    return reason

def is_ttl_reason(reason):
    """ADR-019/030: does an invalidation reason mean TTL expiry? Matches
    what _ttl_expired writes ('ttl expired (N days)') by prefix, so the
    check and the writer cannot drift on the parenthetical. FALLBACK
    ONLY since the scan started stamping reason_code (v0.9.12 red-team
    F3): ttl_staleness prefers the structured code and consults this
    prefix just for records that predate the stamp."""
    return bool(reason) and reason.startswith("ttl expired")

def ttl_staleness(events, cid):
    """Red-team F3 hardening: is the claim TTL-staled, for triage arm 1?
    Prefers the structured `reason_code: "ttl"` the scan stamps on TTL
    invalidations over free-text parsing. ADR-019 makes TTL expiry
    MONOTONE -- the scan is the only clock reader, the clock never runs
    backwards, and re-verification never resets the TTL -- so ANY
    reason_code=="ttl" invalidation on the claim is durable proof of TTL
    staleness: a LATER invalidation carrying a different free-text
    reason (including a raw-appended forgery) can no longer flip the
    claim out of the re-file arm and into auto-agree. Records that
    predate the stamp have no reason_code, so the latest-reason prefix
    match remains the fallback there; a raw append can still forge that
    plain text -- the general forged-record residual ADR-030 accepts
    (paper sec 8 item 6)."""
    if any(ev.get("kind") == "invalidation"
           and (ev.get("payload") or {}).get("claim") == cid
           and ev["payload"].get("reason_code") == "ttl"
           for _, ev in events):
        return True
    return is_ttl_reason(latest_invalidation_reason(events, cid))

def latest_evidence_refresh(events, cid):
    """ADR-051: the newest `evidence_refresh` filed for the claim, by
    fold_key (the ADR-016 total order), never by file position -- the
    same rule latest_invalidation_reason uses, for the same reason: a
    reader that keys off append order disagrees with the fold on a
    union-merged ledger. Returns the refresh payload or None. Pure."""
    best_key, refresh = None, None
    for ne in events:
        ev = ne[1]
        p = ev.get("payload") or {}
        if ev.get("kind") != "verdict" or p.get("claim") != cid:
            continue
        r = p.get("evidence_refresh")
        if not r:
            continue
        k = fold_key(ne)
        if best_key is None or k > best_key:
            best_key, refresh = k, r
    return refresh

def effective_evidence(capsule, refresh):
    """ADR-051: the capsule a recheck must compare against -- the claim's
    own, with output_hash/returncode overridden by the newest refresh.
    THIS FUNCTION IS THE READER that admits `evidence_refresh` under
    ADR-046's envelope rule; without a consumer the field would be
    decoration and must not exist.
    Why a refresh is needed at all: an `agree` advances the claim's
    EFFECTIVE ANCHOR (F2) so re-verified claims stop re-staling from a
    frozen base, but the capsule lives in the immutable claim record and
    never moved with it. A human who correctly judged that a changed
    output does not disturb the sentence (a grep -n line shift, a count
    that grew) therefore left the claim live and PERMANENTLY
    un-recheckable: every later recheck compares against a hash that can
    no longer be produced, so it auto-diverges, and reaffirm's
    hash-match arm can never take the claim back. Anchor and capsule now
    move together or neither. Pure; a None refresh returns the capsule
    unchanged, so every pre-ADR-051 record behaves exactly as before."""
    if not capsule or not refresh:
        return capsule
    out = dict(capsule)
    if refresh.get("output_hash"):
        out["output_hash"] = refresh["output_hash"]
    if "returncode" in refresh:
        out["returncode"] = refresh["returncode"]
    return out

def previously_agreed(events, cid):
    """ADR-030: has ANY agree verdict ever been filed for the claim?
    Reaffirm re-confirms a verification that already happened; a stale
    claim nobody ever agreed with has no verification to re-confirm --
    auto-filing its FIRST agree would be a first verification without
    judgment, exactly what `verdict --recheck` refuses to do."""
    return any(ev.get("kind") == "verdict"
               and (ev.get("payload") or {}).get("claim") == cid
               and ev["payload"].get("verdict") == "agree"
               for _, ev in events)

def reaffirm_triage(entry, invalidation_reason, current_session, was_agreed,
                    screen_err=None, recheck=None, ttl_staled=None):
    """R3 / ADR-030: the ONE decision per stale claim -- which arm, and
    what reaffirm does about it. Pure: the shell gathers the facts
    (latest invalidation reason, sessions, current-allowlist screen
    result, recheck outcome, and since the red-team F3 hardening the
    structured `ttl_staled` fact from ttl_staleness -- when the shell
    passes it, it overrides the free-text prefix fallback on
    invalidation_reason) and applies the effects; nothing here reads
    a clock, the env, or a file. Returns {"arm", "action"}; arm is one
    of REAFFIRM_ARMS, or the "execute" sentinel telling the shell to run
    the screened recheck and call again with its result. Arm order is
    the R3 contract (TTL, then unexecutable, then session, then the
    recheck outcome), so e.g. a TTL-staled unscreened claim reports the
    TTL re-file path, its more fundamental disability.

    Only a hash-match ever files, and only as `agree` (the one verdict a
    matching hash mechanically supports, given a prior agree to
    re-confirm). A MISMATCH files NOTHING -- not diverge either: whether
    a changed hash is mechanical (recipe drift) or genuine (reality
    moved) is ADR-012's judgment call, and a batch verb has no judge; it
    reports the claim for the dispatch path instead."""
    p = entry["claim"]["payload"]
    ev = p.get("evidence") or {}
    if (ttl_staled if ttl_staled is not None
            else is_ttl_reason(invalidation_reason)):
        return {"arm": "ttl",
                "action": "skipped -- re-file required (ADR-019: TTL "
                          "never resets by re-verification)"}
    if ev.get("screened") is False:
        # The recheck refusal discipline (ADR-009/029): screened=false is
        # the author's own admission, final; the command NEVER executes.
        return {"arm": "manual",
                "action": "skipped -- filed with --evidence-unsafe-ok "
                          "(evidence.screened=false): manual verification "
                          "only (ADR-009)"}
    if entry["claim"].get("session") == current_session:
        return {"arm": "same_session",
                "action": "skipped -- authored by this session; reaffirm "
                          "must not self-agree (ADR-010): dispatch to a "
                          "fresh session"}
    if not ev.get("command"):
        return {"arm": "manual",
                "action": "skipped -- no evidence command recorded: "
                          "manual verification only"}
    if not was_agreed:
        return {"arm": "manual",
                "action": "skipped -- never agreed by any verifier: first "
                          "verification is a judgment, not a "
                          "re-confirmation; dispatch it (ADR-030)"}
    if screen_err:
        return {"arm": "manual",
                "action": "skipped -- recheck will not execute this "
                          f"evidence command ({screen_err}): manual "
                          "verification only"}
    if recheck is None:
        return {"arm": "execute", "action": "run the screened recheck"}
    verdict = recheck[0]
    if verdict == "agree":
        return {"arm": "match", "action": "hash-match -- " + REAFFIRM_BASIS}
    if verdict == "cannot_verify":  # recheck_verdict's exit-127 rule
        return {"arm": "manual",
                "action": "skipped -- evidence command not found at "
                          "recheck (exit 127): environment, not reality; "
                          "manual verification only"}
    return {"arm": "mismatch",
            "action": "diverged evidence -- dispatch for judgment "
                      "(nothing filed: mechanical-vs-genuine is ADR-012's "
                      "call, never a batch verb's)"}
