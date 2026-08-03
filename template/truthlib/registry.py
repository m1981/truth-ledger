"""truthlib.registry -- the machine vocabulary and the fixed lexicons.

Every named set a consumer, satellite, or sibling module would otherwise
hand-copy, exported once: statuses, verdict maps, kinds, tiers, the
ADR-007/035 lexicons, id/ts/concern shapes, policy-file locations, and
the numeric gate knobs.  Pure constants only -- no functions, no I/O
(ADR-043 established the registry; ADR-044 gives it its own module).
"""
import re

LEDGER_REL = ".truth/claims.jsonl"
# ADR-045 (D2): the write-verb serialization lock target -- a separate
# file under the GIT DIR (like .git/truth-whisper.seen), never the
# ledger fd itself, so the O_APPEND append path stays exactly as audited
# (TestAppendSingleWrite) and readers never touch a lock. In the git dir
# deliberately, not a worktree sibling: an untracked lock beside the
# ledger dirtied every consumer's `git status` and refused the
# session-close survival gate (caught by the SC canary on the sibling
# draft); the git dir is machine-local and status-invisible by
# construction, and per-worktree exactly as the checked-out ledger is.
# The file's bytes never matter -- flock(2) state lives in the kernel,
# so a crashed holder's lock dies with its process.
LEDGER_LOCK_NAME = "truth-ledger.lock"
PROMPT_REL = "prompts/truth-verifier.md"
# ADR-036: tombstone citation gate. The scope file is consumer POLICY
# (SI-4): absent -> the built-in default below applies with a notice;
# committed-empty -> consciously nothing (silent). The refusal exit code
# is distinct so a sweep driver can tell "cited, swap first" from
# unknown-id / ack-mismatch / unavailable, which all exit 1 (the
# impact-3/4 / baseline-5 precedent).
CITATION_SCOPE_REL = ".truth/citation-scope"
CITATION_SCOPE_DEFAULT = ("docs/specs/**",)
CITATIONS_EXIT_CITED = 6
# ADR-037: which artifacts are GENERATED is a per-repository fact the
# template cannot know -- consumer policy (SI-4), shipped EMPTY with a
# header (committed-empty = consciously nothing, silent; ABSENT = the
# check is dark, one advisory line says so).
GENERATED_PATHS_REL = ".truth/generated-paths"
# ADR-039: blast forecast. Window and cold-start floor change only with
# the BF faults; the EFFECTIVE floor self-calibrates per repo (P90 of
# stored forecasts over live path-claims once enough exist) because a
# per-repo percentile stored as a universal constant is a category
# error -- at the adoption review the constant floor would have printed
# on ~85% of this repo's own filings (tr-c3087292).
BLAST_WINDOW_DAYS = 30
BLAST_ADVISORY_FLOOR = 15
BLAST_MIN_OBSERVATIONS = 20
EVIDENCE_CLASSES = ("VERIFIED", "INFERRED", "UNVERIFIED")
TIERS = ("P0", "P1", "P2")
VERDICTS = ("agree", "diverge", "cannot_verify", "retracted")
# ADR-049: the retraction cause. NOT a list of observed flavours -- the
# complete truth table of two yes/no questions about the retracted
# SENTENCE ("is it still true?", "was it ever true?"): 2x2 minus the
# impossible cell (still true but never true) = exactly three, so the
# set is exhaustive and mutually exclusive by construction, not by
# survey. Order is the decision order the --help tree prints.
#   restated -- still true; a successor states it better (SUCCESSOR
#               REQUIRED: the gate that earns this field its ADR-046
#               envelope admission)
#   expired  -- was true, the world moved past it (the user-proposed
#               `fixed` and `version` both land here: they differ only
#               in WHO moved the world, which nothing reads)
#   wrong    -- never true, or its evidence never demonstrated it
# `moved` is deliberately absent -- see ADR-049's non-goals. Absent
# entirely on pre-ADR-049 records: readers render that `unrecorded`
# (retraction_cause_report), never silently drop it.
RETRACTION_CAUSES = ("restated", "expired", "wrong")
KINDS = ("claim", "verdict", "invalidation", "premise", "issue",
         "issue_event", "contradicts")
STATUSES = ("unverified", "live", "stale", "diverged", "cannot_verify",
            "retracted", "disputed")
# R13 (P2 contract layer): the two vocabularies every consumer used to
# hand-copy, exported once. ACTIVE_STATUSES is the ADR-018 intake notion
# of "active" ({live, unverified}); VERDICT_STATUS is the fold's
# verdict->status map. The fold indexes VERDICT_STATUS directly, so an
# unknown verdict still raises KeyError there -- deliberately unchanged
# in this phase (three consumers had three unknown-verdict behaviors:
# fold KeyError, half-life silent skip, stats uncounted; unifying them
# is a semantics change, not an extraction).
ACTIVE_STATUSES = frozenset(("live", "unverified"))
VERDICT_STATUS = {"agree": "live", "diverge": "diverged",
                  "cannot_verify": "cannot_verify", "retracted": "retracted"}
