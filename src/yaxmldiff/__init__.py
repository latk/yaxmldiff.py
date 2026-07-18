# yaxmldiff is Yet Another XML Differ <https://github.com/latk/yaxmldiff.py>
# SPDX-FileCopyrightText: 2021-2026 Lukas Atkinson
# SPDX-License-Identifier: Apache-2.0

"""yaxmldiff is Yet Another XML Differ <https://github.com/latk/yaxmldiff.py>.

Functions
---------

* compare_xml() - compare two XML documents
"""

import io

import lxml.etree
from lxml.etree import _Element as Element

from . import _diff, _minidom

__all__ = ["compare_xml"]


def compare_xml(
    left: str | Element,
    right: str | Element,
    *,
    context: int = 3,
    comments: bool = True,
) -> str | None:
    r"""Compare two XML documents.

    If the documents are given as strings, they are parsed first.

    Args:
      left: an input document
      right: an input document
      context: how many lines of context to preserve around each change
      comments: whether comments and processing instructions will be diffed as well (default: true)

    Returns: None if both are equal, a diff otherwise.
    """
    diff_config = _diff.Config(context=context)
    dom_config = _minidom.Config(comments=comments)

    if isinstance(left, str):
        left = lxml.etree.XML(left.encode())

    if isinstance(right, str):
        right = lxml.etree.XML(right.encode())

    diff = list(
        _diff.diff_seq(
            list(_minidom.parse_top(left, config=dom_config)),
            list(_minidom.parse_top(right, config=dom_config)),
            config=diff_config,
        )
    )

    if not any(item.is_diff for item in diff):
        return None

    buf = io.StringIO()
    for item in diff:
        _render(item, buf=buf, indent=0)
    return buf.getvalue().rstrip()


def _render(item: _diff.DiffItem, *, buf: io.StringIO, indent: int) -> None:
    if isinstance(item, _diff.Nested):
        for nested in item.items:
            _render(nested, buf=buf, indent=indent + 1)
        return

    match item:
        case _diff.Same():
            prefix = "  "
        case _diff.Left():
            prefix = "- "
        case _diff.Right():
            prefix = "+ "

    buf.write(prefix)
    buf.write("  " * indent)
    buf.write(item.line)
    buf.write("\n")
