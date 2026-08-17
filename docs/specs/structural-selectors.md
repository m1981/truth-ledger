# Structural Selectors

Status: implemented and **wired** (`template/truthlib/structural.py`,
`template/scripts/test-structural.py`; integration in FAZA 3 step 3.1/3.3 —
see §9)
Applies to: truth-ledger Structural Policy Anchors

A **structural selector** names a sub-tree of a file and reduces it to a stable
digest. Policies anchored to a selector fire when that sub-tree changes and stay
silent otherwise — replacing filesystem globs, which fire on any byte in any
matching file.

```
package.json#/dependencies/stripe   →  sha256:9f2c…   (unchanged by a version bump elsewhere)
pyproject.toml#tool.ruff.lint       →  sha256:41ab…   (unchanged by edits to [tool.pytest])
docs/spec.md#§2-session-management  →  sha256:c70d…   (unchanged by edits to §1 or §3)
src/auth/jwt.ts                     →  sha256:8e11…   (whole file — plain sha256sum)
```

---

## 1. Placement

`template/truthlib/structural.py`, imported as
`from truthlib.structural import extract_structural_hash`.

The module is **not** named `selectors.py`. That name collides with the Python
standard library's `selectors` module, and a top-level `selectors.py` shadows it
and breaks `subprocess` and `asyncio` outright:

```
AttributeError: module 'selectors' has no attribute 'SelectSelector'
```

Package nesting alone would have hidden that (`truthlib.selectors` shadows
nothing), but only for as long as nobody puts `template/truthlib/` itself on
`sys.path`. `structural` removes the hazard rather than avoiding it, and names
the concern better besides.

`structural` is a **leaf of the pure core**: it imports nothing from `truthlib`,
performs no I/O, reads no clock and no environment — it receives file bytes as
data. `TestModulePurity` enforces all of that mechanically.

Requires Python 3.11+ (`tomllib`). No third-party dependencies.

---

## 2. Grammar

```
target      := file_path [ "#" selector ]
selector    := json_path | toml_path | md_query          ; format chosen by extension
```

`target` splits on its **first** `#` only, so selectors may themselves contain
`#` (`spec.md##2-auth`). An absent or empty selector means *whole file*.

### 2.1 Key paths (`.json`, `.toml`)

```
key_path    := pointer | dot_path
pointer     := "" | ( "/" token )+                       ; RFC 6901
token       := *( unescaped | "~0" | "~1" )              ; ~0 → "~",  ~1 → "/"
dot_path    := segment *( "." segment )
segment     := *( char | "\." | "\\" )                   ; \. → ".",  \\ → "\"
```

A leading `/` selects RFC 6901; anything else is a dot-path. The two notations
are interchangeable and produce identical hashes:
`dependencies.stripe` ≡ `/dependencies/stripe`.

**Array segments** must be canonical non-negative integers: `items.0.name`,
`/bin/1/name`. `-1`, `01`, `+0` and RFC 6901's `-` are rejected as
`SelectorNotFoundError` — they are silent-mismatch hazards, not addresses.

**Dict segments** are matched as exact strings, so a JSON object keyed `"0"` is
reachable via `items.0` too. Escape a literal dot in a key as `a\.b`.

### 2.2 Markdown queries (`.md`, `.markdown`)

```
md_query    := [ "#" ] [ "§" ] ( heading_title | anchor_slug )
anchor_slug := lowercased heading with runs of non-word chars collapsed to "-"
```

Leading `#` and `§` are stripped. The query matches a heading if either

- its **title** matches, case-insensitively and with internal whitespace
  collapsed (`2. Session Management`), or
- its **slug** matches (`2-session-management`).

`§2-session-management`, `2-session-management`, `#2-session-management` and
`2. Session Management` all select `## 2. Session Management`.

Where several headings match, **the first in document order wins**. This is
deterministic but silent — prefer unique headings for anchored sections.

---

## 3. Extraction semantics

### 3.1 Whole file (no selector)

Plain SHA-256 of the raw bytes, byte-for-byte. Matches `sha256sum`. Every
extension is supported. Formatting changes *do* alter this hash — that is the
point of a whole-file anchor.

### 3.2 JSON / TOML key paths

The document is parsed (`json.loads` / `tomllib.loads`), the path is resolved,
and the resulting value is canonically encoded (§4) and hashed.

Consequences, all covered by tests:

