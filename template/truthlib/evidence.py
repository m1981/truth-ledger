"""truthlib.evidence -- the evidence discipline (C2): command screens,
recipe lints, determinism, and recheck.

Pure: the shell gathers (allowlists, run output, sessions) and this
module decides.  One screen implementation (ADR-009/014), one screen-side
tokenizer (_evidence_toks), and the ADR-035 exit gate.

The Reproduce-on-Read refactor (step 2.6) removed the R3/ADR-030 reaffirm
triage that used to be the fourth item here; what remains of it is read-side
(REAFFIRM_BASIS, latest_invalidation_reason, ttl_staleness), because the
ledger's historical records still have to be interpretable.
"""
import re

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

# --- ADR-041: the ONE lexer ----------------------------------------------
# Until ADR-041 the screen tokenized an evidence command with shlex and
# the executor handed the SAME STRING to /bin/sh: two interpreters, and
# every divergence between them was a channel. ADR-021 closed the newline
# (word-whitespace to shlex, a statement separator to sh); the 2026-08-01
# review then found `uniq *` (one word to shlex, N to sh), `cat <>F` (a
# WRITE the '<' branch read as input) and `>1` (a file named '1' behind
# the fd-dup carve-out). Enumerating divergences does not terminate,
# because only /bin/sh implements /bin/sh.
#
# So the shell is gone from the evidence path. This lexer is the only
# reader of an evidence command; its output feeds BOTH the screen and the
# runner, and what it cannot express is refused rather than approximated.
#
# Why not shlex any more: shlex's stream cannot tell `2>&1` from `2 >&1`
# -- both lex to ['2', '>&', '1'] -- while /bin/sh reads the first as an
# fd redirection and the second as an argument plus a dup. A screen that
# cannot see that difference cannot gate an executor that acts on it, and
# under shell=False the argv IS the decision. The quoting rules below are
# the POSIX word subset the runner can honour exactly: single quotes,
# double quotes, backslash, and NOTHING that expands (no $VAR, no `cmd`,
# no ~, no arithmetic) -- an evidence recipe that expands its environment
# is not reproducible in a verifier's session anyway (ADR-009).

_SCREEN_SEPARATORS = frozenset((";", "|", "||", "&&"))
_SCREEN_PUNCT = frozenset("();<>|&")
_OPERATOR_CHARS = "|&;<>"
_GLOB_META = "*?["
# The redirections the runner can express as subprocess parameters, and
# therefore the only ones that survive the parse (ADR-041 decision 2).
_REDIR_OPS = ("<", ">", ">>", ">&")

# POSIX: '$' begins an expansion only when what follows can NAME one --
# a parameter, a brace, a subshell, or one of the special parameters.
# Everywhere else it is an ordinary character, which is why `grep "a$"`
# and `grep 'a$'` are the same anchored regex to /bin/sh and stay the
# same command here. Refusing every '$' would have failed a common
# recipe shape for a divergence that does not exist.
_EXPANSION_STARTERS = frozenset("{(@*#?-$!_0123456789")

def _starts_expansion(cmd, i):
    """Would /bin/sh expand the '$' at cmd[i]?"""
    nxt = cmd[i + 1] if i + 1 < len(cmd) else ""
    return bool(nxt) and (nxt.isalpha() or nxt in _EXPANSION_STARTERS)

def _glob_quote(s):
    """Neutralize glob metacharacters that came out of QUOTES. `'*'` is a
    literal star to the shell and must stay one after expansion, so the
    pattern half of a word escapes exactly the characters the text half
    took from a quoted or backslash-escaped span."""
    return "".join("[" + c + "]" if c in _GLOB_META else c for c in s)

