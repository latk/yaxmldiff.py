import dataclasses
import io
import pathlib
import sys
import traceback
from unittest.mock import ANY

import inline_snapshot
import pytest

from yaxmldiff._cli import main


def test_diff(tmp_path: pathlib.Path) -> None:
    """Show a normal diff."""
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.write_text(r"<foo>left</foo>")
    right.write_text(r"<foo>right</foo>")

    diff: str = inline_snapshot.snapshot(
        """\
<foo>
-   left
+   right
  </foo>\
"""
    )

    assert _invoke(left, right) == _Output(0, diff, "")
    assert _invoke("--exit-code", left, right) == _Output(1, diff, "")
    assert _invoke("--quiet", left, right) == _Output(1, "", "")


def test_same(tmp_path: pathlib.Path) -> None:
    """Show behavior when inputs are equivalent."""
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.write_text(r"<foo>same</foo>")
    right.write_text(r"<foo>same</foo>")

    assert _invoke(left, right) == _Output(0, "", "")
    assert _invoke("--exit-code", left, right) == _Output(0, "", "")
    assert _invoke("--quiet", left, right) == _Output(0, "", "")


def test_html(tmp_path: pathlib.Path) -> None:
    """Show that HTML documents can be parsed as well."""
    a = tmp_path / "a.html"
    b = tmp_path / "b.html"
    a.write_text("<p>input a")
    b.write_text("<p>input b")

    diff_ab: str = inline_snapshot.snapshot("""\
<html>
    <body>
      <p>
-       input a
+       input b
      </p>
    </body>
  </html>\
""")

    assert _invoke(a, a) == _Output(2, "", ANY)
    assert _invoke("--html", a, a) == _Output(0, "", "")
    assert _invoke("--html", a, b) == _Output(0, diff_ab, "")


def test_errors(tmp_path: pathlib.Path) -> None:
    """Demonstrate CLI errors."""
    a = tmp_path / "a"
    assert _invoke(a, a) == _Output(2, "", f"{a}: not a file")

    a.write_text("not an xml document")
    assert _invoke(a, a) == _Output(
        2, "", f"{a}: Start tag expected, '<' not found, line 1, column 1"
    )


def test_version() -> None:
    """Demonstrate the `--version` output."""
    expected: str = inline_snapshot.snapshot("yaxmldiff 0.2.0")
    assert _invoke("--version") == _Output(0, stdout=expected, stderr="")


@dataclasses.dataclass
class _Output:
    status: int
    stdout: str
    stderr: str


def _invoke(*args: str | pathlib.Path) -> _Output:
    with pytest.MonkeyPatch.context() as m:
        m.setattr(sys, "stdout", stdout := io.StringIO())
        m.setattr(sys, "stderr", stderr := io.StringIO())
        m.setattr(sys, "argv", ["yaxmldiff", *(str(arg) for arg in args)])

        with pytest.raises(SystemExit) as exc:
            main()

    traceback.print_exception(exc.value)  # for debugging

    # Decode the SystemExit argument per the docs:
    # <https://docs.python.org/3/library/sys.html#sys.exit>
    match exc.value.code:
        case int() as code:
            pass
        case str():
            code = 1
        case None:
            code = 0

    return _Output(code, stdout.getvalue().strip(), stderr.getvalue().strip())
