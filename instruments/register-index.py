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

--- THE THREE CHECKS -----------------------------------------------------
(a) EXISTENCE. Every path named in a `location` cell of the index exists
    on disk. A location cell may name several paths; each is checked.
    Not baselined: an index pointing at a path that is not there is
    wrong today, with nothing to relitigate.

(b) ADR ACCOUNTING. Every ADR-nnn that has a file in the decision
    register (live plus frozen archive) is mentioned SOMEWHERE in the
    roadmap. The ones that are not are UNACCOUNTED: the plan has never
    said a word about them, in any tense. The count and the ids are
    printed whether the check fails or not -- the point is the
    measurement, and a check that hides its reading is a check nobody
    can argue with.

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
    decision stays on the board. One token clears exactly the one
    decision it names, which is the same amount of reading as citing it
    honestly.

    Unaccounted ids are gated by .truth/register-index-baseline under the
    key prefix `adr-unaccounted:`, which cannot collide with the document
    paths check (c) records in the same file. Today's set is recorded so
    the sweep refuses the NEXT unmentioned decision rather than
    relitigating the current backlog. Baselining is honest here in a way
    it would not have been for the gap: it freezes a BACKLOG, not a wrong
    measure. The mirror rule below applies to these entries unchanged --
    an id recorded here that the roadmap now mentions is itself a
    failure.

