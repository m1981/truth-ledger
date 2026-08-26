#!/usr/bin/env python3
"""map -- one line per navigable artifact, so an agent greps instead of reads.

META-REPO ONLY (ADR-003 rule 2, ADR-046 Tier C).

--- WHY THIS EXISTS ------------------------------------------------------
The entry cost of this repository grows with the repository. README's
"Reading order" is three items long and two of them point at paths deleted
by 687dbdc, so the one artifact whose job was orientation was also the one
nobody could see rot. A hand-maintained reading order is a ROSTER, and this
repository has now been defeated by a roster three times: arm-index's source
list, register-index's table parser, and gate-reachability's eleven globs.

So orientation and retrieval are split. `docs/scope.md` is READ, once, and
capped at 120 lines by this instrument. `docs/map.txt` is QUERIED, never
read end to end, and is generated -- it cannot describe a file wrongly
unless the file describes itself wrongly, because the description IS the
file's own first line.

--- THE POPULATION, WHICH IS WHERE THE FIRST VERSION WAS WRONG -----------
This instrument's first version read `git ls-files` and called the result
"the tree". It is the INDEX. An adversarial audit on 2026-08-25 showed the
consequence: the instrument, the charter whose ceiling it enforces, and the
prompt that invokes it were all untracked, so the sweep printed a fifteen-row
census with NO `charter` line and exited 0 -- having classified a population
that excluded itself. A partition over the wrong set is still a complete
partition, and still reports zero unclassified.

So the population is now the index UNION the untracked non-ignored files,
deduplicated across merge stages, with every path checked to exist on disk.
`docs/map.txt` still carries only the tracked rows -- otherwise a scratch
file would trip the drift gate -- but an untracked file is classified,
purpose-checked, counted, and findable by `--for`.

--- THE PARTITION --------------------------------------------------------
Every file in the population is classified, with unclassified forced to
zero, and the classification is checked in the direction nobody checks:
every RULE must match something too, or it is a roster entry that running
the instrument can never falsify. `route` is NOT a second classification --
it is a projection of `kind`, printed as a column because that is the axis
an agent picks its entry door by. Saying "both directions" of kind-and-route
would be one classification wearing two columns, and an audit said so. That is deliberate and it is the shape that F1 of the
2026-08-25 external audit says gate-reachability.sh should have had: a
roster answers "is this one of the things I listed", a partition answers
"which side is this on", and only the second one fails loudly when somebody
adds a file nobody thought about.

A file whose kind requires a purpose line and has none is a FINDING, not a
gap in the map. A map that silently omits what it could not describe is the
same defect one level up.

Exit: 0 clean, 1 findings, 2 usage, 3 an input could not be read,
      8 nothing was measured (ADR-042 rule 2).
"""
from __future__ import annotations

import ast
import os
import re
import subprocess
import sys

EXIT_FINDINGS, EXIT_USAGE, EXIT_INPUT, EXIT_VACUOUS = 1, 2, 3, 8

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCOPE_REL = "docs/scope.md"
MAP_REL = "docs/map.txt"
SCOPE_MAX_LINES = 120
# Lines are the one property of a document that word-wrap makes free to
# change: 101 lines of 4000 characters passed the ceiling at 404 KB.
SCOPE_MAX_BYTES = 12000