def _lex_word(cmd, i, shell_free):
    """One shell WORD, from cmd[i] up to the first unquoted whitespace or
    operator character.

    Returns (text, pat, has_meta, quoted, j, err). `text` is the word
    after quote removal -- what the shell would have passed as an argv
    entry with no pathname expansion. `pat` is the same word as a glob
    PATTERN, with metacharacters that came out of quotes escaped, and it
    is the runner's input when `has_meta` says an UNQUOTED metacharacter
    is present. Keeping both is what makes `uniq '*'` and `uniq *` two
    different commands here, as they are to the shell and were not to the
    old screen."""
    n = len(cmd)
    text, pat = [], []
    has_meta = quoted = False
    while i < n:
        c = cmd[i]
        if c in " \t" or c in _OPERATOR_CHARS:
            break
        if c in "()":
            return None, None, False, False, i, (
                f"unscreenable shell construct {c!r} -- a subshell has no "
                "argv equivalent, and the runner executes argv (ADR-041)")
        if c == "`":
            return None, None, False, False, i, (
                "command substitution (backtick) is not screenable (ADR-009)")
        if c == "$" and shell_free and _starts_expansion(cmd, i):
            return None, None, False, False, i, (
                "'$' expansion is not available in an evidence command -- "
                "the runner executes argv and never a shell (ADR-041), so a "
                "value the shell used to substitute would now be a literal, "
                "silently changing the recorded output. Quote it ('$') if "
                "the character is the fact; an environment-dependent recipe "
                "is not reproducible in a verifier's session anyway (ADR-009).")
        if c == "~" and not text and shell_free:
            return None, None, False, False, i, (
                "'~' expansion is not available in an evidence command -- it "
                "would name a different directory in every verifier's "
                "session; write the repo-relative path (ADR-041)")
        if c == "\\":
            if i + 1 >= n:
                return None, None, False, False, i, (
                    "trailing backslash escapes nothing (ADR-041)")
            text.append(cmd[i + 1])
            pat.append(_glob_quote(cmd[i + 1]))
            quoted = True
            i += 2
            continue
        if c == "'":
            j = cmd.find("'", i + 1)
            if j < 0:
                return None, None, False, False, i, (
                    "unbalanced single quote (ADR-041)")
            text.append(cmd[i + 1:j])
            pat.append(_glob_quote(cmd[i + 1:j]))
            quoted = True
            i = j + 1
            continue
        if c == '"':
            i += 1
            quoted = True
            while True:
                if i >= n:
                    return None, None, False, False, i, (
                        "unbalanced double quote (ADR-041)")
                d = cmd[i]
                if d == '"':
                    i += 1
                    break
                if d == "`":
                    return None, None, False, False, i, (
                        "command substitution (backtick) is not screenable "
                        "(ADR-009)")
                if d == "$" and shell_free and _starts_expansion(cmd, i):
                    return None, None, False, False, i, (
                        "'$' expands inside double quotes -- the runner "
                        "executes argv and never a shell (ADR-041); use "
                        "single quotes if the character is the fact")
                if d == "\\" and i + 1 < n and cmd[i + 1] in '"\\`$':
                    text.append(cmd[i + 1])
                    pat.append(_glob_quote(cmd[i + 1]))
                    i += 2
                    continue
                text.append(d)
                pat.append(_glob_quote(d))
                i += 1
            continue
        if c in _GLOB_META:
            has_meta = True
        text.append(c)
        pat.append(c)
        i += 1
    return "".join(text), "".join(pat), has_meta, quoted, i, None

def _lex_operator(cmd, i):
    """The operator at cmd[i]. Returns (op, j, err)."""
    c, two = cmd[i], cmd[i:i + 2]
    if c == "&":
        if two == "&&":
            return "&&", i + 2, None
        return None, i, (
            "'&' backgrounds a command -- the runner executes argv and "
            "waits for it (ADR-041), and a backgrounded probe's output is "
            "not reproducible evidence (ADR-009)")
    if c == "|":
        return ("||", i + 2, None) if two == "||" else ("|", i + 1, None)
    if c == ";":
        if two == ";;":
            return None, i, "';;' belongs to a case statement (ADR-041)"
        return ";", i + 1, None
    if c == ">":
        if two == ">>":
            return ">>", i + 2, None
        if two == ">&":
            return ">&", i + 2, None
        return ">", i + 1, None
    if two == "<>":
        return None, i, (
            "'<>' opens the target for WRITING as well as reading -- it "
            "CREATES the file, which is why the old screen's read-only "
            "reading of every '<' was a write channel (ADR-040 R4b, "
            "ADR-041)")
    if two == "<&":
        return None, i, ("'<&' duplicates an input descriptor -- the runner "
                         "gives a command its stdin, and nothing else "
                         "(ADR-041)")
    if two == "<<":
        return None, i, ("a here-document has no argv equivalent (ADR-041)")
    return "<", i + 1, None

def _evidence_lex(cmd, shell_free=True):
    """The ONE tokenization of an evidence command. Returns (toks, err),
    where a token is ('w', text, pat_or_None) or ('o', op, fd_or_None) --
    `fd` being the descriptor a redirection was GLUED to (`2>&1` -> fd 2;
    `2 >&1` is the argument '2' and a dup of fd 1, exactly as the shell
    reads them)."""
    toks, i, n = [], 0, len(cmd)
    while i < n:
        c = cmd[i]
        if c in " \t":
            i += 1
            continue
        if c == "#":
            break  # an unquoted '#' at word start starts a comment (POSIX)
        if c in _OPERATOR_CHARS:
            op, i, err = _lex_operator(cmd, i)
            if err:
                return None, err
            toks.append(("o", op, None))
            continue
        text, pat, has_meta, quoted, j, err = _lex_word(cmd, i, shell_free)
        if err:
            return None, err
        if not quoted and text.isdigit() and j < n and cmd[j] in "<>":
            op, j, err = _lex_operator(cmd, j)
            if err:
                return None, err
            toks.append(("o", op, int(text)))
            i = j
            continue
        toks.append(("w", text, pat if has_meta else None))
        i = j
    return toks, None

