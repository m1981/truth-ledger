#!/usr/bin/env python3
"""register-index -- is the index of registers itself administered?

META-REPO ONLY (ADR-003 rule 2, ADR-046 Tier C): it sweeps THIS
repository's own prose corpus against THIS repository's register index
and is never shipped to a consumer.

--- WHY THIS EXISTS ------------------------------------------------------
This repository keeps nine or ten administered lists -- decisions,
invariants, arms, the plan, briefs, claims, gate metrics, shelved
designs, the citation scope -- and each has its own custodian mechanism.
What it did not keep was a list OF the lists, and the absence has a
measurable cost in both directions:

  forward   a location moves and the index that names it keeps naming
            the old path. `doc-health.sh` catches this only for markdown
            LINKS; a path written as prose or in backticks is invisible
            to it, and backtick mentions are excluded there deliberately
            ("shorthand is endemic and legitimate").

  reverse   a document is written under docs/ and belongs to no register
            at all. Nothing notices, because every existing sweep starts
            from a register and walks outward. Measured on 2026-08-24 at
            the moment this instrument was introduced: 25 live markdown
            files under docs/ that no register claimed -- including
            docs/specs/, which `.truth/citation-scope` protects and which
            the paper cites, but which no index listed.

ISO/IEC 11179 states the rule this file implements: THE REGISTRY IS
REGISTERED. An index is not a vantage point outside the corpus; it is
another administered item with its own decay mode, and its decay mode is
the worst-placed of the set -- it is read at the start of a session and
edited at the end of a different one. So docs/registers.md carries a row
for itself and this sweep treats that row like any other.

--- THE GOVERNING RULE: EVERY CHECK IS BIDIRECTIONAL ---------------------
This file has now been defeated twice in the same way, by two independent
reviews, and both defeats had one shape: a check that walks from A to B
and never walks back. An id filed with nothing pointing at it was caught;
an id pointed at with nothing filed was not, so ONE LINE naming decisions
that do not exist yet pre-accounted every future decision on arrival,
silently and permanently. A location cell that named a path was checked;
a location cell that named nothing at all printed OK.

So the rule is written down here rather than left to be re-learned: a
reading in one direction is half a check. Checks (a), (b) and (c) below
each state both directions and fail on both -- with ONE declared
exception, the `currency evidence` column under (a), which is read one
way and says so in place rather than claiming a symmetry it does not
have.

The same rule caught this file's parser a third time. Reading the index
as "every line that looks like a table row" is a FILTER, and a filter
cannot distinguish a line it rejected from a line that was never there:
deleting one trailing pipe un-administered a register in total silence.
`index_rows` now reads the table as a BLOCK.

--- THE THREE CHECKS -----------------------------------------------------
(a) EXISTENCE, both ways.
    forward   every path named in a `location` cell exists on disk.
    reverse   every row NAMES at least one location this sweep can read.
              A cell whose paths are not backticked yields nothing, and a
              register whose location cannot be read is un-administered
              exactly as a dropped row would be. It is a failure, and the
              row is marked FAIL, not OK.
    A location must also be a repo-relative path that stays inside the
    repository: an absolute path or one containing `..` is refused, since
    check (a) is otherwise satisfiable by any path on the machine.
    Not baselined: an index pointing at a path that is not there is wrong
    today, with nothing to relitigate.

    The `currency evidence` column -- the column this file exists for --
    is read ONE WAY ONLY, and the asymmetry is deliberate. Every
    backticked token in it CONTAINING A SLASH is a path and must exist; a
    token with no slash (`currency evidence`, `adr-unaccounted:`,
    `nnn-slug.md`) is prose and is left alone. An EMPTY cell is a
    failure. But a cell that is full of prose and names no path at all
    does NOT fail, unlike a location cell, because one register measures
    its currency by a per-row review date rather than by a file, and
    failing it would be fitting the rule to nothing. That row would
    otherwise be indistinguishable in the output from a row whose paths
    were all checked and found, so the sweep PRINTS how many paths it
    checked and NAMES every row where that number is zero. Visible, not
    enforced -- and the docstring says which, because the previous
    version of this paragraph claimed the column was "read the same way"
    and it never was.

    What this still cannot check is whether the mechanism a cell NAMES is
    wired into any gate -- see WHAT THIS CANNOT DO.

(b) ADR ACCOUNTING, both ways.
    forward   every ADR-nnn with a file in the decision register (live
              plus frozen archive) is mentioned SOMEWHERE in the roadmap.
              The ones that are not are UNACCOUNTED: the plan has never
              said a word about them, in any tense.
    reverse   every ADR-nnn the roadmap MENTIONS has a file. The ones
              that do not are PHANTOM: the plan accounts for a decision
              that does not exist. This is the direction whose absence
              defeated the check -- appending one comment naming
              ADR-063 through ADR-200 cost nothing and accounted for
              every decision that would ever arrive.

    The count and the ids are printed whether the check fails or not --
    the point is the measurement, and a check that hides its reading is a
    check nobody can argue with.

    This measures ACCOUNTING, not recency, and the difference is why it
    replaced the gap check this file used to carry (defect 5 of
    docs/reviews/register-index-review-2026-08-24.md). Comparing the
    highest cited id against the highest filed id failed the roadmap for
    behaving CORRECTLY -- it is a history log and correctly cites the
    ids that were live when each entry was written, which docs/registers.md
    documents as intended -- and its only green path was gameable:
    appending the single token `ADR-061` closed a gap of 28 with zero
    review. Accounting cannot be closed that way. Appending `ADR-061`
    accounts for ADR-061 and for nothing else; every other unaccounted
    decision stays on the board. Nor can it be closed FORWARD any more:
    a line naming ids with no records now produces one finding per id.

    Both directions are gated by .truth/register-index-baseline, under
    key prefixes that cannot collide with the document paths check (c)
    records in the same file: `adr-unaccounted:` and `adr-phantom:`.
    Today's sets are recorded so the sweep refuses the NEXT divergence
    rather than relitigating the current backlog. Baselining is honest
    here in a way it would not have been for the gap: it freezes a
    BACKLOG, not a wrong measure.

    THE MIRROR RULE, and the distinction it was missing. A baselined
    entry with no corresponding finding is itself a failure. But an
    `adr-unaccounted:` entry can stop being a finding for two opposite
    reasons, and the tool used to report both as the first:
      resolved    the roadmap now mentions it        -> drop the line
      REGRESSED   the decision record no longer      -> restore the record
                  exists, so it is no longer filed      (do NOT drop it)
    Reporting a deleted decision record as "the roadmap now mentions it"
    made the prescribed remedy the regression itself: dropping the line
    turned a vanished record into exit 0.

(c) COVERAGE, both ways.
    forward   every *.md under docs/, excluding docs/archive/** (frozen
              verbatim, AGENTS.md and the .githooks/pre-commit guard),
              falls under some register's location.
    reverse   every baselined path is still uncovered, and still exists.

    Uncovered files are reported and gated by
    .truth/register-index-baseline -- today's backlog is recorded so the
    sweep refuses the NEXT uncovered document rather than relitigating
    the current set, the arrangement .truth/label-coupling-opt-out uses
    for module pairs. A baseline nobody prunes stops meaning "today's
    backlog" and starts meaning "whatever used to be true", which is the
    decay this whole file is about, one level up.

    A baseline line must carry a REASON. A bare key excuses a finding
    while recording nothing about why, which is the shape of an override
    admitted on an empty sentence -- the thing ADR-059 exists to extract
    and nothing here should mint.

--- READING THE INPUTS ---------------------------------------------------
Every input this sweep depends on is REQUIRED, and its absence is loud.
A declared ADR directory that is not on disk does not silently shrink the
measurement -- it suspends the accounting check and says so, because a
shrunken reading is worse than none: the finding gets SMALLER after a real
regression. A file in an ADR directory whose name this sweep cannot parse
is reported rather than skipped, for the same reason: the count is taken
from the directory, not from the matches, so the reading cannot hide its
own omissions. An unreadable input is an ENVIRONMENT failure with its own
exit code, never a traceback and never conflated with a finding.

--- WHAT THIS CANNOT DO --------------------------------------------------
It does not judge a register's CONTENTS, and although it now checks that
the paths in the `currency evidence` column EXIST, it cannot tell whether
the mechanism one of them names is wired into any gate -- that question
is answered per instrument by docs/governance/gate-metrics.md and
scripts/gate-reachability.sh. Coverage is by path prefix, so a register
whose membership is a LIST rather than a directory
(`.truth/citation-scope` is one) covers nothing here, by construction and
on purpose: prefix containment is checkable, list membership would need
each register's own reader.

Stdlib only; no truthlib import -- like every Tier C instrument, it
exercises the surfaces any external reader has.

Exit: 0 clean, 1 findings, 2 usage, 3 an input could not be read
(ENVIRONMENT, not governance -- the sweep did not run), 8 examined
nothing (ADR-042 rule 2: a sweep that swept nothing has not passed, it
has failed to run).

Usage: python3 instruments/register-index.py [--json] [--record-baseline]
Gate:  template/scripts/test-integrations.py (TestTierCInstruments), which
       exercises the ADR-042 empty guard, the environment exit and BOTH
       directions of check (b) against a throwaway tree.
"""
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

