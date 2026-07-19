import argparse
import contextlib
import dataclasses
import pathlib
import re
import sys
import typing as t

import lxml.etree

from yaxmldiff import compare_xml


def main() -> None:
    args = parse_args()

    parser: t.Callable[[bytes], lxml.etree._Element] = lxml.etree.XML
    if args.html:
        parser = lxml.etree.HTML

    with _handle_parse_errors(args.left):
        left = parser(args.left.read_bytes())
    with _handle_parse_errors(args.right):
        right = parser(args.right.read_bytes())

    diff = compare_xml(
        left,
        right,
        context=args.context,
        comments=args.comments,
    )

    if diff and not args.quiet:
        print(diff)
    if diff and (args.exit_code or args.quiet):
        sys.exit(1)
    sys.exit(0)


@dataclasses.dataclass
class Args:
    left: pathlib.Path
    right: pathlib.Path
    html: bool
    comments: bool
    context: int
    exit_code: bool
    quiet: bool


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        formatter_class=_ParagraphHelpFormatter,
        description="""\
Compare two XML files via a structural diff.

The output is similar to an unified diff (like the one used by Git),
but the diff is performed structurally: element by element, not line by line.
Whitespace is generally ignored.
""",
        epilog="""\
Exit code: exits with `0` on success, or `2` if there was a problem.
If `--exit-code` or `--quiet` were enabled, exit with code `1` if the files differ.

More info at the yaxmldiff website: <https://github.com/latk/yaxmldiff.py>
""",
    )
    p.add_argument(
        "left", metavar="<left>", type=pathlib.Path, help="a file to compare"
    )
    p.add_argument(
        "right", metavar="<right>", type=pathlib.Path, help="a file to compare"
    )
    p.add_argument(
        "--html",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Parse the files as HTML.",
    )
    p.add_argument(
        "--comments",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Whether comments and processing instructions will be diffed as well.",
    )
    p.add_argument(
        "-U",
        "--context",
        "--unified",
        type=int,
        default=3,
        metavar="<n>",
        help="""\
How many lines of context to show around each change.

The output will always use the "unified diff" format, never the "context" format.
Where content is elided,
the output cannot use the `@@ ... @@` markers due to the structural nature of the diff,
and will instead insert a placeholder like `... skipped 12 lines`.
        """,
    )
    p.add_argument(
        "--exit-code",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Exit with code 1 if files differ, just like the standard `diff` tool.",
    )
    p.add_argument(
        "--quiet",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Don't print the diff, only check if the inputs differ. Implies `--exit-code`.",
    )
    return p


def parse_args(args: t.Iterable[str] | None = None) -> Args:
    return Args(**vars(build_parser().parse_args(args)))  # type: ignore[misc]


class _ParagraphHelpFormatter(argparse.HelpFormatter):
    """Override HelpFormatter in order to preserve paragraphs."""

    def _split_lines(self, text: str, width: int) -> list[str]:
        import textwrap  # noqa: PLC0415  # top-level import

        lines: list[str] = []
        for p in re.split(r"\n\n+", text):
            if lines:
                lines.append("")  # paragraph separator
            lines.extend(textwrap.wrap(p, width))
        return lines

    def _fill_text(self, text: str, width: int, indent: str) -> str:
        lines = self._split_lines(text, width - len(indent))
        return "\n".join(line and f"{indent}{line}" for line in lines)

    def _get_help_string(self, action: argparse.Action) -> str | None:
        s = super()._get_help_string(action)
        if (
            not s
            or "%(default)" in s
            or action.required
            or t.cast(object, action.default) is argparse.SUPPRESS
        ):
            return s
        # insert the default at the end of the 1st line
        return re.sub("(?m)$", " (default: %(default)s)", s, count=1)


def _warn(msg: str) -> None:
    print(f"yaxmldiff: {msg}", file=sys.stderr)


def _die(msg: str) -> t.NoReturn:
    _warn(msg)
    sys.exit(2)


@contextlib.contextmanager
def _handle_parse_errors(filename: pathlib.Path) -> t.Generator[None, None, None]:
    try:
        yield
    except (FileNotFoundError, IsADirectoryError):
        _die(f"{filename}: not a file")
    except lxml.etree.XMLSyntaxError as err:
        _die(f"{filename}: {err.msg}")
