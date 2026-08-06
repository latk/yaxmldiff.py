import contextlib
import importlib.metadata
import pathlib
import sys
import typing as t

import cappa
import lxml.etree

from . import compare_xml

NAME = "yaxmldiff"  # must match the distribution name, and the CLI name


def main() -> None:
    args = cappa.parse(Yaxmldiff, version=_version())

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


_GROUP_INPUT = cappa.Group(name="Input Options")


@cappa.command(
    epilog="""\
**Exit code:** exits with `0` on success, or `2` if there was a problem.
If `--exit-code` or `--quiet` were enabled, exit with code `1` if the files differ.

More info at the yaxmldiff website: <https://github.com/latk/yaxmldiff.py>
""",
)
class Yaxmldiff:
    """Compare two XML files via a structural diff.

    The output is similar to an unified diff (like the one used by Git),
    but the diff is performed structurally: element by element, not line by line.
    Whitespace is generally ignored.
    """

    left: t.Annotated[pathlib.Path, cappa.Arg(group=_GROUP_INPUT)]
    """A file to compare."""

    right: t.Annotated[pathlib.Path, cappa.Arg(group=_GROUP_INPUT)]
    """A file to compare."""

    html: t.Annotated[bool, cappa.Arg(long="--html/--no-html", group=_GROUP_INPUT)] = (
        False
    )
    """Parse the files as HTML."""

    comments: t.Annotated[bool, cappa.Arg(long="--comments/--no-comments")] = True
    """Whether comments and processing instructions will be diffed as well."""

    context: t.Annotated[
        int, cappa.Arg(short="-U", long="--context, --unified", value_name="n")
    ] = 3
    """How many lines of context to show around each change.

    The output will always use the "unified diff" format, never the "context" format.
    Where content is elided, the output cannot use the `@@ ... @@` markers due to the structural nature of the diff,
    and will instead insert a placeholder like `... skipped 12 lines`.
    """

    exit_code: t.Annotated[bool, cappa.Arg(long="--exit-code/--no-exit-code")] = False
    """Exit with code 1 if files differ, just like the standard `diff` tool."""

    quiet: t.Annotated[bool, cappa.Arg(long="--quiet/--no-quiet")] = False
    """Don't print the diff, only check if the inputs differ. Implies `--exit-code`."""

    help_markdown: t.Annotated[bool, cappa.Arg(hidden=True, long=True)] = False


def _warn(msg: str) -> None:
    print(msg, file=sys.stderr)


@contextlib.contextmanager
def _handle_parse_errors(filename: pathlib.Path) -> t.Generator[None, None, None]:
    try:
        yield
    except (FileNotFoundError, IsADirectoryError) as err:
        _warn(f"{filename}: not a file")
        raise SystemExit(2) from err
    except lxml.etree.XMLSyntaxError as err:
        _warn(f"{filename}: {err.msg}")
        raise SystemExit(2) from err


def _version() -> str | None:
    try:
        version = importlib.metadata.version(NAME)
    except importlib.metadata.PackageNotFoundError:  # pragma: no cover
        return None
    return f"{NAME} {version}"
