"""truthlib.shellio -- ALL I/O: git probes, files, clock, env,
subprocess (C5 edge).

The only truthlib module that imports subprocess.  Gathers facts and
applies effects -- repo/ledger paths, the ADR-015 clock, the single
append_records writer path, loaders, the ADR-011 human-ack ceremony, and
the hook/CI wiring probes.  Imports kernel and registry only.

ADR-044 left the pre-existing sys.exit sites "as-is this phase"; A1 is
that phase.  Four of the seven became returns (tracker_issues ×3,
events_at_ref), because `ready` and `baseline` are their only callers
and can act.  Three remain and each carries its reason inline:
repo_root and ledger_lock have no partial answer to give, and
load_events would need (events, err) threaded through 22 call sites (26
with the Tier C instruments) to reproduce one exit -- an exit the
adversary pass then showed is WRONG for `validate`, whose contract is
reporting every bad record and which dies on the first.  An undeclared
exception is the defect; a declared one is a decision.
"""
import contextlib
import fcntl
import hashlib
import io
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

from truthlib.registry import *
from truthlib.kernel import *

# --- A3: the explicit substitution seam ----------------------------------
# What this replaces: `scripts/truth` used to install a _MirrorModule whose
# __setattr__ pushed every assignment into the eight truthlib modules, and
# a _self_module() that found its own module object via gc.get_referrers().
# All of that existed so a test could write `tm.ledger_path = ...` and have
# the three modules that star-imported the name (gates, shellio, cli) see
# it. Seven assignments of TWO names, paid for with metaclass surgery in
# the production loading path and a gc walk that a Python upgrade could
# break in a way nobody could read (ADR-044 shipped it knowingly, as the
# equivalence proof for the package split; the migration is over).
#
# The indirection now lives INSIDE the function instead of in module
# namespaces, so every star-imported binding already points at the one
# object that consults this dict. Nothing needs mirroring.
_OVERRIDES = {}
# An allowlist, not a free dict: the old seam silently did nothing when a
# name was bound nowhere, so a typo was indistinguishable from a patch.
CONFIGURABLE = frozenset(("repo_root", "ledger_path", "tracked_files"))

def configure(**fns):
    """A3: the ONE supported way to substitute an I/O primitive, for tests.
    Returns a zero-argument restore callable, so each caller puts back
    exactly what it found and nesting is safe -- `reset_configuration()`
    clears everything and is the blunt instrument."""
    unknown = sorted(set(fns) - CONFIGURABLE)
    if unknown:
        raise ValueError(
            f"truthlib.configure: {', '.join(unknown)} is not configurable "
            f"(allowed: {', '.join(sorted(CONFIGURABLE))}). The old mirror "
            "seam accepted any name and silently did nothing when it was "
            "bound nowhere, which made a typo look like a patch.")
    missing = object()
    previous = {k: _OVERRIDES.get(k, missing) for k in fns}
    _OVERRIDES.update(fns)

    def restore():
        for k, v in previous.items():
            if v is missing:
                _OVERRIDES.pop(k, None)
            else:
                _OVERRIDES[k] = v
    return restore

def reset_configuration():
    """Drop every override. Production never calls this; it is the reset a
    suite runs between cases when it does not want to thread restores."""
    _OVERRIDES.clear()

def repo_root():
    """A1 -- DECLARED EXCEPTION, this exit stays. Fourteen call sites take
    the result as a path and build on it; there is no partial answer to
    hand back, because outside a git repository there is no ledger, no
    policy file and no anchor. An undeclared exception is the defect A1
    names; a declared one is a decision, and this is the decision.

    CORRECTED after the adversary pass: this reason first said "every
    verb's precondition is gone", and that is false. `truth vocab` runs
    outside a repository and exits 0 -- it reads only registry constants
    and never calls this function. The operative claim (every CALLER of
    repo_root needs a path) holds; the universal one did not, and a
    plausible-sounding reason that does not hold is worse than none."""
    if "repo_root" in _OVERRIDES:            # A3 seam; empty in production
        return _OVERRIDES["repo_root"]()
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("truth: not inside a git repository")
    return r.stdout.strip()

def ledger_path():
    if "ledger_path" in _OVERRIDES:          # A3 seam; empty in production
        return _OVERRIDES["ledger_path"]()
    return os.path.join(repo_root(), LEDGER_REL)