# Ordered; first match wins. The final rule is a catch-all that FAILS --
# never a bucket. Adding a file in a shape nobody anticipated must stop the
# sweep, not be absorbed by it.
RULES: tuple[tuple[str, str, str | None, str | None], ...] = (
    # (pattern, kind, route, why an empty population is acceptable)
    #
    # Ordered; first match wins. Governance is matched by LOCATION, never by
    # extension: an ADR written as .txt used to be swallowed by the extension
    # rule and vanish from the map at exit 0. A directory that holds norms
    # holds norms whatever anybody names the file.
    # Before the location rules: a directory of norms also holds its own
    # index, and an index is not a norm. Classifying by location is right;
    # classifying README as what surrounds it is the location rule's one
    # false positive.
    (r"^docs/.*/README\.md$",                 "doc",        "record",    None),
    (r"^docs/scope\.md$",                     "charter",    "record",    None),
    (r"^docs/(registers|waivers|roadmap-v3)\.", "register",  "record",    None),
    (r"^docs/decisions/",                     "norm",       "record",    None),
    (r"^docs/archive/adr/",                   "norm-frozen","record",    None),
    (r"^docs/truth-ledger-paper-v3\.",        "norm",       "record",    None),
    (r"^docs/reviews/",                       "brief",      "record",    None),
    (r"^prompts$",                            "prompt",     "record",    None),
    (r"^trial-prompts/.*\.md$",               "trial",      "record",    None),
    (r"^trial-prompts/",                      "trial-data", None,        None),
    (r"^docs/books/.*\.pdf$",                 "reference",  None,        None),
    (r"^docs/diagnosis-[0-9-]+/.*\.sh$",      "instrument", "execution", None),
    (r"^docs/.*\.md$",                        "doc",        "record",    None),
    (r"^[^/]*\.md$",                          "doc",        "record",    None),
    (r"^\.truth/claims\.jsonl$",              "ledger",     "execution", None),
    (r"^\.truth/",                            "policy",     "execution", None),
    (r"^\.githooks/",                         "instrument", "execution", None),
    (r"^(instruments|scripts)/.*\.(py|sh)$",  "instrument", "execution", None),
    (r"^scripts/truth$",                      "instrument", "execution", None),
    (r"\.deny$",                              "policy",     "execution", None),
    (r"^template/scripts/",                   "instrument", "execution", None),
    (r"^template/[^/]+/.*\.py$",              "code",       "execution", None),
    (r"^(tests?|.*/tests?)/",                 "fixture",    None,
     "no test directory exists in this repository today"),
    (r"^mutmut_config\.py$",                  "config",     None,        None),
    (r"(^|/)\.gitignore$",                    "config",     None,        None),
    (r"^\.claude/",                           "config",     None,        None),
    (r"\.(json|toml|cfg|ini|yml|yaml|lock|txt)$", "config", None,        None),
    (r"^(Makefile|\.gitattributes)$",          "config",    None,        None),
    (r"^template/",                           "template",   None,        None),
)

# Always a finding, never a classification. A stray copy of append-only
# evidence classified as an ordinary policy file sat one line below the real
# ledger in the map, indistinguishable from it.
REFUSE: tuple[tuple[str, str], ...] = (
    (r"\.(bak|orig|rej|swp|tmp|save)$",
     "is a scratch copy -- delete it or name it something the map can "
     "describe; a copy of append-only evidence must never sit in a register "
     "looking like the original"),
)

# First lines that are BYTES, not a purpose. Without this the check that
# refuses a file which will not say what it is for was satisfied by a
# shebang (7 rows in the shipped map) and by `<<<<<<< HEAD`.
NOT_A_PURPOSE: tuple[str, ...] = ("!/", "<<<<<<<", "=======", ">>>>>>>",
                                  "-*- coding", "!")


# Kinds an agent navigates by. Everything else is classified but not mapped.
MAPPED = ("charter", "register", "norm", "norm-frozen", "brief", "doc",
          "instrument", "policy", "ledger", "code", "prompt", "trial")
# Kinds whose whole reason to be in the map is that they say what they are
# for. Silence here is a finding.
PURPOSE_REQUIRED = ("charter", "register", "norm", "instrument")


def _ls(*args: str) -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z", *args], cwd=REPO,
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise InputError("git ls-files %s failed: %s"
                         % (" ".join(args), out.stderr.strip()))
    return [p for p in out.stdout.split("\0") if p]


class InputError(Exception):
    """An input could not be read. Exit 3, never a silent zero."""


def population() -> tuple[list[str], set[str], list[str]]:
    """The index UNION the untracked, deduplicated, checked to exist.

    `--deduplicate` is not cosmetic: during an unresolved merge `git
    ls-files` emits a conflicted path once per stage, and without it one
    file became three rows, three counted files, and three copies of
    `<<<<<<< HEAD` published as a norm's purpose.

    `-z` is not cosmetic either: without it a non-ASCII name arrives
    quoted, and the quotes defeat every anchored rule in RULES. That failed
    loudly rather than silently, but it failed for a reason no added rule
    could ever fix.
    """
    indexed = _ls("--deduplicate")
    untracked = set(_ls("--others", "--exclude-standard"))
    missing = [p for p in indexed
               if not os.path.lexists(os.path.join(REPO, p))]
    paths = sorted(set(indexed) | untracked)
    return paths, untracked, missing