def _evidence_toks(cmd):
    """The flat token stream the ADR-037 recipe lints consume (and the
    Tier C instruments reach through `scripts/truth`): words as the shell
    would pass them, operators as text, an fd prefix glued to its
    operator. One lexer, two readers -- a second screen-side parser is
    forbidden (the F1/F5 drift lesson). Returns (toks, err)."""
    toks, err = _evidence_lex(cmd)
    if err:
        return None, err
    return [t[1] if t[0] == "w" else
            ("" if t[2] is None else str(t[2])) + t[1] for t in toks], None

# ADR-037: recipe-lint lexicons. Shapes and carve-outs change only with
# the RC-canary faults (the ADR-007 constants-with-faults precedent).
GREP_FAMILY = frozenset(("grep", "rg", "egrep", "fgrep", "zgrep"))

# RULING 8 (2026-08-22). Flags whose output is a SET or its SIZE, short
# bundled forms included (-oE, -rl, -cE). A grep carrying one of these
# counts what its PATTERN RECOGNISES, not what exists -- so a form the
# pattern predates is simply absent, the number stays plausible, and the
# capsule reproduces green while its fact drifts. That is not theory:
# tr-38d32bc7 did exactly this for four days.
_SET_EMITTING_SHORT = frozenset("colL")
_SET_EMITTING_LONG = frozenset((
    "--count", "--only-matching", "--files-with-matches",
    "--files-without-match"))
_INVERT_FLAGS = frozenset(("-v", "--invert-match"))
VERSION_SHAPE_RE = re.compile(r"\bv?\d+\.\d+(?:\.\d+)?\b")
DATE_SHAPE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
SCHEMA_ID_RE = re.compile(r"truth-ledger-record\.v\d")
FROZEN_DATE_RE = re.compile(r"(?:Accepted|Amended|Date:)\s*\(?\d{4}-")

def _set_emitting(tok):
    """Does this grep flag make the output a set or a count? Short flags
    bundle (-oE, -rl), so the test is membership in the bundle rather than
    equality -- an equality test would miss every real recipe in the
    ledger, which is how a lint ships and fires on nothing."""
    if tok in _SET_EMITTING_LONG:
        return True
    return (tok.startswith("-") and not tok.startswith("--")
            and bool(_SET_EMITTING_SHORT & set(tok[1:])))


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
    # Whole-recipe property, so it is computed once rather than re-asked
    # per token: a `-v` anywhere means the author is already subtracting.
    guarded = any(t in _INVERT_FLAGS
                  or (t.startswith("-") and not t.startswith("--")
                      and "v" in t[1:])
                  for t in toks)
    enum_flagged = False
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
        # RULING 8: warn on the fail-open enumerating shape -- but stay
        # SILENT when the recipe already subtracts its own recognised
        # forms (a `-v` anywhere in it), because that is the fail-closed
        # pairing this lint is asking for and scolding it would teach the
        # opposite of the lesson.
        if program in GREP_FAMILY and not enum_flagged and not guarded \
                and _set_emitting(t):
            enum_flagged = True
            msgs.append("recipe: this grep emits a SET or its SIZE, so it "
                        "counts what the pattern recognises rather than "
                        "what exists -- fail-OPEN to a form invented "
                        "later, which reproduces green while the fact "
                        "drifts (RULING 8, 2026-08-22). Consider pairing "
                        "it with an assertion that the complement is "
                        "empty: `... | grep -v '<recognised forms>' | "
                        "wc -l` reading 0. Legitimate as filed; measured "
                        "by instruments/capsule-blindness.py.")
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

# --- ADR-041: the parse IS the execution ---------------------------------
# The plan the parser returns is the runner's whole input, and it is
# deliberately shell-free DATA -- no string a downstream interpreter could
# re-read:
#
#   plan     := [{"op": None|"&&"|"||"|";", "pipeline": [segment, ...]}, ...]
#   segment  := {"words":  [(text, pattern_or_None), ...],
#                "stdin":  None | path,
#                "stdout": "pipe" | "devnull",
#                "stderr": "devnull" | "merge"}
#
# `op` joins a pipeline to the one before it (None on the first), and the
# runner evaluates the and-or list left to right on the running exit code
# -- POSIX's own rule, and the one /bin/sh applied to these same commands
# before ADR-041. "pipe" is the captured stream whose bytes become the
# output hash; "merge" is `2>&1`. Redirections are resolved HERE, in
# order, so the runner sets file descriptors and never parses.