INDEX_REL = "docs/registers.md"
ROADMAP_REL = "docs/roadmap-v3.md"
ADR_DIRS = ("docs/decisions", "docs/archive/adr")
BASELINE_REL = ".truth/register-index-baseline"
DOCS_REL = "docs"
# Frozen verbatim; its files are records of what was true then and belong
# to no living register by design.
COVERAGE_EXCLUDE = ("docs/archive/",)
# Not decision records: the register's own README. Named explicitly so an
# unparseable FILENAME stays a finding (see filed_adrs) instead of being
# swallowed by a broad rule.
ADR_DIR_NON_RECORDS = ("README.md",)

# Key prefixes for check (b)'s two directions in the shared baseline file.
# Check (c) records document paths there; a path never starts with either,
# so the three key spaces cannot collide however the backlog grows.
ADR_KEY_PREFIX = "adr-unaccounted:"
PHANTOM_KEY_PREFIX = "adr-phantom:"
GAP_KEY_PREFIX = "adr-gap:"
ADR_PREFIXES = (ADR_KEY_PREFIX, PHANTOM_KEY_PREFIX, GAP_KEY_PREFIX)

EXIT_FINDINGS = 1
EXIT_USAGE = 2
EXIT_ENV = 3
EXIT_EMPTY = 8

