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
from lxml.etree import _Element as Element

from . import _minidom as dom

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
    _compare_dom_top(writer, dom.parse_top(left), dom.parse_top(right))

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


def _compare_dom_top(
    writer: _DiffWriter,
    left_items: t.Iterable[dom.DOM],
    right_items: t.Iterable[dom.DOM],
) -> None:
    for pair in itertools.zip_longest(left_items, right_items):
        match pair:
            case None, right:
                writer.write_diff(None, _concise(right))
            case left, None:
                writer.write_diff(_concise(left), None)
            case left, right:
                _compare_dom(writer, left, right)


def _compare_dom(writer: _DiffWriter, left: dom.DOM, right: dom.DOM) -> None:
    match (left, right):
        case _ if left == right:
            writer.write_same(_concise(left))
        case _ if type(left) is not type(right):
            writer.write_diff(_concise(left), _concise(right))
        case str(), str():
            writer.write_diff(left, right)
        case dom.Elem(), dom.Elem() if left.tag != right.tag:
            writer.write_diff(_concise(left), _concise(right))
        case dom.Comment(), dom.Comment():
            writer.write_same("<!--")
            with writer.indented() as inner:
                _compare_dom(inner, left.content, right.content)
            writer.write_same("-->")
        case dom.PI(), dom.PI() if left.target != right.target:
            writer.write_diff(_concise(left), _concise(right))
        case dom.PI(), dom.PI():
            writer.write_same(f"<?{left.target}")
            with writer.indented() as inner:
                _compare_dom(inner, left.content, right.content)
            writer.write_same("?>")
        case dom.Elem(), dom.Elem():
            _compare_elem(writer, left, right)


def _compare_elem(writer: _DiffWriter, left: dom.Elem, right: dom.Elem) -> None:
    has_content = len(left.content) or len(right.content)
    closer = ">" if has_content else "/>"
    attrs = _compare_attributes(left.attrs, right.attrs)
    if attrs.left_only or attrs.right_only:
        writer.write_same(_tag_open(left.tag, attrs=" ".join(attrs.same)))

        with writer.indented() as inner:
            for left_attr in attrs.left_only:
                inner.write_diff(left_attr, None)
            for right_attr in attrs.right_only:
                inner.write_diff(None, right_attr)

        writer.write_same(closer)

    else:
        writer.write_same(
            f"{_tag_open(left.tag, attrs='...' if attrs.same else None)}{closer}"
        )

    if not has_content:
        return

    with writer.only_show_if_diff(indented=True) as inner:
        _compare_dom_top(inner, left.content, right.content)

    writer.write_same(f"</{left.tag.localname}>")


@dataclasses.dataclass
class _AttrDiff:
    same: list[str]
    left_only: list[str]
    right_only: list[str]


def _compare_attributes(
    left_attrs: t.Mapping[str, str], right_attrs: t.Mapping[str, str]
) -> _AttrDiff:
    attrs = _AttrDiff([], [], [])

    for key in sorted({*left_attrs, *right_attrs}):
        match left_attrs.get(key), right_attrs.get(key):
            case str() as left, None:
                attrs.left_only.append(f'{key}="{left}"')
            case None, str() as right:
                attrs.right_only.append(f'{key}="{right}"')
            case str() as left, str() as right if left == right:
                attrs.same.append(_abbreviate_attr(key, left))
            case str() as left, str() as right:
                attrs.left_only.append(f'{key}="{left}"')
                attrs.right_only.append(f'{key}="{right}"')
            case left, right:
                raise AssertionError(f"unreachable: {left=} {right=}")

    return attrs


_MAX_ABBREV_VALUE = 4


def _abbreviate_attr(key: str, value: str) -> str:
    if len(value) > _MAX_ABBREV_VALUE:
        value = "..."
    return f'{key}="{value}"'


def _tag_open(tag: lxml.etree.QName, *, attrs: str | None) -> str:
    out = f"<{tag.localname}"
    if tag.namespace:
        out += f' xmlns="{tag.namespace}"'
    if attrs:
        out += f" {attrs}"
    return out


def _concise(item: dom.DOM, *, maxlen: int = 40) -> str:
    # A "..." placeholder requires at least 3 chars,
    # so don't bother truncating short strings.
    maxlen = max(maxlen, _MAX_ABBREV_VALUE)

    match item:
        case str():
            if len(item) <= maxlen:
                return item
            if maxlen <= _MAX_ABBREV_VALUE:  # small budget, just replace with ellipsis
                return "..."
            # otherwise, lots of space is available, so truncate
            return f"{item[: maxlen - len('...')]}..."
        case dom.Comment():
            template_len = len("<!--  -->")
            return f"<!-- {_concise(item.content, maxlen=maxlen - template_len)} -->"
        case dom.PI():
            template_len = len("<? ?>") + len(item.target)
            return f"<?{item.target} {_concise(item.content, maxlen=maxlen - template_len)}?>"
        case dom.Elem():
            out = _tag_open(item.tag, attrs=("..." if item.attrs else None))
            if item.content:
                out += f">...</{item.tag.localname}>"
            else:
                out += "/>"
            return out