def _resolve_sinks(redirs):
    """Apply a segment's redirections in order to the descriptor table,
    the way the shell does -- `>/dev/null 2>&1` discards both, `2>&1
    >/dev/null` does not. Returns (sinks, err)."""
    table = {1: "pipe", 2: "devnull"}
    stdin = None
    for fd, kind, target in redirs:
        if kind == "in":
            stdin = target
        elif kind == "out":
            table[fd] = "devnull"
        else:
            table[fd] = table[int(target)]
    if table[2] == "pipe" and table[1] != "pipe":
        return None, ("this redirection order sends stderr to the captured "
                      "output while stdout is discarded -- the runner "
                      "captures one stream (ADR-041); write '>/dev/null "
                      "2>&1' if you meant to discard both")
    return {"stdin": stdin, "stdout": table[1],
            "stderr": "merge" if table[2] == "pipe" else "devnull"}, None

def _add_redir(redirs, fd, op, text, pat):
    """One redirection, screened structurally rather than by inspecting
    shell punctuation: ADR-009 ever allowed exactly two sinks, and both
    are descriptors the runner sets directly."""
    if pat is not None:
        return ("a glob in a redirection target is not screenable -- the "
                "word the screen counted is not the word that would open "
                "(ADR-041)")
    if op == "<":
        if fd not in (None, 0):
            return (f"input redirection on fd {fd} -- the runner gives a "
                    "command its stdin, and nothing else (ADR-041)")
        redirs.append((0, "in", text))
        return None
    if op in (">", ">>"):
        if text != "/dev/null":
            return (f"output redirection to {text!r} is refused -- evidence "
                    "commands must be read-only, and '/dev/null' is the only "
                    "allowed sink (ADR-009). A digit is a valid target only "
                    "after an fd dup ('2>&1'), never after a plain '>'.")
        if fd not in (None, 1, 2):
            return (f"output redirection on fd {fd} has no runner equivalent "
                    "(ADR-041)")
        redirs.append((1 if fd is None else fd, "out", text))
        return None
    if text not in ("1", "2"):
        return (f"fd duplication to {text!r} is refused -- '>&' duplicates a "
                "file descriptor, so its target is stdout or stderr; "
                "anything else is a write, and closing a descriptor has no "
                "runner equivalent (ADR-009/ADR-041)")
    if fd not in (None, 1, 2):
        return (f"fd duplication of fd {fd} has no runner equivalent "
                "(ADR-041)")
    redirs.append((1 if fd is None else fd, "dup", text))
    return None

def parse_evidence_command(cmd, shell_free=True):
    """ADR-041: parse an evidence command into the argv plan the runner
    executes with shell=False. Returns (plan, err) -- and the error is the
    screen's, because THE SCREEN IS THIS PARSE: `screen_evidence_command`
    calls it and then checks program names on the very words that will be
    passed to execve. A construct with no argv equivalent is refused here
    rather than approximated, which is the whole content of "one
    interpreter, not two".

    `shell_free=False` is the ADR-014 acceptance oracle, which STILL runs
    through /bin/sh on purpose (it executes repository code -- that is its
    job). It shares this parse for the program-position screen only, so
    the expansions the shell will really perform for it ($, ~) stay
    parse-clean there and refused here."""
    toks, err = _evidence_lex(cmd, shell_free)
    if err:
        return None, err
    if not toks:
        return None, "empty command (ADR-009)"
    plan, pipeline, words, redirs = [], [], [], []
    pending, op = None, None

    def close_segment():
        sinks, serr = _resolve_sinks(redirs)
        if serr:
            return serr
        seg = {"words": list(words)}
        seg.update(sinks)
        pipeline.append(seg)
        del words[:]
        del redirs[:]
        return None

    for t in toks:
        if t[0] == "w":
            if pending is None:
                words.append((t[1], t[2]))
                continue
            e = _add_redir(redirs, pending[0], pending[1], t[1], t[2])
            if e:
                return None, e
            pending = None
            continue
        if pending is not None:
            return None, (f"redirection operator {pending[1]!r} has no "
                          "target (ADR-009)")
        if t[1] in _REDIR_OPS:
            pending = (t[2], t[1])
            continue
        if not words:
            return None, (f"nothing to run before {t[1]!r} (ADR-009)")
        e = close_segment()
        if e:
            return None, e
        if t[1] == "|":
            continue
        plan.append({"op": op, "pipeline": list(pipeline)})
        del pipeline[:]
        op = t[1]
    if pending is not None or not words:
        return None, "dangling operator at end of command (ADR-009)"
    e = close_segment()
    if e:
        return None, e
    plan.append({"op": op, "pipeline": list(pipeline)})
    return plan, None

