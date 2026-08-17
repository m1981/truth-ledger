"""test-structural.py -- test matrix for truthlib.structural.

The suite is organized around the property that actually matters for policy
anchors: *isolation*. A selector's hash must change when -- and only when -- the
sub-tree it names changes.
"""

from __future__ import annotations

import datetime
import hashlib
import re
import time
import unittest

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.dirname(HERE)
if TEMPLATE_DIR not in sys.path:          # `truthlib` lives under template/
    sys.path.insert(0, TEMPLATE_DIR)

from truthlib.structural import (
    SUPPORTED_STRUCTURED_EXTENSIONS,
    MalformedFileError,
    SelectorNotFoundError,
    UnsupportedFormatError,
    canonicalize,
    extract_markdown_section,
    extract_structural_hash,
    resolve_json_pointer,
    resolve_toml_pointer,
    split_selector_target,
)

HASH_RE = re.compile(r"\Asha256:[0-9a-f]{64}\Z")


def h(content: str, ext: str, selector: str | None = None) -> str:
    return extract_structural_hash(content.encode("utf-8"), ext, selector)


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

PACKAGE_JSON = """
{
  "name": "billing-api",
  "version": "4.2.0",
  "dependencies": {
    "stripe": "^14.1.0",
    "zod": "^3.22.4"
  },
  "devDependencies": {
    "vitest": "^1.2.0"
  }
}
"""

PYPROJECT_TOML = """
[project]
name = "truth-ledger"
version = "0.9.1"

[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I"]
ignore = ["E501"]

[tool.pytest.ini_options]
addopts = "-q"
"""

SPEC_MD = """# Protocol Specification

Intro paragraph.

## 1. Transport

Transport rules go here.

## 2. Session Management

Sessions expire after 30 minutes.

### 2.1 Refresh

Refresh tokens rotate on use.

## 3. Errors

Error taxonomy.

## 4. Compatibility

Two same-level headings must follow section 2, or a terminator search that
takes the LAST match instead of the FIRST reads as correct.
"""


# --------------------------------------------------------------------------
# Whole-file hashing
# --------------------------------------------------------------------------


class WholeFileTests(unittest.TestCase):
    def test_no_selector_is_plain_sha256_of_bytes(self) -> None:
        payload = b"export const x = 1;\n"
        expected = "sha256:" + hashlib.sha256(payload).hexdigest()
        self.assertEqual(extract_structural_hash(payload, "ts", None), expected)

    def test_empty_selector_is_treated_as_whole_file(self) -> None:
        payload = b'{"a": 1}'
        self.assertEqual(
            extract_structural_hash(payload, "json", ""),
            extract_structural_hash(payload, "json", None),
        )

    def test_whole_file_hash_is_formatting_sensitive(self) -> None:
        self.assertNotEqual(h('{"a":1}', "json"), h('{ "a": 1 }', "json"))

    def test_whole_file_works_for_any_extension(self) -> None:
        for ext in ("py", "ts", "rs", "", "weird"):
            with self.subTest(ext=ext):
                self.assertRegex(h("content", ext), HASH_RE)

    def test_hash_format(self) -> None:
        self.assertRegex(h(PACKAGE_JSON, "json", "dependencies"), HASH_RE)


# --------------------------------------------------------------------------
# JSON key isolation
# --------------------------------------------------------------------------