| Source change                                   | Hash of `#dependencies` |
|-------------------------------------------------|-------------------------|
| Reindent the file                                | unchanged |
| Swap key order inside `dependencies`             | unchanged |
| Rewrite `"version"` elsewhere in the file        | unchanged |
| Rewrite a TOML comment                           | unchanged |
| Inline table ↔ expanded `[table]`                | unchanged |
| TOML dotted key ↔ `[table]` syntax               | unchanged |
| A JSON unicode escape ↔ the literal character    | unchanged |
| Bump `stripe`'s version                          | **changed** |
| Add a key to `dependencies`                      | **changed** |
| Reorder an array                                 | **changed** |

Array order is preserved, not sorted — reordering a JSON array is a semantic
change, not a formatting one.

### 3.3 Markdown sections

The section runs from its heading line through everything below it, up to (but
excluding) the next heading of **equal or higher level**. Nested subsections are
included: `## 2` swallows `### 2.1` and stops at the next `##` or `#`. The last
section in a file runs to EOF.

The heading line is part of the hashed text, so renaming a heading changes the
hash.

Normalization applied before hashing:

- `\r\n` and `\r` → `\n`
- the heading is rewritten as `<hashes> <title with whitespace collapsed>`;
  a closing hash sequence (`## A ##`) is dropped
- trailing whitespace stripped from every line
- leading and trailing blank lines removed; no trailing newline

Only **ATX** headings (`#`…`######`) are recognized. Headings inside fenced code
blocks (```` ``` ```` and `~~~`) are ignored, so a `## Install` line in a shell
example neither terminates a section nor becomes selectable. Setext (underlined)
headings are **out of scope** and are invisible to this module.

---

## 4. Canonical encoding

Resolved JSON/TOML values are encoded with:

```python
json.dumps(value, sort_keys=True, ensure_ascii=False,
           separators=(",", ":"), allow_nan=False, default=…)
```

then UTF-8 encoded. Mappings sort by key; sequences keep order; floats use
Python's shortest round-trip repr (`1.50` and `1.5` collide; `1` and `1.0` do
not).

TOML's native temporal values have no JSON form, so they are encoded as a tagged
single-key object:

```json
{"$structural-selector/temporal": "datetime:2026-08-17T09:30:00+00:00"}
```

Non-finite floats (`NaN`, `Infinity` — which `json.loads` accepts by default)
are rejected as `MalformedFileError` rather than hashed, since they have no
canonical form.

### 4.1 Domain separation

Hashed payloads are prefixed before digesting:

| Selector kind      | Prefix                            |
|--------------------|-----------------------------------|
| whole file         | *(none — plain `sha256sum`)*      |
| JSON / TOML value  | `structural-selector/v1/value\n`  |
| Markdown section   | `structural-selector/v1/markdown\n` |

JSON and TOML share one domain deliberately: equal logical values hash equally
across formats, so migrating `dependencies` from `package.json` into
`pyproject.toml` preserves the anchor. Bump `v1` if the encoding ever changes —
every stored anchor digest would need re-baselining.

---

## 5. Error contract

```
SelectorError                       (Exception)
├── SelectorNotFoundError           (also KeyError)
├── UnsupportedFormatError
└── MalformedFileError
```

| Condition | Raised |
|---|---|
| Key or array index absent | `SelectorNotFoundError` |
| Index out of range, non-canonical index, index on a mapping's non-key | `SelectorNotFoundError` |
| Descending into a scalar (`a.b` where `a` is `1`) | `SelectorNotFoundError` |
| No Markdown heading matches the query | `SelectorNotFoundError` |
| Selector applied to `.py`, `.ts`, or any other extension | `UnsupportedFormatError` |
| File is not valid UTF-8 | `MalformedFileError` |
| File does not parse as JSON/TOML | `MalformedFileError` |
| Value is non-finite or otherwise non-canonicalizable | `MalformedFileError` |

Every message names the offending selector and the breadcrumb where traversal
stopped, e.g.

```
JSON selector 'dependencies.nope': key 'nope' not found at dependencies
```

`SelectorNotFoundError` also subclasses `KeyError` so existing `except KeyError`
call sites around lookups keep working. Nothing in this module returns a
sentinel — a missing anchor is an error, never a hash.

---

## 6. API

```python
extract_structural_hash(file_content_bytes: bytes, file_ext: str,
                        selector: str | None) -> str      # "sha256:<64-hex>"

resolve_json_pointer(data: dict | list, key_path: str) -> Any
resolve_toml_pointer(data: dict, key_path: str) -> Any
extract_markdown_section(text: str, heading_query: str) -> str
canonicalize(value: Any) -> bytes
split_selector_target(target: str) -> tuple[str, str | None]
```

