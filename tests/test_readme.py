import dataclasses
import io
import pathlib
import re
import typing as t

import cappa
import cappa.help
import cappa.output
import inline_snapshot
import pytest
import rich.text
from typing_extensions import override

from yaxmldiff._cli import Yaxmldiff

_README = pathlib.Path(__file__).parent / "../README.md"
_T = t.TypeVar("_T")


def test_cli_docs_up_to_date(capsys: pytest.CaptureFixture[str]) -> None:
    """Make sure that the CLI docs in the README are up to date.

    If the CLI docs ever change, inline-snapshot will show a diff and offer to apply it.
    """
    with (
        pytest.MonkeyPatch.context() as m,
        pytest.raises(SystemExit) as err,
    ):
        m.setenv("COLUMNS", "9999")  # effectively disable any line wrapping
        cappa.parse(
            Yaxmldiff,
            argv=["--help"],
            input=io.StringIO(),
            help_formatter=_PlainMarkdownHelpFormatter(),
            version="yaxmldiff dev",
        )
    stdout, stderr = capsys.readouterr()
    assert (err.value.code, stderr) == (0, "")
    usage = stdout.strip()
    readme_contents = _README.read_text()
    begin, end = "<!-- begin usage -->", "<!-- end usage -->"
    pattern = re.compile(rf"(?ms)^({re.escape(begin)})$.*?^({re.escape(end)})$")
    assert begin in readme_contents
    assert end in readme_contents
    assert pattern.search(readme_contents)
    updated: str = pattern.sub(
        lambda m: f"{m[1]}\n\n{usage}\n\n{m[2]}", readme_contents
    )
    assert updated == inline_snapshot.external_file(_README, format=".txt")


class _PlainMarkdownHelpFormatter(cappa.help.HelpFormatter):
    @override
    def long(
        self, command: cappa.FinalCommand[object], prog: str
    ) -> list[cappa.output.Displayable]:
        help_markdown = "\n".join(_MdRenderer().command(command, prog=prog))
        return [rich.text.Text(help_markdown)]


@dataclasses.dataclass(kw_only=True)
class _MdRenderer:
    indent: str = ""
    firstindent: str = ""

    def with_extra_indent(
        self, indent: str, *, firstindent: str | None = None
    ) -> "_MdRenderer":
        if firstindent is None:
            firstindent = indent
        return dataclasses.replace(
            self,
            indent=f"{self.indent}{indent}",
            firstindent=f"{self.indent}{firstindent}",
        )

    def command(
        self, cmd: cappa.FinalCommand[object], *, prog: str
    ) -> t.Generator[str, None, None]:
        groups = cappa.help.ArgGroup.collect(cmd)

        usage = rich.text.Text.from_markup(
            cappa.help.add_short_args(prog, groups)
        ).plain
        usage = usage.removeprefix("Usage:").strip()
        yield from self.indented(f"Usage: `{usage}`")

        for cmd_help in _lift(cmd.help):
            yield ""
            yield from self.indented(cmd_help)

        for desc in _lift(cmd.description):
            yield ""
            yield from self.indented(desc)

        for group in groups:
            yield ""
            yield from self.indented(f"**{group.name}:**")
            for f in group.field_groups:
                yield ""
                yield from self.field(f)

        for epilog in _lift(cmd.epilog):
            yield ""
            yield from self.indented(epilog)

    def field(self, field: cappa.help.FieldGroup) -> t.Generator[str, None, None]:
        args: list[cappa.FinalArg[object]] | None = field.args
        name = rich.text.Text.from_markup(cappa.help.format_arg_name(field, ", "))
        yield from self.with_extra_indent("  ", firstindent="- ").indented(
            f"`{name.plain}`"
        )
        for i, arg_help in enumerate(arg.help for arg in args or () if arg.help):
            if i == 0:
                yield ""
            yield from self.with_extra_indent("  ").indented(arg_help)

    def indented(self, text: str) -> t.Generator[str, None, None]:
        match text.strip().splitlines():
            case [first, *rest]:
                yield f"{self.firstindent}{first}"
                for line in rest:
                    if line:
                        yield f"{self.indent}{line}"
                    else:
                        yield ""


def _lift(value: _T | None) -> tuple[_T] | tuple[()]:
    """Convert a nullable value into an iterable."""
    if value is None:
        return ()
    return (value,)
