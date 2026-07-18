import typing as t

import yaxmldiff._diff as diff


def _render_shorthand(item: diff.DiffItem | t.Sequence[diff.DiffItem]) -> str:
    match item:
        case diff.Left(value):
            return f"-{value}"
        case diff.Right(value):
            return f"+{value}"
        case diff.Same(value):
            return value
        case diff.Nested(items):
            return f"({_render_shorthand(items)})"
        case multiple:
            return " ".join(_render_shorthand(x) for x in multiple)


def test_diff_seq_with_lookahead() -> None:
    """Verify that the inner diff function can calculate valid diffs."""

    def diff_and_render(left: str, right: str) -> str:
        return _render_shorthand(list(diff._diff_seq_with_lookahead(left, right)))

    assert diff_and_render("", "") == ""
    assert diff_and_render("abc", "abc") == "a b c"
    assert diff_and_render("ab", "a") == "a -b"
    assert diff_and_render("a", "ab") == "a +b"
    assert diff_and_render("aba", "aa") == "a -b a"
    assert diff_and_render("aa", "aba") == "a +b a"
    assert diff_and_render("aba", "aca") == "a -b +c a"