class JsonIsolationTests(unittest.TestCase):
    def test_scalar_lookup_dot_path(self) -> None:
        self.assertRegex(h(PACKAGE_JSON, "json", "dependencies.stripe"), HASH_RE)

    def test_dot_path_and_json_pointer_agree(self) -> None:
        self.assertEqual(
            h(PACKAGE_JSON, "json", "dependencies.stripe"),
            h(PACKAGE_JSON, "json", "/dependencies/stripe"),
        )

    def test_unselected_key_change_does_not_alter_hash(self) -> None:
        mutated = PACKAGE_JSON.replace('"version": "4.2.0"', '"version": "9.9.9"')
        self.assertEqual(
            h(PACKAGE_JSON, "json", "dependencies"),
            h(mutated, "json", "dependencies"),
        )

    def test_sibling_table_change_does_not_alter_hash(self) -> None:
        mutated = PACKAGE_JSON.replace('"vitest": "^1.2.0"', '"vitest": "^2.0.0"')
        self.assertEqual(
            h(PACKAGE_JSON, "json", "dependencies"),
            h(mutated, "json", "dependencies"),
        )

    def test_target_key_change_alters_hash(self) -> None:
        mutated = PACKAGE_JSON.replace('"stripe": "^14.1.0"', '"stripe": "^15.0.0"')
        self.assertNotEqual(
            h(PACKAGE_JSON, "json", "dependencies.stripe"),
            h(mutated, "json", "dependencies.stripe"),
        )

    def test_adding_key_to_target_subtree_alters_hash(self) -> None:
        mutated = PACKAGE_JSON.replace('"zod": "^3.22.4"', '"zod": "^3.22.4", "ky": "^1.0.0"')
        self.assertNotEqual(
            h(PACKAGE_JSON, "json", "dependencies"),
            h(mutated, "json", "dependencies"),
        )

    def test_key_order_swap_is_canonical(self) -> None:
        a = '{"dependencies": {"stripe": "1", "zod": "2"}}'
        b = '{"dependencies": {"zod": "2", "stripe": "1"}}'
        self.assertEqual(h(a, "json", "dependencies"), h(b, "json", "dependencies"))

    def test_indentation_is_canonical(self) -> None:
        a = '{"cfg":{"a":1,"b":[1,2]}}'
        b = '{\n  "cfg" : {\n     "a" :  1,\n     "b" : [ 1, 2 ]\n  }\n}'
        self.assertEqual(h(a, "json", "cfg"), h(b, "json", "cfg"))

    def test_root_pointer_canonicalizes_whole_document(self) -> None:
        # RFC 6901 root is "", not "/" (which names the key ""). Since an empty
        # selector means "whole file", root canonicalization is reached through
        # the resolver directly.
        a = resolve_json_pointer({"a": 1, "b": 2}, "")
        b = resolve_json_pointer({"b": 2, "a": 1}, "")
        self.assertEqual(canonicalize(a), canonicalize(b))

    def test_nested_subtree(self) -> None:
        doc = '{"auth": {"token_expiry": {"access": 900, "refresh": 604800}}}'
        self.assertRegex(h(doc, "json", "auth.token_expiry"), HASH_RE)

    def test_array_index(self) -> None:
        doc = '{"items": [{"name": "a"}, {"name": "b"}]}'
        self.assertEqual(
            h(doc, "json", "items.0.name"),
            h('{"items": [{"name": "a"}, {"name": "zzz"}]}', "json", "items.0.name"),
        )

    def test_array_order_is_semantic(self) -> None:
        a = '{"items": [1, 2, 3]}'
        b = '{"items": [3, 2, 1]}'
        self.assertNotEqual(h(a, "json", "items"), h(b, "json", "items"))

    def test_booleans_and_null_are_distinct(self) -> None:
        hashes = {
            h('{"v": true}', "json", "v"),
            h('{"v": false}', "json", "v"),
            h('{"v": null}', "json", "v"),
            h('{"v": "true"}', "json", "v"),
        }
        self.assertEqual(len(hashes), 4)

    def test_int_and_float_are_distinct(self) -> None:
        self.assertNotEqual(h('{"v": 1}', "json", "v"), h('{"v": 1.0}', "json", "v"))

    def test_float_notation_is_canonical(self) -> None:
        self.assertEqual(h('{"v": 1.5}', "json", "v"), h('{"v": 1.50}', "json", "v"))
        self.assertEqual(h('{"v": 100.0}', "json", "v"), h('{"v": 1.0e2}', "json", "v"))

    def test_unicode_value(self) -> None:
        self.assertRegex(h('{"greeting": "héllo — 世界 🎯"}', "json", "greeting"), HASH_RE)

    def test_unicode_escape_is_canonical(self) -> None:
        self.assertEqual(
            h('{"v": "caf\\u00e9"}', "json", "v"),
            h('{"v": "café"}', "json", "v"),
        )

    def test_unicode_key_lookup(self) -> None:
        self.assertRegex(h('{"クエリ": {"n": 1}}', "json", "クエリ"), HASH_RE)

    def test_nested_arrays(self) -> None:
        doc = '{"matrix": [[1, 2], [3, [4, 5]]]}'
        self.assertEqual(
            resolve_json_pointer({"matrix": [[1, 2], [3, [4, 5]]]}, "matrix.1.1.0"), 4
        )
        self.assertRegex(h(doc, "json", "matrix.1.1"), HASH_RE)

    def test_escaped_dot_in_key(self) -> None:
        doc = '{"a.b": {"c": 1}, "a": {"b": {"c": 2}}}'
        self.assertNotEqual(h(doc, "json", r"a\.b"), h(doc, "json", "a.b"))
        self.assertEqual(resolve_json_pointer({"a.b": 42}, r"a\.b"), 42)

    def test_escaped_backslash_in_key(self) -> None:
        self.assertEqual(resolve_json_pointer({"a\\": {"b": 7}}, r"a\\.b"), 7)

    def test_escape_at_the_very_end_of_the_path(self) -> None:
        """A path ending in an escaped dot: the lookahead must still fire.

        `a\\.` is the key "a." -- one segment, not ["a\\", ""]. This is the
        boundary an off-by-one in the escape lookahead gets wrong while every
        mid-path escape keeps working.
        """
        self.assertEqual(resolve_json_pointer({"a.": 1, "a": {"": 2}}, "a\\."), 1)

    def test_backslash_before_an_unescapable_char_is_literal(self) -> None:
        """Only `\\.` and `\\\\` are escapes. `\\x` is two literal characters.

        The escape set is a membership test, so widening it is invisible until
        a backslash meets a character that was never meant to be escapable.
        """
        for char in ("x", "X", "n", "1", "/", "~", " ", "\t", "-"):
            with self.subTest(char=char):
                key = "a\\" + char
                self.assertEqual(resolve_json_pointer({key: 1, "a" + char: 2},
                                                      key), 1)

    def test_trailing_lone_backslash_is_literal(self) -> None:
        """A dangling backslash has nothing to escape, so it IS the key.

        The lookahead must be bounds-checked before indexing: reading one past
        the end here is an IndexError, not a miss.
        """
        self.assertEqual(resolve_json_pointer({"a\\": 1}, "a\\"), 1)
        self.assertEqual(resolve_json_pointer({"\\": 1}, "\\"), 1)

    def test_rfc6901_escapes(self) -> None:
        data = {"a/b": 1, "m~n": 2}
        self.assertEqual(resolve_json_pointer(data, "/a~1b"), 1)
        self.assertEqual(resolve_json_pointer(data, "/m~0n"), 2)

    def test_empty_pointer_returns_whole_document(self) -> None:
        data = {"a": 1}
        self.assertIs(resolve_json_pointer(data, ""), data)

    def test_empty_string_key(self) -> None:
        self.assertEqual(resolve_json_pointer({"": 5}, "/"), 5)


