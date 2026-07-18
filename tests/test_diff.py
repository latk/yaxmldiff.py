import re
import typing as t

import yaxmldiff._diff as diff


def _render_picture(item: diff.DiffItem | t.Sequence[diff.DiffItem]) -> str:
    """Create a short one-line picture representing the diff."""
    match item:
        case diff.Left(value):
            return f"-{value}"
        case diff.Right(value):
            return f"+{value}"
        case diff.Same(value) if m := re.fullmatch(
            r"\.\.\. skipped (\d+) lines", value
        ):
            return m[1]
        case diff.Same(value):
            return value
        case diff.Nested(items):
            return f"({_render_picture(items)})"
        case multiple:
            return " ".join(_render_picture(x) for x in multiple)


def test_diff_seq_with_lookahead() -> None:
    """Verify that the inner diff function can calculate valid diffs."""

    def diff_picture(left: str, right: str) -> str:
        return _render_picture(list(diff._diff_seq_with_lookahead(left, right)))

    assert diff_picture("", "") == ""
    assert diff_picture("abc", "abc") == "a b c"
    assert diff_picture("ab", "a") == "a -b"
    assert diff_picture("a", "ab") == "a +b"
    assert diff_picture("aba", "aa") == "a -b a"
    assert diff_picture("aa", "aba") == "a +b a"
    assert diff_picture("aba", "aca") == "a -b +c a"


def test_collapse_common_context() -> None:
    """Verify that common context can be collapsed safely.

    In the output pictures, collapsed lines are marked with a number.
    """

    def diff_picture(left: str, right: str) -> str:
        return _render_picture(list(diff.diff_seq(left, right)))

    # leading examples
    assert diff_picture("abcX", "abcY") == "a b c -X +Y"
    assert diff_picture("abcdX", "abcdY") == "a b c d -X +Y"
    assert diff_picture("abcdeX", "abcdeY") == "2 c d e -X +Y"
    assert diff_picture("abcdefX", "abcdefY") == "3 d e f -X +Y"

    # trailing examples
    assert diff_picture("Xabc", "Yabc") == "-X +Y a b c"
    assert diff_picture("Xabcd", "Yabcd") == "-X +Y a b c d"
    assert diff_picture("Xabcde", "Yabcde") == "-X +Y a b c 2"
    assert diff_picture("Xabcdef", "Yabcdef") == "-X +Y a b c 3"

    # middle examples
    assert diff_picture("XabcdefX", "YabcdefY") == "-X +Y a b c d e f -X +Y"
    assert diff_picture("XabcdefgX", "YabcdefgY") == "-X +Y a b c d e f g -X +Y"
    assert diff_picture("XabcdefghX", "YabcdefghY") == "-X +Y a b c 2 f g h -X +Y"
    assert diff_picture("XabcdefghiX", "YabcdefghiY") == "-X +Y a b c 3 g h i -X +Y"