`file_ext` is normalized: `".JSON"`, `"json"` and `" json "` are equivalent.

---

## 7. Explicit non-goals

This is a point-lookup addresser, not a query language. The following are
**deliberately unsupported** and will not be added:

- wildcards (`dependencies.*`), recursive descent (`..name`)
- array slices (`items[0:5]`), negative indices
- predicate filters (`items[?(@.price < 10)]`)
- expressions, functions, sorting, projection
- YAML, XML, INI; AST-level selectors into `.py` / `.ts` bodies
- Setext Markdown headings; heading disambiguation beyond first-match

A selector that needs any of these is a signal to restructure the config, not to
extend the grammar.

---

## 8. Performance

Budget: **< 1 ms per extraction**, including parse. Measured over 1,000
iterations on Python 3.14 / Apple Silicon:

| Selector | Per extraction |
|---|---|
| `package.json#dependencies` | ~5 µs |
| `pyproject.toml#tool.ruff.lint` | ~30 µs |
| `docs/spec.md#§2-session-management` | ~15 µs |
| 500-dependency JSON `#dependencies` | ~265 µs |

Cost is dominated by parsing, which is redone on every call — the module is
stateless by design. Callers hashing many selectors against one large file
should parse once and use `resolve_*` + `canonicalize` directly.

`reproduce_sweep` keys a `hash_cache` on `(target, revision)` for exactly this
reason: claims sharing a watch policy would otherwise re-read and re-parse the
same `package.json` once per claim.

---

## 9. Integration (FAZA 3, step 3.1 / 3.3)

The module was a leaf with no importers until FAZA 3. It is now reached through
two seams and no others.

**`kernel.watch_target_path`** — the file half of a target. `match_paths` strips
the selector from each *pattern* before globbing, so every consumer of
`evidence_paths` (the whisper, `impact --inverse`, the ADR-038 dirty-watch
advisory, the ADR-039 churn forecast, the reproduce differ) is selector-correct
without knowing selectors exist. Doing it in the matcher rather than at six call
sites is deliberate: `#` is not a glob metacharacter, so an unstripped pattern
would be `re.escape`d into something git can never emit — a dead tripwire of the
exact INV-M shape, arrived at silently.

**`shellio.structural_hash(target, rev=None)`** — the bytes-to-digest path, the
only place a file is read for a selector. Returns `(digest, err)` where `err` is
a `(kind, detail)` pair, `kind ∈ {missing, unsupported, malformed, not-found,
selector-error}`. The kinds are kept apart because they mean different things: a
`package.json` that no longer parses says *nothing* about
`/dependencies/stripe`, and reporting it as drift would be a false alarm of the
precise kind this feature exists to remove.

### What changes for a claim

| | whole-file watch | selector watch |
|---|---|---|
| pre-edit whisper | fires on any edit | fires on any edit *(unchanged — a pre-edit reader cannot hash a file that has not been written)* |
| `truth reproduce` | any byte moves → `watched-moved` | only a moved **sub-tree digest** counts |
| one-path budget (`MAX_FREEHAND_WATCH_PATHS`) | counted | **exempt** |
| ADR-039 churn floor | refuses at the floor | **exempt**; the advisory still reports the file-level forecast |

The two exemptions are not a courtesy to a new feature. The budget exists
because watch sets were *accumulated* rather than chosen, and a selector cannot
be accumulated by accident — the author names an exact key path or heading and
INV-M reads the file to confirm it resolves. The churn floor is measured on the
file, which for a selector target is an upper bound so loose it is nearly noise;
refusing on it would refuse the very narrowing the gate asks for, which is a gate
teaching its own bypass (ADR-049).

### Intake refusals (INV-M, step 3.1)

A selector is refused at filing — never at first read, days later, on a claim
that already looks healthy — when it is:

- **on a glob** (`template/**#/a/b`) — a selector names a sub-tree of *one*
  document, so there is no single file for the digest to be of;
- **on an unsupported format** (`gates.py#foo`) — see §7;
- **resolving to nothing today** — the live arm calls `structural_hash` and
  refuses a key path or heading that names no sub-tree in the file as it stands.

An *absent file* is not refused here: `dead_literal_paths` already owns that.

### Known limitation: commas

`--paths` is comma-split, so a selector may not contain a comma. Markdown
heading queries are the only selectors where this is reachable in practice; use
the slug form (`#2-session-management`) rather than the literal title
(`#2. Session, Management`). The split is ambiguous by construction — `a.md#X, b`
could be one target or two — so this is a documented restriction, not a parser
bug to fix later.
