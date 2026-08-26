#!/usr/bin/env python3
"""waiver-index -- is the list of ways to bypass a gate itself administered?

META-REPO ONLY (ADR-003 rule 2, ADR-046 Tier C): it sweeps THIS
repository's waiver register against THIS repository's CLI and is never
shipped to a consumer.

--- WHY THIS EXISTS ------------------------------------------------------
Every other register in this repository lists things that were CREATED --
decisions, invariants, arms, documents. `docs/waivers.md` lists the places
where a rule was SET ASIDE, and it is the register whose absence is least
visible: a waiver leaves a record only where somebody built one to leave.

The measured cost of having no such list: `--exit-ok`, A FLAG THAT HAS
NEVER EXISTED, was carried simultaneously by template/CHANGELOG.md,
docs/decisions/059-asynchronous-semantic-audit.md and
instruments/semantic-audit.py, all three citing ADR-035, whose own text
says `--evidence-exit-ok`. Three surfaces agreed with each other and none
of them with the parser, for as long as nobody happened to run it.

--- THE RULE, WHICH THIS REPOSITORY KEEPS RE-LEARNING --------------------
A check that walks from A to B and never walks back is half a check.
`register-index` was defeated twice by that shape; `arm-index` once; this
instrument is written with both directions from the start:

  forward   every flag the register lists is accepted by the parser, on
            the verbs the register names, taking the argument the register
            says it takes.
  reverse   every flag the parser accepts, every environment name any
            source reads, and every file in `.truth/` is a row here or a
            classified non-override. A NEW ONE IS A FINDING. Scoping this
            to `--*-ok` let a non-existent flag live in three documents;
            scoping it to FLAGS let the whole environment carrier through.

--- WHERE THE INVENTORY COMES FROM ---------------------------------------
By RUNNING `truth <verb> --help` for every verb the CLI lists, and reading
the usage line. Not by a regex over `template/truthlib/cli.py`.

That choice is the whole reliability argument. A regex over the source
would be a SECOND IMPLEMENTATION of the parser, and this repository's
standing finding is that a second implementation drifts silently, because
both copies look right in isolation -- it is the same defect as a sweep
that hardcoded a corpus the gate read from a file. The parser's own
`--help` is the surface an external reader has, and it cannot disagree
with the parser without argparse being wrong.

Cost: one subprocess per verb (22 today), about a second. Paid once per
sweep, in exchange for an inventory that cannot be stale.

--- WHAT THIS DOES NOT CHECK, NAMED RATHER THAN LEFT BLANK ---------------
The `stamp`, `decays` and `governing record` columns are NOT verified.
Each needs its own reader: whether the kernel really writes that field,
whether the decay is implemented, whether the cited record says what the
row says. A column nobody checks, not marked as unchecked, is precisely
what this register exists to catch -- so they are declared here and in
`docs/waivers.md` rather than implied to be swept.

What the sweep does instead is print the POPULATION: how many records in
the ledger carry each stamp. That answers "how many bypasses are standing"
from the ledger itself, without trusting the column.

The stamp column is read STRUCTURALLY -- a dotted path into the record's
payload, optionally with `= <value>` -- and the ledger is parsed as JSON,
not scanned as text. The first version of this instrument did scan lines
for the field name, and reported ZERO for `accept.screened = false` where
the truth was five: a nested field and a required value are invisible to
a substring match, so the crude reading was silently wrong about exactly
the three flags this register was built to surface. A population count
that under-reports is worse than none, for the same reason a shrunken ADR
count is: the number gets SMALLER as the problem gets bigger.

It is still reported as `record(s)`, not `overrides`, because this
instrument does not fold and must not imply that it derived a status.

--- NO BASELINE, AND WHY -------------------------------------------------
Every other sweep here carries one, because each was introduced onto an
existing backlog. There is no backlog to freeze: the reverse direction is
total per harvested carrier, so anything unclassified fails rather than
waiting, and a baseline file would be an empty apparatus inviting its
first entry. If a divergence
appears it is new, and new is exactly what should fail.

ADR-042 rule 2 still applies in both halves: a sweep that read zero rows,
or harvested zero verbs, has measured nothing and has not passed.

Stdlib only; no truthlib import -- it exercises the surfaces any external
reader has, which is the same argument as reading `--help`.

Exit: 0 clean, 1 findings, 2 usage, 3 an input could not be read
(ENVIRONMENT, not governance -- the sweep did not run), 8 examined
nothing (ADR-042 rule 2).

Usage: python3 instruments/waiver-index.py [--json]
Gate:  template/scripts/test-integrations.py (TestTierCInstruments), which
       exercises both directions, the argument-shape check and the
       ADR-042 empty guard against a stub CLI.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

REGISTER_REL = "docs/waivers.md"
CLI_REL = "scripts/truth"
LEDGER_REL = ".truth/claims.jsonl"
POLICY_DIR_REL = ".truth"

# A waiver is carried by something. Only some carriers can be ENUMERATED
# from a source, and the difference is the whole honesty of this register:
# for a harvested carrier the reverse direction is real, and for the rest
# there is no list to walk back from.
HARVESTED_CARRIERS = ("flag", "env", "file")
UNBOUNDED_CARRIERS = ("syntax", "config", "code")
ALL_CARRIERS = HARVESTED_CARRIERS + UNBOUNDED_CARRIERS

# The register must SAY that it is not total. Gated, because a limit
# sentence with nothing holding it is the first thing a redraft deletes --
# which is how the sentence naming six overdue gate-metrics reviews was
# lost earlier this same effort.
LIMIT_MARKER = "THIS REGISTER IS NOT TOTAL"
# A stamp cell that cannot separate "the waiver was used" from ordinary
# traffic says so with this literal, and no number is printed for it.
UNCOUNTABLE = "NOT COUNTABLE"

# Where a name is read from the environment. Python is exact; shell is a
# syntactic approximation of one idiom, and the register says so.
PY_ENV_RE = re.compile(r'(?:os\.environ\.get\(\s*|os\.environ\[\s*'
                       r'|os\.getenv\(\s*)["\']([A-Z_][A-Z0-9_]*)["\']')
SH_ENV_RE = re.compile(r'\$\{([A-Z_][A-Z0-9_]*)\s*:[-?]')
SH_ENVRUN_RE = re.compile(r'\benv\s+([A-Z_][A-Z0-9_]*)=')
SH_ASSIGN_RE = re.compile(r'^\s*([A-Z_][A-Z0-9_]*)=', re.M)
SOURCE_ROOTS = ("template", "scripts", "instruments", ".githooks")
SOURCE_SKIP = ("__pycache__", "/.git/", "/node_modules/")
# Every git hook name, not the three this repository happens to have: a
# `post-commit` reading an inherited variable was invisible, and the hook
# directory is where gate-disabling lives.
HOOK_NAMES = ("pre-commit", "pre-push", "pre-merge-commit", "post-commit",
              "post-merge", "post-checkout", "commit-msg", "prepare-commit-msg",
              "pre-rebase", "pre-applypatch", "post-applypatch", "post-rewrite",
              "pre-receive", "update", "post-receive", "post-update")
# Extensionless files that are nonetheless source. `scripts/truth` is the
# CLI ENTRY POINT and is Python with no suffix, so an environment read
# added to the program this register is about was outside the harvest.
# Read by shebang rather than by name, so a new one needs no edit here.
SHEBANG_PY = ("#!/usr/bin/env python", "#!/usr/bin/python")
SHEBANG_SH = ("#!/usr/bin/env bash", "#!/bin/bash", "#!/bin/sh",
              "#!/usr/bin/env sh")

EXIT_FINDINGS = 1
EXIT_USAGE = 2
EXIT_ENV = 3
EXIT_EMPTY = 8

# A verb line in `truth --help`: four spaces, the name, then two or more.
# `[a-z0-9-]` and not `[a-z-]`: a verb with a digit in its name was
# invisible, and an invisible verb takes every flag on it out of scope.
VERB_RE = re.compile(r"^\s{4}([a-z][a-z0-9-]*)\s{2,}", re.M)
# A flag in the `options:` section: exactly two spaces, the flag, then an
# optional metavar of ANY shape (`SENTENCE`, `PATHS`, `{P0,P1,P2}`, a
# lowercase word). Read from `options:` rather than from the usage line
# because argparse renders usage with wrapping, `|` alternation groups
# and unbracketed required arguments, and a reader of usage that assumes
# `[--flag METAVAR]` walks past every one of those shapes.
OPT_FLAG_RE = re.compile(r"^  (--[A-Za-z0-9][\w-]*)(?:[ =](\S+))?\s*$|"
                         r"^  (--[A-Za-z0-9][\w-]*)(?:[ =](\S+))?  +\S",
                         re.M)
# The same flags as they appear in a usage line, used ONLY as a
# cross-check against the options section. Any metavar shape, inside or
# outside brackets, alternation groups included.
USAGE_FLAG_RE = re.compile(r"(?:\[|\||\s)(--[A-Za-z0-9][\w-]*)"
                           r"(?:[ =]([^\]\|\s]+))?")
# argparse gives every parser its own --help; it is not a repository flag.
UNIVERSAL_FLAGS = frozenset(("--help",))
# Where a flag is declared NOT to be an override, with a reason.
NOT_OVERRIDE_REL = ".truth/waiver-not-an-override"
# Words a finished reason does not end on. Not a grammar: a closed list of
# the joins a sentence breaks at, which is what a reason abandoned
# mid-clause actually ends with. Three entries in this file were truncated
# that way on the first pass, and a half-written reason is worse than a
# missing one -- it reads as a judgement somebody made rather than one
# nobody finished, so nothing prompts anyone to finish it.
# Deliberately NOT every conjunction and preposition: pronouns and
# negations end sentences perfectly well ("never by this.", "rather than
# through it.", "it does not."), and a first cut that listed them produced
# five false positives on legitimate reasons. A check that fires on a
# valid input is worse than one that misses, so this is the narrower set:
# words after which an English sentence cannot stop.
DANGLING_WORDS = frozenset("""
a an the and or but so if because that which who whose when while for to of
in on at by from with without into onto over under than then as is are was
were be been being nor both either neither about after before between
during through against upon toward towards per via
""".split())
SENTENCE_END = (".", "!", "?", ":")
# The two shapes an override has HISTORICALLY taken here. Used only to
# make an excused flag that looks like one VISIBLE -- never to decide
# what is or is not an override, because both shapes missed a real one:
# `--refresh-evidence` (a sentence, no -ok suffix) and `--single-run`
# (neither, and it leaves no trace in the record at all).
def looks_like_override(name, arg):
    return name.endswith("-ok") or arg == "SENTENCE"
SEP_RE = re.compile(r"^\|[\s:|-]+\|$")
TICK_RE = re.compile(r"`([^`]+)`")
# What the register writes in the `admitted on` column for a bare flag.
BARE = "nothing"


class InputError(Exception):
    """An input could not be read. ENVIRONMENT, not a finding."""


def read(path, what):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError as e:
        raise InputError("cannot read %s (%s): %s"
                         % (what, os.path.relpath(path, ROOT), e.strerror))


def listdir(path, what):
    try:
        return os.listdir(path)
    except OSError as e:
        raise InputError("cannot list %s (%s): %s"
                         % (what, os.path.relpath(path, ROOT), e.strerror))


def cli_help(*argv):
    """`truth [verb] --help`, or an InputError naming what broke."""
    cmd = ([sys.executable, os.path.join(ROOT, CLI_REL)]
           + list(argv) + ["--help"])
    try:
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                           timeout=60)
    except OSError as e:
        raise InputError("cannot run %s (%s): %s"
                         % (CLI_REL, " ".join(argv) or "<top level>",
                            e.strerror))
    except subprocess.TimeoutExpired:
        raise InputError("%s %s --help did not return within 60s"
                         % (CLI_REL, " ".join(argv)))
    if r.returncode != 0:
        raise InputError("%s %s --help exited %d: %s"
                         % (CLI_REL, " ".join(argv), r.returncode,
                            (r.stderr or "").strip()[:200]))
    return r.stdout


def parser_flags():
    """{flag: {"arg": metavar|None, "verbs": [...]}} for EVERY flag.

    Every flag, not every flag matching a naming convention. The first
    version of this function harvested `--*-ok` only, and that scoping
    was wrong twice over in the same repository: `--refresh-evidence`
    lifts a hard refusal in `policy.py` and takes a sentence, and
    `--single-run` skips the G6 determinism double-run "accepting
    false-divergence risk" and leaves NO trace in the record at all.
    A reverse check that can only see one spelling is not a reverse
    check; it is a grep wearing the argument for one.

    So the inventory is total, and the register plus
    `.truth/waiver-not-an-override` must between them account for all of
    it. Deciding whether a flag lifts a gate is a judgement, and the
    judgement is written down per flag rather than inferred from its name.

    Read from the `options:` section, cross-checked against the usage
    line. A flag in one and not the other is a finding: the two renderings
    come from one parser, so a disagreement means this reader is wrong
    about at least one of them, and a reader that is quietly wrong about
    the shape of a flag is how an override goes unlisted.
    """
    verbs = VERB_RE.findall(cli_help())
    if not verbs:
        raise InputError("%s --help listed no subcommands -- the inventory "
                         "would be empty and this sweep would report health "
                         "having harvested nothing" % CLI_REL)
    flags, conflicts = {}, []
    for verb in verbs:
        text = cli_help(verb)
        usage, _, rest = text.partition("\n\n")
        opts = rest[rest.index("options:"):] if "options:" in rest else ""

        from_opts = {}
        for m in OPT_FLAG_RE.finditer(opts):
            name = m.group(1) or m.group(3)
            arg = m.group(2) if m.group(1) else m.group(4)
            if name in UNIVERSAL_FLAGS:
                continue
            from_opts[name] = arg

        from_usage = {}
        for m in USAGE_FLAG_RE.finditer(usage):
            if m.group(1) in UNIVERSAL_FLAGS:
                continue
            from_usage[m.group(1)] = m.group(2)

        for name in sorted(set(from_opts) ^ set(from_usage)):
            conflicts.append(
                "%s: %s appears in the %s of `%s %s --help` and not the "
                "other -- this sweep is misreading one of the two "
                "renderings of a single parser"
                % (verb, name, "options section" if name in from_opts
                   else "usage line", CLI_REL, verb))

        for name, arg in from_opts.items():
            entry = flags.setdefault(name, {"arg": arg, "verbs": []})
            if entry["arg"] != arg:
                conflicts.append(
                    "%s takes %s on some verbs and %s on others -- one flag, "
                    "two shapes" % (name, entry["arg"] or BARE, arg or BARE))
            if verb not in entry["verbs"]:
                entry["verbs"].append(verb)
    for entry in flags.values():
        entry["verbs"].sort()
    return verbs, flags, conflicts


def harvest_env():
    """{NAME: [files that read it]} across the whole source tree.

    The second source this register needed. `--*-ok` was never the shape
    of the escape surface: `TRUTH_SELF_VERDICT=1` lifts the ADR-010
    author-is-not-verifier refusal -- the separation the paper treats as
    the property most worth admiring -- and it is a flag nowhere, takes no
    sentence, stamps nothing, and is deliberately absent from the refusal
    text (an error that names its own bypass is an instruction to a
    compliant agent). A register of flags cannot hold it.

    Python is read exactly, from the three ways the stdlib exposes an
    environment read. Shell is a SYNTACTIC APPROXIMATION of one idiom --
    `${NAME:-default}`, `${NAME:?}` and `env NAME=` -- with names assigned
    in the same file treated as locals. That approximation is why three
    shell locals appear in the classification with "a local, not
    inherited" as their reason: the harvest over-reports rather than
    under-reports, which is the direction a safety reading must fail in.
    """
    found = {}
    for root in SOURCE_ROOTS:
        full = os.path.join(ROOT, root)
        if not os.path.isdir(full):
            continue
        for dirpath, dirnames, filenames in os.walk(full):
            rel_dir = os.path.relpath(dirpath, ROOT) + "/"
            if any(skip in "/" + rel_dir for skip in SOURCE_SKIP):
                continue
            for name in sorted(filenames):
                path = os.path.join(dirpath, name)
                rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
                text = None
                if name.endswith((".py", ".sh")) or name in HOOK_NAMES:
                    text = read(path, "a source file")
                    kind = ("py" if name.endswith(".py") else
                            "sh" if name.endswith(".sh") else None)
                else:
                    # No extension: ask the shebang. Skips binaries and
                    # data files without listing them.
                    try:
                        head = open(path, "rb").read(64).decode(
                            "utf-8", "replace")
                    except OSError:
                        continue
                    if head.startswith(SHEBANG_PY):
                        kind, text = "py", read(path, "a source file")
                    elif head.startswith(SHEBANG_SH):
                        kind, text = "sh", read(path, "a source file")
                    else:
                        continue
                # A hook name with NO shebang has no declared language.
                # Defaulting it to Python read a shell hook with the wrong
                # regex and missed the idiom entirely -- so an
                # undetermined file is scanned with BOTH, which is the
                # over-reporting direction this harvest is supposed to
                # fail in.
                if kind is None:
                    if text.startswith(SHEBANG_SH):
                        kind = "sh"
                    elif text.startswith(SHEBANG_PY):
                        kind = "py"
                    else:
                        kind = "both"
                if kind in ("py", "both"):
                    for m in PY_ENV_RE.finditer(text):
                        found.setdefault(m.group(1), []).append(rel)
                if kind in ("sh", "both"):
                    # `NAME="${NAME:-default}"` is the commonest bash way
                    # to READ an inherited variable, and treating the
                    # assignment as proof of locality missed exactly that
                    # shape -- the one this repository's own scripts use.
                    # A name is local only when it is assigned WITHOUT
                    # reading itself.
                    local = set()
                    for am in SH_ASSIGN_RE.finditer(text):
                        line_end = text.find("\n", am.start())
                        line = text[am.start():line_end if line_end > 0
                                    else len(text)]
                        if ("${%s" % am.group(1)) not in line:
                            local.add(am.group(1))
                    for m in SH_ENV_RE.finditer(text):
                        if m.group(1) in local:
                            continue
                        found.setdefault(m.group(1), []).append(rel)
                    for m in SH_ENVRUN_RE.finditer(text):
                        found.setdefault(m.group(1), []).append(rel)
    for name in found:
        found[name] = sorted(set(found[name]))
    return found


def harvest_policy_files():
    """Every file in .truth/, because editing one excuses findings.

    A baseline or opt-out file is a waiver carrier by construction: the
    sweep that reads it treats an entry there as a reason not to fail.
    They are enumerable -- it is a directory -- so the reverse direction
    is available and is taken.

    The reflexive case is the point. `.truth/waiver-not-an-override` is
    THIS register's own excuse file: adding a line to it removes a flag
    from the register's scope. An escape surface whose own escape surface
    is unregistered is the shape this whole effort keeps finding.
    """
    full = os.path.join(ROOT, POLICY_DIR_REL)
    if not os.path.isdir(full):
        return {}
    out = {}
    for name in sorted(listdir(full, "the policy directory")):
        if os.path.isdir(os.path.join(full, name)):
            continue
        rel = "%s/%s" % (POLICY_DIR_REL, name)
        readers = []
        for root in SOURCE_ROOTS:
            rfull = os.path.join(ROOT, root)
            if not os.path.isdir(rfull):
                continue
            for dirpath, dirnames, filenames in os.walk(rfull):
                if any(skip in "/" + os.path.relpath(dirpath, ROOT) + "/"
                       for skip in SOURCE_SKIP):
                    continue
                for f in filenames:
                    if not (f.endswith((".py", ".sh")) or f in HOOK_NAMES):
                        continue
                    p = os.path.join(dirpath, f)
                    if rel in read(p, "a source file"):
                        readers.append(
                            os.path.relpath(p, ROOT).replace(os.sep, "/"))
        out[rel] = sorted(set(readers))
    return out


def load_not_override(path):
    """(declared, unreasoned): `<flag>  <why it is not an override>`.

    The complement of the register. Together they must cover every flag
    the parser accepts, so that a NEW flag of any shape fails this sweep
    until somebody has decided which side it is on. A reason is required
    for the same reason it is required in every other policy file here:
    an excuse that says nothing is an override admitted on an empty
    sentence, which is the defect this whole register is about.
    """
    declared, unreasoned, unfinished = {}, [], []
    if not os.path.exists(path):
        return declared, unreasoned, unfinished
    for raw in read(path, "the not-an-override policy").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        flag, _, why = line.partition(" ")
        flag, why = flag.strip(), why.strip()
        declared[flag] = why
        if not why:
            unreasoned.append(flag)
            continue
        # ONE ENTRY PER LINE is the format, so the last word of the line
        # is the last word of the reason. A continuation line would be
        # read as a flag named after its first word, which is why the
        # format forbids them rather than supporting them.
        tail = why.split()[-1]
        bare_tail = re.sub(r"[^\w-]+$", "", tail).lower()
        ended = why.endswith(SENTENCE_END)
        if bare_tail in DANGLING_WORDS:
            # A joining word cannot end a sentence, with or without a
            # full stop after it -- "it is content, so." is still half an
            # argument.
            unfinished.append(
                (flag, "on the joining word %r%s" % (
                    bare_tail, "" if ended else " and with no full stop")))
        elif not ended:
            unfinished.append((flag, "with %r and no sentence-final mark"
                               % tail[-14:]))
    return declared, unreasoned, unfinished


# The three things a waiver can be admitted on, and the parser can tell
# them apart: a rationale, a value that is not one, or nothing at all.
ADMITTED_SENTENCE = "sentence"
ADMITTED_VALUE = "a value"


def _admitted_is(cell):
    """One of the three allowed values, or None for anything else.

    A controlled vocabulary rather than prose. Substring-matching this
    column read the legitimate cell `SENTENCE, never nothing` as bare --
    a check going red on a valid input, which is worse than one that
    misses. `a value` exists because `--ttl-days` takes a number: a
    number admits the override without justifying it, which is neither
    of the other two and is worth being able to say.
    """
    plain = cell.replace("*", "").replace("`", "").strip().lower()
    if plain in (BARE, ADMITTED_SENTENCE, ADMITTED_VALUE):
        return plain
    return None


def register_rows(path):
    """The waiver table, read as a BLOCK.

    Same parser discipline as `register-index`: reading a table as "every
    line that looks like a row" is a FILTER, and a filter cannot tell a
    line it rejected from a line that was never there. Deleting one
    trailing pipe would otherwise drop a waiver from the register in
    silence, which is the failure this whole file is about.
    """
    rows, malformed, trailing, state = [], [], [], "before"
    for n, raw in enumerate(read(path, "the waiver register").splitlines(), 1):
        line = raw.strip()
        if state == "before":
            if line.startswith("|") and line.endswith("|"):
                cells = [c.strip() for c in line[1:-1].split("|")]
                # The header is the EIGHT-column one whose first cell is
                # `carrier`. The shape is part of the match because this
                # file carries a SECOND table (the carrier/source/reverse
                # one in the domain statement), and a register that grew a
                # third would otherwise be read from whichever came first.
                # The domain table's first cell is `carrier class`, so the
                # two do not collide TODAY -- the shape check is what
                # keeps that from being load-bearing.
                if (len(cells) == 8 and cells[0].lower() == "carrier"):
                    state = "header"
            continue
        if state == "header":
            if SEP_RE.match(line):
                state = "body"
            else:
                malformed.append((n, "the row after the header is not the "
                                     "|---| separator"))
                state = "body"
            continue
        if state == "after":
            # A blank line ends a GFM table. Rows below it render as
            # ordinary text and administer nothing -- and the reverse
            # check would then report every flag they list as unlisted,
            # prescribing "add the row" for a row that is already there.
            # So the truncation itself is reported, at its own line.
            if line.startswith("|") and line.endswith("|") \
                    and not SEP_RE.match(line):
                cells = [c.strip() for c in line[1:-1].split("|")]
                if cells and cells[0].lower() != "carrier":
                    trailing.append((n, cells[1][:40] if len(cells) > 1
                                     else cells[0][:40]))
            continue
        if not line:
            state = "after"
            continue
        if not (line.startswith("|") and line.endswith("|")):
            malformed.append(
                (n, "a line inside the table block is not a row: %r -- GFM "
                    "renders a body row missing its trailing pipe exactly "
                    "like a complete one" % line[:60]))
            continue
        if SEP_RE.match(line):
            continue
        cells = [c.strip() for c in line[1:-1].split("|")]
        if len(cells) != 8:
            malformed.append(
                (n, "the row for %r has %d columns, not the eight the header "
                    "declares -- a row this sweep cannot read is a waiver it "
                    "cannot administer" % (cells[0] if cells else "?",
                                           len(cells))))
            continue
        flag = TICK_RE.findall(cells[1])
        rows.append({
            "line": n,
            "carrier": cells[0].replace("`", "").strip().lower(),
            "flag": flag[0] if flag else None,
            "flag_cell": cells[1],
            "verbs": [v.strip().strip("`") for v in cells[2].split(",")
                      if v.strip()],
            "gate": cells[3],
            # `admitted on` is a CONTROLLED VOCABULARY, exactly `SENTENCE`
            # or `nothing`. Substring-matching prose here meant a cell
            # reading "SENTENCE, never nothing" was read as bare -- a
            # check that fires on a legitimate input, which is worse than
            # one that misses.
            "admitted": cells[4],
            "admitted_kind": _admitted_is(cells[4]),
            "stamp": cells[5],
            # A field is counted only when its PRESENCE means the waiver
            # was used. `ttl_days` is on every claim, `evidence_paths` on
            # every path-claim, and `session`/`ts` on every record: a
            # count over those measures the ledger, not the escape. Rows
            # whose stamp cannot separate the two carry the literal
            # NOT COUNTABLE, and the sweep reports that instead of a
            # number -- a wrong population is worse than a missing one,
            # because it reads as a measurement.
            "stamp_fields": ([] if UNCOUNTABLE in cells[5]
                             else TICK_RE.findall(cells[5])),
            "decays": cells[6],
            "record": cells[7],
        })
    if state == "before":
        malformed.append((0, "no eight-column table header row (first cell "
                             "`carrier`) was found at all"))
    return rows, malformed, trailing


# A file-carried waiver's uses ARE its lines: one non-comment entry is one
# standing excusal. Marking those NOT COUNTABLE suppressed 209 of them.
ENTRIES_STAMP = "ENTRIES"


def count_entries(rel):
    """Non-comment, non-blank lines of a policy file, or None.

    ZERO IS A RESULT, not an absence. `.truth/generated-paths` is
    deliberately empty and its own header says emptiness is a statement;
    reporting that as unmeasurable threw away the one number it exists to
    make.
    """
    full = os.path.join(ROOT, rel)
    if not os.path.isfile(full):
        return None
    n = 0
    for line in read(full, "a policy file").splitlines():
        t = line.strip()
        if t and not t.startswith("#"):
            n += 1
    return n


def eval_predicate(spec, payload):
    """`(a/b) + c + !d` over one record's payload.

    Conjunction of terms; a term is a disjunction of fields; a field may
    be negated with `!` and may require a value with `= v`. Disjunction
    is `/` and not `|` because these predicates live in a markdown table
    cell, where `|` is the delimiter -- a grammar that cannot be written
    where it must be read is not a grammar. The rest of it
    is this small on purpose -- it exists because `--ttl-days` was
    declared uncountable on the claim that its override is "the ABSENCE
    of ttl_default, which no presence test separates". The separating
    predicate is one line of this grammar, and it answers 2.
    """
    for term in spec.split("+"):
        term = term.strip()
        if not term:
            continue
        ok = False
        for alt in term.split("/"):
            alt = alt.strip().lstrip("(").rstrip(")").strip()
            negate = alt.startswith("!")
            if negate:
                alt = alt[1:].strip()
            path, want = parse_stamp(alt)
            got = dig(payload, path)
            # PRESENT means present AND carrying a value. A JSON `null`
            # is the absence of one: `ttl_days: null` is what a claim
            # filed WITHOUT --ttl-days looks like, and counting those
            # turned a population of 2 into 6.
            if want is PRESENT:
                present = got is not MISSING and got is not None
            else:
                present = got is not MISSING and got == want
            if present != negate:
                ok = True
                break
        if not ok:
            return False
    return True


def parse_stamp(spec):
    """`a.b = false` -> (["a", "b"], False); `a_b` -> (["a_b"], PRESENT).

    PRESENT means "the field exists at all", which is the right test for a
    basis stamp: its presence IS the override. A value is required only
    where the stamp is a flipped boolean on a shared object -- `screened`
    is on every evidence record, and only `false` means a screen was
    lifted, so counting the field's presence there would count every
    claim in the ledger as a bypass.
    """
    field, _, want = spec.partition("=")
    path = [p for p in field.strip().split(".") if p]
    want = want.strip()
    if not want:
        return path, PRESENT
    return path, {"true": True, "false": False}.get(want.lower(), want)


PRESENT = object()


def dig(obj, path):
    """The value at a dotted path, or MISSING."""
    for key in path:
        if not isinstance(obj, dict) or key not in obj:
            return MISSING
        obj = obj[key]
    return obj


MISSING = object()


def stamp_population(specs):
    """How many ledger records carry each stamp, read structurally.

    NOT a substring scan. A nested field (`accept.screened`) and a
    required value (`= false`) are both invisible to one, and the first
    version of this instrument reported 0 where the truth was 5 -- for
    the three flags whose whole reason to be in this register is that
    they leave no rationale. An under-reporting population count is the
    shrinking-measurement failure this repository keeps finding.

    A malformed ledger line is COUNTED, not skipped: a record this sweep
    cannot parse is a record it cannot clear, and silently dropping it is
    how a sweep reports health over what it could not read.
    """
    path = os.path.join(ROOT, LEDGER_REL)
    if not os.path.exists(path):
        return None, 0
    counts = dict((s, 0) for s in specs)
    unreadable = 0
    for line in read(path, "the ledger").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            unreadable += 1
            continue
        payload = rec.get("payload")
        if not isinstance(payload, dict):
            continue
        for spec in specs:
            if eval_predicate(spec, payload):
                counts[spec] += 1
    return counts, unreadable


def sweep():
    register_text = read(os.path.join(ROOT, REGISTER_REL),
                         "the waiver register")
    rows, malformed, trailing = register_rows(os.path.join(ROOT, REGISTER_REL))
    verbs, flags, conflicts = parser_flags()
    harvested = {"flag": dict((k, v["verbs"]) for k, v in flags.items()),
                 "env": harvest_env(),
                 "file": harvest_policy_files()}
    declared, unreasoned, unfinished = load_not_override(
        os.path.join(ROOT, NOT_OVERRIDE_REL))

    failures = ["%s line %d: %s" % (REGISTER_REL, n, why)
                for n, why in malformed]
    failures += ["%s: %s" % (CLI_REL, c) for c in conflicts]
    for n, row in trailing:
        failures.append(
            "%s line %d: a table row for %r sits BELOW the blank line that "
            "ended the table, so the register was silently truncated and "
            "this row administers nothing. A blank line inside a GFM table "
            "ends it; move the row up, or the flag reads as unlisted"
            % (REGISTER_REL, n, row))
    for flag in sorted(unreasoned):
        failures.append(
            "%s: %s is declared not-an-override with no reason -- deciding "
            "that a flag does not lift a gate IS a judgement, and one "
            "recorded without its reason cannot be reviewed"
            % (NOT_OVERRIDE_REL, flag))
    for flag, why in sorted(unfinished):
        failures.append(
            "%s: %s's reason is not a finished sentence -- it ends %r. A "
            "reason abandoned mid-clause reads as a judgement somebody made, "
            "so nobody is prompted to finish it, and the flag stays excused "
            "on half an argument" % (NOT_OVERRIDE_REL, flag, why))

    # THE LIMIT STATEMENT. A register that partitions FLAGS while its title
    # reads over BYPASSES is a mis-scoped partition, and a reader takes an
    # unstated domain as universal. Three of six carriers cannot be
    # enumerated from any source, so the register must say so IN ITSELF --
    # and the sentence is gated, because a limit held by nothing is the
    # first thing a redraft removes.
    if LIMIT_MARKER not in register_text:
        failures.append(
            "%s does not contain the marker %r -- the register partitions "
            "only the carriers it can HARVEST (%s), while %s carry waivers "
            "that no source enumerates. Without that stated in the file, a "
            "reader of it alone concludes it covers every way a gate can be "
            "lifted, which is the mis-scoped partition this register exists "
            "to catch" % (REGISTER_REL, LIMIT_MARKER,
                          ", ".join(HARVESTED_CARRIERS),
                          ", ".join(UNBOUNDED_CARRIERS)))

    listed, bad_rows = {}, set()
    for row in rows:
        if row["carrier"] not in ALL_CARRIERS:
            failures.append(
                "%s line %d: carrier %r is not one of %s -- the carrier "
                "decides whether this row has a reverse direction at all"
                % (REGISTER_REL, row["line"], row["carrier"],
                   ", ".join(ALL_CARRIERS)))
            continue
        if not row["flag"]:
            failures.append(
                "%s line %d: the first cell names no backticked flag (%r) -- "
                "a waiver whose flag this sweep cannot read is a waiver it "
                "cannot check in either direction"
                % (REGISTER_REL, row["line"], row["flag_cell"][:60]))
            continue
        if row["flag"] in listed:
            failures.append(
                "%s: %s has two rows -- one waiver, one row"
                % (REGISTER_REL, row["flag"]))
            continue
        listed[row["flag"]] = row

    # --- forward: every listed waiver's carrier really carries it -------
    for name, row in sorted(listed.items()):
        carrier = row["carrier"]
        # The vocabulary check comes FIRST, above the unbounded return:
        # `syntax`, `config` and `code` rows have no source to be checked
        # against, but "what admits this waiver" is a property of the ROW,
        # not of its carrier, and an unbounded row is exactly where an
        # unchecked column is least likely to be noticed.
        if row["admitted_kind"] is None:
            bad_rows.add(name)
            failures.append(
                "%s: %s's `admitted on` cell reads %r -- it must be exactly "
                "`SENTENCE`, `a value` or `nothing`, on every carrier"
                % (REGISTER_REL, name, row["admitted"][:40]))
        if carrier in UNBOUNDED_CARRIERS:
            # syntax, config and code cannot be enumerated from any source,
            # so there is nothing to check the row AGAINST. The row is
            # recorded and the register says which carriers are in this
            # state; claiming otherwise would be the mis-scoping again.
            continue
        if carrier != "flag":
            if name not in harvested[carrier]:
                bad_rows.add(name)
                failures.append(
                    "%s lists %s as carried by %r, and no %s in this "
                    "repository %s -- either it was removed and the row "
                    "outlived it, or the row names one that never existed"
                    % (REGISTER_REL, name, carrier,
                       "source file" if carrier == "env" else "file",
                       "reads it" if carrier == "env" else "is there"))
            else:
                # The `where it applies` column, checked -- the harvest
                # already returns the answer. The flag rows' analogue
                # (verbs) was checked from the start; leaving this half
                # unchecked was the same asymmetry one column over.
                # SUBSET, not equality. The cell is allowed to name the
                # place that matters rather than all six readers of a
                # policy file -- a register nobody can read is not a
                # register. What it may not do is point somewhere the
                # thing does not apply, which is the ghost case and is
                # what this catches.
                claimed = set(row["verbs"])
                real = set(harvested[carrier][name])
                ghosts = sorted(claimed - real)
                if ghosts:
                    bad_rows.add(name)
                    failures.append(
                        "%s says %s applies at %s, and it does not -- this "
                        "repository has it at %s"
                        % (REGISTER_REL, name, ", ".join(ghosts),
                           ", ".join(sorted(real)) or "(nowhere)"))
            continue
        got = flags.get(name)
        if got is None:
            bad_rows.add(name)
            failures.append(
                "%s lists %s, which the CLI accepts on NO verb -- either the "
                "flag was removed and the row outlived it, or the row names a "
                "flag that never existed, which is what happened to "
                "`--exit-ok` across three documents"
                % (REGISTER_REL, name))
            continue
        claimed = row["admitted_kind"]
        if got["arg"] is None:
            really = BARE
        elif got["arg"] == "SENTENCE":
            really = ADMITTED_SENTENCE
        else:
            really = ADMITTED_VALUE
        if claimed is None:
            bad_rows.add(name)
            failures.append(
                "%s: %s's `admitted on` cell reads %r -- it must be exactly "
                "`SENTENCE`, `a value` or `nothing`. Free prose there cannot "
                "be checked against the parser, and substring-matching it "
                "fired on legitimate wording"
                % (REGISTER_REL, name, row["admitted"][:40]))
        elif claimed != really:
            bad_rows.add(name)
            failures.append(
                "%s says %s is admitted on %r; the parser says %r (metavar "
                "%s)" % (REGISTER_REL, name, claimed, really,
                         got["arg"] or "none"))
        if sorted(row["verbs"]) != got["verbs"]:
            bad_rows.add(name)
            failures.append(
                "%s says %s is accepted by %s; the parser accepts it on %s"
                % (REGISTER_REL, name, ", ".join(sorted(row["verbs"])) or
                   "(no verb)", ", ".join(got["verbs"])))

    # --- reverse: EVERY harvested thing is classified -------------------
    #
    # Total per carrier, never scoped to a naming convention. Scoping to
    # `--*-ok` let three real overrides through; scoping to FLAGS let the
    # whole environment carrier through, including the one that lifts the
    # author-is-not-verifier refusal.
    unclassified, excused_shaped = [], []
    for carrier in HARVESTED_CARRIERS:
        for name in sorted(harvested[carrier]):
            key = "%s:%s" % (carrier, name)
            in_reg = (name in listed and listed[name]["carrier"] == carrier)
            in_pol = key in declared
            if in_reg and in_pol:
                failures.append(
                    "%s is BOTH a row in %s and declared not-an-override in "
                    "%s -- one waiver, one side"
                    % (key, REGISTER_REL, NOT_OVERRIDE_REL))
            elif not in_reg and not in_pol:
                unclassified.append(key)
                failures.append(
                    "this repository has %s %s (%s) and NOTHING classifies "
                    "it: no row in %s, no entry in %s. A carrier nobody has "
                    "judged is a gate nobody knows can be lifted. Add the "
                    "row if it lifts a refusal, or declare it with a reason "
                    "if it does not"
                    % ({"flag": "the CLI flag", "env": "the environment name",
                        "file": "the policy file"}[carrier], name,
                       ", ".join(harvested[carrier][name])[:70]
                       or "read by nothing",
                       REGISTER_REL, NOT_OVERRIDE_REL))
            elif in_pol and carrier == "flag" \
                    and looks_like_override(name, flags[name]["arg"]):
                excused_shaped.append(name)

    # mirror: a declaration that outlived its subject
    known = set("%s:%s" % (c, n) for c in HARVESTED_CARRIERS
                for n in harvested[c])
    for key in sorted(declared):
        if ":" not in key:
            failures.append(
                "%s: %r is not a namespaced key -- every entry names its "
                "carrier (%s), because the same name can be a flag on one "
                "carrier and nothing on another"
                % (NOT_OVERRIDE_REL, key, "|".join(HARVESTED_CARRIERS)))
        elif key.split(":", 1)[0] not in HARVESTED_CARRIERS:
            failures.append(
                "%s: %r names carrier %r, which is not harvested -- an "
                "unbounded carrier has no list to be excused FROM"
                % (NOT_OVERRIDE_REL, key, key.split(":", 1)[0]))
        elif key not in known:
            failures.append(
                "%s declares %s not-an-override, and this repository has no "
                "such thing -- the entry outlived its subject; drop the line"
                % (NOT_OVERRIDE_REL, key))

    fields = sorted(set(f for row in listed.values()
                        for f in row["stamp_fields"]
                        if f != ENTRIES_STAMP))
    population, unreadable = stamp_population(fields)
    # A file-carried waiver's uses ARE its lines. Counting them is one
    # `wc -l`, and 209 standing excusals were reported as unmeasurable
    # because no ledger field carries them. Where the waiver lives in a
    # file, the file is the record.
    entry_counts = {}
    for name, row in listed.items():
        if ENTRIES_STAMP in row["stamp_fields"]:
            entry_counts[name] = count_entries(name)
    if unreadable:
        failures.append(
            "%d line(s) of %s could not be parsed as JSON -- the population "
            "counts below are taken over what WAS readable, which is not the "
            "ledger" % (unreadable, LEDGER_REL))

    return {"rows": rows, "listed": listed, "flags": flags, "verbs": verbs,
            "bad_rows": bad_rows,
            "failures": failures, "population": population,
            "stamp_fields": fields, "entry_counts": entry_counts,
            "unreadable_ledger_lines": unreadable,
            "declared_not_override": declared,
            "unclassified": unclassified,
            "harvested": harvested,
            "excused_but_override_shaped": excused_shaped}


def main(argv):
    known = ("--json", "-h", "--help")
    for arg in argv:
        if arg not in known:
            print("waiver-index: unknown argument %r\n%s" % (arg, __doc__),
                  file=sys.stderr)
            return EXIT_USAGE
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0

    reg = os.path.join(ROOT, REGISTER_REL)
    if not os.path.exists(reg):
        print("waiver-index: %s not found -- run from the meta-repo"
              % REGISTER_REL, file=sys.stderr)
        return EXIT_USAGE

    try:
        r = sweep()
    except InputError as e:
        print("waiver-index: %s -- the sweep did NOT run. This is an "
              "environment failure, not a finding (exit %d)"
              % (e, EXIT_ENV), file=sys.stderr)
        return EXIT_ENV

    # ADR-042 rule 2, aimed at the case where it actually bites.
    #
    # Guarding each side separately was wrong and an arm caught it: with
    # rows in the register and zero flags harvested, "examined nothing" is
    # both inaccurate -- 22 verbs and every row WERE examined -- and less
    # informative than the divergence itself, which is that every waiver
    # in the register names a flag the CLI no longer accepts. Both exits
    # block, so nothing fails open either way; exit 1 says more.
    #
    # The case ADR-042 rule 2 is really about is BOTH sides empty: an
    # empty register agrees with an empty parser, produces no finding, and
    # would report a clean escape surface having read neither. That is the
    # most comfortable way to be wrong about how many gates can be
    # bypassed, and it is the one that must not exit 0.
    #
    # Extended to EVERY harvested carrier when they were added: guarding
    # only rows-and-flags left `env` and `file` able to harvest nothing
    # and agree with a register that lists nothing for them.
    empty_carriers = [c for c in HARVESTED_CARRIERS
                      if not r["harvested"][c]
                      and not any(row["carrier"] == c
                                  for row in r["listed"].values())]
    if not r["listed"] and not r["flags"]:
        print("waiver-index: read ZERO waiver rows from %s AND harvested "
              "ZERO flags from %d verb(s) of %s --help. Empty agrees "
              "with empty, so this sweep has measured nothing rather than "
              "found nothing (ADR-042 rule 2). Check the table's eight "
              "columns, and that the CLI still prints usage lines."
              % (REGISTER_REL, len(r["verbs"]), CLI_REL), file=sys.stderr)
        return EXIT_EMPTY
    if empty_carriers:
        print("waiver-index: harvested ZERO for carrier(s) %s and the "
              "register lists none either -- empty agrees with empty, so "
              "this sweep measured nothing about %s rather than finding "
              "nothing (ADR-042 rule 2). This repository always has flags, "
              "environment reads and .truth/ files, so a zero here is a "
              "broken harvest, not a clean surface."
              % (", ".join(empty_carriers),
                 "them" if len(empty_carriers) > 1 else "it"),
              file=sys.stderr)
        return EXIT_EMPTY

    if "--json" in argv:
        print(json.dumps({
            "register": REGISTER_REL,
            "limit_marker_present": LIMIT_MARKER in read(
                os.path.join(ROOT, REGISTER_REL), "the waiver register"),
            "carriers": {
                "harvested": list(HARVESTED_CARRIERS),
                "unbounded": list(UNBOUNDED_CARRIERS),
            },
            "inventory": dict(
                (c, {"harvested": len(r["harvested"][c]),
                     "waivers": sum(1 for row in r["listed"].values()
                                    if row["carrier"] == c),
                     "declared_not_override": sum(
                         1 for k in r["declared_not_override"]
                         if k.startswith(c + ":"))})
                for c in HARVESTED_CARRIERS),
            "waivers": dict(
                (n, {"carrier": row["carrier"],
                     "where": row["verbs"],
                     "admitted_on": row["admitted_kind"],
                     "stamp_fields": row["stamp_fields"],
                     "countable": bool(row["stamp_fields"])})
                for n, row in r["listed"].items()),
            "unbounded_rows": sorted(
                n for n, row in r["listed"].items()
                if row["carrier"] in UNBOUNDED_CARRIERS),
            # Explicitly separated: a machine reader that summed the
            # countable half and called it the escape surface would be
            # wrong by two thirds, and the flags-only JSON this replaced
            # invited exactly that.
            "population": {
                "countable": r["population"],
                "not_countable": sorted(
                    n for n, row in r["listed"].items()
                    if not row["stamp_fields"]),
                "note": ("every total is a LOWER BOUND: the not_countable "
                         "waivers leave no field separating their use from "
                         "ordinary traffic"),
            },
            "unreadable_ledger_lines": r["unreadable_ledger_lines"],
            "unclassified": r["unclassified"],
            "failures": r["failures"],
        }, indent=2))
        return EXIT_FINDINGS if r["failures"] else 0

    # The escape surface is the REGISTERED waivers, not every flag the
    # parser accepts. Counting all 50 flags here reported 22 "admitted on
    # nothing" including `--json` and `--live`, which is a number about
    # argparse rather than about this system's gates.
    bare = sorted(n for n, row in r["listed"].items()
                  if row["admitted_kind"] == BARE)
    sent = sorted(n for n, row in r["listed"].items()
                  if row["admitted_kind"] == ADMITTED_SENTENCE)
    valued = sorted(n for n, row in r["listed"].items()
                    if row["admitted_kind"] == ADMITTED_VALUE)
    for name in sorted(r["listed"]):
        row = r["listed"][name]
        # NAME-SCOPED, not a substring search over every failure line.
        # Matching `name in failure_text` marked the row for
        # `.truth/waiver-not-an-override` as failing whenever any message
        # merely NAMED that policy file -- the same defect as reading the
        # `admitted on` column by substring.
        mark = "FAIL " if name in r["bad_rows"] else "OK   "
        print("%s %-22s %-9s %s" % (mark, name,
                                    row["admitted_kind"] or "?",
                                    ", ".join(row["verbs"])))
    print("  %-22s %d waiver(s): %d admitted on a sentence, %d on a value "
          "that is not one, %d on NOTHING"
          % ("escape surface", len(r["listed"]), len(sent), len(valued),
             len(bare)))
    if valued:
        print("  %-22s %s" % ("admitted on a value", ", ".join(valued)))
    if bare:
        print("  %-22s %s" % ("admitted on nothing", ", ".join(bare)))
    for carrier in HARVESTED_CARRIERS:
        total = len(r["harvested"][carrier])
        regd = sum(1 for row in r["listed"].values()
                   if row["carrier"] == carrier)
        decl = sum(1 for k in r["declared_not_override"]
                   if k.startswith(carrier + ":"))
        print("  %-22s %d harvested: %d waiver(s), %d declared not-an-"
              "override, %d unclassified"
              % (carrier + " inventory", total, regd, decl,
                 total - regd - decl))
    unb = sorted(n for n, row in r["listed"].items()
                 if row["carrier"] in UNBOUNDED_CARRIERS)
    print("  %-22s %d recorded by hand, from NO list: %s"
          % ("unbounded carriers", len(unb), ", ".join(unb) or "(none)"))
    print("  %-22s syntax, config and code cannot be harvested, so this "
          "register is NOT total and says so in its own text"
          % "")
    if r["excused_but_override_shaped"]:
        print("  %-22s %s" % ("excused, override-shaped",
                              ", ".join(r["excused_but_override_shaped"])))
    if r["population"] is None:
        print("  %-22s %s not on disk -- population unknown"
              % ("population", LEDGER_REL))
    else:
        for f in r["stamp_fields"]:
            print("  %-22s %-28s %d record(s) in history"
                  % ("population", f, r["population"][f]))
        for name in sorted(r["entry_counts"]):
            n = r["entry_counts"][name]
            print("  %-22s %-28s %s"
                  % ("population", name,
                     "not on disk" if n is None else
                     "%d standing entr%s" % (n, "y" if n == 1 else "ies")))
        stampless = sorted(n for n, row in r["listed"].items()
                           if not row["stamp_fields"])
        if stampless:
            print("  %-22s NOT COUNTABLE (%d): %s"
                  % ("population", len(stampless), ", ".join(stampless)))
            print("  %-22s -- each leaves no field that separates its use "
                  "from ordinary traffic, so every total here is a LOWER "
                  "BOUND" % "")
    for f in r["failures"]:
        print("FAIL  " + f)
    print("waiver-index: %d waiver(s) over %d verb(s) -- %d failure(s)"
          % (len(r["listed"]), len(r["verbs"]), len(r["failures"])))
    return EXIT_FINDINGS if r["failures"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
