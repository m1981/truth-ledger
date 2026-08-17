"""Structural Policy Anchors: deterministic sub-tree extraction and hashing.

This module turns a *structural selector* -- a file path with an optional
``#selector`` suffix -- into a stable ``sha256:<64-hex>`` digest of exactly the
sub-tree it names, so that a policy can observe ``package.json#/dependencies/stripe``
without being woken up by an unrelated edit three keys over.

Design constraints (deliberate non-goals are listed in ``docs/specs/structural-selectors.md``):

* **Point lookups only.** RFC 6901 JSON Pointers and plain dot-paths. No
  wildcards, no slicing, no predicates -- this is not a query engine.
* **Standard library only.** ``json``, ``tomllib``, ``hashlib``, ``re``, ``datetime``.
* **Canonical hashing.** Source formatting (indentation, key order, unicode
  escaping, CRLF) never reaches the digest.

Public surface
--------------
``extract_structural_hash``  -- the entry point.
``resolve_json_pointer``     -- RFC 6901 / dot-path resolution against parsed JSON.
``resolve_toml_pointer``     -- the same, against a parsed TOML document.
``extract_markdown_section`` -- normalized text of one Markdown heading's section.
``canonicalize``             -- the canonical byte encoding used for hashing.
``SelectorError`` and its three subclasses.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
import tomllib
from typing import Any, Final

__all__ = [
    "SelectorError",
    "SelectorNotFoundError",
    "UnsupportedFormatError",
    "MalformedFileError",
    "extract_structural_hash",
    "resolve_json_pointer",
    "resolve_toml_pointer",
    "extract_markdown_section",
    "canonicalize",
    "split_selector_target",
    "SUPPORTED_STRUCTURED_EXTENSIONS",
]


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class SelectorError(Exception):
    """Base class for every failure raised by this module."""


class SelectorNotFoundError(SelectorError, KeyError):
    """The selector is syntactically fine but names nothing in the document.

    Also raised for structurally impossible traversals (indexing a scalar,
    using a non-integer segment on an array, an out-of-range index).

    Inherits from :class:`KeyError` so existing ``except KeyError`` call sites
    around dict-ish lookups keep working.
    """

    def __str__(self) -> str:  # KeyError.__str__ would repr() the message
        return SelectorError.__str__(self)


class UnsupportedFormatError(SelectorError):
    """A sub-tree selector was applied to a file type that has no sub-trees.

    Whole-file hashing works for every extension; only ``.json``, ``.toml`` and
    ``.md``/``.markdown`` support a ``#selector``.
    """


class MalformedFileError(SelectorError):
    """The file could not be decoded or parsed as its declared format."""


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Extensions (normalized, no leading dot) that accept a ``#selector``.
SUPPORTED_STRUCTURED_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {"json", "toml", "md", "markdown"}
)

#: Domain-separation tag for canonical *value* digests (JSON and TOML alike).
#: Two documents in different formats that resolve to the same logical value
#: therefore produce the same hash -- a useful property when a project migrates
#: ``package.json`` metadata into ``pyproject.toml``.
_VALUE_DOMAIN: Final[bytes] = b"structural-selector/v1/value\n"

#: Domain-separation tag for Markdown section digests.
_MARKDOWN_DOMAIN: Final[bytes] = b"structural-selector/v1/markdown\n"

#: Key used to tag TOML temporal values, which have no native JSON encoding.
_TEMPORAL_TAG: Final[str] = "$structural-selector/temporal"

_HASH_PREFIX: Final[str] = "sha256:"


# ---------------------------------------------------------------------------
# Selector parsing
# ---------------------------------------------------------------------------


def split_selector_target(target: str) -> tuple[str, str | None]:
    """Split ``"path/to/file.json#a.b"`` into ``("path/to/file.json", "a.b")``.

    Splits on the *first* ``#`` only, so selectors may contain ``#`` themselves
    (Markdown queries such as ``spec.md##2-auth`` or ``spec.md#§2``). A target
    with no ``#``, or with an empty selector, yields ``None`` for the selector,
    meaning "whole file".
    """
    path, sep, selector = target.partition("#")
    if not sep or not selector:
        return path, None
    return path, selector


def _parse_dot_path(key_path: str) -> list[str]:
    """Split a dot-path into segments, honouring ``\\.`` and ``\\\\`` escapes.

    ``a.b``      -> ``["a", "b"]``
    ``a\\.b.c``   -> ``["a.b", "c"]``
    ``a\\\\.b``    -> ``["a\\\\", "b"]``

    A trailing lone backslash is kept verbatim rather than treated as an error;
    the segment simply will not match any key.
    """
    segments: list[str] = []
    current: list[str] = []
    index = 0
    length = len(key_path)
    while index < length:
        char = key_path[index]
        if char == "\\" and index + 1 < length and key_path[index + 1] in ".\\":
            current.append(key_path[index + 1])
            index += 2
            continue
        if char == ".":
            segments.append("".join(current))
            current = []
            index += 1
            continue
        current.append(char)
        index += 1
    segments.append("".join(current))
    return segments


def _parse_json_pointer(key_path: str) -> list[str]:
    """Split an RFC 6901 pointer into unescaped reference tokens."""
    if key_path == "":
        return []
    # key_path is known to start with "/" here; the leading empty piece is dropped.
    return [
        token.replace("~1", "/").replace("~0", "~")
        for token in key_path.split("/")[1:]
    ]


def _parse_key_path(key_path: str) -> list[str]:
    """Parse either notation. A leading ``/`` selects RFC 6901, else dot-path."""
    if key_path == "" or key_path.startswith("/"):
        return _parse_json_pointer(key_path)
    return _parse_dot_path(key_path)


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------


def _resolve(data: Any, key_path: str, kind: str) -> Any:
    segments = _parse_key_path(key_path)
    node: Any = data
    for depth, segment in enumerate(segments):
        if isinstance(node, dict):
            try:
                node = node[segment]
            except KeyError:
                raise SelectorNotFoundError(
                    f"{kind} selector {key_path!r}: key {segment!r} not found "
                    f"at {_describe(segments[:depth])}"
                ) from None
        elif isinstance(node, list):
            if not _is_index(segment):
                raise SelectorNotFoundError(
                    f"{kind} selector {key_path!r}: segment {segment!r} is not a "
                    f"non-negative array index at {_describe(segments[:depth])}"
                )
            position = int(segment)
            if position >= len(node):
                raise SelectorNotFoundError(
                    f"{kind} selector {key_path!r}: index {position} out of range "
                    f"(length {len(node)}) at {_describe(segments[:depth])}"
                )
            node = node[position]
        else:
            raise SelectorNotFoundError(
                f"{kind} selector {key_path!r}: cannot descend into "
                f"{type(node).__name__} at {_describe(segments[:depth])}"
            )
    return node


def _describe(segments: list[str]) -> str:
    """Human-readable breadcrumb for error messages."""
    return "<root>" if not segments else ".".join(segments)


_INDEX_RE: Final[re.Pattern[str]] = re.compile(r"\A(?:0|[1-9][0-9]*)\Z")


def _is_index(segment: str) -> bool:
    """True for canonical non-negative integers only (rejects ``01``, ``-1``, ``+1``)."""
    return _INDEX_RE.match(segment) is not None


def resolve_json_pointer(data: dict[str, Any] | list[Any], key_path: str) -> Any:
    """Resolve ``key_path`` against parsed JSON ``data``.

    Accepts RFC 6901 (``/dependencies/stripe``, ``""`` for the whole document)
    or dot-notation (``dependencies.stripe``, ``items.0.name``). Array segments
    must be canonical non-negative integers.

    Raises:
        SelectorNotFoundError: the path names nothing, or traversal is impossible.
    """
    return _resolve(data, key_path, "JSON")


def resolve_toml_pointer(data: dict[str, Any], key_path: str) -> Any:
    """Resolve ``key_path`` against a parsed TOML document.

    Identical semantics to :func:`resolve_json_pointer`; TOML tables are dicts
    and arrays-of-tables are lists, so ``tool.ruff.lint`` and
    ``/tool/ruff/lint`` both work, as does ``build.targets.0.name``.

    Raises:
        SelectorNotFoundError: the path names nothing, or traversal is impossible.
    """
    return _resolve(data, key_path, "TOML")


# ---------------------------------------------------------------------------
# Canonicalization
# ---------------------------------------------------------------------------


def _encode_special(value: Any) -> Any:
    """``json.dumps`` fallback for TOML's native date/time values."""
    if isinstance(value, _dt.datetime):
        return {_TEMPORAL_TAG: f"datetime:{value.isoformat()}"}
    if isinstance(value, _dt.date):
        return {_TEMPORAL_TAG: f"date:{value.isoformat()}"}
    if isinstance(value, _dt.time):
        return {_TEMPORAL_TAG: f"time:{value.isoformat()}"}
    raise MalformedFileError(
        f"value of type {type(value).__name__} has no canonical encoding"
    )


def canonicalize(value: Any) -> bytes:
    """Serialize a resolved value to its canonical UTF-8 byte form.

    Mappings are emitted with sorted keys and no insignificant whitespace, so
    key order and indentation in the source file cannot reach the digest.
    Sequences keep their order -- reordering a JSON array *is* a semantic change.

    Raises:
        MalformedFileError: the value contains a non-finite float (``NaN``,
            ``Infinity``) or a type with no canonical encoding.
    """
    try:
        text = json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
            default=_encode_special,
        )
    except ValueError as exc:  # non-finite floats, circular refs
        raise MalformedFileError(f"value is not canonicalizable: {exc}") from exc
    return text.encode("utf-8")