(c) COVERAGE. Every *.md under docs/, excluding docs/archive/** (frozen
    verbatim, AGENTS.md and the .githooks/pre-commit guard), falls under
    some register's location. Uncovered files are reported and are gated
    by .truth/register-index-baseline -- today's backlog is recorded so
    the sweep refuses the NEXT uncovered document rather than
    relitigating the current set, the arrangement
    .truth/label-coupling-opt-out uses for module pairs.

    The baseline carries the mirror rule those instruments carry: an
    entry with no corresponding finding is ITSELF a failure. A baseline
    nobody prunes stops meaning "today's backlog" and starts meaning
    "whatever used to be true", which is the decay this whole file is
    about, one level up.

--- WHAT THIS CANNOT DO --------------------------------------------------
It does not judge a register's CONTENTS and it cannot tell whether the
mechanism named in the index's `currency evidence` column is wired into
any gate -- that question is answered per instrument by
docs/governance/gate-metrics.md and scripts/gate-reachability.sh.
Coverage is by path prefix, so a register whose membership is a LIST
rather than a directory (`.truth/citation-scope` is one) covers nothing
here, by construction and on purpose: prefix containment is checkable,
list membership would need each register's own reader.

Stdlib only; no truthlib import -- like every Tier C instrument, it
exercises the surfaces any external reader has.

Exit: 0 clean, 1 findings, 8 examined nothing (ADR-042 rule 2: a sweep
that swept nothing has not passed, it has failed to run), 2 usage.

Usage: python3 instruments/register-index.py [--json] [--record-baseline]
Gate:  NONE yet -- wire it once check (c)'s backlog is closed.
"""
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

# Key prefix for check (b)'s entries in the shared baseline file. Check
# (c) records document paths there; a path never starts with this, so the
# two key spaces cannot collide however the backlog grows.
ADR_KEY_PREFIX = "adr-unaccounted:"

EXIT_FINDINGS = 1
EXIT_EMPTY = 8
EXIT_USAGE = 2

ADR_CITE_RE = re.compile(r"\bADR-(\d{1,4})\b")
ADR_FILE_RE = re.compile(r"^(\d{1,4})-.*\.md$")
# A path inside a location cell. Backticked on purpose rather than linked:
# doc-health.sh judges markdown LINKS, so a linked location would already be
# half-checked and a backticked one is checked by nothing -- which is the
# half this instrument was built for.
CELL_PATH_RE = re.compile(r"`([^`]+)`")
# A table row: leading pipe, trailing pipe, and not the `|---|` separator.
SEP_RE = re.compile(r"^\|[\s:|-]+\|$")


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def index_rows(path):
    """(register, purpose, [locations], status, currency) per table row.

    The index is read as the five-column table its own header declares.
    A row with a different arity is NOT guessed at -- an invented column
    would be an invented location -- but neither is it skipped: a skipped
    row un-administers its register silently, which is the failure this
    instrument exists to catch (an instrument once named nine sources and
    read four for nine days). Malformed rows are returned alongside the
    good ones so the caller can fail on them.
    """
    rows, malformed = [], []
    for line in read(path).splitlines():
        line = line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        if SEP_RE.match(line):
            continue
        cells = [c.strip() for c in line[1:-1].split("|")]
        if len(cells) != 5:
            malformed.append((cells[0] if cells else "?", len(cells)))
            continue
        if cells[0].lower() == "register":  # the header row
            continue
        rows.append({"register": cells[0], "purpose": cells[1],
                     "locations": CELL_PATH_RE.findall(cells[2]),
                     "status": cells[3], "currency": cells[4]})
    return rows, malformed


def cited_adrs(path):
    """Every ADR id mentioned in the roadmap -- a set, not a maximum.

    A set because the question is accounting, not recency: an id buried
    in a 2026-07 entry accounts for that decision exactly as well as one
    in the last paragraph, and the roadmap is a history log whose ids are
    not ordered by relevance.
    """
    return set(int(n) for n in ADR_CITE_RE.findall(read(path)))


def filed_adrs():
    """Every id that has a record, across the live and frozen halves.

    Both halves, because the number space is single and is never
    restarted (docs/decisions/README.md): reading only the live directory
    would silently stop asking the roadmap to account for 001-053.
    """
    nums, seen = set(), 0
    for rel in ADR_DIRS:
        full = os.path.join(ROOT, rel)
        if not os.path.isdir(full):
            continue
        for name in os.listdir(full):
            m = ADR_FILE_RE.match(name)
            if not m:
                continue
            seen += 1
            nums.add(int(m.group(1)))
    return nums, seen


def live_docs():
    """Every *.md under docs/ that is not frozen reference."""
    out = []
    root = os.path.join(ROOT, DOCS_REL)
    for dirpath, dirnames, filenames in os.walk(root):
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
    """`<key>  <reason>` per line; '#' comments and blanks ignored.

    The same shape .truth/label-coupling-opt-out uses -- key up to the
    first space, the rest is why. State is reported (absent / empty /
    populated) because an ABSENT baseline and an EMPTY one mean different
    things: the first cannot tell a deliberate gap from an oversight, the
    second is a conscious, dated "nothing is excused" (SI-4, ADR-053).
    """
    recorded, state = {}, "absent"
    if not os.path.exists(path):
        return recorded, state
    state = "empty"
    for raw in read(path).splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        state = "populated"
        key, _, reason = line.partition(" ")
        recorded[key.strip()] = reason.strip()
    return recorded, state


BASELINE_HEADER = """\
# register-index: the baseline for checks (b) and (c).
#
# Format:  <key>  <reason>.  The shape .truth/label-coupling-opt-out uses.
# Two key spaces share this file and cannot collide:
#   check (c)   a docs/... path, covered by no register's location
#   check (b)   adr-unaccounted:ADR-nnn, a filed decision the roadmap
#               mentions nowhere
#
# MIRROR RULE, both key spaces: an entry here with no corresponding finding
# is ITSELF a failure -- drop the line. A baseline nobody prunes stops
# meaning "today's backlog" and starts meaning "whatever used to be true".

# --- check (c): docs/*.md covered by no register -------------------------
#
# BASELINE 2026-08-24, UNRESOLVED. These entries record the state at the
# moment the coverage check was introduced -- not a verdict that the files
# below belong nowhere. Resolving one is separate work: either a register
# claims it, or a new register is added to docs/registers.md with a location
# that contains it. The point of this file is that the NEXT uncovered
# document does not pass unnoticed.

"""

ADR_BASELINE_SECTION = """
# --- check (b): filed decisions the roadmap accounts for nowhere ---------
#
# BASELINE 2026-08-24, UNRESOLVED. A backlog, not a verdict: each id below
# has a file in docs/decisions or docs/archive/adr and is mentioned nowhere
# in docs/roadmap-v3.md. Resolving one means citing it in the roadmap where
# it bears on the plan -- which is why this baseline is honest where the
# ADR-gap check it replaced was not: it freezes a backlog, not a wrong
# measure. The point is that the NEXT unaccounted decision does not pass.

"""


def sweep(baseline):
    rows, malformed = index_rows(os.path.join(ROOT, INDEX_REL))
    locations, missing = [], []
    for row in rows:
        for loc in row["locations"]:
            locations.append(loc)
            if not os.path.exists(os.path.join(ROOT, loc)):
                missing.append(
                    "%s: the index names location %r, which does not exist "
                    "on disk -- move the register or fix the row in %s"
                    % (row["register"], loc, INDEX_REL))

    roadmap_path = os.path.join(ROOT, ROADMAP_REL)
    cited = cited_adrs(roadmap_path) if os.path.exists(roadmap_path) else None
    filed, adr_files = filed_adrs()
    accounting = {"adr_files": adr_files, "filed": len(filed),
                  "mentioned": None if cited is None else len(cited),
                  "unaccounted": []}
    stale = []
    if cited is None:
        stale.append(
            "adr accounting cannot be measured: %s is not on disk -- the "
            "roadmap register is not where this sweep looks" % ROADMAP_REL)
    elif not filed:
        stale.append(
            "adr accounting cannot be measured: no ADR-nnn file under %s -- "
            "the decision register is not where this sweep looks"
            % " or ".join(ADR_DIRS))
    else:
        accounting["unaccounted"] = ["ADR-%03d" % n for n in sorted(filed - cited)]

    docs = live_docs()
    uncovered, covered = [], {}
    for rel in docs:
        loc = covered_by(rel, locations)
        if loc:
            covered[rel] = loc
        else:
            uncovered.append(rel)

    return {"rows": rows, "malformed": malformed, "locations": locations, "missing": missing,
            "accounting": accounting, "stale": stale, "docs": docs,
            "covered": covered, "uncovered": uncovered}


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
    baseline, base_state = load_baseline(baseline_path)
    r = sweep(baseline)

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
        with open(baseline_path, "w", encoding="utf-8") as f:
            f.write(BASELINE_HEADER)
            for rel in r["uncovered"]:
                f.write("%s  baseline 2026-08-24, unresolved: covered by no "
                        "register\n" % rel)
            f.write(ADR_BASELINE_SECTION)
            for adr in r["accounting"]["unaccounted"]:
                f.write("%s%s  baseline 2026-08-24, unresolved: %s mentions "
                        "it nowhere\n" % (ADR_KEY_PREFIX, adr, ROADMAP_REL))
        print("register-index: recorded %d uncovered doc(s) and %d unaccounted "
              "ADR(s) in %s" % (len(r["uncovered"]),
                                len(r["accounting"]["unaccounted"]),
                                BASELINE_REL))
        return 0

    failures = [
        "%s: the index row for %r has %d columns, not the five its header "
        "declares -- a row this sweep cannot read is a register it cannot "
        "administer" % (INDEX_REL, name, n)
        for name, n in r.get("malformed", [])
    ] + list(r["missing"]) + list(r["stale"])
    excused_adrs = []
    unaccounted = r["accounting"]["unaccounted"]
    for adr in unaccounted:
        if ADR_KEY_PREFIX + adr in baseline:
            excused_adrs.append(adr)
        else:
            failures.append(
                "%s has a file in the decision register and is mentioned "
                "nowhere in %s -- the plan accounts for it in no tense. Cite "
                "it where it bears on the plan, or record %s%s in %s with a "
                "reason" % (adr, ROADMAP_REL, ADR_KEY_PREFIX, adr,
                            BASELINE_REL))
    for key in sorted(k for k in baseline if k.startswith(ADR_KEY_PREFIX)):
        if key[len(ADR_KEY_PREFIX):] not in set(unaccounted):
            failures.append(
                "%s is recorded in %s but %s now mentions it -- the baseline "
                "entry outlived its finding; drop the line"
                % (key, BASELINE_REL, ROADMAP_REL))

    excused = []
    for rel in r["uncovered"]:
        if rel in baseline:
            excused.append(rel)
        else:
            failures.append(
                "%s is covered by no register's location -- name a register "
                "for it in %s, or record it in %s with a reason"
                % (rel, INDEX_REL, BASELINE_REL))
    coverage_keys = set(k for k in baseline if not k.startswith(ADR_KEY_PREFIX))
    for rel in sorted(coverage_keys - set(r["uncovered"])):
        failures.append(
            "%s is recorded in %s but is no longer uncovered -- the baseline "
            "entry outlived its finding; drop the line" % (rel, BASELINE_REL))

    warnings = []
    if base_state == "absent":
        warnings.append(
            "no %s on record -- this sweep cannot tell a deliberate coverage "
            "gap from an oversight, so it excused NOTHING" % BASELINE_REL)

    report = {
        "registers": len(r["rows"]),
        "locations": len(r["locations"]),
        "missing_locations": r["missing"],
        "adr_accounting": r["accounting"],
        "docs_examined": len(r["docs"]),
        "covered": len(r["covered"]),
        "uncovered": r["uncovered"],
        "excused": excused,
        "excused_adrs": excused_adrs,
        "baseline_state": base_state,
        "failures": failures,
        "warnings": warnings,
    }
    if "--json" in argv:
        print(json.dumps(report, indent=2))
        return EXIT_FINDINGS if failures else 0

    a = r["accounting"]
    for row in r["rows"]:
        mark = "FAIL " if any(
            not os.path.exists(os.path.join(ROOT, l)) for l in row["locations"]
        ) else "OK   "
        print("%s %-18s %s" % (mark, row["register"][:18],
                               ", ".join(row["locations"]) or "(no location)"))
    print("  %-18s %d ADR file(s), %d id(s) filed, %s mentioned in %s; "
          "%d unaccounted (%d excused)"
          % ("adr accounting", a["adr_files"], a["filed"],
             a["mentioned"] if a["mentioned"] is not None else "???",
             ROADMAP_REL, len(a["unaccounted"]), len(excused_adrs)))
    if a["unaccounted"]:
        print("  %-18s %s" % ("unaccounted", ", ".join(a["unaccounted"])))
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