def screen_evidence_command(cmd, allowlist, allow_rel=EVIDENCE_ALLOW_REL,
                            missing_tail=None, unlisted_hint=None,
                            allow_paths=False, denylist=None,
                            shell_free=True):
    """ADR-009/ADR-041: evidence commands re-execute later in a
    *verifier's* session (recheck) -- deferred code execution across the
    trust seam G11 protects.

    Since ADR-041 the screen is a pass over the PARSE that will execute:
    `parse_evidence_command` refuses every construct the shell-free runner
    cannot express, and what survives is a list of argv arrays. So the
    screen has exactly two things left to decide, and both are about
    programs rather than about punctuation:

      (a) every segment's program is a bare name on the allowlist and not
          on the deny baseline (ADR-022), and
      (b) no argument is one of the program's own exec/file-write flags
          (PROGRAM_ARG_DENY, ADR-021 H4).

    What is GONE is the modelling race: the old screen reasoned about what
    /bin/sh would do with `>`, `>&`, a control character or a glob, and
    lost that race three times (ADR-040 R4a-R4c). The words checked below
    are now the words that reach execve.

    ADR-014 reuses this screen verbatim for acceptance oracles via
    screen_accept_command (a second screen implementation is forbidden --
    the F1/F5 drift lesson); only the allowlist, the two list-naming
    messages and `shell_free` differ. Returns an error string or None."""
    if allowlist is None:
        return ("no command allowlist at " + allow_rel +
                " -- the safety screen fails closed. " +
                (missing_tail or "Create it (one command name per line; "
                 "the template ships a read-only default) before filing "
                 "VERIFIED claims (ADR-009)."))
    if "$(" in cmd or "`" in cmd:
        return ("command substitution ('$(' or backtick) is not "
                "screenable (ADR-009)")
    # ADR-021 (H4), kept after ADR-041 made it redundant for evidence:
    # the acceptance oracle still runs through /bin/sh (that is its
    # purpose), and there a newline is still a statement separator that
    # would drop an unallowlisted program into a screened command. For
    # evidence the reason it is redundant -- the lexer no longer hands the
    # string to anything -- is too subtle to trade for the defence.
    ctrl = next((c for c in cmd
                 if (ord(c) < 0x20 and c != "\t") or ord(c) == 0x7f), None)
    if ctrl is not None:
        return (f"control character {ctrl!r} is not screenable -- it is "
                "word-whitespace to the screen's lexer but a command "
                "separator to a shell (a newline is /bin/sh's statement "
                "terminator); commands must be a single printable line "
                "(ADR-021)")
    plan, err = parse_evidence_command(cmd, shell_free=shell_free)
    if err:
        return err
    for entry in plan:
        for seg in entry["pipeline"]:
            argv = [w[0] for w in seg["words"]]
            program = argv[0]
            if seg["words"][0][1] is not None:
                # A pattern in program position: the word the allowlist
                # would be asked about is not the word that would execve,
                # because the runner expands it (ADR-041 decision 3). No
                # allowlist entry can carry a metacharacter, so this can
                # only ever be an attempt to reach one sideways.
                return (f"program {program!r} is a pattern, not a bare "
                        "command name -- the allowlist screens the word, "
                        "and pathname expansion would replace it (ADR-041)")
            if denylist and program in denylist:
                # ADR-022: deny-wins over the allowlist. Shells/executors
                # are never read-only evidence; refuse even if a consumer
                # allowlisted one by accident (the H4 footgun).
                return (f"'{program}' is on the template-owned evidence deny "
                        f"baseline ({EVIDENCE_DENY_REL}) -- shells and "
                        "generic executors turn the read-only screen into "
                        "arbitrary execution and are never valid evidence, "
                        "even if allowlisted (ADR-022). To run repository "
                        "code on purpose, use an acceptance oracle (ADR-014).")
            if "/" in program:
                # Issue #7 (v0.7.2, accept screen only): an ALLOWLISTED
                # exact repo-relative path may run as an oracle -- the
                # committed entry bounds precisely which executable, which
                # is stronger than an interpreter bare-name. Absolute
                # paths and `..` segments never pass; the evidence screen
                # (allow_paths=False) keeps ADR-009's blanket refusal.
                if not (allow_paths and program in allowlist
                        and not program.startswith("/")
                        and ".." not in program.split("/")):
                    return (f"program {program!r} is a path, not a bare "
                            "command name -- " +
                            ("add the exact repo-relative path to "
                             f"{allow_rel} to admit it as an oracle; "
                             "absolute paths and '..' never pass (issue #7, "
                             "ADR-014)" if allow_paths else
                             "repo-local executables are not screenable "
                             "(ADR-009)"))
            elif program not in allowlist:
                return (f"'{program}' is not in {allow_rel}. " +
                        (unlisted_hint or "Add it there if it is read-only "
                         "and you accept it re-running inside verifier "
                         "sessions, or file with --evidence-unsafe-ok "
                         "(recheck will then refuse to execute it) "
                         "(ADR-009)."))
            # F1/v0.6.2: an allowlisted program can still open an exec or
            # file-write channel through its own flags (find -exec, sort
            # -o, git -c alias=!cmd). The bare-name check above cannot see
            # this; the per-program deny table can. Since ADR-041 these
            # are the argv words themselves, so the table is sound for
            # written flags -- a GLOB that expands into one at run time is
            # the residual the ADR names, and is the shell's too.
            denied = PROGRAM_ARG_DENY.get(program)
            if denied:
                for tok in argv[1:]:
                    if tok.split("=", 1)[0] in denied:
                        return (f"{program} {tok.split('=', 1)[0]!r} opens an "
                                "exec or file-write channel -- evidence "
                                "commands must be read-only, and this one "
                                "would re-run inside a verifier session "
                                "(ADR-009)")
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
        allow_paths=True, shell_free=False)

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