# --------------------------------------------------------------------------
# JSON errors
# --------------------------------------------------------------------------


class JsonErrorTests(unittest.TestCase):
    def test_missing_key(self) -> None:
        with self.assertRaises(SelectorNotFoundError):
            h(PACKAGE_JSON, "json", "dependencies.nope")

    def test_index_out_of_range(self) -> None:
        with self.assertRaises(SelectorNotFoundError):
            h('{"items": [1]}', "json", "items.5")

    def test_non_index_segment_on_array(self) -> None:
        with self.assertRaises(SelectorNotFoundError):
            h('{"items": [1]}', "json", "items.name")

    def test_index_exactly_one_past_the_end(self) -> None:
        """The `>= len` boundary, not just a wildly out-of-range index.

        `items.2` on a 2-element array is the only index that tells `>=` apart
        from `>`, and getting it wrong raises IndexError instead of the
        module's own error -- a different failure mode for a caller.
        """
        with self.assertRaises(SelectorNotFoundError):
            h('{"items": [1, 2]}', "json", "items.2")
        self.assertEqual(resolve_json_pointer({"items": [1, 2]}, "items.1"), 2)

    def test_negative_and_padded_indices_rejected(self) -> None:
        for bad in ("items.-1", "items.01", "items.+0"):
            with self.subTest(selector=bad), self.assertRaises(SelectorNotFoundError):
                h('{"items": [1, 2]}', "json", bad)

    def test_descend_into_scalar(self) -> None:
        with self.assertRaises(SelectorNotFoundError):
            h('{"a": 1}', "json", "a.b")

    def test_error_message_names_the_selector(self) -> None:
        with self.assertRaises(SelectorNotFoundError) as ctx:
            h(PACKAGE_JSON, "json", "dependencies.nope")
        self.assertIn("dependencies.nope", str(ctx.exception))

    def test_error_message_breadcrumb_locates_the_failure(self) -> None:
        """The breadcrumb is the contract (spec section 5), not decoration.

        `key 'x' not found at <root>` and `... at dependencies` are what tell
        a caller WHERE a long path broke, so both ends of the breadcrumb are
        pinned -- otherwise the two collapse into each other unnoticed.
        """
        with self.assertRaises(SelectorNotFoundError) as top:
            h(PACKAGE_JSON, "json", "nope")
        self.assertEqual(
            str(top.exception),
            "JSON selector 'nope': key 'nope' not found at <root>")

        with self.assertRaises(SelectorNotFoundError) as nested:
            h(PACKAGE_JSON, "json", "dependencies.nope")
        self.assertEqual(
            str(nested.exception),
            "JSON selector 'dependencies.nope': key 'nope' not found "
            "at dependencies")

        # a one-segment breadcrumb renders the same whatever joins it, so the
        # separator is only pinned once the trail is at least two deep
        deep = '{"a": {"b": {"c": 1}}}'
        with self.assertRaises(SelectorNotFoundError) as ctx:
            h(deep, "json", "a.b.nope")
        self.assertEqual(
            str(ctx.exception),
            "JSON selector 'a.b.nope': key 'nope' not found at a.b")

    def test_malformed_json(self) -> None:
        with self.assertRaises(MalformedFileError):
            h('{"a": ', "json", "a")

    def test_invalid_utf8(self) -> None:
        with self.assertRaises(MalformedFileError):
            extract_structural_hash(b'{"a": "\xff\xfe"}', "json", "a")

    def test_non_finite_number_rejected(self) -> None:
        with self.assertRaises(MalformedFileError):
            h('{"v": NaN}', "json", "v")

    def test_unsupported_type_rejected_by_canonicalize(self) -> None:
        with self.assertRaises(MalformedFileError):
            canonicalize({"v": object()})