ADR_CITE_RE = re.compile(r"\bADR-(\d{1,4})\b")
ADR_FILE_RE = re.compile(r"^(\d{1,4})-.*\.md$")
# A path inside a location cell. Backticked on purpose rather than linked:
# doc-health.sh judges markdown LINKS, so a linked location would already be
# half-checked and a backticked one is checked by nothing -- which is the
# half this instrument was built for.
CELL_PATH_RE = re.compile(r"`([^`]+)`")
# A table row: leading pipe, trailing pipe, and not the `|---|` separator.
SEP_RE = re.compile(r"^\|[\s:|-]+\|$")
# `baseline <date>, ...` at the head of a baseline reason. Preserved across
# --record-baseline so the file records when a finding was FIRST excused;
# a re-record that restamped every line with today would make the
# anti-staleness file its own staleness generator.
BASELINE_DATE_RE = re.compile(r"^baseline (\d{4}-\d{2}-\d{2})\b")


class InputError(Exception):
    """An input could not be read. ENVIRONMENT, not a finding: the sweep
    did not run, so it has neither passed nor failed (ADR-042 rule 2's
    reasoning, applied to the read rather than to the count)."""


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


def location_problem(loc):
    """Why this string is not usable as a repo-relative location, or None.

    Without this, check (a) is satisfiable by any path on the machine:
    `/etc/passwd` exists, so a row naming it read OK.
    """
    if not loc:
        return "is empty"
    if os.path.isabs(loc) or loc.startswith("~"):
        return "is an absolute path -- locations are repo-relative"
    parts = loc.replace(os.sep, "/").split("/")
    if ".." in parts:
        return "escapes the repository with '..' -- locations stay inside it"
    return None


def index_rows(path):
    """(register, purpose, [locations], status, currency) per table row.

    The index is read as the five-column table its own header declares.

    THE TABLE IS READ AS A BLOCK, NOT AS A SET OF MATCHING LINES, and that
    is the whole point of this function. Reading it as "every line that
    starts and ends with a pipe" is a filter, and a filter cannot tell a
    line it rejected from a line that was never there. Deleting ONE
    trailing pipe -- which GitHub-Flavoured Markdown renders identically,
    so no human and no `doc-health.sh` link check sees any difference --
    used to remove that register from the sweep with no finding, no
    changed exit code, and no output difference except a count nothing
    gates. That is the nine-sources-four-read shape, reproduced one layer
    ABOVE the layer that was hardened against it.

    So: once the header and its separator have been seen, EVERY non-blank
    line up to the blank line that ends the table is a body row and must
    parse as five cells. A line that does not is returned in `malformed`
    with the reason, and the caller fails on it. The table ends at the
    first blank line, which is what GFM itself uses.
    """
    rows, malformed, state = [], [], "before"
    for n, raw in enumerate(read(path, "the register index").splitlines(), 1):
        line = raw.strip()
        if state == "before":
            # The header is the first pipe-line whose first cell is
            # `register`; anything before it is prose.
            if line.startswith("|") and line.endswith("|"):
                cells = [c.strip() for c in line[1:-1].split("|")]
                if cells and cells[0].lower() == "register":
                    state = "header"
            continue
        if state == "header":
            if SEP_RE.match(line):
                state = "body"
            else:
                malformed.append(
                    (n, "the row after the header is not the |---| "
                        "separator, so the table's shape is not declared"))
                state = "body"
            continue
        if state == "after":
            # One table, and it has ended. A second table lower in the
            # file is prose as far as this sweep is concerned; registers.md
            # has exactly one, and if that changes this is where to look.
            continue
        # state == "body": the block runs to the first blank line.
        if not line:
            state = "after"
            continue
        if not (line.startswith("|") and line.endswith("|")):
            malformed.append(
                (n, "a line inside the table block is not a row: %r. GFM "
                    "renders a body row missing its trailing pipe exactly "
                    "like a complete one, so this is invisible to a reader "
                    "and used to be invisible to this sweep" % line[:60]))
            continue
        if SEP_RE.match(line):
            continue
        cells = [c.strip() for c in line[1:-1].split("|")]
        if len(cells) != 5:
            malformed.append(
                (n, "the row for %r has %d columns, not the five the "
                    "header declares -- a row this sweep cannot read is a "
                    "register it cannot administer"
                    % (cells[0] if cells else "?", len(cells))))
            continue
        rows.append({"register": cells[0], "purpose": cells[1],
                     "locations": CELL_PATH_RE.findall(cells[2]),
                     "status": cells[3], "currency": cells[4],
                     # A backticked token with a slash in it is a path and
                     # is checked; one without is prose and is not. Stated
                     # in the docstring so the rule is predictable.
                     "currency_paths": [
                         t for t in CELL_PATH_RE.findall(cells[4])
                         if "/" in t]})
    if state == "before":
        malformed.append(
            (0, "no table header row (a row whose first cell is "
                "`register`) was found at all"))
    return rows, malformed


def cited_adrs(path):
    """Every ADR id mentioned in the roadmap -- a set, not a maximum.

    A set because the question is accounting, not recency: an id buried
    in a 2026-07 entry accounts for that decision exactly as well as one
    in the last paragraph, and the roadmap is a history log whose ids are
    not ordered by relevance.
    """
    return set(int(n) for n in ADR_CITE_RE.findall(read(path, "the roadmap")))


