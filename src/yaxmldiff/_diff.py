# yaxmldiff is Yet Another XML Differ <https://github.com/latk/yaxmldiff.py>
# SPDX-FileCopyrightText: 2021-2026 Lukas Atkinson
# SPDX-License-Identifier: Apache-2.0

"""Produce a data structure that represents an XML diff."""

import dataclasses
import itertools
import typing as t

import lxml.etree

from . import _minidom as dom

DiffItem: t.TypeAlias = "Same | Left | Right | Nested"


@dataclasses.dataclass
class Same:
    line: str

    is_diff: t.Literal[False] = False


@dataclasses.dataclass
class Left:
    line: str

    is_diff: t.Literal[True] = True


@dataclasses.dataclass
class Right:
    line: str

    is_diff: t.Literal[True] = True


@dataclasses.dataclass
class Nested:
    items: t.Sequence[DiffItem]

    @property
    def is_diff(self) -> bool:
        return any(item.is_diff for item in self.items)


def diff_seq(
    left_items: t.Sequence[dom.DOM], right_items: t.Sequence[dom.DOM]
) -> t.Iterable[DiffItem]:
    for left, right in itertools.zip_longest(left_items, right_items, fillvalue=None):
        if left is not None and right is not None:
            yield from diff(left, right)
        elif left is not None:
            yield Left(_concise(left))
        elif right is not None:
            yield Right(_concise(right))
        else:  # pragma: no cover
            raise AssertionError(f"unreachable: {left=} {right=}")


def diff(left: dom.DOM, right: dom.DOM) -> t.Iterable[DiffItem]:
    match (left, right):
        case _ if left == right:
            yield Same(_concise(left))
        case _ if type(left) is not type(right):
            yield Left(_concise(left))
            yield Right(_concise(right))
        case str(), str():
            yield Left(_concise(left))
            yield Right(_concise(right))
        case dom.Elem(), dom.Elem() if left.tag != right.tag:
            yield Left(_concise(left))
            yield Right(_concise(right))
        case dom.Comment(), dom.Comment():
            yield Same("<!--")
            yield Nested(tuple(diff(left.content, right.content)))
            yield Same("-->")
        case dom.PI(), dom.PI() if left.target != right.target:
            yield Left(_concise(left))
            yield Right(_concise(right))
        case dom.PI(), dom.PI():
            yield Same(f"<?{left.target}")
            yield Nested(tuple(diff(left.content, right.content)))
            yield Same("?>")
        case dom.Elem(), dom.Elem():
            yield from _diff_elem(left, right)
        case _:  # pragma: no cover
            raise TypeError(f"unreachable: {left=} {right=}")


def _diff_elem(left: dom.Elem, right: dom.Elem) -> t.Iterable[DiffItem]:
    has_content = len(left.content) or len(right.content)
    closer = ">" if has_content else "/>"
    attrs = _compare_attributes(left.attrs, right.attrs)
    if attrs.left_only or attrs.right_only:
        yield Same(_tag_open(left.tag, attrs=" ".join(attrs.same)))

        yield Nested(
            (
                *(Left(attr) for attr in attrs.left_only),
                *(Right(attr) for attr in attrs.right_only),
            )
        )

        yield Same(closer)

    else:
        yield Same(
            f"{_tag_open(left.tag, attrs='...' if attrs.same else None)}{closer}"
        )

    if not has_content:
        return

    inner = tuple(diff_seq(left.content, right.content))
    if not any(x.is_diff for x in inner):
        inner = (Same("..."),)  # collapse irrelevant content
    yield Nested(inner)

    yield Same(f"</{left.tag.localname}>")


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
                attrs.same.append(f'{key}="{_concise(left, maxlen=0)}"')
            case str() as left, str() as right:
                attrs.left_only.append(f'{key}="{left}"')
                attrs.right_only.append(f'{key}="{right}"')
            case left, right:  # pragma: no cover
                raise AssertionError(f"unreachable: {left=} {right=}")

    return attrs


def _tag_open(tag: lxml.etree.QName, *, attrs: str | None) -> str:
    out = f"<{tag.localname}"
    if tag.namespace:
        out += f' xmlns="{tag.namespace}"'
    if attrs:
        out += f" {attrs}"
    return out


_MAX_ABBREV_VALUE = 4


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
        case _:  # pragma: no cover
            raise TypeError(f"unreachable: {item=}")
