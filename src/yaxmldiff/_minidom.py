# yaxmldiff is Yet Another XML Differ <https://github.com/latk/yaxmldiff.py>
# SPDX-FileCopyrightText: 2021-2026 Lukas Atkinson
# SPDX-License-Identifier: Apache-2.0

"""Simplified DOM that's easier to diff."""

import dataclasses
import typing as t

import lxml.etree

DOM: t.TypeAlias = "Elem | str | Comment | PI"


@dataclasses.dataclass(slots=True, frozen=True)
class Elem:
    tag: lxml.etree.QName
    attrs: t.Sequence[tuple[str, str]]
    """Effectively a hashable `Mapping[str,str]`, guaranteed to have consistent order."""
    content: t.Sequence[DOM]


@dataclasses.dataclass(slots=True, frozen=True)
class Comment:
    content: str


@dataclasses.dataclass(slots=True, frozen=True)
class PI:
    target: str
    content: str


def parse(elem: lxml.etree.Element) -> DOM:
    if elem.tag is lxml.etree.Comment:  # type: ignore[comparison-overlap]
        return Comment((elem.text or "").strip())  # type: ignore[unreachable]

    if elem.tag is lxml.etree.PI:  # type: ignore[comparison-overlap]
        return PI(elem.target, (elem.text or "").strip())  # type: ignore[unreachable] # pyright: ignore[reportAttributeAccessIssue]

    match elem.tag:
        case str():
            tag = lxml.etree.QName(elem.tag)
        case lxml.etree.QName():  # pragma: no cover  # never observed in practice
            tag = elem.tag
        case tag:  # pragma: no cover  # all known cases have been handled
            raise TypeError(f"unsupported special element: {tag=} {type(tag)=}")
    attrs = tuple(sorted(elem.attrib.items()))
    content: list[DOM] = []
    if elem.text and (text := elem.text.strip()):
        content.append(text)
    for child in list(elem):
        content.extend(parse_top(child))
    return Elem(tag, attrs, tuple(content))


def parse_top(elem: lxml.etree.Element) -> t.Iterable[DOM]:
    yield parse(elem)
    if elem.tail and (tail := elem.tail.strip()):
        yield tail