# --------------------------------------------------------------------------
# Canonical encoding -- the byte contract
# --------------------------------------------------------------------------


class CanonicalEncodingTests(unittest.TestCase):
    """The encoding itself, pinned to exact bytes.

    Every other test compares one hash against another, which proves the
    encoder is CONSISTENT but not that it is the encoder we specified: flip
    `sort_keys`, `ensure_ascii` or the separators and both sides move
    together, so equality still holds and the digests silently change for
    every stored anchor. These assertions are the ones that would notice.
    """

    def test_mappings_sort_and_carry_no_whitespace(self) -> None:
        self.assertEqual(
            canonicalize({"b": 1, "a": [1, 2], "A": None}),
            b'{"A":null,"a":[1,2],"b":1}')

    def test_nested_mappings_sort_at_every_depth(self) -> None:
        self.assertEqual(
            canonicalize({"z": {"y": 1, "x": 2}}),
            b'{"z":{"x":2,"y":1}}')

    def test_non_ascii_is_emitted_literally_not_escaped(self) -> None:
        self.assertEqual(canonicalize("café"), '"café"'.encode("utf-8"))
        self.assertEqual(canonicalize("世界"), '"世界"'.encode("utf-8"))

    def test_sequences_keep_source_order(self) -> None:
        self.assertEqual(canonicalize(["b", "a"]), b'["b","a"]')

    def test_temporal_values_carry_their_tag_and_type(self) -> None:
        """TOML's dates have no JSON form, so the tag IS the encoding.

        A blank or drifting tag still round-trips deterministically, which is
        why this is pinned to bytes rather than to self-consistency.
        """
        self.assertEqual(
            canonicalize(datetime.date(2026, 8, 17)),
            b'{"$structural-selector/temporal":"date:2026-08-17"}')
        self.assertEqual(
            canonicalize(datetime.time(9, 30)),
            b'{"$structural-selector/temporal":"time:09:30:00"}')
        self.assertEqual(
            canonicalize(datetime.datetime(2026, 8, 17, 9, 30,
                                           tzinfo=datetime.timezone.utc)),
            b'{"$structural-selector/temporal":'
            b'"datetime:2026-08-17T09:30:00+00:00"}')

    def test_datetime_is_tagged_before_date(self) -> None:
        """datetime subclasses date -- the isinstance order is load-bearing."""
        self.assertIn(b'"datetime:', canonicalize(datetime.datetime(2026, 8, 17)))


# --------------------------------------------------------------------------
# TOML
# --------------------------------------------------------------------------


class TomlTests(unittest.TestCase):
    def test_nested_table(self) -> None:
        self.assertRegex(h(PYPROJECT_TOML, "toml", "tool.ruff.lint"), HASH_RE)

    def test_adjacent_table_change_does_not_alter_hash(self) -> None:
        mutated = PYPROJECT_TOML.replace('addopts = "-q"', 'addopts = "-vv"')
        self.assertEqual(
            h(PYPROJECT_TOML, "toml", "tool.ruff.lint"),
            h(mutated, "toml", "tool.ruff.lint"),
        )

    def test_parent_scalar_change_does_not_alter_child_hash(self) -> None:
        mutated = PYPROJECT_TOML.replace("line-length = 100", "line-length = 88")
        self.assertEqual(
            h(PYPROJECT_TOML, "toml", "tool.ruff.lint"),
            h(mutated, "toml", "tool.ruff.lint"),
        )
        self.assertNotEqual(
            h(PYPROJECT_TOML, "toml", "tool.ruff"),
            h(mutated, "toml", "tool.ruff"),
        )

    def test_target_table_change_alters_hash(self) -> None:
        mutated = PYPROJECT_TOML.replace('ignore = ["E501"]', 'ignore = []')
        self.assertNotEqual(
            h(PYPROJECT_TOML, "toml", "tool.ruff.lint"),
            h(mutated, "toml", "tool.ruff.lint"),
        )

    def test_inline_table_equals_expanded_table(self) -> None:
        inline = 'deps = { serde = "1.0", tokio = "1.35" }'
        expanded = '[deps]\ntokio = "1.35"\nserde = "1.0"\n'
        self.assertEqual(h(inline, "toml", "deps"), h(expanded, "toml", "deps"))

    def test_dotted_keys_equal_table_syntax(self) -> None:
        dotted = 'tool.ruff.lint.select = ["E"]\n'
        tabled = '[tool.ruff.lint]\nselect = ["E"]\n'
        self.assertEqual(h(dotted, "toml", "tool.ruff.lint"), h(tabled, "toml", "tool.ruff.lint"))

    def test_array_of_tables_index(self) -> None:
        doc = '[[bin]]\nname = "a"\n\n[[bin]]\nname = "b"\n'
        self.assertEqual(resolve_toml_pointer({"bin": [{"name": "a"}]}, "bin.0.name"), "a")
        self.assertNotEqual(h(doc, "toml", "bin.0"), h(doc, "toml", "bin.1"))

    def test_json_pointer_syntax_on_toml(self) -> None:
        self.assertEqual(
            h(PYPROJECT_TOML, "toml", "tool.ruff.lint"),
            h(PYPROJECT_TOML, "toml", "/tool/ruff/lint"),
        )

    def test_temporal_values_are_canonicalizable(self) -> None:
        doc = "[meta]\nreleased = 2026-08-17T09:30:00Z\nday = 2026-08-17\nat = 09:30:00\n"
        self.assertRegex(h(doc, "toml", "meta"), HASH_RE)
        self.assertEqual(h(doc, "toml", "meta"), h(doc, "toml", "meta"))

    def test_temporal_value_change_alters_hash(self) -> None:
        a = "[meta]\nday = 2026-08-17\n"
        b = "[meta]\nday = 2026-08-18\n"
        self.assertNotEqual(h(a, "toml", "meta"), h(b, "toml", "meta"))

    def test_comment_and_whitespace_changes_are_canonical(self) -> None:
        a = '[deps]\n# pinned for CVE-2026-1\nserde = "1.0"\n'
        b = '[deps]\n\n\nserde   =    "1.0"\n'
        self.assertEqual(h(a, "toml", "deps"), h(b, "toml", "deps"))

    def test_cross_format_value_equality(self) -> None:
        self.assertEqual(
            h('{"deps": {"serde": "1.0"}}', "json", "deps"),
            h('[deps]\nserde = "1.0"\n', "toml", "deps"),
        )

    def test_malformed_toml(self) -> None:
        with self.assertRaises(MalformedFileError):
            h("[tool\nbroken", "toml", "tool")

    def test_missing_toml_key(self) -> None:
        with self.assertRaises(SelectorNotFoundError):
            h(PYPROJECT_TOML, "toml", "tool.mypy")

    def test_toml_invalid_utf8(self) -> None:
        with self.assertRaises(MalformedFileError):
            extract_structural_hash(b'name = "\xff"', "toml", "name")


