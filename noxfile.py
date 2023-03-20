import nox
import glob

nox.options.sessions = ["lint", "typecheck", "test"]

SOURCES = ["yaxmldiff.py"]


@nox.session
def lint(session: nox.Session) -> None:
    """check code style"""
    session.install("flake8", "black", "pylint", ".")
    session.run("black", "--diff", "--check", ".")
    session.run("flake8", ".")
    session.run("pylint", *SOURCES)


@nox.session
def reformat(session: nox.Session) -> None:
    """reformat the code"""
    session.install("black ~= 23.0")
    session.run("black", ".")


@nox.session
def typecheck(session: nox.Session) -> None:
    """run mypy typechecker"""
    session.install("mypy", "lxml-stubs")
    session.run("mypy", *SOURCES)


@nox.session
def test(session: nox.Session) -> None:
    """run all tests"""
    session.install("pytest", ".")
    session.run("pytest", "--doctest-glob=*.md")


@nox.session
def dist(session: nox.Session) -> None:
    """package the module"""
    session.install("build", "twine")
    session.run("python3", "-m", "build")
    session.run("twine", "check", "dist/*")

    # check that the dist can be installed
    wheels = glob.glob("dist/yaxmldiff-*.whl")
    assert len(wheels) == 1, f"Should only have one wheel but got {wheels!r}"
    session.install(wheels[0])
    session.run(
        "python",
        "-c",
        "import yaxmldiff; assert yaxmldiff.compare_xml('<x/>', '<x/>') is None",
    )