# ------------------------------- invalidation readers (R3, ADR-030 legacy)

# READ-SIDE ONLY since refactor step 2.6. The `truth reaffirm`
# verb is retired; this constant survives it because reports.staling_report
# identifies historical machine-cleared stalings by exactly this basis
# string, and the ledger holds 1283 of them. REAFFIRM_ARMS went with the
# triage that produced them -- nothing reads an arm name off a record.
REAFFIRM_BASIS = "reaffirm: hash-match, no judgment re-run"

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

# is_ttl_reason MOVED to truthlib.kernel (refactor step 2.5) and
# arrives here through `from truthlib.kernel import *`, so every caller
# below keeps its spelling. It had to move: fold() is now a caller, and
# kernel sits below evidence in the ADR-044 DAG. Its per-record twin,
# kernel.ttl_invalidation, is the single discriminator the fold and its
# readers share.

def ttl_staleness(events, cid):
    """HISTORICAL READER ONLY SINCE ADR-057 -- read this before using it.

    It answers "was a TTL expiry ever RECORDED for this claim", which
    stopped being the same question as "is this claim TTL-stale" the
    moment expiry became a read-time derivation. Nothing writes those
    records any more, so for every claim filed after ADR-057 this
    returns False no matter how long expired. The live question is
    `kernel.ttl_expiry(claim_record, now)`, or simply the status the
    fold derives.

    It survives because the ~1997 records already in the ledger stay
    readable forever (J-012, EPI-501) and this is the ONE place that
    reads them correctly, including the pre-stamp fallback below. Its
    only production consumer was the `reaffirm` triage, retired in
    refactor step 2.6, so it has none today.

    Red-team F3 hardening: is the claim TTL-staled, for triage arm 1?
    Prefers the structured `reason_code: "ttl"` the scan stamps on TTL
    invalidations over free-text parsing. ADR-019 makes TTL expiry
    MONOTONE -- the clock never runs backwards and re-verification never
    resets the TTL (ADR-057 kept both; it only moved WHO reads the
    clock) -- so ANY
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

# -------------------------------------------- reproduction sweep (F1.1)

REPRODUCE_ARMS = ("reproduces", "capsule-stale", "unexecutable", "no-capsule")

# Why a live claim's capsule no longer reproduces. Named shapes, not a
# free-text guess: the whole point of the sweep is that "capsule-stale"
# alone conflates three different repairs.
REPRODUCE_SHAPES = ("uncommitted", "watched-moved", "orphaned-capsule",
                    "unexplained")

def reproduce_triage(entry, screen_err=None, recheck=None):
    """F1.1: the ONE decision per LIVE claim -- can its recorded evidence
    capsule still be produced on this machine, right now?

    This is the question no existing verb asks. `invalidate-scan` asks
    whether a watched PATH moved (right 1 time in 8 -- the 7:1 false-
    staling ratio this instrument exists to measure against); `reaffirm`
    and `verdict --recheck` re-run capsules, but only for claims already
    knocked out of `live`. A claim that is live and whose capsule died
    quietly is invisible to all three, which is exactly how 13 of this
    repo's live claims became permanently un-recheckable before ADR-051.

    Pure, and deliberately the same SHAPE as reaffirm_triage: the shell
    gathers (current-allowlist screen result, run outcome) and applies;
    nothing here reads a clock, the env, or a file. Returns
    {"arm", "detail"}; arm is one of REPRODUCE_ARMS, or the "execute"
    sentinel telling the shell to run the screened command and call again
    with its result.

    Arm order is the contract, most fundamental disability first: a claim
    with no capsule cannot be screened, and a claim the screen refuses
    cannot be run. So a no-capsule claim reports no-capsule even if it
    somehow also carried screened=false.

    NOTHING IS EVER FILED. This verb reports; it is not in WRITE_VERBS.
    A mismatching hash is ADR-012's judgment call (mechanical drift vs
    reality moved) and a batch verb has no judge -- the same rule that
    keeps reaffirm's mismatch arm from filing a diverge."""
    p = entry["claim"]["payload"]
    ev = p.get("evidence") or {}
    if not ev.get("command"):
        return {"arm": "no-capsule",
                "detail": "no evidence command recorded -- this claim's "
                          "standing rests on judgment alone, and no "
                          "mechanical check can ever contradict it"}
    if ev.get("screened") is False:
        # ADR-009/029 recheck refusal discipline: screened=false is the
        # author's own admission, final; the command NEVER executes here.
        return {"arm": "unexecutable",
                "detail": "filed with --evidence-unsafe-ok "
                          "(evidence.screened=false): never re-executed "
                          "(ADR-009)"}
    if screen_err:
        return {"arm": "unexecutable",
                "detail": "the CURRENT allowlist refuses this command -- "
                          + screen_err}
    if recheck is None:
        return {"arm": "execute", "detail": "run the screened command"}
    verdict = recheck[0]
    if verdict == "agree":
        return {"arm": "reproduces",
                "detail": "output hash and returncode match the effective "
                          "capsule (ADR-051)"}
    if verdict == "cannot_verify":
        # recheck_verdict's exit-127 rule: the program is absent, which
        # says nothing about the fact. An unexecutable capsule is a
        # DIFFERENT defect from a stale one and must not be counted as
        # drift -- exit 7 would then fire on a missing `rg`.
        return {"arm": "unexecutable",
                "detail": "command not found at re-run (exit 127): "
                          "environment, not reality"}
    return {"arm": "capsule-stale",
            "detail": "the recorded capsule can no longer be produced "
                      "here -- this claim is un-recheckable until someone "
                      "judges it and refreshes (ADR-051)"}