# --------------------------------------------------------------------------
# Markdown
# --------------------------------------------------------------------------


class MarkdownTests(unittest.TestCase):
    def test_section_body_extracted(self) -> None:
        section = extract_markdown_section(SPEC_MD, "2-session-management")
        self.assertTrue(section.startswith("## 2. Session Management"))
        self.assertIn("Sessions expire after 30 minutes.", section)

    def test_subsections_are_included(self) -> None:
        section = extract_markdown_section(SPEC_MD, "2-session-management")
        self.assertIn("### 2.1 Refresh", section)
        self.assertIn("Refresh tokens rotate on use.", section)

    def test_next_equal_level_heading_terminates(self) -> None:
        section = extract_markdown_section(SPEC_MD, "2-session-management")
        self.assertNotIn("Error taxonomy", section)
        self.assertNotIn("## 3. Errors", section)

    def test_preceding_section_excluded(self) -> None:
        section = extract_markdown_section(SPEC_MD, "2-session-management")
        self.assertNotIn("Transport rules", section)

    def test_section_isolation(self) -> None:
        mutated = SPEC_MD.replace("Transport rules go here.", "Totally rewritten transport.")
        self.assertEqual(
            h(SPEC_MD, "md", "2-session-management"),
            h(mutated, "md", "2-session-management"),
        )

    def test_target_section_change_alters_hash(self) -> None:
        mutated = SPEC_MD.replace("expire after 30 minutes", "expire after 5 minutes")
        self.assertNotEqual(
            h(SPEC_MD, "md", "2-session-management"),
            h(mutated, "md", "2-session-management"),
        )

    def test_subsection_change_alters_parent_hash(self) -> None:
        mutated = SPEC_MD.replace("rotate on use", "are single-use")
        self.assertNotEqual(
            h(SPEC_MD, "md", "2-session-management"),
            h(mutated, "md", "2-session-management"),
        )

    def test_section_symbol_prefix_accepted(self) -> None:
        self.assertEqual(
            h(SPEC_MD, "md", "§2-session-management"),
            h(SPEC_MD, "md", "2-session-management"),
        )

    def test_literal_title_query_accepted(self) -> None:
        self.assertEqual(
            h(SPEC_MD, "md", "2. Session Management"),
            h(SPEC_MD, "md", "2-session-management"),
        )

    def test_query_is_case_insensitive(self) -> None:
        self.assertEqual(
            h(SPEC_MD, "md", "2. SESSION management"),
            h(SPEC_MD, "md", "2-session-management"),
        )

    def test_hash_prefixed_query_accepted(self) -> None:
        self.assertEqual(
            h(SPEC_MD, "md", "#2-session-management"),
            h(SPEC_MD, "md", "2-session-management"),
        )

    def test_normalized_section_text_is_exact(self) -> None:
        """The normalization contract, pinned to a literal.

        Comparing two hashes only proves the normalizer treats two inputs
        alike; it passes just as well if the normalizer keeps a stray blank
        line at both ends, or eats a real one. This is the assertion that
        says which text is hashed.
        """
        self.assertEqual(
            extract_markdown_section("## A  \n\nbody\n\n\n", "a"),
            "## A\nbody")

    def test_interior_blank_lines_are_preserved(self) -> None:
        """Only LEADING and TRAILING blanks are stripped -- paragraph breaks
        inside the section are content and must survive."""
        self.assertEqual(
            extract_markdown_section("## A\n\npara one\n\npara two\n", "a"),
            "## A\npara one\n\npara two")

    def test_heading_only_section_has_no_body(self) -> None:
        """A section with nothing under it normalizes to just its heading.

        The one-line body is also the case where a leading-blank strip that
        does not bounds-check reads past the end of the section.
        """
        self.assertEqual(
            extract_markdown_section("## A\n\n## B\n\nb body\n", "a"), "## A")

    def test_trailing_blank_lines_normalized(self) -> None:
        a = "## A\n\nbody\n"
        b = "## A\n\nbody\n\n\n\n"
        self.assertEqual(h(a, "md", "a"), h(b, "md", "a"))

    def test_trailing_whitespace_normalized(self) -> None:
        self.assertEqual(h("## A\n\nbody\n", "md", "a"), h("## A   \n\nbody   \n", "md", "a"))

    def test_heading_internal_whitespace_normalized(self) -> None:
        self.assertEqual(
            h("## Session   Management\n\nx\n", "md", "session-management"),
            h("##  Session Management\n\nx\n", "md", "session-management"),
        )

    def test_closing_hashes_heading_form(self) -> None:
        self.assertEqual(h("## A ##\n\nbody\n", "md", "a"), h("## A\n\nbody\n", "md", "a"))

    def test_crlf_is_normalized(self) -> None:
        self.assertEqual(
            h(SPEC_MD.replace("\n", "\r\n"), "md", "2-session-management"),
            h(SPEC_MD, "md", "2-session-management"),
        )

    def test_bare_cr_is_normalized(self) -> None:
        """Classic-Mac CR endings, not just CRLF -- the spec promises both.

        Asserted on the extracted text, because a CR that survives into the
        body is invisible to a hash-vs-hash comparison of two CR documents.
        """
        self.assertEqual(
            extract_markdown_section("## A\r\rbody\r", "a"), "## A\nbody")
        self.assertEqual(
            h(SPEC_MD.replace("\n", "\r"), "md", "2-session-management"),
            h(SPEC_MD, "md", "2-session-management"),
        )

    def test_query_prefix_stripping_does_not_eat_title_characters(self) -> None:
        """`#` and `§` are stripped as PREFIXES, not as a character set.

        `str.lstrip` takes a set of characters, so widening its argument by
        one letter silently truncates every query that begins with that
        letter -- and the heading it was meant to find stops resolving.
        """
        doc = "## XML Transport\n\nbody\n"
        self.assertEqual(extract_markdown_section(doc, "XML Transport"),
                         "## XML Transport\nbody")
        self.assertEqual(extract_markdown_section(doc, "#§xml-transport"),
                         "## XML Transport\nbody")

    def test_headings_inside_code_fences_are_ignored(self) -> None:
        doc = "## A\n\n```sh\n## B\necho hi\n```\n\ntail\n\n## C\n\nc body\n"
        section = extract_markdown_section(doc, "a")
        self.assertIn("## B", section)
        self.assertIn("tail", section)
        self.assertNotIn("c body", section)
        with self.assertRaises(SelectorNotFoundError):
            extract_markdown_section(doc, "b")

    def test_tilde_fences_are_honoured(self) -> None:
        doc = "## A\n\n~~~\n## B\n~~~\n\ntail\n"
        self.assertIn("## B", extract_markdown_section(doc, "a"))

    def test_a_fence_is_not_closed_by_the_other_marker_character(self) -> None:
        """`~~~` inside a ``` block is content, not the closing fence.

        Both clauses of the close test have to hold. If either alone were
        enough, the block would end early and the `## B` below it would become
        a real heading -- terminating section A and inventing a section B.
        """
        doc = "## A\n\n```\n~~~\n## B\n```\n\ntail\n"
        section = extract_markdown_section(doc, "a")
        self.assertIn("tail", section)
        self.assertIn("## B", section)
        with self.assertRaises(SelectorNotFoundError):
            extract_markdown_section(doc, "b")

    def test_a_longer_fence_is_not_closed_by_a_shorter_one(self) -> None:
        """A ``` run inside a ```` block is content: the closer must be
        at least as long as the opener."""
        doc = "## A\n\n````\n```\n## B\n````\n\ntail\n"
        section = extract_markdown_section(doc, "a")
        self.assertIn("tail", section)
        with self.assertRaises(SelectorNotFoundError):
            extract_markdown_section(doc, "b")

    def test_title_match_uses_case_FOLDING_not_lowercasing(self) -> None:
        """The one query shape the slug path cannot also serve.

        Every ASCII title query has a slug that matches too, so the title arm
        looks redundant until a character whose casefold differs from its
        lowercase appears: casefold('Straße') == 'strasse', but the slug keeps
        the ß. Delete the title comparison and this query stops resolving.
        """
        doc = "## Straße Regeln\n\nbody\n"
        self.assertEqual(extract_markdown_section(doc, "STRASSE REGELN"),
                         "## Straße Regeln\nbody")
        with self.assertRaises(SelectorNotFoundError):
            extract_markdown_section(doc, "strasse-regeln")

    def test_last_section_runs_to_end_of_file(self) -> None:
        section = extract_markdown_section(SPEC_MD, "4-compatibility")
        self.assertTrue(section.endswith("reads as correct."), repr(section[-40:]))

    def test_terminator_is_the_FIRST_equal_level_heading(self) -> None:
        """Sections 3 and 4 both terminate section 2; the nearer one wins.

        With one trailing section a search that kept scanning would still
        land on the right line, which is why SPEC_MD carries four.
        """
        section = extract_markdown_section(SPEC_MD, "2-session-management")
        self.assertNotIn("Error taxonomy", section)
        self.assertNotIn("Compatibility", section)
        self.assertTrue(section.endswith("Refresh tokens rotate on use."),
                        repr(section[-40:]))

    def test_higher_level_heading_terminates_subsection(self) -> None:
        section = extract_markdown_section(SPEC_MD, "2-1-refresh")
        self.assertIn("Refresh tokens rotate on use.", section)
        self.assertNotIn("Error taxonomy", section)

    def test_unicode_heading(self) -> None:
        doc = "## Café — Résumé\n\nbody\n"
        self.assertRegex(h(doc, "md", "café-résumé"), HASH_RE)
        self.assertRegex(h(doc, "md", "Café — Résumé"), HASH_RE)

    def test_first_match_wins_for_duplicate_headings(self) -> None:
        doc = "## Dup\n\nfirst\n\n## Dup\n\nsecond\n"
        section = extract_markdown_section(doc, "dup")
        self.assertIn("first", section)
        self.assertNotIn("second", section)

    def test_missing_heading(self) -> None:
        with self.assertRaises(SelectorNotFoundError):
            h(SPEC_MD, "md", "9-nonexistent")

    def test_markdown_extension_alias(self) -> None:
        self.assertEqual(h(SPEC_MD, "markdown", "3-errors"), h(SPEC_MD, "md", "3-errors"))