def now_dt():
    """The only place TRUTH_NOW is honored (test hook; never in prod).
    ADR-015: the override is normalized to aware-UTC so now_iso() always
    renders the canonical profile -- a naive or Z-suffix TRUTH_NOW must
    not mint a record validate would then reject."""
    override = os.environ.get("TRUTH_NOW")
    if override:
        dt = datetime.fromisoformat(override.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    return datetime.now(timezone.utc)

def now_iso():
    return now_dt().isoformat(timespec="microseconds")  # v0.4: second-
    # granularity made same-second events tie, leaving order to the
    # random id tie-break; microseconds make ts the real order key

def head_commit():
    r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None

def commit_reachable(sha):
    r = subprocess.run(["git", "cat-file", "-e", f"{sha}^{{commit}}"],
                       capture_output=True)
    return r.returncode == 0

def changed_files_between(a, b):
    """Returns (changed_files or None, error or None) for a..b.

    --no-renames: with rename detection active, a `git mv` of a watched
    file emits only the DESTINATION path, so the watched (old) path never
    appears and the scan silently misses the change -- a rename must show
    as delete+add so the tripwire fires on the old path.

    THE ONE DIFFER. F1.1 needed a second window (own-anchor..effective-
    anchor, what the agrees buried) alongside the scan's anchor..HEAD;
    a second `git diff` call site is how the F1/F5 screen drift started,
    so the range became a parameter instead."""
    r = subprocess.run(["git", "diff", "--name-only", "--no-renames",
                        f"{a}..{b}"], capture_output=True, text=True)
    if r.returncode != 0:
        return None, r.stderr.strip()
    return r.stdout.splitlines(), None

def changed_files_since(anchor):
    """The invalidate-scan window: anchor..HEAD. Unchanged behaviour."""
    return changed_files_between(anchor, "HEAD")

def tracked_files():
    """INV-M fact-gathering: the tracked-file universe a literal
    evidence_path must belong to. Works with zero commits (reads the
    index, not HEAD).

    Configurable (A3) since the gate's two refusal bodies -- dead literal
    and dead glob -- were the only INTAKE_GATES branches no unit test
    could reach: they sit behind this subprocess, and a suite that spawns
    git is not the fast inner loop this one is."""
    if "tracked_files" in _OVERRIDES:        # A3 seam; empty in production
        return _OVERRIDES["tracked_files"]()
    r = subprocess.run(["git", "ls-files"], capture_output=True, text=True)
    return r.stdout.splitlines() if r.returncode == 0 else []

def actor():
    return os.environ.get("TRUTH_ACTOR", os.environ.get("USER", "unknown"))

def session():
    explicit = os.environ.get("TRUTH_SESSION")
    if explicit:
        return explicit
    # Fallback correlation without coordination: our own PID changes per
    # command, but the invoking shell/harness is stable for a sitting, so
    # ppid+date groups records filed from one operating context. This is
    # forensic grouping, not identity -- set TRUTH_SESSION for real ids.
    return f"s-{os.getppid()}-{now_dt():%Y%m%d}"

def run_evidence(cmd, cwd=None):
    """The ONE evidence executor (intake, recheck, reaffirm, reproduce) --
    a second one would drift from the screen that gates it (ADR-009/029).

    `cwd` is F1.1's addition: `reproduce` pins execution to the repo root
    so a sweep run from a subdirectory does not report drift that is
    really the caller's working directory. Default None keeps intake,
    recheck and reaffirm byte-identical -- they inherit the caller's cwd,
    exactly as they always have."""
    r = subprocess.run(cmd, shell=True, capture_output=True, cwd=cwd)
    return hashlib.sha256(r.stdout).hexdigest(), r.returncode

def run_accept_command(command, cwd):
    """ADR-014: execute the acceptance oracle at `done` time (SHELL --
    subprocess).  Returns (returncode, combined_output) -- stdout+stderr
    concatenated, which is everything cmd_done needs to decide and to
    render the failure tail.  Lives here, not in cli, so the ADR-044
    "shellio is the only subprocess importer" row is a fact the purity
    test enforces rather than a claim the record makes; screening the
    command against the allowlist stays the caller's (ADR-009) job and
    happens BEFORE this is reached."""
    r = subprocess.run(command, shell=True, cwd=cwd, capture_output=True,
                       text=True)
    return r.returncode, r.stdout + r.stderr

def load_allowlist(rel=EVIDENCE_ALLOW_REL):
    """ADR-009: the evidence-command allowlist, or None when absent
    (the screen then fails closed for VERIFIED intake and recheck).
    ADR-014 loads the acceptance allowlist through the same reader
    (rel=ACCEPT_ALLOW_REL)."""
    path = os.path.join(repo_root(), rel)
    if not os.path.exists(path):
        return None
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                out.append(line)
    return out

def read_policy_file(rel):
    """F3.1: a policy file's raw text, or None when absent. SHELL. One
    reader for every attestable policy file -- the state decision is
    policy_file_state's, and giving it the bytes instead of a parsed
    shape is what keeps `# attested ...` visible to it (every existing
    loader strips comments, which is precisely where the attestation
    lives)."""
    path = os.path.join(repo_root(), rel)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except (OSError, ValueError):
        return None

def load_denylist():
    """ADR-022: the template-owned evidence deny baseline, or None if the
    file is absent (an older deployment simply has no extra deny -- the
    allowlist stays the boundary, so this layer fails open harmlessly)."""
    return load_allowlist(EVIDENCE_DENY_REL)

def human_ack_error(target_id, what):
    """ADR-011: tombstones require TRUTH_HUMAN=1 plus either an
    interactive typed-id confirmation or an id-specific TRUTH_HUMAN_ACK
    (headless human use; documented in --help and .truth/README.md, and
    deliberately NOT named in the agent-facing refusals below -- an
    error message that names the bypass is an instruction to a
    compliant agent, the exact failure F4's fix left open)."""
    if os.environ.get("TRUTH_HUMAN") != "1":
        return (f"truth: {what} is a human tombstone decision (G12). If "
                "you are an agent: file `diverge` (or close with a basis) "
                "saying it should die, and stop -- the human queue "
                "decides. If you are a human: re-run this in your own "
                "terminal.")
    ack = os.environ.get("TRUTH_HUMAN_ACK")
    if ack is not None:
        if ack == target_id:
            return None
        return (f"truth: the acknowledgment names {ack!r}, not "
                f"{target_id} -- it must cite the exact id it kills "
                "(ADR-011); a lingering environment variable may not "
                "authorize arbitrary tombstones")
    if not sys.stdin.isatty():
        return (f"truth: {what} is confirmed interactively -- re-run "
                "this in your own terminal (ADR-011). Agents: file "
                "`diverge` with a basis and stop; the human queue "
                "decides.")
    typed = input(f"type {target_id} to confirm {what}: ").strip()
    if typed != target_id:
        return "truth: confirmation mismatch -- nothing filed"
    return None

@contextlib.contextmanager
def ledger_lock():
    """ADR-045 (D2): one EXCLUSIVE advisory lock held around a write
    verb's entire load->gates->append critical section (main() wraps
    args.fn for WRITE_VERBS), closing the R10 same-machine TOCTOU
    catalogue: the G8 duplicate screen, the contradicts dormant/live
    decision, and the issue_event transition check all read a fold that
    can no longer go stale under a concurrent writer's append. Read
    verbs never touch the lock (flock is advisory; readers are safe by
    O_APPEND line-atomicity as before), and the lock target is
    LEDGER_LOCK_NAME under the GIT DIR -- never the ledger itself (the
    audited O_APPEND append path, TestAppendSingleWrite, is untouched)
    and never a worktree sibling (an untracked lock file dirtied
    `git status` and tripped the session-close survival gate; see the
    registry comment). Blocking acquire, deliberately no timeout: a
    flock(2) lock dies with its holder's process (kernel-owned state,
    not a lock FILE convention), so a crashed holder cannot orphan the
    lock and the wait is bounded by the FS-3-priced critical section.
    Multi-machine remains out of scope -- paper sec 8 item 4 stands
    (ADR-045)."""
    r = subprocess.run(["git", "rev-parse", "--git-dir"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        # A1 -- DECLARED EXCEPTION, repo_root's twin and for its reason:
        # this is a context manager whose whole purpose is the exclusive
        # flock, and with no git dir there is nowhere to place the lock.
        # Yielding unlocked would silently drop the ADR-045 critical
        # section, which is worse than not running.
        sys.exit("truth: not inside a git repository")
    gd = os.path.abspath(r.stdout.strip())  # --git-dir is cwd-relative
    fd = os.open(os.path.join(gd, LEDGER_LOCK_NAME),
                 os.O_CREAT | os.O_RDWR, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)  # close releases the flock, even on a refusal exit

# R15: append's tail read used to scan the WHOLE ledger per write; only
# the last line matters. A ledger line is far under this window (the
# largest record shapes -- evidence capsules, reaffirm_cleared lists --
# are hundreds of bytes to a few KB), so one tail read almost always
# holds a complete last line; correctness never depends on it (fallback
# below).
_LAST_TS_TAIL_BYTES = 64 * 1024

def _last_ledger_ts():
    """The ts of the ledger's last well-formed line, or None.

    Reads only the ledger TAIL (seek to size - 64KB, R15): the first
    line of the window is dropped when the file is larger than the
    window (it is almost certainly cut mid-line), junk tail lines walk
    back a line, and a window with no parseable line at all falls back
    to the old full scan -- correctness first, the seek is only an
    optimization. errors="replace" keeps a mid-character cut or a
    corrupt byte from crashing the append path; the mangled line then
    fails json.loads and is walked past exactly like other junk."""
    path = ledger_path()
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(max(0, size - _LAST_TS_TAIL_BYTES))
        chunk = f.read()
    if size > _LAST_TS_TAIL_BYTES:
        chunk = chunk.split(b"\n", 1)[1] if b"\n" in chunk else b""
    for line in reversed(chunk.decode("utf-8",
                                      errors="replace").splitlines()):
        if not line.strip():
            continue
        try:
            return json.loads(line).get("ts")  # last well-formed line's
            # ts, present or not -- exactly what the full scan returned
        except json.JSONDecodeError:
            continue
    if size > _LAST_TS_TAIL_BYTES:
        # Nothing parseable in the window (a >64KB junk tail): full scan.
        last = None
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    last = json.loads(line).get("ts")
                except json.JSONDecodeError:
                    continue
        return last
    return None

def append_records(kinds_payloads):
    """Append a batch of records in ONE write(2) call -- all or nothing.

    Items are (kind, payload, prefix) triples. Every record is built
    BEFORE any byte lands, then the batch is serialized into one buffer
    and written with a single os.write on an O_APPEND fd: the
    concurrent-append safety statement (paper sec 1) assumes
    single-write-call O_APPEND atomicity, and that same assumption now
    carries multi-record transactions -- cmd_done's claim+event pair is
    "both records or neither" literally, not aspirationally (R2).
    The sole writer path: append_record delegates here with n=1."""
    ts = now_iso()
    # ADR-015 clock-push (the HLC 'physical clock catch-up' half, and
    # nothing more): a real-clock record must not sort before the ledger
    # tail it causally follows. Small honest skew (same-machine append
    # races, NTP steps) is absorbed by bumping 1 microsecond past the
    # tail; skew beyond ADR-008's tolerance is NOT absorbed -- the
    # honest clock is kept and order_check's existing regression warning
    # surfaces it, so a forged far-future tail cannot drag every later
    # record with it. TRUTH_NOW (test hook) disables the push: seeded
    # backdating is the point of the hook (canary FAULT D).
    if not os.environ.get("TRUTH_NOW"):
        last = _last_ledger_ts()
        if last and TS_RE.match(str(last)) and ts <= last:
            last_dt = parse_ts(last)
            if (last_dt - now_dt()).total_seconds() <= SKEW_TOLERANCE_SECONDS:
                ts = (last_dt + timedelta(microseconds=1)) \
                    .isoformat(timespec="microseconds")
    recs = []
    for kind, payload, prefix in kinds_payloads:
        recs.append(make_record(kind, payload, actor(), session(), ts, prefix))
        # The same clock-push idiom, applied WITHIN the batch: each later
        # record sorts strictly after the one before it, so file order =
        # ts order (ADR-015's total order never leans on the id tiebreak
        # for records born in one transaction).
        ts = (parse_ts(ts) + timedelta(microseconds=1)) \
            .isoformat(timespec="microseconds")
    path = ledger_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # One write(2) call for the whole buffer: the buffered text layer can
    # split anything longer than the stdio buffer across several write(2)
    # calls, so the fd is written raw.
    buf = b"".join((json.dumps(r, sort_keys=True) + "\n").encode("utf-8")
                   for r in recs)
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        os.write(fd, buf)
    finally:
        os.close(fd)
    return recs

def append_record(kind, payload, prefix="tr-"):
    return append_records([(kind, payload, prefix)])[0]

def load_events(stream=None):
    events = []
    if stream is not None:
        lines = stream.read().splitlines()
    else:
        path = ledger_path()
        if not os.path.exists(path):
            return events
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    for n, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            events.append((n, json.loads(line)))
        except json.JSONDecodeError:
            # A1 -- DECLARED EXCEPTION, and the one I am least happy
            # about. 22 call sites in template/ (26 counting the four
            # Tier C instruments) take the event list, and threading
            # (events, err) through all of them to reproduce one
            # identical exit would be churn with no reader.
            #
            # CORRECTED after the adversary pass, twice. The count first
            # said 23, which counted this function's own `def` line --
            # in a commit whose centrepiece was correcting the brief's
            # grep arithmetic. And the reason first claimed "a corrupt
            # line means the same thing at every one of them", which is
            # FALSE and has a live counter-example:
            #
            #   printf 'not json\n{"also":"bad"}\n' | truth validate --stdin
            #   -> truth: line 1 is not valid JSON
            #
            # `validate` is the one verb whose entire contract is
            # reporting EVERY bad record, and it dies from library depth
            # on the first, never reaching line 2 or its own reporting
            # loop. The behaviour predates A1; the stated reason was the
            # defect.
            #
            # So the residual is now sharper, not softer: this exit is
            # wrong for at least one caller, and the clean answer is a
            # raised exception caught in main() -- catchable, testable,
            # byte-identical for every other verb. That is a DESIGN
            # CHOICE this brief does not authorise, and choosing rather
            # than reporting is the failure mode A1's own licence
            # forbids. Reported, not taken; `validate`'s all-records
            # contract is the concrete case that should decide it.
            sys.exit(f"truth: line {n} is not valid JSON")
    return events

def load_generated_globs():
    """Shell (ADR-037/SI-4): the consumer's generated-artifact globs.
    Returns (globs, source, err), source in {'file','empty','absent'};
    err carries the refusal for a pathspec-magic line and globs is then
    None (R14a: loaders RETURN errors, callers decide -- _gate_generated
    returns it per the gate-table contract, the citation twin sys.exits
    at the verb; message and exit code byte-identical to the old
    in-loader exit). utf-8-sig; magic line starts refused (SI-1)."""
    path = os.path.join(repo_root(), GENERATED_PATHS_REL)
    if not os.path.exists(path):
        return [], "absent", None
    globs = []
    with open(path, encoding="utf-8-sig") as f:
        for i, line in enumerate(f, 1):
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if s[0] in ":-!":
                return None, "file", (
                    f"truth: {GENERATED_PATHS_REL} line {i} starts "
                    f"with {s[0]!r} -- pathspec magic is refused; "
                    "the list holds CLI globs (ADR-037/SI-1)")
            globs.append(s)
    return globs, ("file" if globs else "empty"), None

# --- ADR-038: the dirty-watch shell probe (SHELL -- subprocess) -----------
def working_tree_status():
    """SI-2: NUL-separated unquoted status at the repo root. Returns
    raw text or None when git cannot answer -- incl. an undecodable
    byte in some unrelated untracked filename (text=True decodes
    strictly; UnicodeDecodeError is a ValueError -- the R4 adversarial
    review's catch: the advisory stays silent, it never gates and never
    tracebacks past a successful append)."""
    try:
        # -uall: expand untracked DIRECTORIES into their files (default
        # porcelain collapses them to 'ns/', hiding which file under a
        # glob watch is the restale-at-birth vector)
        r = subprocess.run(["git", "status", "--porcelain=v1", "-z",
                            "--untracked-files=all"],
                           capture_output=True, text=True, cwd=repo_root())
    except (OSError, ValueError):
        return None
    return r.stdout if r.returncode == 0 else None

# --- ADR-039: blast history (SHELL -- subprocess) -------------------------
def blast_history():
    """SI-2: (history, state), state in {'ok','shallow','unavailable'}.
    Shallow clones truncate `git log` SILENTLY -- a quietly-cold
    forecast would be the exact silent skip the design forbids, so
    shallowness is probed first and nothing is stored for it (a floor
    is not a bound). quotepath=off keeps names raw for match_paths."""
    try:
        sh = subprocess.run(["git", "rev-parse", "--is-shallow-repository"],
                            capture_output=True, text=True, cwd=repo_root())
        if sh.returncode == 0 and sh.stdout.strip() == "true":
            return None, "shallow"
        # --since-as-FILTER, never --since: plain --since STOPS the
        # traversal at the first out-of-window commit, so one backdated
        # commit near the tip empties the whole log -- a quietly-cold
        # forecast stored as 0-under-ok, the exact 0-as-unknown ADR-039
        # forbids (the R5 adversarial review's catch). On git < 2.36
        # the option errors -> rc != 0 -> the loud unavailable path,
        # which is the design's preferred failure mode.
        r = subprocess.run(["git", "-c", "core.quotepath=off", "log",
                            f"--since-as-filter={BLAST_WINDOW_DAYS}.days",
                            "--format=%x01%H", "--name-only",
                            "--no-renames"],
                           capture_output=True, text=True, cwd=repo_root())
    except (OSError, ValueError):
        return None, "unavailable"
    if r.returncode != 0:
        return None, "unavailable"  # incl. unborn HEAD (exit 128)
    return parse_name_log(r.stdout), "ok"

# --- ADR-036: tombstone citation gate -------------------------------------
def load_citation_scope():
    """Shell: the consumer's citation-scope policy (SI-4). Returns
    (globs, source, err), source in {'file','empty','default'}; err
    carries the refusal for a pathspec-magic line (R14a: the loader
    returns, the verb-level callers sys.exit it -- same message, same
    exit code as the old in-loader exit). utf-8-sig (a BOM must not
    deaden the first glob); a line starting ':', '-' or '!' is refused
    -- scope lines are CLI globs filtered by match_paths(), never git
    pathspecs (SI-1: one ':(exclude)' idiom line would silently invert
    the sweep to everything-except)."""
    path = os.path.join(repo_root(), CITATION_SCOPE_REL)
    if not os.path.exists(path):
        return list(CITATION_SCOPE_DEFAULT), "default", None
    globs = []
    with open(path, encoding="utf-8-sig") as f:
        for i, line in enumerate(f, 1):
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if s[0] in ":-!":
                return None, "file", (
                    f"truth: {CITATION_SCOPE_REL} line {i} starts "
                    f"with {s[0]!r} -- pathspec magic is refused; "
                    "scope lines are CLI globs (match_paths), never "
                    "git pathspecs (ADR-036/SI-1)")
            globs.append(s)
    return globs, ("file" if globs else "empty"), None

def load_watch_policies():
    """Shell: the consumer's named watch policies (FAZA 3, defect D-A).
    Returns (policies, state, err) -- policies is name -> [glob, ...] in
    file order, state is one of 'absent' / 'empty' / 'file', and err
    carries a refusal string for a malformed file (R14a: the loader
    returns it, the verb-level caller sys.exit()s it).

    ABSENT IS BENIGN HERE, and that is the one place this loader departs
    from its siblings in this file. `.truth/generated-paths` and
    `.truth/citation-scope` describe a check that runs whether or not you
    configured it, so an absent file means a DARK check and has to be
    voiced. Watch policies configure nothing on their own: a repo that
    names none simply passes --paths by hand, exactly as every repo did
    before this feature, so absence is a legitimate resting state and
    stays silent (see WATCH_POLICIES_REL for why no attestation lane).

    THE FILE IS PARSED, NOT INTERPRETED. One `<name> -- <glob>[, <glob>]`
    per line, '#' comments, blanks ignored -- the .truth/reachability-opt-out
    shape. Deliberately NOT YAML despite the runbook's first sketch: the
    CLI is stdlib-only, so a .yml file would need either a dependency this
    project forbids or a hand-rolled subset parser whose extension
    promises a generality it refuses.

    Every refusal below is a LOUD one for a file that would otherwise
    half-work:
      * pathspec magic (SI-1, verbatim from load_citation_scope) -- these
        globs go to match_paths(), never to git;
      * a missing ' -- ' separator, so a line cannot be silently read as
        a policy named after its own glob;
      * an empty name or an empty glob list -- a policy matching nothing
        is a watch set that reports 'covered' over zero files;
      * a name outside [a-z0-9][a-z0-9-]*, so `--watch-policy` arguments
        cannot collide with flags or need quoting;
      * a DUPLICATE name. Last-wins would mean a committed policy nobody
        can see is silently shadowing the one they are reading."""
    text = read_policy_file(WATCH_POLICIES_REL)
    if text is None:
        return {}, "absent", None
    policies = {}
    for i, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        where = f"{WATCH_POLICIES_REL} line {i}"
        if s[0] in ":-!":
            return None, "file", (
                f"truth: {where} starts with {s[0]!r} -- pathspec magic is "
                "refused; watch globs are CLI globs (match_paths), never "
                "git pathspecs (SI-1)")
        if " -- " not in s:
            return None, "file", (
                f"truth: {where} has no ' -- ' separator: {s!r}. The format "
                "is `<policy-name> -- <glob>[, <glob>...]`")
        name, rest = s.split(" -- ", 1)
        name = name.strip()
        if not WATCH_POLICY_NAME_RE.fullmatch(name):
            return None, "file", (
                f"truth: {where} has an unusable policy name {name!r} -- "
                "names are lowercase [a-z0-9][a-z0-9-]*, so they can be "
                "passed to --watch-policy without quoting")
        if name in policies:
            return None, "file", (
                f"truth: {where} redefines policy {name!r} -- a duplicate "
                "would silently shadow the definition a reader is looking "
                "at; give the second one its own name or merge them")
        globs = [g.strip() for g in rest.split(",") if g.strip()]
        if not globs:
            return None, "file", (
                f"truth: {where} defines policy {name!r} with no globs -- a "
                "policy matching nothing reports 'covered' over zero files")
        for g in globs:
            if g[0] in ":-!":
                return None, "file", (
                    f"truth: {where} glob {g!r} starts with {g[0]!r} -- "
                    "pathspec magic is refused (SI-1)")
        policies[name] = globs
    return policies, ("file" if policies else "empty"), None

def citation_grep(cid):
    """Shell: bare repo-wide `git grep -l -F <cid>` at the repo root
    (SI-2: a subtree cwd truncates the sweep to rc=1 = 'clean'; no
    pathspecs ever -- filtering is the core's job). rc contract PINNED:
    0 = hits, 1 = clean, anything else or spawn failure = unavailable.
    Returns (paths, None) or (None, reason)."""
    try:
        # -z: NUL-separated, UNQUOTED names (SI-2) -- default quotepath
        # octal-quotes any non-ASCII path, which match_paths can never
        # match, silently dropping the hit: fail-open on the fail-closed
        # gate (the R2 adversarial review's catch, TG11). '--' pins cid
        # to the pattern slot (a dash-leading argument is not an option).
        r = subprocess.run(["git", "grep", "-z", "-l", "-F", "--", cid],
                           capture_output=True, text=True, cwd=repo_root())
    except OSError as e:
        return None, f"git grep could not run ({e})"
    if r.returncode == 0:
        return [p for p in r.stdout.split("\x00") if p], None
    if r.returncode == 1:
        return [], None
    return None, f"git grep exited {r.returncode}"

def tracker_issues(a, native=None):
    """The tracker adapter seam (E1, v0.4.1). The join is tracker-agnostic:
    any source that yields a JSON array of issue objects with at least an
    `id` (and ideally `title`) satisfies the contract. Sources, in order:

      --stdin             pipe issues in:   <your-tracker-cmd> | truth ready --stdin
      TRUTH_TRACKER_CMD   a shell command printing the JSON array
      native work kernel  when the ledger holds issue records (ADR-002)
      default             `bd ready --json` (Beads)

    The ledger stands alone without any tracker; `ready` is its consumer,
    not its dependency -- so failure here degrades, never tracebacks.

    A1: returns (issues, err). Every failure here is a TRACKER contract
    failure, and `ready` is the only caller -- so the caller can act, and
    under R14a's rule that means the loader must let it. The refusal
    strings are unchanged; cmd_ready exits them.
    """
    if getattr(a, "stdin_issues", False):
        raw, src = sys.stdin.read(), "stdin"
    else:
        cmd = os.environ.get("TRUTH_TRACKER_CMD")
        if cmd is None and native is not None:
            return native, None
        cmd = cmd or "bd ready --json"
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if r.returncode != 0:
            return None, (
                f"truth: tracker command failed ({cmd!r}, exit {r.returncode}).\n"
                "  The ledger works without a tracker -- fallback: truth list --live.\n"
                "  To wire one: set TRUTH_TRACKER_CMD to any command printing a JSON\n"
                "  array of {id, title} issues, or pipe: <tracker-cmd> | truth ready --stdin")
        raw, src = r.stdout, repr(cmd)
    try:
        issues = json.loads(raw or "[]")
    except json.JSONDecodeError:
        return None, (f"truth: {src} output is not JSON -- tracker contract may "
                      "have drifted (known E1 risk); report, do not patch around")
    if not isinstance(issues, list):
        return None, (f"truth: {src} output is JSON but not an array -- the "
                      "adapter contract is a JSON array of issue objects")
    return issues, None

def events_at_ref(ref):
    """The ledger's content at a git ref, folded-ready.

    A1: returns (events, err). An unreadable ref is USAGE, not data, and
    the exit code for it is 2 -- but which code to exit with is the
    verb's contract (`baseline` documents exit 2 in its own --help), not
    a loader's, so the loader hands back the message and cmd_baseline
    exits it. Same bytes on stderr, same exit 2."""
    r = subprocess.run(["git", "show", f"{ref}:{LEDGER_REL}"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None, (
            f"truth: cannot read {LEDGER_REL} at {ref!r} -- "
            f"{r.stderr.strip().splitlines()[-1] if r.stderr.strip() else 'git show failed'} "
            "(exit 2: usage)")
    return load_events(io.StringIO(r.stdout)), None

def _short_sha(ref):
    r = subprocess.run(["git", "rev-parse", "--short", ref],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else "?"

def git_hooks_dir(root):
    """The hooks dir git actually consults: core.hooksPath when set, else
    $GIT_DIR/hooks. Hooks live where core.hooksPath says, not where an
    installer wrote them -- checking .git/hooks on a husky/lefthook repo
    reports health the repo does not have (TL-1). Returns
    (hooks_dir, hookspath_cfg); the cfg string lets doctor say WHY
    .git/hooks was ignored."""
    r = subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True,
                       text=True, cwd=root)
    gd = r.stdout.strip()
    if not os.path.isabs(gd):
        gd = os.path.join(root, gd)
    hp_cfg = subprocess.run(["git", "config", "core.hooksPath"],
                            capture_output=True, text=True,
                            cwd=root).stdout.strip()
    if hp_cfg:
        hooks_dir = hp_cfg if os.path.isabs(hp_cfg) else os.path.join(root, hp_cfg)
    else:
        hooks_dir = os.path.join(gd, "hooks")
    return hooks_dir, hp_cfg

def find_gate_hook(hooks_dir, names, needle):
    """The hook arm of the ADR-025 gate decision (factored out of doctor
    so the R2 write-verb banner shares it -- one detection, no fork):
    the first active hook under hooks_dir naming `needle`, or None.
    Candidates are (path, must_be_executable): git requires +x in the
    effective dir; manager-delegated user hooks (husky runs `.husky/<name>`
    from the `_` shim dir via sh) commonly are not executable themselves.
    isfile + try/except: a *directory* named `pre-commit`, or an
    executable-not-readable hook, must yield a decision, not a traceback
    (a doctor that crashes cannot decide the gate)."""
    for name in names:
        cands = [(os.path.join(hooks_dir, name), True)]
        if os.path.basename(hooks_dir.rstrip(os.sep)) == "_":
            cands.append((os.path.join(
                os.path.dirname(hooks_dir.rstrip(os.sep)), name), False))
        for hp, need_x in cands:
            try:
                if os.path.isfile(hp) \
                        and (not need_x or os.access(hp, os.X_OK)) \
                        and needle in open(hp, encoding="utf-8",
                                           errors="replace").read():
                    return hp
            except OSError:
                continue
    return None

def commit_gate_wired():
    """R2 (roadmap-v3): the minimal ADR-025 commit-gate decision -- an
    active check-truth pre-commit hook OR a CI config naming the gate
    script -- shared with doctor's fuller report via git_hooks_dir/
    find_gate_hook/ci_gate_names. Called at most once per CLI invocation
    (main, write verbs only); file existence + grep, no network. Any
    error deciding (no work tree, unreadable config, ...) counts as
    wired: the banner is advisory noise and must never crash or block a
    verb, so a weird repo state stays silent."""
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            return True
        root = r.stdout.strip()
        hooks_dir, _ = git_hooks_dir(root)
        if find_gate_hook(hooks_dir, ("pre-commit",), "check-truth"):
            return True
        return ci_gate_names("check-truth", root) is not None
    except Exception:
        return True

def ci_gate_names(needle, root):
    """ADR-025 (H6): does a known CI config name `needle` (the commit-gate
    script, e.g. 'check-truth')? The README makes 'a local hook OR CI' the
    one MUST, but doctor could see only the hook -- so a correctly
    CI-gated repo got a FAIL and learned to ignore doctor. This lets doctor
    decide the CI arm too. Best-effort with the SAME rigor as the
    discovery-snippet grep: a CI file mentioning the gate is doctor's
    evidence it runs where local hooks are absent, NOT proof the pipeline
    fires on the right events -- exactly as the AGENTS.md grep is not proof
    an agent reads it. Returns the repo-relative file, or None."""
    files = []
    for d in CI_GATE_DIRS:
        dp = os.path.join(root, d)
        if os.path.isdir(dp):
            # TOP LEVEL only, *.yml/*.yaml only -- exactly what the CI runs.
            # A `disabled/` subdir or a `truth.yml.disabled` rename is a
            # gate the CI does NOT run, so it must not satisfy the MUST.
            try:
                entries = sorted(os.listdir(dp))
            except OSError:
                entries = []
            for f in entries:
                if f.endswith((".yml", ".yaml")) \
                        and os.path.isfile(os.path.join(dp, f)):
                    files.append(os.path.join(dp, f))
    for rel in CI_GATE_FILES:
        p = os.path.join(root, rel)
        if os.path.isfile(p):
            files.append(p)
    for p in files:
        try:
            if needle in open(p, encoding="utf-8", errors="replace").read():
                return os.path.relpath(p, root)
        except OSError:
            continue
    return None