def classify(path: str) -> tuple[str | None, str | None, int | None]:
    for index, (pattern, kind, route, _why) in enumerate(RULES):
        if re.search(pattern, path):
            return kind, route, index
    return None, None, None


def refused(path: str) -> str | None:
    for pattern, why in REFUSE:
        if re.search(pattern, path):
            return why
    return None


def purpose(path: str) -> str | None:
    """The file's own first self-description. Never a second source.

    Containment is checked first: `open()` follows symlinks, and a tracked
    symlink pointing outside the repository published the first line of a
    file nobody here reviewed as that file's "own" description.
    """
    full = os.path.join(REPO, path)
    if not os.path.realpath(full).startswith(REPO + os.sep):
        return None
    try:
        with open(full, encoding="utf-8", errors="replace") as fh:
            head = fh.read(8192)
    except OSError:
        return None

    def clean(text: str) -> str | None:
        text = text.strip()
        if not text or any(text.startswith(b) for b in NOT_A_PURPOSE):
            return None
        return text

    # Python is recognised by its SHEBANG as well as its suffix. `scripts/truth`
    # -- the core executable of this repository -- carries its docstring on
    # line 2 and no extension, so a suffix test sent it to the comment reader,
    # which found no `#` and gave up. Name-based dispatch fails the same way
    # location-based classification fails when it defers to an extension.
    first = head.split("\n", 1)[0]
    if path.endswith(".py") or re.match(r"^#!.*python", first):
        try:
            doc = ast.get_docstring(ast.parse(head))
        except SyntaxError:
            try:
                with open(full, encoding="utf-8", errors="replace") as fh:
                    doc = ast.get_docstring(ast.parse(fh.read()))
            except (OSError, SyntaxError):
                return None
        return clean(doc.splitlines()[0]) if doc else None
    if path.endswith(".md"):
        for line in head.splitlines():
            if line.startswith("#"):
                return clean(line.lstrip("#"))
            if line.strip():
                return clean(line)
        return None
    for line in head.splitlines():          # scripts, hooks, policy files
        if line.startswith("#!"):
            continue                        # a shebang is not a purpose
        if line.startswith("#"):
            got = clean(line.lstrip("#"))
            if got:
                return got
        elif line.strip():
            break
    return None


def build() -> dict:
    paths, untracked, missing = population()
    rows, unclassified, purposeless, kinds = [], [], [], {}
    fired = [0] * len(RULES)
    failures = []

    for path in paths:
        why = refused(path)
        if why is not None:
            failures.append("%s %s" % (path, why))
            continue
        kind, route, rule = classify(path)
        if kind is None:
            unclassified.append(path)
            continue
        fired[rule] += 1
        kinds[kind] = kinds.get(kind, 0) + 1
        if kind not in MAPPED:
            continue
        text = purpose(path)
        if text is None and kind in PURPOSE_REQUIRED:
            purposeless.append(path)
        rows.append((path, kind, route or "-", text or "(says nothing)",
                     path in untracked))

    for path in missing:
        failures.append("%s is in the index and not on disk -- a rename or "
                        "delete that skipped git. The map would describe a "
                        "file that is gone, which is the exact rot this "
                        "instrument exists to catch" % path)
    for path in unclassified:
        failures.append("%s matches no classification rule -- decide which "
                        "side it is on in instruments/map.py RULES; a file "
                        "nobody classified is a file nobody navigates" % path)
    for path in purposeless:
        failures.append("%s carries no first-line purpose -- the map "
                        "describes a file with the file's own words or not "
                        "at all" % path)
    # A rule nobody's input reaches is a roster entry that cannot be
    # falsified by running the instrument. That is the exact defect this
    # instrument's docstring indicts in arm-index, register-index and
    # gate-reachability; two such rules shipped in its own first version.
    for index, (pattern, kind, _route, excused) in enumerate(RULES):
        if fired[index] == 0 and excused is None:
            failures.append("RULES[%d] %s -> %s matched nothing -- it is "
                            "shadowed by an earlier rule or its population "
                            "is gone. Delete it, reorder it, or declare why "
                            "empty is acceptable" % (index, pattern, kind))
    return {"rows": rows, "kinds": kinds, "examined": len(paths),
            "classified": len(paths) - len(unclassified),
            "unclassified": len(unclassified), "untracked": len(untracked),
            "fired": fired, "failures": failures}