def _digest(domain: bytes, payload: bytes) -> str:
    hasher = hashlib.sha256()
    hasher.update(domain)
    hasher.update(payload)
    return _HASH_PREFIX + hasher.hexdigest()


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

_ATX_HEADING_RE: Final[re.Pattern[str]] = re.compile(
    r"\A {0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*\Z"
)
_FENCE_RE: Final[re.Pattern[str]] = re.compile(r"\A {0,3}(`{3,}|~{3,})(.*)\Z")
_CLOSING_HASHES_RE: Final[re.Pattern[str]] = re.compile(r"[ \t]+#+\Z")
_SLUG_STRIP_RE: Final[re.Pattern[str]] = re.compile(r"[^\w]+", re.UNICODE)
_WHITESPACE_RE: Final[re.Pattern[str]] = re.compile(r"\s+")


def _slugify(text: str) -> str:
    """GitHub-ish anchor slug: lowercase, non-word runs collapsed to ``-``."""
    return _SLUG_STRIP_RE.sub("-", text.strip().lower()).strip("-")


def _normalize_title(text: str) -> str:
    """Collapse internal whitespace so ``##  A   B`` == ``## A B``."""
    return _WHITESPACE_RE.sub(" ", text.strip())


def _iter_headings(lines: list[str]) -> list[tuple[int, int, str]]:
    """Return ``(line_index, level, title)`` for every ATX heading outside fences.

    Setext (underlined) headings are intentionally out of scope; see the spec.
    """
    headings: list[tuple[int, int, str]] = []
    fence: str | None = None
    for index, line in enumerate(lines):
        fence_match = _FENCE_RE.match(line)
        if fence_match is not None:
            marker = fence_match.group(1)
            if fence is None:
                fence = marker
                continue
            # A closing fence uses the same character, is at least as long, and
            # carries no info string.
            if (
                marker[0] == fence[0]
                and len(marker) >= len(fence)
                and not fence_match.group(2).strip()
            ):
                fence = None
            continue
        if fence is not None:
            continue
        heading_match = _ATX_HEADING_RE.match(line)
        if heading_match is None:
            continue
        raw_title = heading_match.group(2) or ""
        raw_title = _CLOSING_HASHES_RE.sub("", raw_title)
        headings.append((index, len(heading_match.group(1)), _normalize_title(raw_title)))
    return headings