def filed_adrs():
    """(ids, files_seen, unparsed, missing_dirs) across both halves.

    Both halves, because the number space is single and is never
    restarted (docs/decisions/README.md): reading only the live directory
    would silently stop asking the roadmap to account for 001-053.

    `files_seen` counts every *.md in those directories, not every one
    whose name PARSED. Counting matches let the reading hide its own
    skip: `ADR-063-new.md` does not match, so it vanished from a count
    that still called itself "62 ADR file(s)". `unparsed` carries the
    names, and `missing_dirs` the directories that were not there at all
    -- neither is allowed to shrink the measurement quietly.
    """
    nums, seen, unparsed, missing = set(), 0, [], []
    for rel in ADR_DIRS:
        full = os.path.join(ROOT, rel)
        if not os.path.isdir(full):
            missing.append(rel)
            continue
        for name in sorted(listdir(full, "the decision register")):
            if not name.endswith(".md") or name in ADR_DIR_NON_RECORDS:
                continue
            seen += 1
            m = ADR_FILE_RE.match(name)
            if not m:
                unparsed.append("%s/%s" % (rel, name))
                continue
            nums.add(int(m.group(1)))
    return nums, seen, unparsed, missing


def live_docs():
    """Every *.md under docs/ that is not frozen reference.

    `os.walk` DISCARDS errors by default and yields nothing for a subtree
    it cannot list. That is the same silent shrink `filed_adrs` was
    hardened against, and leaving it here produced the same downstream
    lie: an unreadable `docs/specs` made the coverage reading smaller,
    and the mirror rule then reported a file that still exists as "no
    longer exists -- drop the line", whose remedy permanently
    un-baselines a real finding. So the walk raises.
    """
    out = []
    root = os.path.join(ROOT, DOCS_REL)

    def boom(e):
        raise InputError("cannot list %s (%s): %s"
                         % ("a subtree of " + DOCS_REL,
                            os.path.relpath(e.filename, ROOT), e.strerror))

    for dirpath, dirnames, filenames in os.walk(root, onerror=boom):
        dirnames.sort()
        for name in sorted(filenames):
            if not name.endswith(".md"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, name), ROOT)
            rel = rel.replace(os.sep, "/")
            if any(rel.startswith(p) for p in COVERAGE_EXCLUDE):
                continue
            out.append(rel)
    return out


def covered_by(rel, locations):
    """Prefix containment: the file IS the location, or lives under it."""
    for loc in locations:
        loc = loc.rstrip("/")
        if rel == loc or rel.startswith(loc + "/"):
            return loc
    return None


def load_baseline(path):
    """(recorded, state, unreasoned): `<key>  <reason>` per line.

    The same shape .truth/label-coupling-opt-out uses -- key up to the
    first space, the rest is why. State is reported (absent / empty /
    populated) because an ABSENT baseline and an EMPTY one mean different
    things: the first cannot tell a deliberate gap from an oversight, the
    second is a conscious, dated "nothing is excused" (SI-4, ADR-053).

    A key with no reason is returned in `unreasoned` and fails. An
    excuse that says nothing is an override admitted on an empty
    sentence, and this repository refuses those at intake everywhere else.
    """
    recorded, state, unreasoned = {}, "absent", []
    if not os.path.exists(path):
        return recorded, state, unreasoned
    state = "empty"
    for raw in read(path, "the baseline").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        state = "populated"
        key, _, reason = line.partition(" ")
        key, reason = key.strip(), reason.strip()
        recorded[key] = reason
        if not reason:
            unreasoned.append(key)
    return recorded, state, unreasoned


def first_seen(reason, today):
    """The date a baseline entry was first recorded, or today.

    Re-recording must not restamp an entry that was already there: the
    age of an excuse is the one thing this file measures about itself,
    and a --record-baseline that reset every line to today would erase
    it while claiming to be an anti-staleness mechanism.
    """
    m = BASELINE_DATE_RE.match(reason or "")
    return m.group(1) if m else today


BASELINE_HEADER = """\
# register-index: the baseline for checks (b) and (c).
#
# Format:  <key>  <reason>.  The shape .truth/label-coupling-opt-out uses.
# A REASON IS REQUIRED: a bare key excuses a finding while recording
# nothing about why, and this repository refuses empty override sentences
# everywhere else.
#
# Three key spaces share this file and cannot collide:
#   check (c)   a docs/... path, covered by no register's location
#   check (b)   adr-unaccounted:ADR-nnn, a filed decision the roadmap
#               mentions nowhere
#   check (b)   adr-phantom:ADR-nnn, an id the roadmap mentions that has
#               no decision record at all
#
# MIRROR RULE, all three key spaces: an entry here with no corresponding
# finding is ITSELF a failure -- drop the line. A baseline nobody prunes
# stops meaning "today's backlog" and starts meaning "whatever used to be
# true". The ONE exception the tool distinguishes for you: an
# adr-unaccounted: entry whose decision RECORD has vanished is a
# regression, not a resolution, and the remedy is to restore the record.
#
# Dates below are FIRST-SEEN and are preserved across --record-baseline.

# --- check (c): docs/*.md covered by no register -------------------------
#
# UNRESOLVED. These entries record the state at the moment the coverage
# check was introduced -- not a verdict that the files below belong
# nowhere. Resolving one is separate work: either a register claims it, or
# a new register is added to docs/registers.md with a location that
# contains it. The point of this file is that the NEXT uncovered document
# does not pass unnoticed.

"""

ADR_BASELINE_SECTION = """
# --- check (b) forward: filed decisions the roadmap accounts for nowhere -
#
# UNRESOLVED. A backlog, not a verdict: each id below has a file in
# docs/decisions or docs/archive/adr and is mentioned nowhere in
# docs/roadmap-v3.md. Resolving one means citing it in the roadmap where it
# bears on the plan -- which is why this baseline is honest where the
# ADR-gap check it replaced was not: it freezes a backlog, not a wrong
# measure. The point is that the NEXT unaccounted decision does not pass.

"""