def render(rows) -> str:
    """Only TRACKED rows reach the file.

    An untracked scratch file would otherwise trip the drift gate on every
    run, and a gate that cries wolf is unwired within a week. Untracked
    files are still classified, still purpose-checked, still counted, and
    still findable with `--for`.
    """
    kept = [r for r in rows if not r[4]]
    width = max((len(r[0]) for r in kept), default=0)
    out = ["# GENERATED by instruments/map.py -- do not edit by hand.",
           "# Query it, do not read it:  grep <what-you-are-touching> " + MAP_REL,
           "# columns: path  kind  route  purpose (the file's own first line)",
           "# Tracked files only. Untracked ones are classified and counted "
           "but not filed here; ask `map.py --for <path>`.",
           ""]
    for path, kind, route, why, _untracked in kept:
        out.append("%-*s  %-11s  %-9s  %s" % (width, path, kind, route, why))
    return "\n".join(out) + "\n"


def scope_findings() -> list[str]:
    full = os.path.join(REPO, SCOPE_REL)
    if not os.path.exists(full):
        return ["%s is absent -- there is no statement of what this system "
                "refuses, so every finding is in scope by default" % SCOPE_REL]
    try:
        with open(full, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        raise InputError("%s: %s" % (SCOPE_REL, exc))
    lines = raw.count(b"\n")
    found = []
    if lines > SCOPE_MAX_LINES:
        found.append("%s is %d lines, ceiling %d -- a scope statement that "
                     "may grow becomes the thing it replaces. Move a section "
                     "into a decision record" % (SCOPE_REL, lines,
                                                 SCOPE_MAX_LINES))
    if len(raw) > SCOPE_MAX_BYTES:
        found.append("%s is %d bytes, ceiling %d -- the line ceiling alone "
                     "is evadable: 101 lines of 4000 characters is 404 KB and "
                     "passed clean" % (SCOPE_REL, len(raw), SCOPE_MAX_BYTES))
    return found


def addresses(path: str) -> list[str]:
    """Every string a document might use to cite this file.

    A norm is cited by its ID, not by its filename -- asking only for the
    basename reported "governed by nothing" for ADR-061, which ADR-062
    governs. A query whose empty answer is wrong teaches the reader to stop
    asking, so it is a worse defect than no query at all.
    """
    names = [os.path.basename(path)]
    m = re.match(r"^(\d{3})-", os.path.basename(path))
    if m and ("/decisions/" in path or "/archive/adr/" in path):
        names.append("ADR-%s" % m.group(1))
    return names


def mentions(needle: str, rows) -> tuple[list[str], int]:
    """Which RECORD-route documents name this path -- grep, not inference.

    Split, not merged: norms and registers GOVERN, briefs RECORD. Listing
    38 documents for .truth/claims.jsonl is a haystack, not an entry point.
    """
    names = addresses(needle)
    governing, recording = [], 0
    for path, kind, route, _why, _untracked in rows:
        if route != "record" or path == needle:
            continue
        try:
            with open(os.path.join(REPO, path), encoding="utf-8",
                      errors="replace") as fh:
                text = fh.read()
        except OSError:
            continue
        if not any(n in text for n in names):
            continue
        if kind in ("norm", "register", "charter"):
            governing.append(path)
        else:
            recording += 1
    return governing, recording


USAGE = "usage: map.py [--write] [--for PATH]"
KNOWN = ("--write", "--for")


def report_for(target: str, r: dict) -> int:
    """`--for` must answer or say why it cannot. Silence taught as an answer
    is worse than no query: the first version said `not in the map` for its
    own source file and for the charter, never mentioning that the reason
    was untrackedness, and printed `kind: charter` -- a kind that IS mapped
    -- alongside `is not in the map`, contradicting itself unnoticed."""
    abs_target = target if os.path.isabs(target) else os.path.join(REPO, target)
    rel = os.path.relpath(os.path.abspath(abs_target), REPO)
    if rel.startswith(".."):
        print("%s is outside %s -- this instrument maps one repository"
              % (target, REPO))
        return EXIT_FINDINGS
    if not os.path.lexists(os.path.join(REPO, rel)):
        print("%s does not exist -- a classification would describe nothing"
              % rel)
        return EXIT_FINDINGS
    if os.path.isdir(os.path.join(REPO, rel)):
        print("%s is a directory; ask about a file, or `grep ^%s %s`"
              % (rel, rel, MAP_REL))
        return 0
    row = next((x for x in r["rows"] if x[0] == rel), None)
    if row is None:
        kind, _route, _i = classify(rel)
        why = refused(rel)
        if why:
            print("%s %s" % (rel, why))
        elif kind is None:
            print("%s matches no classification rule -- it is UNCLASSIFIED "
                  "and the sweep fails on it" % rel)
        else:
            print("%s is kind %s, which is classified but not navigated "
                  "(not in MAPPED)" % (rel, kind))
        return EXIT_FINDINGS if (kind is None or why) else 0
    print("  %-12s %s%s" % ("path", row[0],
                            "   [UNTRACKED -- not in %s yet]" % MAP_REL
                            if row[4] else ""))
    print("  %-12s %s" % ("kind", row[1]))
    print("  %-12s %s" % ("route", row[2]))
    print("  %-12s %s" % ("purpose", row[3]))
    governing, recording = mentions(rel, r["rows"])
    if governing:
        print("  %-12s %s" % ("governed by", ", ".join(governing)))
    else:
        print("  %-12s no norm, register or charter names this file -- "
              "nothing you can find this way governs it" % "governed by")
    print("  %-12s %d brief(s)/doc(s) -- history, not governance"
          % ("mentioned in", recording))
    return 0


def main(argv: list[str]) -> int:
    unknown = [a for a in argv
               if a.startswith("-") and a not in KNOWN]
    if unknown:
        print("map.py: unknown option %s\n%s" % (", ".join(unknown), USAGE),
              file=sys.stderr)
        return EXIT_USAGE
    write = "--write" in argv
    target = None
    if "--for" in argv:
        i = argv.index("--for")
        if i + 1 >= len(argv):
            print(USAGE, file=sys.stderr)
            return EXIT_USAGE
        target = argv[i + 1]
    stray = [a for a in argv
             if not a.startswith("-") and a != target]
    if stray:
        print("map.py: stray argument %s -- did you mean `--for %s`?\n%s"
              % (stray[0], stray[0], USAGE), file=sys.stderr)
        return EXIT_USAGE

    try:
        r = build()
        if not r["examined"]:
            # DECLARED UNREACHABLE since the population became index UNION
            # untracked: this file is itself untracked until committed, so
            # it is always in its own population. Kept as a floor, not as
            # evidence -- and declared here rather than left as dead code,
            # because a branch nobody can reach is the same defect this
            # instrument fails RULES for. The vacuity that CAN happen now is
            # a rule matching nothing, and that is checked in build().
            print("map: the population is empty -- measuring nothing has not "
                  "passed (ADR-042 rule 2)", file=sys.stderr)
            return EXIT_VACUOUS
        if target:
            return report_for(target, r)

        text = render(r["rows"])
        full = os.path.join(REPO, MAP_REL)
        if write:
            with open(full, "w", encoding="utf-8") as fh:
                fh.write(text)
        elif not os.path.exists(full):
            r["failures"].append("%s has never been generated -- run "
                                 "`map.py --write`" % MAP_REL)
        else:
            with open(full, encoding="utf-8", errors="replace") as fh:
                if fh.read() != text:
                    r["failures"].append(
                        "%s disagrees with the tree -- the tree wins. "
                        "Regenerate with `map.py --write`; do not edit the "
                        "map" % MAP_REL)
        r["failures"].extend(scope_findings())
    except InputError as exc:
        print("map: %s" % exc, file=sys.stderr)
        return EXIT_INPUT

    for kind in sorted(r["kinds"]):
        print("  %-14s %4d file(s)%s" % (kind, r["kinds"][kind],
              "" if kind in MAPPED else "   (classified, not mapped)"))
    print("  %-14s %4d row(s) tracked -> %s" % ("mapped",
          sum(1 for x in r["rows"] if not x[4]), MAP_REL))
    if r["untracked"]:
        print("  %-14s %4d file(s) in the population, not filed in the map"
              % ("untracked", r["untracked"]))
    for f in r["failures"]:
        print("FAIL  " + f)
    print("map: %d file(s) in the population, %d classified, %d unclassified "
          "-- %d failure(s)" % (r["examined"], r["classified"],
                                r["unclassified"], len(r["failures"])))
    return EXIT_FINDINGS if r["failures"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