# --------------------------------------------------------------------------
# Dispatch, extensions, target parsing
# --------------------------------------------------------------------------


class DispatchTests(unittest.TestCase):
    def test_selector_on_python_is_unsupported(self) -> None:
        with self.assertRaises(UnsupportedFormatError):
            h("def f(): pass\n", "py", "f")

    def test_selector_on_typescript_is_unsupported(self) -> None:
        with self.assertRaises(UnsupportedFormatError):
            h("export const f = 1;\n", ".ts", "f")

    def test_advertised_extensions_are_exactly_the_dispatched_ones(self) -> None:
        """The published set and the dispatch ladder must not drift apart.

        SUPPORTED_STRUCTURED_EXTENSIONS is what the error message promises and
        what callers introspect; the `if extension == ...` chain is what
        actually runs. Nothing but this test couples them, so an entry added
        to one and not the other advertises support that raises.
        """
        sample = {"json": '{"a": 1}', "toml": "a = 1\n",
                  "md": "## A\n\nbody\n", "markdown": "## A\n\nbody\n"}
        self.assertEqual(set(sample), set(SUPPORTED_STRUCTURED_EXTENSIONS))
        for ext, content in sample.items():
            with self.subTest(ext=ext):
                self.assertRegex(h(content, ext, "a"), HASH_RE)
        for ext in ("py", "ts", "yaml", "ini", "txt"):
            with self.subTest(ext=ext):
                self.assertNotIn(ext, SUPPORTED_STRUCTURED_EXTENSIONS)
                with self.assertRaises(UnsupportedFormatError):
                    h("a = 1", ext, "a")

    def test_extension_normalization(self) -> None:
        reference = h(PACKAGE_JSON, "json", "dependencies")
        for ext in (".json", "JSON", ".JSON", " json "):
            with self.subTest(ext=ext):
                self.assertEqual(h(PACKAGE_JSON, ext, "dependencies"), reference)

    def test_split_selector_target(self) -> None:
        self.assertEqual(split_selector_target("a/b.json"), ("a/b.json", None))
        self.assertEqual(split_selector_target("a/b.json#x.y"), ("a/b.json", "x.y"))
        self.assertEqual(split_selector_target("a/b.json#"), ("a/b.json", None))

    def test_split_selector_target_keeps_later_hashes(self) -> None:
        self.assertEqual(split_selector_target("d.md##2-auth"), ("d.md", "#2-auth"))
        self.assertEqual(split_selector_target("d.md#§2"), ("d.md", "§2"))

    def test_errors_share_a_base_class(self) -> None:
        from truthlib.structural import SelectorError

        for exc in (SelectorNotFoundError, UnsupportedFormatError, MalformedFileError):
            with self.subTest(exc=exc.__name__):
                self.assertTrue(issubclass(exc, SelectorError))

    def test_not_found_is_also_a_key_error(self) -> None:
        with self.assertRaises(KeyError):
            h(PACKAGE_JSON, "json", "missing")

    def test_hashes_are_stable_across_calls(self) -> None:
        first = h(PYPROJECT_TOML, "toml", "tool.ruff.lint")
        self.assertEqual(first, h(PYPROJECT_TOML, "toml", "tool.ruff.lint"))