PHANTOM_BASELINE_SECTION = """
# --- check (b) reverse: ids the roadmap names that have no record --------
#
# UNRESOLVED. Each id below is mentioned in docs/roadmap-v3.md and has no
# file in either decision directory. The plan accounts for a decision that
# does not exist. Resolving one means filing the record, or correcting the
# roadmap. This direction exists because its absence let one comment naming
# ADR-063 through ADR-200 pre-account every decision that would ever
# arrive, in silence.

"""


GAP_BASELINE_SECTION = """
# --- check (b) third: holes in the decision number space -----------------
#
# UNRESOLVED. Each id below has no record while higher-numbered decisions
# do. docs/decisions/README.md: the space is single and never restarted,
# and a superseded record is superseded IN PLACE, so a hole is a record
# that vanished. This direction exists because the other two go blind to a
# deleted record the moment its baseline line is dropped -- which is the
# remedy the mirror rule used to prescribe for exactly that case.

"""


def sweep():
    rows, malformed = index_rows(os.path.join(ROOT, INDEX_REL))
    locations, missing, shape, unlocated, currency = [], [], [], [], []
    currency_unchecked = []
    for row in rows:
        for loc in row["locations"]:
            problem = location_problem(loc)
            if problem:
                shape.append(
                    "%s: the index names location %r, which %s. Fix the "
                    "row in %s" % (row["register"], loc, problem, INDEX_REL))
                continue
            locations.append(loc)
            if not os.path.exists(os.path.join(ROOT, loc)):
                missing.append(
                    "%s: the index names location %r, which does not exist "
                    "on disk -- move the register or fix the row in %s"
                    % (row["register"], loc, INDEX_REL))
        if not row["locations"]:
            unlocated.append(
                "%s: the index row names no location this sweep can read -- "
                "locations are backticked paths, and a register whose "
                "location cannot be read is un-administered exactly as a "
                "dropped row would be (%s)" % (row["register"], INDEX_REL))
        if not row["currency"]:
            currency.append(
                "%s: the currency evidence cell is empty -- if nothing "
                "measures this register's freshness, the cell says so; "
                "blank is the one thing it may not be (%s)"
                % (row["register"], INDEX_REL))
        if row["currency"] and not row["currency_paths"]:
            # NOT a failure: `gates` legitimately measures its currency by
            # a per-row review date, which is prose, not a path. But it is
            # not nothing either -- this row's currency evidence is
            # asserted and swept by no part of this instrument, and that
            # must be VISIBLE rather than indistinguishable in the output
            # from a row whose three paths were all checked and found.
            currency_unchecked.append(row["register"])
        for tok in row["currency_paths"]:
            problem = location_problem(tok)
            if problem:
                currency.append(
                    "%s: the currency evidence names %r, which %s (%s)"
                    % (row["register"], tok, problem, INDEX_REL))
            elif not os.path.exists(os.path.join(ROOT, tok)):
                currency.append(
                    "%s: the currency evidence names %r, which does not "
                    "exist on disk -- the column names what would report "
                    "this register's decay, so a dead path there is a "
                    "register whose staleness nothing reports (%s)"
                    % (row["register"], tok, INDEX_REL))

    roadmap_path = os.path.join(ROOT, ROADMAP_REL)
    cited = cited_adrs(roadmap_path) if os.path.exists(roadmap_path) else None
    filed, adr_files, unparsed, missing_dirs = filed_adrs()
    # `filed_ids` and `cited_ids` are carried, not just their counts: the
    # mirror rule needs to tell "the roadmap now mentions it" (resolved)
    # from "the record no longer exists" (a regression), and those two are
    # only distinguishable by asking which SET the id left.
    accounting = {"adr_files": adr_files, "filed": len(filed),
                  "mentioned": None if cited is None else len(cited),
                  "unaccounted": [], "phantom": [], "gaps": [],
                  "unparsed": unparsed, "missing_dirs": missing_dirs,
                  "measured": False,
                  "filed_ids": sorted(filed),
                  "cited_ids": None if cited is None else sorted(cited)}
    stale = []
    for rel in missing_dirs:
        stale.append(
            "the decision register directory %s is not a readable "
            "directory -- the ADR "
            "accounting check is SUSPENDED rather than run against half a "
            "register. A shrunken reading is worse than none: the finding "
            "gets smaller after a real regression" % rel)
    for name in unparsed:
        stale.append(
            "%s is a markdown file in the decision register whose name this "
            "sweep cannot read as ADR-nnn -- rename it to `nnn-slug.md` or "
            "move it out. A file it cannot parse is a decision it cannot "
            "account for, in either direction" % name)
    if cited is None:
        stale.append(
            "adr accounting cannot be measured: %s is not on disk -- the "
            "roadmap register is not where this sweep looks" % ROADMAP_REL)
    elif missing_dirs:
        pass  # already named above; the measure is suspended, not reported
    elif not filed:
        stale.append(
            "adr accounting cannot be measured: no ADR-nnn file under %s -- "
            "the decision register is not where this sweep looks"
            % " or ".join(ADR_DIRS))
    else:
        accounting["measured"] = True
        accounting["unaccounted"] = ["ADR-%03d" % n
                                     for n in sorted(filed - cited)]
        accounting["phantom"] = ["ADR-%03d" % n
                                 for n in sorted(cited - filed)]
        # The third direction. docs/decisions/README.md: the number space
        # is single, continues at 054 and is NEVER restarted, and a
        # superseded record is superseded IN PLACE rather than removed. So
        # a hole in 1..max is a record that vanished -- the one failure
        # mode the other two directions cannot see once its baseline line
        # has been dropped, which is precisely the remedy the old mirror
        # message used to prescribe.
        accounting["gaps"] = ["ADR-%03d" % n
                              for n in range(1, max(filed) + 1)
                              if n not in filed]

    docs = live_docs()
    uncovered, covered = [], {}
    for rel in docs:
        loc = covered_by(rel, locations)
        if loc:
            covered[rel] = loc
        else:
            uncovered.append(rel)

    return {"rows": rows, "malformed": malformed, "locations": locations,
            "missing": missing, "shape": shape, "unlocated": unlocated,
            "currency": currency, "currency_unchecked": currency_unchecked,
            "accounting": accounting, "stale": stale,
            "docs": docs, "covered": covered, "uncovered": uncovered,
            # A row is FAIL when anything about ITS cells is wrong, so the
            # per-row mark cannot read OK while the summary reads 1 failure.
            "bad_rows": set()}


