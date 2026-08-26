#!/usr/bin/env python3
"""arm-index -- which arm guards what? (A6)

META-REPO ONLY (ADR-003 rule 2, ADR-046 Tier C): it sweeps THIS
repository's instruments and is never shipped to a consumer.

--- WHY THIS EXISTS ------------------------------------------------------
The machinery has three structural levels. Two are pinned mechanically and
one is not:

    modules   8      TestStructureDocMatchesDisk (both sides derived)  pinned
    checks   13      gate-reachability.sh (closure from roots)         pinned
    arms   ~830      nothing

"Which arms guard ADR-051?" is answerable only by grep. When an ADR moves,
nothing says which arms move with it; when an arm stops guarding what its
name claims, nothing notices. Three defects of exactly that shape landed
in one session (2026-08-13/14): three ADR-011 arms asserted a HEADLESS
refusal without redirecting stdin and passed on a typed-text mismatch; a
hand-transcribed atlas drifted from the canary it describes; and two
seeded mutations missed silently, each looking exactly like an arm that
held.

--- THE FOUR SPECIES, KEPT APART -----------------------------------------
"Arm" names four different things, and conflating them is half the
cognitive load this index exists to reduce:

  seeded-fault   canary: plant a defect, assert the gate catches it
  unit-test      core + v04: pure functions over plain data
  meta-arm       test-*.sh: test that the CHECKERS work
  probe          fingerprint: asserts NOTHING; the whole file is compared

A probe cannot "fail" in isolation, so it is never subject-checked; it is
counted and indexed so the reverse lookup is complete.

--- THE SUBJECT RULE, AND WHERE IT IS ENFORCED ---------------------------
A family declares its subject in its own header:

    say "FAULT DG (ADR-025): doctor decides the commit gate via CI ..."
    say "FAULT B  (INV-C):   commit touching evidence paths ..."

ENFORCED for the canary, where the convention exists and is 89% followed
(108 of 122 families at the time of writing). A family there without a
subject FAILS.

REPORTED, NOT ENFORCED, everywhere else -- and this is a declared limit,
not an oversight. The meta-suites use `CASE n` / `ARM n` headers and only
2 of 28 cite a subject; core unit tests name a function, not an ADR.
Failing ~70 arms for a convention that was never adopted would be a gate
refusing legitimate work, which teaches its own bypass (ADR-014's
confused-deputy lesson, the reason ADR-037's lints are warnings). Adopt
the convention there first, then move the species into ENFORCED.

--- WHAT THIS CANNOT DO --------------------------------------------------
It maps DECLARED subjects. It cannot verify that an arm does what its
header says -- a family headed `(ADR-051)` whose body exercises something
else is indexed under ADR-051 and this instrument will never know. That
stays red-proof, by hand, per arm. What changes is that you can see WHERE
to run it.

It also parses rather than executes, deliberately: an index that costs ten
minutes will not be run. The consequence is that static arm counts differ
from runtime ones -- the canary's if/else pairs mean 280 `ok` call sites
produce 283 exercised arms -- so both numbers are reported and neither is
silently preferred.

--- THE RECONCILIATION PASS (2026-08-24) ---------------------------------
The subject rule above is ONE-DIRECTIONAL: it asks whether an arm declares
a subject, never whether the register that names the arm still agrees. That
gap has a measured cost. Four Appendix A rows were found describing retired
machinery, and the mechanism of the break is visible in this file's own
docstring example:

    was:  say "FAULT B  (INV-C):   commit touching evidence paths ..."
    now:  say "FAULT B (step 2.5): a commit touching evidence paths must NOT ..."

At the moment the arm was INVERTED its subject was rewritten from the
invariant to the refactor step -- locally correct, since the arm's subject
really did change -- and the paper row kept promising a protection that no
longer exists. A row that is MISSING is visible to a review; a row that
outlived its mechanism reads like a working guarantee.

So this pass reads Appendix A and reconciles it against the arms, in three
classes: a row naming no recognisable arm, a row naming an arm that does
not exist, and a row whose named arm does not point back. The third is the
one that catches an inversion.

Reported against a baseline, never enforced wholesale: today's state is
recorded so the sweep refuses the NEXT divergence rather than relitigating
the current backlog -- the same discipline label-coupling uses. Matching is
deliberately conservative: an unrecognised token is ignored rather than
guessed at, so this pass under-reports by construction.

Exit: 0 clean, 1 subject-less families in an enforced species OR an
unrecorded paper/arm divergence OR a SOURCES entry that no longer exists,
8 zero arms examined (ADR-042 rule 2 -- an index that indexed nothing has
not passed).

Usage: python3 instruments/arm-index.py [--json] [--subject ADR-051]
                                       [--record-links]
Gate:  NONE yet -- wire it once the enforced backlog is closed, or this
       file becomes the thing it was built to detect.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPT_OUT_REL = ".truth/arm-subject-opt-out"
PAPER_REL = "docs/truth-ledger-paper-v3.md"
BASELINE_REL = ".truth/arm-index-paper-baseline"
HASHES_REL = ".truth/arm-index-link-hashes"
PROSE_HASHES_REL = ".truth/arm-index-prose-hashes"
# Documents whose normative prose cites positions (ADR-060 half two).
PROSE_DOCS = ("docs/truth-ledger-paper-v3.md", "docs/truth-ledger-explained.md")
# A paragraph is normative when it carries a modal, per ADR-060: a surface
# lint, never a model -- "no NLP, by design".
MODAL_RE = re.compile(r"\b(must|never|always|only|cannot)\b", re.I)
POSITION_RE = re.compile(r"\b(ADR-\d{1,4}|INV-[A-Z]{1,3})\b")
EXIT_SUBJECTLESS = 1
EXIT_EMPTY = 8

# A subject is an ADR, an invariant, a G-number, a roadmap/TL item, or a
# tracked issue. Deliberately broad: the point is traceability to SOME
# named decision, not to one register.
SUBJECT_RE = re.compile(
    r"\b(ADR-\d+|INV-[A-Z]\b|G\d+\b|FS-\d+|TL-\d+|SI-\d+|R\d+\b|issue #\d+)")

# An Appendix A row: `| INV-x | property | falsified by | gate |`.
INV_ROW_RE = re.compile(r"^\|\s*(INV-[A-Z]{1,3})\s*\|(.*)\|\s*$")
# The arm code a family header opens with: `FAULT AC1 (...)` -> `AC1`.
ARM_CODE_RE = re.compile(r"^(?:FAULT|ARM|CASE|LANE|DOCTOR)S?\s+([A-Z][A-Z0-9]*)")
# A candidate reference inside a Gate cell. Two shapes, both filtered against
# real arm codes afterwards, so an unknown token costs a miss and never an
# invented edge. A BARE single letter is not accepted: "Tier C" would
# otherwise read as arm `C`, which is how this matcher first mis-fired.
# The keyword may repeat ("Seeded canary FAULT SD-decay"), so it is a group
# with a +: matching only the first would capture the word FAULT itself.
REF_KEYWORD_RE = re.compile(
    r"\b(?:(?:FAULTS?|ARM|CASE|LANE|DOCTOR|canary|Seeded)\s+)+`?([A-Z][A-Z0-9]{0,3})`?")
# The code sometimes leads instead: "Seeded H-faults".
REF_SUFFIX_RE = re.compile(r"\b([A-Z][A-Z0-9]{0,3})-faults?\b")
REF_BARE_RE = re.compile(r"\b([A-Z]{1,3}\d{1,2})\b")
# A Python arm is named by its method, not by a code.
REF_TEST_RE = re.compile(r"\b(test_\w+)\b")
# `AC1-AC8`, `V1--V3`: expanded, then filtered the same way.
RANGE_RE = re.compile(r"\b([A-Z]{1,3})(\d{1,2})\s*[-\u2013\u2014]+\s*(?:([A-Z]{1,3}))?(\d{1,2})\b")

SOURCES = (
    # (path, species, enforced)
    ("template/scripts/truth-canary.sh", "seeded-fault", True),
    ("scripts/test-release-battery.sh", "meta-arm", False),
    # 32022c6 (2026-08-15) replaced the bash scaffolding -- fingerprint.sh,
    # test-instruments.sh, test-fact-health.sh, test-session-digest.sh and
    # test-whisper-hook.sh -- with ONE stdlib runner. This table kept naming
    # the five dead files for nine days while build() skipped them silently,
    # so the sweep reported "over 9 instruments" while reading four.
    ("template/scripts/test-integrations.py", "integration", False),
    ("template/scripts/test-truth-core.py", "unit-test", False),
    ("template/scripts/test-truth-v04.py", "unit-test", False),
)

# The header vocabulary is an ENUMERATION, and an enumeration over spellings
# is fail-open to a form invented later -- the same class as the capsule that
# counted `^# --- [0-9]+[.]` and went blind to `5b.` (J-047, wk-96a3bd63).
# Here it cost a FALSE POSITIVE rather than a false negative, which is the
# safe direction and is why this was survivable: `DOCTOR (G4)` at
# truth-canary.sh:71 declares its subject perfectly well, but the pattern
# could not see the header at all, so its 12 arms were reported as
# "(no family header)" and the instrument FAILED. The subject was never
# missing; the parser was.
# DOCTOR earned its place by causing that failure -- do not add spellings
# speculatively. Verified before adding: of every `say`/`echo` header in the
# swept suites, DOCTOR is the ONLY one that declares a subject and is missed
# by this pattern.
FAMILY_RE = re.compile(
    r'^\s*(?:say|echo)\s+"((?:FAULT|ARM|CASE|LANE|DOCTOR)[^"]*)"')
ASSERT_RE = re.compile(r'(?:^|\s)(ok|miss|bad)\s+"')
PROBE_RE = re.compile(r'^probe\s+"([^"]+)"')
CLASS_RE = re.compile(r"^class\s+(Test\w+)")
TESTDEF_RE = re.compile(r"^\s+def\s+(test_\w+)")


# The convention AS PRACTISED, which is wider than one register: a family
# header declares its subject in the parenthesis right after its id.
# `FAULT DG (ADR-025)` names an ADR; `FAULT S1 (spec-health)` names the
# script it guards; `FAULT RP (F1.1)` names a plan item. All three are
# traceable, which is the whole point -- "what does this arm guard?" is
# answered by any of them. Insisting on ADR-nnn alone reported 15 families
# as subject-less when 13 of them plainly declare a subject, and a rule
# that calls a followed convention a violation gets switched off.
PAREN_TAG_RE = re.compile(r"^(?:FAULT|ARM|CASE|LANE|DOCTOR)\s*\S*\s*\(([^)]+)\)")


def _subject(text):
    """Canonical register first, then the parenthesised tag as practised."""
    m = SUBJECT_RE.search(text or "")
    if m:
        return m.group(1)
    t = PAREN_TAG_RE.match((text or "").strip())
    return t.group(1).strip() if t else None


def scan_shell(path, species, rel):
    """Shell suites: a family is a say/echo header; arms are the ok/miss
    calls that follow it until the next header."""
    arms, family, fam_line = [], None, 0
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            m = FAMILY_RE.match(line)
            if m:
                family, fam_line = m.group(1), n
                continue
            if species == "probe":
                p = PROBE_RE.match(line)
                if p:
                    label = p.group(1)
                    arms.append({"instrument": rel, "species": species,
                                 "family": label.split(":")[0],
                                 "label": label, "line": n,
                                 "subject": _subject(label)})
                continue
            if ASSERT_RE.search(line):
                arms.append({"instrument": rel, "species": species,
                             "family": family or "(no family header)",
                             "label": line.strip()[:70], "line": n,
                             "family_line": fam_line,
                             "subject": _subject(family)})
    return arms


def scan_python(path, species, rel):
    """Unit suites: the class is the family, each test_* is an arm.

    The subject may sit in the class name or docstring -- but a class can
    cover several registers (TestTierCInstruments spans five instruments),
    so a METHOD docstring naming a subject wins for that arm. Without this,
    a per-arm back-pointer has nowhere to live.
    """
    import ast
    src = open(path, encoding="utf-8").read()
    arms = []
    for node in ast.parse(src).body:
        if not isinstance(node, ast.ClassDef):
            continue
        subj = _subject(node.name + " " + (ast.get_docstring(node) or ""))
        for sub in node.body:
            if isinstance(sub, ast.FunctionDef) and sub.name.startswith("test_"):
                arms.append({"instrument": rel, "species": species,
                             "family": node.name, "label": sub.name,
                             "line": sub.lineno, "family_line": node.lineno,
                             "subject": (_subject(ast.get_docstring(sub) or "")
                                         or subj or _subject(sub.name))})
    return arms


def load_opt_out():
    """SI-4 + ADR-053: absent -> loud warning; committed-empty -> conscious
    and dated; populated -> `<family> -- <reason>` per line."""
    path = os.path.join(ROOT, OPT_OUT_REL)
    if not os.path.exists(path):
        return "absent", {}
    entries = {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        k, _, why = line.partition("--")
        entries[k.strip()] = why.strip()
    return ("populated" if entries else "empty"), entries


def build():
    """Arms, plus the sources that have gone missing.

    A source that vanished used to be skipped, which let the sweep report a
    count of instruments it had not read -- the same fail-open shape ADR-042
    rule 2 refuses one level up. Missing sources are returned so the caller
    can fail on them.
    """
    arms, missing = [], []
    for rel, species, enforced in SOURCES:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            missing.append(rel)
            continue
        got = (scan_python(path, species, rel) if path.endswith(".py")
               else scan_shell(path, species, rel))
        for a in got:
            a["enforced"] = enforced
        arms += got
    return arms, missing


def paper_rows():
    """(invariant, gate-cell) for every Appendix A row, or [] if absent."""
    path = os.path.join(ROOT, PAPER_REL)
    if not os.path.exists(path):
        return []
    rows, inside = [], False
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("## Appendix A"):
                inside = True
                continue
            if inside and line.startswith("## "):
                break
            if not inside:
                continue
            m = INV_ROW_RE.match(line.rstrip("\n"))
            if m:
                cells = [c.strip() for c in m.group(2).split("|")]
                rows.append((m.group(1), cells[-1] if cells else ""))
    return rows


def arm_codes(families, arms):
    """Every name a Gate cell may legitimately point at.

    Two registers, because the machinery has two arm shapes: a canary family
    opens with a code (`FAULT AC1`), a Python arm is a test method. A row may
    name either, and after 32022c6 several properties are gated only by the
    second.
    """
    out = {}
    for fam in families.values():
        if not fam["enforced"]:
            continue
        m = ARM_CODE_RE.match(fam["family"])
        if m:
            out.setdefault(m.group(1), fam)
    for a in arms:
        if a["species"] in ("integration", "unit-test") and a["label"].startswith("test_"):
            out.setdefault(a["label"], {"family": a["family"], "subject": a["subject"],
                                      "instrument": a["instrument"], "enforced": False})
    return out


def _referenced(gate, known):
    """Arm codes a Gate cell names. Unrecognised tokens are dropped.

    Backticks are normalised away first: the register is written both as
    ``Seeded `FAULT B` `` and as ``Seeded FAULT B``, and a matcher that sees
    only one of them reports the other as unreferenced.
    """
    gate = gate.replace("`", " ")
    hits = set()
    for pre, lo, pre2, hi in RANGE_RE.findall(gate):
        if pre2 and pre2 != pre:
            continue
        for n in range(int(lo), int(hi) + 1):
            hits.add(f"{pre}{n}")
    hits.update(REF_KEYWORD_RE.findall(gate))
    hits.update(REF_SUFFIX_RE.findall(gate))
    hits.update(REF_BARE_RE.findall(gate))
    hits.update(REF_TEST_RE.findall(gate))
    return sorted(h for h in hits if h in known)


def arm_text(fam, arms):
    """The text a link points at: the family header plus its arm labels.

    Hashed rather than compared, because the question is not "did anything
    change" but "did THIS link's target change" -- and a header rewritten at
    an inversion is exactly the change that must be seen.
    """
    labels = sorted(a["label"] for a in arms
                    if a["instrument"] == fam["instrument"] and a["family"] == fam["family"])
    return fam["family"] + "\n" + "\n".join(labels)


def load_hashes_at(rel):
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        return "absent", {}
    out = {}
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            key, _, digest = line.rpartition("  ")
            out[key.strip()] = digest.strip()
    return ("populated" if out else "empty"), out


def load_hashes():
    """`INV-x CODE  sha256` per line -- the recorded state of each link."""
    path = os.path.join(ROOT, HASHES_REL)
    if not os.path.exists(path):
        return "absent", {}
    out = {}
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            key, _, digest = line.rpartition("  ")
            out[key.strip()] = digest.strip()
    return ("populated" if out else "empty"), out


def suspect_links(rows, known, arms, recorded):
    """Links whose target changed since the hash was recorded (L2).

    A resolvable link is not a fresh one. FAULT B and FAULT E stayed
    resolvable through their inversion; what moved was their MEANING, and only
    the target's text carries that. Reported as SUSPECT, never as broken: an
    inversion is often correct, and the row is what needs re-reading.
    """
    import hashlib
    suspects, current = [], {}
    for inv, gate in rows:
        for code in _referenced(gate, known):
            key = f"{inv} {code}"
            digest = hashlib.sha256(
                arm_text(known[code], arms).encode("utf-8")).hexdigest()[:16]
            current[key] = digest
            was = recorded.get(key)
            if was is not None and was != digest:
                suspects.append(
                    (key, f"{inv}: the arm {code} it names has CHANGED since the "
                          f"link was recorded ({was} -> {digest}) -- re-read the "
                          f"row, then refresh with --record-links"))
    return suspects, current


def position_state(pos):
    """What a cited position MEANS, as bytes.

    Deliberately not the cited file alone. ADR-019 was never edited; ADR-057
    superseded it from outside, so a hash over ADR-019 would never move. The
    target is therefore the position's own text PLUS every position that amends
    or supersedes it -- the thing that actually changed under the citing prose.
    """
    parts = []
    if pos.startswith("ADR-"):
        num = pos.split("-")[1]
        for d in ("docs/archive/adr", "docs/decisions"):
            for name in sorted(os.listdir(os.path.join(ROOT, d))
                               if os.path.isdir(os.path.join(ROOT, d)) else []):
                if not name.startswith(num) or not name.endswith(".md"):
                    continue
                with open(os.path.join(ROOT, d, name), encoding="utf-8",
                          errors="replace") as f:
                    parts.append(f.read()[:4000])
    for d in ("docs/archive/adr", "docs/decisions"):
        full = os.path.join(ROOT, d)
        if not os.path.isdir(full):
            continue
        for name in sorted(os.listdir(full)):
            if not name.endswith(".md"):
                continue
            with open(os.path.join(full, name), encoding="utf-8", errors="replace") as f:
                head = f.read()[:3000]
            if re.search(r"^(Amends|Supersedes)\s*:.*\b" + re.escape(pos) + r"\b",
                         head, re.M):
                parts.append(f"AMENDED-BY {name}")
    return "\n".join(parts)


def prose_citations():
    """(doc, paragraph index, position) for normative paragraphs that cite."""
    out = []
    for rel in PROSE_DOCS:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8", errors="replace") as f:
            paras = re.split(r"\n\s*\n", f.read())
        for i, para in enumerate(paras):
            if para.lstrip().startswith(("|", "```")) or not MODAL_RE.search(para):
                continue
            for pos in sorted(set(POSITION_RE.findall(para))):
                out.append((rel, i, pos))
    return out


def suspect_prose(recorded):
    """Normative paragraphs whose cited position moved (ADR-060 half two)."""
    import hashlib
    suspects, current = [], {}
    for rel, idx, pos in prose_citations():
        key = f"{rel}#{idx} {pos}"
        digest = hashlib.sha256(position_state(pos).encode("utf-8")).hexdigest()[:16]
        current[key] = digest
        was = recorded.get(key)
        if was is not None and was != digest:
            suspects.append(
                (key, f"{rel} paragraph {idx}: the position {pos} it cites has "
                      f"MOVED since the citation was recorded ({was} -> {digest}) "
                      f"-- re-read the paragraph, then refresh with --record-links"))
    return suspects, current


def load_baseline():
    """`INV-x <class> <detail>` per line; '#' comments and blanks ignored."""
    path = os.path.join(ROOT, BASELINE_REL)
    if not os.path.exists(path):
        return "absent", set()
    recorded, state = set(), "empty"
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            state = "populated"
            recorded.add(line.split("  ")[0].strip())
    return state, recorded


def reconcile(families, arms):
    """Appendix A against the arms. Findings, not verdicts -- see docstring."""
    rows = paper_rows()
    if not rows:
        return None, []
    known = arm_codes(families, arms)
    findings = []
    for inv, gate in rows:
        refs = _referenced(gate, known)
        if not refs:
            findings.append((f"{inv} no-arm",
                             f"{inv}: its Gate names no arm this sweep can "
                             f"recognise -- {gate[:60]!r}"))
            continue
        for code in refs:
            fam = known[code]
            if fam["subject"] != inv:
                findings.append((f"{inv} back-pointer {code}",
                                 f"{inv}: names arm {code}, but that arm "
                                 f"declares {fam['subject']!r} -- the link is "
                                 f"one-way, so an inversion of {code} would "
                                 f"leave this row promising a retired guarantee"))
    return rows, findings


def main(argv):
    arms, missing = build()
    opt_state, opt_entries = load_opt_out()

    families, failures, warnings = {}, [], []
    for rel in missing:
        failures.append(
            f"{rel} is named in SOURCES but does not exist -- the sweep would "
            f"otherwise report an instrument count it never read (fail-open)")
    for a in arms:
        key = (a["instrument"], a["family"])
        fam = families.setdefault(key, {"instrument": a["instrument"],
                                        "family": a["family"],
                                        "species": a["species"],
                                        "enforced": a["enforced"],
                                        "subject": a["subject"], "arms": 0})
        fam["arms"] += 1
        if a["subject"] and not fam["subject"]:
            fam["subject"] = a["subject"]

    for fam in families.values():
        if fam["subject"] or fam["family"] in opt_entries:
            continue
        if fam["enforced"]:
            failures.append(
                f"{fam['instrument']}: family {fam['family']!r} "
                f"({fam['arms']} arm(s)) declares no subject -- name the "
                f"ADR/INV/G it guards in its header, or record the exemption "
                f"in {OPT_OUT_REL} with a reason")
        else:
            warnings.append(f"{fam['instrument']}: {fam['family']!r}")

    for key in opt_entries:
        if not any(f["family"] == key for f in families.values()):
            failures.append(
                f"{key} is exempted in {OPT_OUT_REL} but no family by that "
                "name exists -- the exemption outlived its arm")

    rows, findings = reconcile(families, arms)
    base_state, baseline = load_baseline()
    hash_state, recorded = load_hashes()
    known = arm_codes(families, arms)
    suspects, current_hashes = suspect_links(rows or [], known, arms, recorded)
    _, prose_recorded = load_hashes_at(PROSE_HASHES_REL)
    prose_susp, prose_current = suspect_prose(prose_recorded)
    suspects += prose_susp
    if "--record-links" in argv:
        # A refresh must not bless a degraded measure. Demonstrated 2026-08-26:
        # with one SOURCES entry hidden, the ordinary run raised two failures
        # and this branch printed "recorded 36 link ... hash(es)" and exited 0
        # -- one link FEWER than the file it overwrote, because the arms of the
        # unreadable source had simply vanished from the census. The failure
        # list was already computed above; the early return below just meant
        # nobody ever saw it. That is the shape --record-baseline was caught
        # in, one instrument over, and it was suspected in this file on
        # 2026-08-26 and left unchecked for a whole session.
        if failures:
            print("arm-index: REFUSING to record -- the sweep has %d failure(s) "
                  "and a refresh taken now would freeze a census computed from "
                  "sources it could not read:" % len(failures))
            for text in failures:
                print("  FAIL  %s" % text)
            return 1
        # The header of the recorded file says to refresh only AFTER reading
        # the suspect rows, never instead. Nothing enforced that, so the rows
        # being erased are printed here: the signal is shown at the moment it
        # is destroyed, which is the only moment it can still be read.
        if suspects:
            print("arm-index: %d suspect entr(ies) are being overwritten by "
                  "this refresh -- read them before you accept it:"
                  % len(suspects))
            for _key, text in suspects:
                print("  SUSPECT  %s" % text)
        with open(os.path.join(ROOT, HASHES_REL), "w", encoding="utf-8") as f:
            f.write("# arm-index: hash celu kazdego dowiazania wiersz Appendix A <-> ramie.\n"
                    "# Zmiana hasha czyni wiersz SUSPECT -- nie zepsutym. Inwersja bywa\n"
                    "# poprawna; to WIERSZ wymaga wtedy ponownego przeczytania.\n"
                    "# Odswiez ta lista dopiero PO przeczytaniu wierszy, nie zamiast.\n\n")
            for k in sorted(current_hashes):
                f.write(f"{k}  {current_hashes[k]}\n")
        with open(os.path.join(ROOT, PROSE_HASHES_REL), "w", encoding="utf-8") as f:
            f.write("# arm-index: the hash of each cited POSITION, per normative\n"
                    "# paragraph that cites it (ADR-060 half two). The hash covers the\n"
                    "# position plus everything that amends or supersedes it, because a\n"
                    "# position can be invalidated from outside without being edited.\n\n")
            for k in sorted(prose_current):
                f.write(f"{k}  {prose_current[k]}\n")
        print(f"arm-index: recorded {len(current_hashes)} link and "
              f"{len(prose_current)} prose hash(es)")
        return 0
    for key, text in suspects:
        failures.append(text)
    live_keys = {k for k, _ in findings}
    for key, text in findings:
        (warnings if key in baseline else failures).append(text)
    # Same rule the opt-out already carries: an exemption that outlived what
    # it excused is itself decay, and a baseline nobody prunes stops meaning
    # "today's backlog" and starts meaning "whatever used to be true".
    for key in sorted(baseline - live_keys):
        failures.append(
            f"{key} is recorded in {BASELINE_REL} but no longer diverges -- "
            f"the baseline entry outlived its finding; drop the line")
    if rows is not None and not rows:
        warnings.append(f"{PAPER_REL} has no Appendix A rows -- the "
                        "reconciliation pass examined nothing")

    if not arms:
        print("arm-index: indexed ZERO arms -- an index that indexed nothing "
              "has not passed (ADR-042 rule 2). Check the SOURCES table.",
              file=sys.stderr)
        return EXIT_EMPTY
    if opt_state == "absent":
        warnings.insert(0, f"no {OPT_OUT_REL} on record -- this sweep cannot "
                        "tell a deliberate exemption from an oversight, so it "
                        "excused NOTHING")

    reverse = {}
    for a in arms:
        if a["subject"]:
            reverse.setdefault(a["subject"], []).append(
                f"{a['instrument']}:{a['line']} {a['family']}")

    by_species = {}
    for a in arms:
        by_species[a["species"]] = by_species.get(a["species"], 0) + 1

    if "--subject" in argv:
        want = argv[argv.index("--subject") + 1]
        for row in sorted(reverse.get(want, [])):
            print(f"  {row}")
        print(f"{want}: {len(reverse.get(want, []))} arm(s)")
        return 0

    report = {"arms": len(arms), "families": len(families),
              "paper_rows": len(rows) if rows else 0,
              "reconciliation": [t for _, t in findings],
              "baseline_state": base_state,
              "link_hash_state": hash_state,
              "suspect_links": [t for _, t in suspects],
              "by_species": by_species,
              "subjects": len(reverse),
              "opt_out_state": opt_state,
              "failures": failures, "warnings": warnings,
              "reverse_index": {k: sorted(v) for k, v in sorted(reverse.items())},
              "family_rows": sorted(families.values(),
                                    key=lambda f: (f["instrument"], f["family"]))}
    if "--json" in argv:
        print(json.dumps(report, indent=2))
        return EXIT_SUBJECTLESS if failures else 0

    for sp, n in sorted(by_species.items()):
        print(f"  {sp:14} {n:5} arm(s)")
    print(f"  {'subjects':14} {len(reverse):5} distinct, "
          f"{len(families)} families")
    for w in warnings[:8]:
        print("WARN  " + w)
    if len(warnings) > 8:
        print(f"WARN  ... and {len(warnings) - 8} more family/families with "
              "no declared subject in a REPORTED (non-enforced) species")
    for f in failures:
        print("FAIL  " + f)
    if rows:
        print(f"  {'appendix A':14} {len(rows):5} row(s), {len(findings)} "
              f"unreconciled [{BASELINE_REL}: {base_state}]")
        print(f"  {'links':14} {len(current_hashes):5} hashed, {len(suspects)} "
              f"suspect [{HASHES_REL}: {hash_state}]")
        print(f"  {'prose cites':14} {len(prose_current):5} hashed "
              f"[{PROSE_HASHES_REL}]")
    print(f"arm-index: {len(arms)} arm(s) in {len(families)} families over "
          f"{len(SOURCES)} instruments -- {len(failures)} failure(s) "
          f"[{OPT_OUT_REL}: {opt_state}]")
    return EXIT_SUBJECTLESS if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