# --------------------------------------------------------------------------
# Golden vectors -- the anchors already stored in ledgers
# --------------------------------------------------------------------------


class GoldenVectorTests(unittest.TestCase):
    """Known-answer digests, pinned to literals.

    Every relative assertion in this file survives a change to the domain
    prefix or the canonical encoding, because both sides move together. A
    stored policy anchor does NOT move with them: it was written down once,
    and a silent re-baselining turns every anchor in every consumer ledger
    stale at the same instant, with no test going red to say so.

    Changing a value here is therefore a deliberate act with a migration
    attached -- bump the domain tag to v2 and re-baseline, per spec 4.1.
    """

    def test_json_value_digest(self) -> None:
        self.assertEqual(
            h('{"a": {"b": 1}}', "json", "a"),
            "sha256:23855cccf3c089dae823acf3f3ee6ee7999b6d3da77c92eeb2c93c917"
            "a6f0ab8")

    def test_toml_value_digest_equals_the_json_one(self) -> None:
        """Domain separation puts JSON and TOML in the SAME domain on
        purpose (spec 4.1), so equal values hash equally across formats."""
        self.assertEqual(
            h("[a]\nb = 1\n", "toml", "a"),
            "sha256:23855cccf3c089dae823acf3f3ee6ee7999b6d3da77c92eeb2c93c917"
            "a6f0ab8")

    def test_markdown_section_digest(self) -> None:
        self.assertEqual(
            h("## A\n\nbody\n", "md", "a"),
            "sha256:e73880483f13b9d642057b406a54d263ec4497cae2b2df5513d4d7887"
            "98a878a")

    def test_markdown_and_value_domains_are_separated(self) -> None:
        self.assertNotEqual(h('{"a": "b"}', "json", "a"), h("## A\n\nb\n", "md", "a"))

    def test_whole_file_digest_is_plain_sha256sum(self) -> None:
        self.assertEqual(
            h("x\n", "ts"),
            "sha256:73cb3858a687a8494ca3323053016282f3dad39d42cf62ca4e79dda2a"
            "ac7d9ac")