# The satellites' citation-blocking contract (spec-health CLAIM_BAD /
# fact-health BAD): the statuses that fail a prose citation outright.
# Exported through `truth vocab` and deliberately consumed by NOTHING
# else in this CLI -- the constant exists so the satellites source it at
# runtime instead of hand-copying it (the R1 `disputed` drift incident:
# the gated copies stayed correct, the hand copies did not).
CITATION_BAD = frozenset(("stale", "diverged", "retracted", "disputed"))
ISSUE_EVENTS = ("claimed", "released", "closed", "reopened", "cancelled")
ISSUE_STATUSES = ("open", "claimed", "closed", "cancelled")
# R2 (roadmap-v3): the verbs that append to the ledger -- exactly the set
# whose records the ADR-025 commit gate would screen, so exactly the set
# that warns when that gate is unwired. Read verbs (list, queue, ready,
# stats, impact, dispatch, validate, doctor, issues, baseline, vocab) stay
# silent; `validate --stdin` especially MUST stay exempt -- it runs
# inside the commit gate itself.
WRITE_VERBS = frozenset(("claim", "verdict", "invalidate-scan", "premise",
                         "contradicts", "issue", "start", "done",
                         "reaffirm"))  # R3: reaffirm appends agree verdicts
DISCOVERY_FILES = ("AGENTS.md", "CLAUDE.md", ".cursorrules",
                   ".github/copilot-instructions.md")
# ADR-025: CI config files/dirs doctor greps for the commit-gate script
# name, so it can decide the README's "a hook OR CI must exist" MUST
# instead of false-failing a CI-only repo. Best-effort, same rigor as the
# discovery grep -- a CI file naming the gate is evidence it runs, not
# proof. CI_GATE_DIRS hold pipeline files at the TOP LEVEL only: their CI
# executes exactly those (GitHub Actions/Woodpecker ignore subdirectories
# and non-.yml/.yaml files), so doctor scans exactly what runs -- scanning
# deeper would pass a `truth.yml.disabled` rename or a `disabled/` subdir
# the CI never runs (an H6 adversarial finding).
CI_GATE_FILES = (".gitlab-ci.yml", ".circleci/config.yml",
                 "azure-pipelines.yml", "Jenkinsfile", ".drone.yml",
                 "bitbucket-pipelines.yml", ".woodpecker.yml",
                 ".travis.yml", ".buildkite/pipeline.yml")
CI_GATE_DIRS = (".github/workflows", ".woodpecker")
DUPLICATE_THRESHOLD = 0.6
QUEUE_AGE_WARN_DAYS = 14
# ADR-032: a --scope-ok override (ADR-007) filed without an explicit
# --ttl-days is stamped this default shelf life, so the scope judgment is
# mechanically re-asked when it lapses (expiry rides the unchanged ADR-019
# scan path -> ADR-030 arm 1 routes it to re-file -> ADR-007 re-fires).
# Changed only with ADR-032's adoption gate.
DEFAULT_OVERRIDE_TTL_DAYS = 30
ID_RE = re.compile(r"^tr-[0-9a-f]{8}$")
WK_ID_RE = re.compile(r"^wk-[0-9a-f]{8}$")
# ADR-015: the canonical ts profile -- fixed-width UTC microseconds,
# exactly what now_iso() emits. The fold sorts the raw ts STRING, so
# string order equals time order ONLY on a fixed-width single-offset
# form; Z-suffix, non-UTC offsets, and variable precision all break it.
# Enforced in validate_events in lockstep with the schema's pattern
# (FS-2 corpus holds the two together).
TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}\+00:00$")
# ISO/IEC/IEEE 42010 'concern': LEGACY TRIAGE METADATA (Tier C since
# ADR-046). The filing surface (--concern, list --concern, the stats
# concerns section) is removed -- the field failed the envelope admission
# rule (no fold or blocking gate ever read it). The regex stays because
# validate's legacy branch still shape-checks the records admitted before
# the demotion, and the Tier C reader (the meta-repo's
# instruments/concern-tag.py) still tallies them. The field is CLOSED to
# new records: no verb stamps it, and hand-editing it in is forbidden by
# the admission rule. Anchored \A..\Z, not ^..$: Python's $ also matches
# BEFORE a trailing newline (red-team F1); the schema's pattern carries
# the equivalent guard in ECMA-compatible form.
CONCERN_RE = re.compile(r"\A[a-z0-9-]{1,32}\Z")
# ADR-007: universal-quantifier lexicon (tokens matched word-level via
# tokens(); phrases matched with word boundaries). Changed only together
# with the Q-canary faults.
QUANTIFIER_TOKENS = frozenset(("only", "no", "none", "never", "nowhere",
                               "anywhere", "everywhere", "always", "each",
                               "all", "every", "any", "entire",
                               "whole", "zero"))
QUANTIFIER_PHRASES = ("repo-wide", "the repo", "the codebase", "the project")
# ADR-035: negation lexicon for the positive-claim exit gate. COPIES of
# the five negation-shaped quantifier tokens, deliberately not a shared
# reference -- widening one lexicon must never silently widen the other
# gate (core test X6 pins the subset relation, one-directional: it
# catches removals here, not additions there). Changed only together
# with the X-canary faults.
NEGATION_TOKENS = frozenset(("not", "neither", "nor", "without", "absent",
                             "lacks", "lacking", "missing", "unused",
                             "unreferenced",
                             # the quantifier lexicon's negation-shaped five:
                             "no", "none", "never", "nowhere", "zero"))