def capsule_stale_shape(entry, touched_ahead, touched_buried,
                        dirty_watched=()):
    """F1.1: WHY a live claim's capsule stopped reproducing -- the fact
    that decides which repair applies. Three shapes, three different
    repairs, and lumping them under one "capsule-stale" count is what
    made the population unreadable for as long as it existed.

    Pure. The shell supplies two commit-to-commit diffs of the claim's
    OWN evidence_paths, through the scan's differ and matcher (never a
    second implementation), plus the working tree's dirty watched paths
    through ADR-038's existing `dirty_watch`:

      touched_ahead   effective-anchor..HEAD -- the window the NEXT
                      invalidate-scan will look at.
      touched_buried  own-anchor..effective-anchor -- the past that
                      `agree`s carried the claim over. Empty when the
                      anchor never advanced.
      dirty_watched   watched paths dirty in the WORKING TREE right now.

    Shapes, in decision order:

      uncommitted       a watched path is edited but not committed. It
                        must be judged FIRST and it is not a defect
                        report: both diff windows are commit-to-commit,
                        so an uncommitted edit is invisible to them and
                        would otherwise fall through to `unexplained` --
                        polluting the one arm that is supposed to mean
                        something. This shape was found by running the
                        sweep on the tree that was implementing it: a
                        claim hashing `.truth/generated-paths` reported
                        `unexplained` because the file had been edited
                        and not yet committed. Repair: commit, re-run.
      watched-moved     a watched path changed since the last agree and
                        so did the output. Ordinary: the tripwire has not
                        fired yet. Repair: let the scan stale it, then
                        judge it.
      orphaned-capsule  the watched surface changed BEFORE the last
                        agree, that agree advanced the effective anchor
                        (F2) and the capsule stayed at the pre-change
                        hash. The exact pre-ADR-051 shape; repair is
                        `agree --refresh-evidence`, ONE HUMAN JUDGMENT AT
                        A TIME -- refreshing this population by script is
                        judgment laundering (ADR-030), and it would turn
                        a visible orphan count into an invisible one.
      unexplained       nothing watched changed in EITHER window, and the
                        output still differs. The command reads something
                        outside its own evidence_paths: an untracked or
                        gitignored file, or the machine. The arm worth
                        reading -- it names claims whose watched set is
                        wrong, which no other surface reports.

    `anchor_advanced` alone was the first cut of this and it is too weak:
    it labels a dark-dependency claim "orphaned" whenever any unrelated
    agree happened to move the anchor. The buried-window diff is what
    makes the label mean what it says.

    Returns {"shape", "anchor_advanced", "watched_touched",
    "watched_buried"}."""
    p = entry["claim"]["payload"]
    own = p.get("anchor_commit")
    effective = entry.get("anchor")
    advanced = bool(own and effective and effective != own)
    ahead = sorted(touched_ahead or [])
    buried = sorted(touched_buried or [])
    dirty = sorted(dirty_watched or [])
    if dirty:
        shape = "uncommitted"
    elif ahead:
        shape = "watched-moved"
    elif buried:
        shape = "orphaned-capsule"
    else:
        shape = "unexplained"
    return {"shape": shape, "anchor_advanced": advanced,
            "watched_touched": ahead, "watched_buried": buried,
            "watched_dirty": dirty}