def extract_markdown_section(text: str, heading_query: str) -> str:
    """Return the normalized text of the section introduced by ``heading_query``.

    The section spans the heading line itself through everything below it, up to
    (but excluding) the next heading of equal or higher level. Nested
    subsections are therefore included.

    ``heading_query`` may be the heading's literal title, or its anchor slug.
    Leading ``§`` and ``#`` characters are stripped from the query, so
    ``§2-session-management``, ``2-session-management`` and
    ``2. Session Management`` all select ``## 2. Session Management``.

    Matching is case-insensitive and whitespace-insensitive. Where several
    headings match, the first in document order wins.

    Normalization applied to the returned text: CRLF/CR line endings become LF,
    the heading is rewritten as ``<hashes> <collapsed title>``, trailing
    whitespace is stripped from every line, and leading/trailing blank lines are
    removed. The result has no trailing newline.

    Raises:
        SelectorNotFoundError: no heading matches the query.
    """
    normalized_text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized_text.split("\n")
    headings = _iter_headings(lines)

    query = heading_query.strip().lstrip("#").lstrip("§").strip()
    query_slug = _slugify(query)
    query_title = _normalize_title(query).casefold()

    match: tuple[int, int, str] | None = None
    for position, (line_index, level, title) in enumerate(headings):
        if title.casefold() == query_title or _slugify(title) == query_slug:
            match = (position, line_index, level)
            break

    if match is None:
        raise SelectorNotFoundError(
            f"Markdown selector {heading_query!r}: no heading matches "
            f"(title or slug {query_slug!r})"
        )

    position, start, level = match
    end = len(lines)
    for line_index, other_level, _title in headings[position + 1 :]:
        if other_level <= level:
            end = line_index
            break

    body = [line.rstrip() for line in lines[start:end]]
    body[0] = f"{'#' * level} {headings[position][2]}".rstrip()

    while body and not body[-1]:
        body.pop()
    while len(body) > 1 and not body[1]:
        del body[1]

    return "\n".join(body)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _normalize_extension(file_ext: str) -> str:
    return file_ext.strip().lstrip(".").lower()


