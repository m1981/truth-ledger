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

(b) ROADMAP CURRENCY. The highest ADR-nnn cited anywhere in the roadmap,
    against the highest ADR file number in the decision register (live
    plus frozen archive). A gap larger than ADR_GAP_THRESHOLD fails.
    Both numbers are printed whether it fails or not: the point is the
    measurement, and a threshold that hides the reading is a threshold
    nobody can argue with.

    This is a PROXY and is disclosed as one. It does not read what the
    roadmap says; it asks whether the plan has looked at the decision
    register recently enough that the two could still be about the same
    system. Deciding a large gap requires reading both documents, which
    is why the check names a number rather than a verdict.

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

# The gap the plan may run behind the decision register before the two
# stop being about the same system. A constant, not a flag: a threshold
# passed in at the call site is a threshold that gets raised at the call
# site.
ADR_GAP_THRESHOLD = 5

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


def highest_cited_adr(path):
    nums = [int(n) for n in ADR_CITE_RE.findall(read(path))]
    return max(nums) if nums else None


def highest_adr_file():
    """The highest numbered record across the live and frozen halves.

    Both halves, because the number space is single and is never
    restarted (docs/decisions/README.md): reading only the live directory
    would report 61 as 61 by luck and would report an empty live
    directory as zero.
    """
    best, seen = None, 0
    for rel in ADR_DIRS:
        full = os.path.join(ROOT, rel)
        if not os.path.isdir(full):
            continue
        for name in os.listdir(full):
            m = ADR_FILE_RE.match(name)
            if not m:
                continue
            seen += 1
            n = int(m.group(1))
            best = n if best is None else max(best, n)
    return best, seen


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
    """`<path>  <reason>` per line; '#' comments and blanks ignored.

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
# register-index: baseline for check (c), docs/*.md covered by no register.
#
# Format:  <path>  <reason>.  The shape .truth/label-coupling-opt-out uses.
#
# BASELINE 2026-08-24, UNRESOLVED. These entries record the state at the
# moment the coverage check was introduced -- not a verdict that the files
# below belong nowhere. Resolving one is separate work: either a register
# claims it, or a new register is added to docs/registers.md with a location
# that contains it. The point of this file is that the NEXT uncovered
# document does not pass unnoticed.
#
# MIRROR RULE: an entry here whose file is no longer uncovered is ITSELF a
# failure -- drop the line. A baseline nobody prunes stops meaning "today's
# backlog" and starts meaning "whatever used to be true".

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
    cited = highest_cited_adr(roadmap_path) if os.path.exists(roadmap_path) else None
    filed, adr_files = highest_adr_file()
    currency = {"cited": cited, "filed": filed, "adr_files": adr_files,
                "threshold": ADR_GAP_THRESHOLD, "gap": None}
    stale = []
    if cited is None or filed is None:
        stale.append(
            "roadmap currency cannot be measured: %s cites no ADR (%r) or the "
            "decision register holds none (%r) -- one of the two registers is "
            "not where this sweep looks"
            % (ROADMAP_REL, cited, filed))
    else:
        gap = filed - cited
        currency["gap"] = gap
        if gap > ADR_GAP_THRESHOLD:
            stale.append(
                "roadmap currency: %s cites ADR-%03d at the highest, the "
                "decision register holds ADR-%03d -- a gap of %d exceeds the "
                "threshold of %d. The plan and the decisions may no longer be "
                "about the same system; read both, then cite what still applies"
                % (ROADMAP_REL, cited, filed, gap, ADR_GAP_THRESHOLD))

    docs = live_docs()
    uncovered, covered = [], {}
    for rel in docs:
        loc = covered_by(rel, locations)
        if loc:
            covered[rel] = loc
        else:
            uncovered.append(rel)

    return {"rows": rows, "malformed": malformed, "locations": locations, "missing": missing,
            "currency": currency, "stale": stale, "docs": docs,
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
        print("register-index: recorded %d uncovered doc(s) in %s"
              % (len(r["uncovered"]), BASELINE_REL))
        return 0

    failures = [
        "%s: the index row for %r has %d columns, not the five its header "
        "declares -- a row this sweep cannot read is a register it cannot "
        "administer" % (INDEX_REL, name, n)
        for name, n in r.get("malformed", [])
    ] + list(r["missing"]) + list(r["stale"])
    excused = []
    for rel in r["uncovered"]:
        if rel in baseline:
            excused.append(rel)
        else:
            failures.append(
                "%s is covered by no register's location -- name a register "
                "for it in %s, or record it in %s with a reason"
                % (rel, INDEX_REL, BASELINE_REL))
    for rel in sorted(set(baseline) - set(r["uncovered"])):
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
        "roadmap_currency": r["currency"],
        "docs_examined": len(r["docs"]),
        "covered": len(r["covered"]),
        "uncovered": r["uncovered"],
        "excused": excused,
        "baseline_state": base_state,
        "failures": failures,
        "warnings": warnings,
    }
    if "--json" in argv:
        print(json.dumps(report, indent=2))
        return EXIT_FINDINGS if failures else 0

    c = r["currency"]
    for row in r["rows"]:
        mark = "FAIL " if any(
            not os.path.exists(os.path.join(ROOT, l)) for l in row["locations"]
        ) else "OK   "
        print("%s %-18s %s" % (mark, row["register"][:18],
                               ", ".join(row["locations"]) or "(no location)"))
    print("  %-18s roadmap cites ADR-%s, register holds ADR-%s over %d file(s)"
          "; gap %s, threshold %d"
          % ("adr currency",
             "%03d" % c["cited"] if c["cited"] is not None else "???",
             "%03d" % c["filed"] if c["filed"] is not None else "???",
             c["adr_files"],
             c["gap"] if c["gap"] is not None else "unmeasurable",
             c["threshold"]))
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