def mark_bad_rows(r):
    """Which register names appear in a row-scoped finding."""
    bad = set()
    for row in r["rows"]:
        name = row["register"]
        prefix = name + ":"
        for msg in r["missing"] + r["shape"] + r["unlocated"] + r["currency"]:
            if msg.startswith(prefix):
                bad.add(name)
    return bad


def record_baseline(path, r, baseline):
    """Rewrite the baseline, preserving each entry's FIRST-SEEN date.

    Prints every key it records. `--record-baseline` is a one-command
    green by construction -- that is what recording a backlog IS -- so
    the least it can do is put the whole blessed set in front of the
    operator who ran it, rather than a count. Reading the entries first
    is the discipline; printing them is what makes skipping it visible.
    """
    today = datetime.date.today().isoformat()
    a = r["accounting"]
    sections = [
        (BASELINE_HEADER, "", r["uncovered"],
         "covered by no register"),
        (ADR_BASELINE_SECTION, ADR_KEY_PREFIX, a["unaccounted"],
         "%s mentions it nowhere" % ROADMAP_REL),
        (PHANTOM_BASELINE_SECTION, PHANTOM_KEY_PREFIX, a["phantom"],
         "%s mentions it but no decision record exists" % ROADMAP_REL),
        (GAP_BASELINE_SECTION, GAP_KEY_PREFIX, a["gaps"],
         "a hole in the decision number space"),
    ]
    lines, recorded = [], []
    for header, prefix, keys, why in sections:
        lines.append(header)
        for k in keys:
            key = prefix + k
            when = first_seen(baseline.get(key, ""), today)
            lines.append("%s  baseline %s, unresolved: %s\n"
                         % (key, when, why))
            recorded.append((key, when))
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("".join(lines))
    except OSError as e:
        raise InputError("cannot write the baseline (%s): %s"
                         % (BASELINE_REL, e.strerror))
    for key, when in recorded:
        print("  record  %-58s first seen %s" % (key, when))
    print("register-index: recorded %d uncovered doc(s), %d unaccounted, "
          "%d phantom and %d number-space gap(s) in %s -- every key is "
          "printed above, because a baseline is only honest if someone "
          "read it" % (len(r["uncovered"]), len(a["unaccounted"]),
                       len(a["phantom"]), len(a["gaps"]), BASELINE_REL))