# --------------------------------------------------------------------------
# Performance
# --------------------------------------------------------------------------


class PerformanceTests(unittest.TestCase):
    ITERATIONS = 1000
    BUDGET_SECONDS = 1.0

    def _benchmark(self, label: str, payload: bytes, ext: str, selector: str) -> None:
        extract_structural_hash(payload, ext, selector)  # warm any lazy imports
        start = time.perf_counter()
        for _ in range(self.ITERATIONS):
            extract_structural_hash(payload, ext, selector)
        elapsed = time.perf_counter() - start
        per_call_us = elapsed / self.ITERATIONS * 1e6
        print(f"  {label:<28} {elapsed:.4f}s total, {per_call_us:7.1f} µs/extraction")
        self.assertLess(
            elapsed,
            self.BUDGET_SECONDS,
            f"{label}: {self.ITERATIONS} extractions took {elapsed:.4f}s "
            f"({per_call_us:.1f} µs each), budget is 1000 µs each",
        )

    def test_json_extraction_under_budget(self) -> None:
        self._benchmark("json #dependencies", PACKAGE_JSON.encode(), "json", "dependencies")

    def test_toml_extraction_under_budget(self) -> None:
        self._benchmark("toml #tool.ruff.lint", PYPROJECT_TOML.encode(), "toml", "tool.ruff.lint")

    def test_markdown_extraction_under_budget(self) -> None:
        self._benchmark("md #2-session-management", SPEC_MD.encode(), "md", "2-session-management")

    def test_large_json_extraction_under_budget(self) -> None:
        import json as _json

        big = _json.dumps(
            {
                "dependencies": {f"pkg-{i}": f"^{i}.0.0" for i in range(500)},
                "noise": [{"id": i, "tags": ["a", "b"]} for i in range(500)],
            }
        ).encode()
        self._benchmark("large json #dependencies", big, "json", "dependencies")


if __name__ == "__main__":
    unittest.main(verbosity=2)