def _decode(file_content_bytes: bytes, label: str) -> str:
    try:
        return file_content_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MalformedFileError(f"{label} file is not valid UTF-8: {exc}") from exc


def extract_structural_hash(
    file_content_bytes: bytes,
    file_ext: str,
    selector: str | None,
) -> str:
    """Hash either a whole file or the sub-tree named by ``selector``.

    Args:
        file_content_bytes: Raw file bytes, exactly as read from disk.
        file_ext: The file's extension, with or without a leading dot, any case
            (``".JSON"``, ``"json"``, ``".md"`` are all accepted).
        selector: ``None`` or ``""`` hashes the raw bytes. Otherwise a JSON/TOML
            key-path or a Markdown heading query.

    Returns:
        ``"sha256:<64-hex>"``.

        With no selector this is the plain SHA-256 of the file bytes, so it
        matches ``sha256sum``. With a selector it is the SHA-256 of a
        domain-separated canonical encoding of the sub-tree -- see
        :func:`canonicalize` and :func:`extract_markdown_section`.

    Raises:
        UnsupportedFormatError: a selector was given for a format without
            sub-tree support (``.py``, ``.ts``, ...).
        MalformedFileError: the file is not valid UTF-8, does not parse, or
            resolves to a non-canonicalizable value.
        SelectorNotFoundError: the selector names nothing in the document.
    """
    if not selector:
        return _HASH_PREFIX + hashlib.sha256(file_content_bytes).hexdigest()

    extension = _normalize_extension(file_ext)

    if extension == "json":
        try:
            document = json.loads(file_content_bytes)
        except UnicodeDecodeError as exc:
            raise MalformedFileError(f"JSON file is not valid UTF-8: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise MalformedFileError(f"invalid JSON: {exc}") from exc
        return _digest(_VALUE_DOMAIN, canonicalize(resolve_json_pointer(document, selector)))

    if extension == "toml":
        try:
            document = tomllib.loads(_decode(file_content_bytes, "TOML"))
        except tomllib.TOMLDecodeError as exc:
            raise MalformedFileError(f"invalid TOML: {exc}") from exc
        return _digest(_VALUE_DOMAIN, canonicalize(resolve_toml_pointer(document, selector)))

    if extension in ("md", "markdown"):
        section = extract_markdown_section(_decode(file_content_bytes, "Markdown"), selector)
        return _digest(_MARKDOWN_DOMAIN, section.encode("utf-8"))

    raise UnsupportedFormatError(
        f"file extension {file_ext!r} has no sub-tree selector support; "
        f"supported: {', '.join(sorted(SUPPORTED_STRUCTURED_EXTENSIONS))} "
        f"(omit the selector to hash the whole file)"
    )