# ADR-007: option tokens that narrow an evidence command's domain
# (-t/--type is ripgrep's type filter -- a scope narrower that carries no
# slash, so it evaded the positional check, F3/v0.6.2).
SCOPE_OPTION_TOKENS = frozenset(("--include", "--exclude", "--include-dir",
                                 "--exclude-dir", "-g", "--glob", "--path",
                                 "-t", "--type"))

# ADR-008: same-machine append races invert timestamps by milliseconds;
# anything beyond this is a clock regression worth a warning.
SKEW_TOLERANCE_SECONDS = 300
EVIDENCE_ALLOW_REL = ".truth/evidence-allow"
# ADR-022: a TEMPLATE-OWNED baseline deny for the EVIDENCE screen only.
# The allowlist is the security boundary (ADR-021); this is an anti-footgun
# guardrail so a consumer who accidentally allowlists a shell or generic
# executor -- which would turn the read-only screen into arbitrary
# execution -- is still refused (deny-wins over the allowlist). It lists
# only programs whose SOLE job is to run OTHER programs (never a read-only
# check), so it makes NO completeness claim (that trap is ADR-021's
# lesson) and has zero false-positive cost. It does NOT apply to the
# ACCEPTANCE screen (ADR-014 oracles execute code on purpose, e.g. `bash
# canary.sh`). Grey-zone interpreters/VCS with plausible read-only uses
# (git, python, awk, sed, curl, ...) are NOT hard-denied -- doctor warns
# about them instead (below), leaving the policy to the consumer.
EVIDENCE_DENY_REL = ".truth/evidence-deny"
# ADR-022: doctor advisory set -- programs that CAN execute code or write
# files but have plausible read-only uses, so they are surfaced (WARN),
# not blocked. Blocking these would fight legitimate workflows; ignoring
# them let H4's git-in-the-allowlist slip in unnoticed.
# ADR-040 adds rg/file/date, found by auditing every entry of the shipped
# allowlist rather than waiting for an incident: `rg --pre PROG` and
# `--hostname-bin PROG` execute arbitrary programs, `file -C -m PATH`
# writes a compiled magic file to an arbitrary path, and `date` sets the
# system clock (GNU -s/--set, or a bare BSD positional -- the uniq-shaped
# channel a flag table cannot see). They left the shipped default in the
# same change; this set is what reaches a consumer whose OWN allowlist,
# which the template never clobbers, still carries them.
DOCTOR_GREY_ZONE = frozenset((
    "git", "python", "python3", "python2", "perl", "ruby", "node", "make",
    "pytest", "tox", "awk", "gawk", "sed", "curl", "wget", "ssh", "scp",
    "rsync", "docker", "npm", "npx", "pip", "pip3", "cargo", "go",
    "rg", "file", "date"))
# ADR-014: acceptance oracles execute repository code at `done` time --
# their own allowlist, never the read-only evidence one.
ACCEPT_ALLOW_REL = ".truth/accept-allow"
ACCEPT_KINDS = ("verification", "validation")  # 12207's two V's
# FS-3: the scale gate -- doctor warns when load+fold exceeds this;
# the snapshot cache stays unimplemented until the warning fires. The
# gate watches the READ path (load+fold+fold_issues, timed in doctor)
# and, since v0.9.29, stands for the WRITE path too: every write verb
# loads and folds inside the ledger lock, so the same latency prices
# the critical section a concurrent writer waits behind. The linear
# scans that remain (append's tail read is tail-seek since v0.9.29;
# reaffirm/invalidate-scan walk every claim by design) are
# watched-by-design residuals, not sensor-covered ones: no separate
# alarm exists for them, this constant's trip is their proxy.
FOLD_LATENCY_WARN_MS = 200
HALF_LIFE_MIN_OBS = 5  # FS-1: below this, intake suggests nothing (noise)

# ADR-033: 'dead' for the override-velocity repeat detector. A claim has
# no 'superseded' status in this system (supersede is premise-scoped,
# ADR-013), so the dead set is exactly the three terminal-for-now claim
# statuses the fold produces below live/unverified.
DEAD_CLAIM_STATUSES = frozenset(("stale", "diverged", "retracted"))

# ADR-010 separation instrument (2026-08-01). Derived by MEASUREMENT, not
# chosen: one CLI invocation costs ~0.11-0.15s on the reference machine, so
# `dispatch` + `verdict` is ~0.26s of pure process cost before a verifier
# has read a dispatch packet or re-run any evidence. A first `agree`
# landing inside this floor therefore leaves no room for the work a
# verification IS -- the ledger records a different session STRING and
# nothing more. Advisory only, and deliberately never a refusal: a gate
# keyed on elapsed time is defeated by `sleep` and would TEACH that
# bypass, which is the ADR-011 confused-deputy shape.
SEPARATION_FLOOR_SECONDS = 1.0