def selector_screen(paths, changed):
    """FAZA 3 step 3.3: split a set of changed files by WHO watched them.

    Returns (settled, contested).

      settled    files matched by at least one SELECTOR-FREE target. A
                 plain path watch means "any byte in this file", so the
                 touch is the answer and nothing needs reading.
      contested  {file: [selector target, ...]} -- files matched ONLY by
                 targets naming a sub-tree. A touch here is not yet an
                 answer: it says the file moved, and the claim watches a
                 part of it. Deciding needs the bytes at two revisions,
                 which is the shell's job (shellio.structural_hash) and
                 structural_moved's to judge.

    THE ASYMMETRY IS THE FEATURE. Settled is decided by matching alone,
    so a repo that uses no selectors pays nothing: contested is empty and
    every caller behaves exactly as it did before this function existed.
    Only a selector-bearing claim ever costs a file read, and only for
    the files its own watch set matched.

    A file matched by BOTH a plain and a selector target is settled --
    the plain watch already said "any byte", and no sub-tree digest can
    withdraw a broader claim the same author also filed. Pure."""
    plain = [p for p in paths if not split_selector_target(p)[1]]
    sel = [p for p in paths if split_selector_target(p)[1]]
    settled, contested = [], {}
    for f in changed:
        if match_paths(f, plain):
            settled.append(f)
            continue
        watchers = [t for t in sel if match_paths(f, [t])]
        if watchers:
            contested[f] = watchers
    return settled, contested

def structural_moved(contested, digests):
    """Which contested files actually moved, given two digests per target.

    `digests` maps a target to (before, after, err); `err` is None or the
    (kind, detail) pair shellio.structural_hash returns for a revision it
    could not reduce. Returns (moved, undecided):

      moved      files where some watching target's sub-tree digest
                 differs between the two revisions. THE ONE THING THIS
                 FEATURE PROMISES: a file whose every watching selector
                 hashes identically is absent from this list, so a
                 dependency bump three keys over stops being an event.
      undecided  [(file, target, reason)] -- a target whose digest could
                 not be computed at one end.

    UNDECIDED IS NOT SILENCE, and the direction matters. A caller must
    treat an undecided file as MOVED: "I could not read the sub-tree" is
    not evidence that the fact held, and a feature whose failure mode is
    to quietly suppress drift would be worse than the noise it replaces.
    The reasons ride along so the report can say which files it could not
    judge and why -- an unparseable file and an unchanged one must never
    render as the same line. Pure."""
    moved, undecided = set(), []
    for f in sorted(contested):
        for t in contested[f]:
            before, after, err = digests.get(
                t, (None, None, ("not-probed", "no digest was gathered")))
            if err:
                undecided.append((f, t, err))
                moved.add(f)      # fail toward reporting, never toward silence
            elif before != after:
                moved.add(f)
    return sorted(moved), undecided

# previously_agreed and reaffirm_triage were REMOVED in refactor step 2.6
# together with the `truth reaffirm` verb they served. Their
# subject no longer exists: reaffirm operated on stale claims, and after
# the step-2.5 double-invalidation rule the ONLY way to be stale is TTL
# expiry -- which was already reaffirm_triage's FIRST arm and always a
# refusal ("re-file required; ADR-019: TTL never resets by
# re-verification"). Every remaining input to the verb was one it declined
# by contract, so this was dead machinery, not a capability withdrawn.
#
# What replaced each arm: `truth reproduce` for the batch question (does
# the recorded capsule still produce its recorded output, for every live
# claim), and `verdict --recheck` for the per-claim one. Both go through
# the SAME screened executor this module still owns -- a second executor
# was forbidden then and is forbidden now (ADR-005's drift lesson).
#
# The READ side is untouched, deliberately (J-012): REAFFIRM_BASIS stays
# above, because reports.staling_report classifies the historical
# `reaffirm:`-basis and `reaffirm_cleared` records by it. Retiring a
# writer is not breaking a reader.
