# yaxmldiff is Yet Another XML Differ <https://github.com/latk/yaxmldiff.py>
# Copyright 2021 Lukas Atkinson
# SPDX-License-Identifier: Apache-2.0

"""
yaxmldiff is Yet Another XML Differ <https://github.com/latk/yaxmldiff.py>

Functions
---------

* compare_xml() - compare two XML documents
"""

from io import StringIO
from typing import Union, List, Tuple, Optional, Iterator
from itertools import zip_longest
from contextlib import contextmanager

from lxml.etree import _Element as Element, _Attrib as Attrib, XML as XmlParser

__all__ = ["compare_xml"]

__version__ = "0.1.0"


def compare_xml(
    left: Union[str, Element],
    right: Union[str, Element],
) -> Optional[str]:
    r"""
    Compare two XML documents.

    If the documents are given as strings, they are parsed first.

    Returns: None if both are equal, a diff otherwise.
    """

    if isinstance(left, str):
        left = XmlParser(left.encode())

    if isinstance(right, str):
        right = XmlParser(right.encode())

    writer = DiffWriter()
    compare_elem_with_trailer(writer, left, right)

    if writer.has_diff:
        return str(writer)
    return None


class DiffWriter:
    def __init__(self, *, indent: int = 0, buffer: StringIO = None) -> None:
        self._buffer = buffer or StringIO()
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

    def write_diff(self, left: Optional[str], right: Optional[str]) -> None:
        self.has_diff = True
        if left is not None:
            self._write_line("- ", left)
        if right is not None:
            self._write_line("+ ", right)

    @contextmanager
    def indented(self) -> Iterator["DiffWriter"]:
        inner = DiffWriter(
            indent=self._indent + 1,
            buffer=self._buffer,  # directly share buffer
        )

        yield inner

        self.has_diff = self.has_diff or inner.has_diff

    @contextmanager
    def only_show_if_diff(self, *, indented: bool = False) -> Iterator["DiffWriter"]:
        inner = DiffWriter(indent=self._indent + indented)

        yield inner

        content = str(inner)
        if inner.has_diff:
            self.has_diff = True
            self._buffer.write(content)
            self._buffer.write("\n")
        elif content:
            self.write_same("...")


def compare_elem_with_trailer(
    writer: DiffWriter, left: Element, right: Element
) -> None:
    compare_elem(writer, left, right)
    assert not isinstance(left.tail, bytes)
    assert not isinstance(right.tail, bytes)
    compare_text(writer, left.tail, right.tail)


def compare_elem(writer: DiffWriter, left: Element, right: Element) -> None:
    if left.tag != right.tag:
        writer.write_diff(_tag_only(left), _tag_only(right))
        return

    has_content = len(left) or len(right) or left.text or right.text

    (
        attrs_same,
        attrs_left_only,
        attrs_diff,
        attrs_right_only,
    ) = compare_attributes(left.attrib, right.attrib)

    # write the opening tag, possibly showing differing attributes
    if attrs_left_only or attrs_diff or attrs_right_only:

        if attrs_same:
            writer.write_same(f"<{left.tag} " + " ".join(attrs_same))
        else:
            writer.write_same(f"<{left.tag}")

        with writer.indented() as inner:
            for left_attr in attrs_left_only:
                inner.write_diff(left_attr, None)
            for left_attr, right_attr in attrs_diff:
                inner.write_diff(left_attr, right_attr)
            for right_attr in attrs_right_only:
                inner.write_diff(None, right_attr)

        if has_content:
            writer.write_same(">")
        else:
            writer.write_same("/>")
            return

    elif has_content:
        writer.write_same(f"<{left.tag} ...>" if attrs_same else f"<{left.tag}>")

    else:
        writer.write_same(f"<{left.tag} .../>" if attrs_same else f"<{left.tag}/>")
        return

    with writer.only_show_if_diff(indented=True) as inner:
        compare_content(inner, left, right)

    writer.write_same(f"</{left.tag}>")


def compare_attributes(
    left_attrs: Attrib,
    right_attrs: Attrib,
) -> Tuple[List[str], List[str], List[Tuple[str, str]], List[str]]:
    attrs_shared = []
    attrs_left_only = []
    attrs_changed = []
    attrs_right_only = []

    for key in sorted(set([*left_attrs, *right_attrs])):
        left_value = left_attrs.get(key)
        right_value = right_attrs.get(key)

        assert left_value is None or isinstance(left_value, str)
        assert right_value is None or isinstance(right_value, str)

        if left_value is None:
            assert right_value is not None
            attrs_right_only.append(abbreviate_attr(key, right_value))
        elif right_value is None:
            assert left_value is not None
            attrs_left_only.append(abbreviate_attr(key, left_value))
        elif left_value == right_value:
            attrs_shared.append(abbreviate_attr(key, left_value))
        else:
            attrs_changed.append(
                (
                    f'{key}="{left_value}"',
                    f'{key}="{right_value}"',
                )
            )

    return attrs_shared, attrs_left_only, attrs_changed, attrs_right_only


def abbreviate_attr(key: str, value: str) -> str:
    if len(value) > 4:
        value = "..."
    return f'{key}="{value}"'


def compare_content(writer: DiffWriter, left: Element, right: Element) -> None:
    assert left.text is None or isinstance(left.text, str)
    assert right.text is None or isinstance(right.text, str)
    compare_text(writer, left.text, right.text)

    for left_child, right_child in zip_longest(list(left), list(right)):
        if left_child is None:
            writer.write_diff(None, _tag_only(right_child))
        elif right_child is None:
            writer.write_diff(_tag_only(left_child), None)
        else:
            compare_elem_with_trailer(writer, left_child, right_child)


def compare_text(
    writer: DiffWriter,
    left: Optional[str],
    right: Optional[str],
) -> None:
    left = "" if left is None else left.strip()
    right = "" if right is None else right.strip()

    if left == right == "":
        return

    if left == right:
        writer.write_same("...")
    else:
        writer.write_diff(left if left else None, right if right else None)


def _tag_only(elem: Element) -> str:
    abbreviated = "<" + elem.tag
    if elem.attrib:
        abbreviated += " ..."
    if len(elem) or elem.text:
        abbreviated += ">...</" + elem.tag + ">"
    else:
        abbreviated += "/>"
    return abbreviated
