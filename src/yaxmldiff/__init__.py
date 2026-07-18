# yaxmldiff is Yet Another XML Differ <https://github.com/latk/yaxmldiff.py>
# SPDX-FileCopyrightText: 2021-2026 Lukas Atkinson
# SPDX-License-Identifier: Apache-2.0

"""yaxmldiff is Yet Another XML Differ <https://github.com/latk/yaxmldiff.py>.

Functions
---------

* compare_xml() - compare two XML documents
"""

import contextlib
import dataclasses
import io
import itertools
import typing as t

import lxml.etree
from lxml.etree import _Attrib as Attrib
from lxml.etree import _Element as Element

__all__ = ["compare_xml"]


def compare_xml(
    left: str | Element,
    right: str | Element,
) -> str | None:
    r"""Compare two XML documents.

    If the documents are given as strings, they are parsed first.

    Returns: None if both are equal, a diff otherwise.
    """
    if isinstance(left, str):
        left = lxml.etree.XML(left.encode())

    if isinstance(right, str):
        right = lxml.etree.XML(right.encode())

    writer = _DiffWriter()
    _compare_elem_with_trailer(writer, left, right)

    if writer.has_diff:
        return str(writer)
    return None


class _DiffWriter:
    def __init__(
        self,
        *,
        indent: int = 0,
        buffer: io.StringIO | None = None,
    ) -> None:
        self._buffer = buffer or io.StringIO()
        self._indent = indent
        self.has_diff = False

    def __str__(self) -> str:
        return self._buffer.getvalue().rstrip()

    def _write_line(self, prefix: str, contents: str) -> None:
        self._buffer.write(prefix)
        self._buffer.write("  " * self._indent)
        self._buffer.write(contents)
        self._buffer.write("\n")

    def write_same(self, line: str) -> None:
        self._write_line("  ", line)

    def write_diff(self, left: str | None, right: str | None) -> None:
        self.has_diff = True
        if left is not None:
            self._write_line("- ", left)
        if right is not None:
            self._write_line("+ ", right)

    @contextlib.contextmanager
    def indented(self) -> t.Generator["_DiffWriter", None, None]:
        inner = _DiffWriter(
            indent=self._indent + 1,
            buffer=self._buffer,  # directly share buffer
        )

        yield inner

        self.has_diff = self.has_diff or inner.has_diff

    @contextlib.contextmanager
    def only_show_if_diff(
        self, *, indented: bool = False
    ) -> t.Generator["_DiffWriter", None, None]:
        inner = _DiffWriter(indent=self._indent + indented)

        yield inner

        content = str(inner)
        if inner.has_diff:
            self.has_diff = True
            self._buffer.write(content)
            self._buffer.write("\n")
        elif content:
            self.write_same("...")


def _compare_elem_with_trailer(
    writer: _DiffWriter, left: Element, right: Element
) -> None:
    _compare_elem(writer, left, right)
    assert not isinstance(left.tail, bytes)
    assert not isinstance(right.tail, bytes)
    _compare_text(writer, left.tail, right.tail)


def _compare_elem(writer: _DiffWriter, left: Element, right: Element) -> None:
    if left.tag != right.tag:
        writer.write_diff(_tag_only(left), _tag_only(right))
        return

    tagname = _tagname(left)
    has_content = len(left) or len(right) or left.text or right.text

    # write the opening tag, possibly showing differing attributes
    attrs = _compare_attributes(left.attrib, right.attrib)
    if attrs.left_only or attrs.changed or attrs.right_only:
        if attrs.same:
            writer.write_same(f"<{tagname} " + " ".join(attrs.same))
        else:
            writer.write_same(f"<{tagname}")

        with writer.indented() as inner:
            for left_attr in attrs.left_only:
                inner.write_diff(left_attr, None)
            for left_attr, right_attr in attrs.changed:
                inner.write_diff(left_attr, right_attr)
            for right_attr in attrs.right_only:
                inner.write_diff(None, right_attr)

        if has_content:
            writer.write_same(">")
        else:
            writer.write_same("/>")
            return

    elif has_content:
        writer.write_same(f"<{tagname} ...>" if attrs.same else f"<{tagname}>")

    else:
        writer.write_same(f"<{tagname} .../>" if attrs.same else f"<{tagname}/>")
        return

    with writer.only_show_if_diff(indented=True) as inner:
        _compare_content(inner, left, right)

    writer.write_same(f"</{tagname}>")


@dataclasses.dataclass
class _AttrDiff:
    same: list[str]
    left_only: list[str]
    changed: list[tuple[str, str]]
    right_only: list[str]


def _compare_attributes(left_attrs: Attrib, right_attrs: Attrib) -> _AttrDiff:
    attrs = _AttrDiff([], [], [], [])

    for key in sorted({*left_attrs.keys(), *right_attrs.keys()}):
        match left_attrs.get(key), right_attrs.get(key):
            case str() as left, None:
                attrs.left_only.append(_abbreviate_attr(key, left))
            case None, str() as right:
                attrs.right_only.append(_abbreviate_attr(key, right))
            case str() as left, str() as right if left == right:
                attrs.same.append(_abbreviate_attr(key, left))
            case str() as left, str() as right:
                attrs.changed.append(
                    (
                        f'{key}="{left}"',
                        f'{key}="{right}"',
                    )
                )
            case left, right:
                raise AssertionError(f"unreachable: {left=} {right=}")  # noqa: TRY003

    return attrs


_MAX_ABBREV_VALUE = 4


def _abbreviate_attr(key: str, value: str) -> str:
    if len(value) > _MAX_ABBREV_VALUE:
        value = "..."
    return f'{key}="{value}"'


def _compare_content(writer: _DiffWriter, left: Element, right: Element) -> None:
    assert left.text is None or isinstance(left.text, str)
    assert right.text is None or isinstance(right.text, str)
    _compare_text(writer, left.text, right.text)

    for left_child, right_child in itertools.zip_longest(list(left), list(right)):
        if left_child is None:
            writer.write_diff(None, _tag_only(right_child))
        elif right_child is None:
            writer.write_diff(_tag_only(left_child), None)
        else:
            _compare_elem_with_trailer(writer, left_child, right_child)


def _compare_text(writer: _DiffWriter, left: str | None, right: str | None) -> None:
    left = "" if left is None else left.strip()
    right = "" if right is None else right.strip()

    if left == right == "":
        return

    if left == right:
        writer.write_same("...")
    else:
        writer.write_diff(left if left else None, right if right else None)


def _tag_only(elem: Element) -> str:
    tagname = _tagname(elem)
    abbreviated = f"<{tagname}"
    if elem.attrib:
        abbreviated += " ..."
    if len(elem) or elem.text:
        abbreviated += f">...</{tagname}>"
    else:
        abbreviated += "/>"
    return abbreviated


def _tagname(tag: str | bytes | bytearray | lxml.etree.QName | Element) -> str:
    """A tagname, for display purposes only."""
    if isinstance(tag, Element):
        tag = tag.tag
    match tag:
        case str():
            return tag
        case lxml.etree.QName():
            # Returning `.text` would be unambiguous but too verbose.
            # In nearly all cases, the `.localname` will be sufficient.
            return tag.localname
        case bytes() | bytearray():
            # Backslashes aren't valid syntax, but should make the rare non-UTF-8 name stand out.
            return tag.decode(encoding="utf-8", errors="backslashreplace")