def main(argv):
    known = ("--json", "--record-baseline", "-h", "--help")
    for arg in argv:
        if arg not in known:
            print("register-index: unknown argument %r\n%s" % (arg, __doc__),
                  file=sys.stderr)
            return EXIT_USAGE
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0

    index_path = os.path.join(ROOT, INDEX_REL)
    if not os.path.exists(index_path):
        print("register-index: %s not found -- run from the meta-repo"
              % INDEX_REL, file=sys.stderr)
        return EXIT_USAGE

    baseline_path = os.path.join(ROOT, BASELINE_REL)
    try:
        baseline, base_state, unreasoned = load_baseline(baseline_path)
        r = sweep()
    except InputError as e:
        print("register-index: %s -- the sweep did NOT run. This is an "
              "environment failure, not a finding (exit %d)"
              % (e, EXIT_ENV), file=sys.stderr)
        return EXIT_ENV

    # ADR-042 rule 2, both halves: a sweep with no registers to read and a
    # sweep with no documents to judge have each measured nothing, and
    # nothing is not a pass.
    if not r["rows"]:
        print("register-index: read ZERO register rows from %s -- the sweep "
              "did not run (ADR-042 rule 2). Check the table's five columns."
              % INDEX_REL, file=sys.stderr)
        return EXIT_EMPTY
    if not r["docs"]:
        print("register-index: examined ZERO live doc(s) under %s/ -- the "
              "coverage check did not run (ADR-042 rule 2)" % DOCS_REL,
              file=sys.stderr)
        return EXIT_EMPTY

    if "--record-baseline" in argv:
        # ADR-042 rule 2 again, and the door next to the one already
        # guarded. The zero-rows guard above stops a record over an
        # unreadable INDEX; this stops a record over an unread REGISTER.
        # With an ADR directory or the roadmap absent, `unaccounted`,
        # `phantom` and `gaps` are all empty because nothing was
        # measured -- and writing that empty reading DELETED the real
        # backlog and its first-seen dates, at exit 0, while the ordinary
        # sweep was refusing to so much as report the same reading.
        if not r["accounting"]["measured"]:
            print("register-index: refusing to record -- the ADR "
                  "accounting measure is SUSPENDED (%s). Recording now "
                  "would write an empty reading over the real backlog and "
                  "its first-seen dates. Restore the missing input first:\n"
                  "  %s" % ("; ".join(r["stale"][:1]) or "input missing",
                            "\n  ".join(r["stale"])), file=sys.stderr)
            return EXIT_EMPTY
        try:
            record_baseline(baseline_path, r, baseline)
        except InputError as e:
            print("register-index: %s" % e, file=sys.stderr)
            return EXIT_ENV
        return 0

    a = r["accounting"]
    failures = [
        "%s line %d: %s" % (INDEX_REL, n, why)
        for n, why in r["malformed"]
    ] + list(r["missing"]) + list(r["shape"]) + list(r["unlocated"]) \
      + list(r["currency"]) + list(r["stale"])

    for key in sorted(unreasoned):
        failures.append(
            "%s is recorded in %s with no reason -- a bare key excuses a "
            "finding while recording nothing about why. Give it one, or "
            "drop the line" % (key, BASELINE_REL))

    # --- check (b), forward -------------------------------------------
    excused_adrs = []
    unaccounted = set(a["unaccounted"])
    for adr in a["unaccounted"]:
        if ADR_KEY_PREFIX + adr in baseline:
            excused_adrs.append(adr)
        else:
            failures.append(
                "%s has a file in the decision register and is mentioned "
                "nowhere in %s -- the plan accounts for it in no tense. Cite "
                "it where it bears on the plan, or record %s%s in %s with a "
                "reason" % (adr, ROADMAP_REL, ADR_KEY_PREFIX, adr,
                            BASELINE_REL))

    # --- check (b), reverse: the direction whose absence defeated it ---
    excused_phantom = []
    phantom = set(a["phantom"])
    for adr in a["phantom"]:
        if PHANTOM_KEY_PREFIX + adr in baseline:
            excused_phantom.append(adr)
        else:
            failures.append(
                "%s is mentioned in %s and has no decision record in %s -- "
                "the plan accounts for a decision that does not exist, and "
                "an id accounted for before it is filed is accounted for by "
                "nobody. File the record, correct the roadmap, or record "
                "%s%s in %s with a reason"
                % (adr, ROADMAP_REL, " or ".join(ADR_DIRS),
                   PHANTOM_KEY_PREFIX, adr, BASELINE_REL))

    # --- check (b), third direction: a hole in the number space -------
    excused_gaps = []
    gaps = set(a["gaps"])
    for adr in a["gaps"]:
        if GAP_KEY_PREFIX + adr in baseline:
            excused_gaps.append(adr)
        else:
            failures.append(
                "%s has no record in %s, but higher-numbered decisions do "
                "-- the number space is single and never restarted "
                "(docs/decisions/README.md), and a superseded record is "
                "superseded in place rather than removed, so a hole in it "
                "is a record that VANISHED. Restore it, or record %s%s in "
                "%s with a reason"
                % (adr, " or ".join(ADR_DIRS), GAP_KEY_PREFIX, adr,
                   BASELINE_REL))

    # --- the mirror rule for all three ADR key spaces ------------------
    # Only meaningful when the measure actually ran: with a register
    # directory missing, EVERY id looks resolved and the mirror rule
    # would misdiagnose the whole baseline as stale.
    if a["measured"]:
        filed_ids = set(a["filed_ids"])
        cited_ids = set(a["cited_ids"])
        for key in sorted(k for k in baseline
                          if k.startswith(ADR_KEY_PREFIX)):
            adr = key[len(ADR_KEY_PREFIX):]
            if adr in unaccounted:
                continue
            num = int(adr[4:]) if adr[:4] == "ADR-" and adr[4:].isdigit() \
                else None
            if num is None:
                failures.append(
                    "%s in %s is not a well-formed ADR key -- the sweep "
                    "cannot tell whether its finding still stands, which is "
                    "the one thing a baseline entry must be able to say"
                    % (key, BASELINE_REL))
            elif num not in filed_ids:
                # It stopped being unaccounted because its RECORD vanished,
                # not because the plan accounted for it. Reporting this as
                # a resolution made the prescribed remedy the regression:
                # dropping the line turned a deleted decision into exit 0.
                failures.append(
                    "%s is recorded in %s, but %s no longer has a decision "
                    "record in %s -- the entry stopped being a finding "
                    "because the RECORD VANISHED, not because %s accounts "
                    "for it. That is a regression, not a resolution: restore "
                    "the record. Do NOT drop the line"
                    % (key, BASELINE_REL, adr, " or ".join(ADR_DIRS),
                       ROADMAP_REL))
            elif num in cited_ids:
                failures.append(
                    "%s is recorded in %s but %s now mentions it -- the "
                    "baseline entry outlived its finding; drop the line"
                    % (key, BASELINE_REL, ROADMAP_REL))
            else:
                # Belt and braces: filed, uncited, and yet not in the
                # unaccounted set is arithmetically impossible. If it ever
                # happens the sweep says so rather than picking a story.
                failures.append(
                    "%s is recorded in %s and the sweep cannot account for "
                    "its disappearance from the finding set -- this is a bug "
                    "in the sweep, not in the register" % (key, BASELINE_REL))
        for key in sorted(k for k in baseline
                          if k.startswith(PHANTOM_KEY_PREFIX)):
            adr = key[len(PHANTOM_KEY_PREFIX):]
            if adr not in phantom:
                failures.append(
                    "%s is recorded in %s but %s now has a decision record "
                    "(or %s no longer mentions it) -- the baseline entry "
                    "outlived its finding; drop the line"
                    % (key, BASELINE_REL, adr, ROADMAP_REL))
        for key in sorted(k for k in baseline
                          if k.startswith(GAP_KEY_PREFIX)):
            adr = key[len(GAP_KEY_PREFIX):]
            if adr not in gaps:
                failures.append(
                    "%s is recorded in %s but %s has a record again (or no "
                    "higher-numbered decision exists any more) -- the "
                    "baseline entry outlived its finding; drop the line"
                    % (key, BASELINE_REL, adr))

    # --- check (c) -----------------------------------------------------
    excused = []
    for rel in r["uncovered"]:
        if rel in baseline:
            excused.append(rel)
        else:
            failures.append(
                "%s is covered by no register's location -- name a register "
                "for it in %s, or record it in %s with a reason"
                % (rel, INDEX_REL, BASELINE_REL))
    coverage_keys = set(k for k in baseline
                        if not k.startswith(ADR_PREFIXES))
    for rel in sorted(coverage_keys - set(r["uncovered"])):
        if not os.path.exists(os.path.join(ROOT, rel)):
            failures.append(
                "%s is recorded in %s and no longer exists -- the entry "
                "outlived its subject; drop the line" % (rel, BASELINE_REL))
        else:
            failures.append(
                "%s is recorded in %s but is no longer uncovered -- the "
                "baseline entry outlived its finding; drop the line"
                % (rel, BASELINE_REL))

    warnings = []
    if base_state == "absent":
        warnings.append(
            "no %s on record -- this sweep cannot tell a deliberate coverage "
            "gap from an oversight, so it excused NOTHING" % BASELINE_REL)

    r["bad_rows"] = mark_bad_rows(r)

    report = {
        "registers": len(r["rows"]),
        "locations": len(r["locations"]),
        "missing_locations": r["missing"],
        "malformed_locations": r["shape"],
        "unlocated_rows": r["unlocated"],
        "currency_findings": r["currency"],
        "currency_unchecked_rows": r["currency_unchecked"],
        "currency_paths_checked": sum(len(row["currency_paths"])
                                      for row in r["rows"]),
        "adr_accounting": a,
        "docs_examined": len(r["docs"]),
        "covered": len(r["covered"]),
        "uncovered": r["uncovered"],
        "excused": excused,
        "excused_adrs": excused_adrs,
        "excused_phantom": excused_phantom,
        "excused_gaps": excused_gaps,
        "baseline_state": base_state,
        "unreasoned_baseline_keys": unreasoned,
        "failures": failures,
        "warnings": warnings,
    }
    if "--json" in argv:
        print(json.dumps(report, indent=2))
        return EXIT_FINDINGS if failures else 0

    for row in r["rows"]:
        mark = "FAIL " if row["register"] in r["bad_rows"] else "OK   "
        print("%s %-18s %s" % (mark, row["register"][:18],
                               ", ".join(row["locations"]) or "(no location)"))
    if not a["measured"]:
        # Never print a shrunken reading as though it were a measurement:
        # "9 ADR file(s)" after an archive went missing is the exact shape
        # of a finding getting SMALLER because of a regression.
        print("  %-18s SUSPENDED -- %s (read %d file(s) from the half that "
              "was there; that number is NOT the register)"
              % ("adr accounting",
                 "missing: " + ", ".join(a["missing_dirs"])
                 if a["missing_dirs"] else "the roadmap is not on disk",
                 a["adr_files"]))
    else:
        print("  %-18s %d ADR file(s), %d id(s) filed, %d mentioned in %s; "
              "%d unaccounted (%d excused), %d phantom (%d excused)"
              % ("adr accounting", a["adr_files"], a["filed"],
                 a["mentioned"], ROADMAP_REL,
                 len(a["unaccounted"]), len(excused_adrs),
                 len(a["phantom"]), len(excused_phantom)))
    if a["unaccounted"]:
        print("  %-18s %s" % ("unaccounted", ", ".join(a["unaccounted"])))
    if a["phantom"]:
        print("  %-18s %s" % ("phantom", ", ".join(a["phantom"])))
    if a["gaps"]:
        print("  %-18s %s (%d excused)"
              % ("number-space gaps", ", ".join(a["gaps"]),
                 len(excused_gaps)))
    print("  %-18s %d path(s) checked across %d row(s); %d row(s) name no "
          "checkable path%s"
          % ("currency evidence",
             sum(len(row["currency_paths"]) for row in r["rows"]),
             len(r["rows"]), len(r["currency_unchecked"]),
             (": " + ", ".join(r["currency_unchecked"])
              if r["currency_unchecked"] else "")))
    print("  %-18s %d live doc(s), %d covered, %d uncovered (%d excused) [%s: %s]"
          % ("coverage", len(r["docs"]), len(r["covered"]),
             len(r["uncovered"]), len(excused), BASELINE_REL, base_state))
    for w in warnings:
        print("WARN  " + w)
    for f in failures:
        print("FAIL  " + f)
    print("register-index: %d register(s) over %d location(s) -- %d failure(s)"
          % (len(r["rows"]), len(r["locations"]), len(failures)))
    return EXIT_FINDINGS if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
