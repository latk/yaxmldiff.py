# yaxmldiff – Yet Another XML Diff Library

[ GitHub: [latk/yaxmldiff.py](https://github.com/latk/yaxmldiff.py)
| PyPI: [yaxmldiff](https://pypi.org/project/yaxmldiff/)
]

This library checks if two XML documents seem semantically equivalent.
If not, it produces something similar to a unified diff.

Example:

```pycon
>>> from yaxmldiff import compare_xml
>>> print(compare_xml("<same/>", "  <same /> <!--ignored-->"))
None
>>> print(compare_xml("<doc><a id='a'/></doc>", "<doc><a name='a'/></doc>"))
  <doc>
    <a
-     id="a"
+     name="a"
    />
  </doc>

```

## Installation

Yaxmldiff is available on PyPI: <https://pypi.org/project/yaxmldiff>

If you want to use yaxmldiff as a **Python library**, add it to your project dependencies.
How to do this depends on your project manager. Examples:

* `pip install yaxmldiff`
* `uv add yaxmldiff`
* `poetry add yaxmldiff`

Installing the library will also install the command line interface.

If you only want to use the **CLI**, you can install into a dedicated venv using tools
such as [uv](https://docs.astral.sh/uv/guides/tools/)
or [pipx](https://pipx.pypa.io/):

* `uv tool install yaxmldiff`
* `pipx install yaxmldiff`

If you want to try out the CLI without installing permanently, you can use:

* `uvx yaxmldiff`
* `pipx run yaxmldiff`

You can also preview a bleeding-edge version from GitHub:

* `uvx git+https://github.com/latk/yaxmldiff.py`
* `pipx run --spec git+https://github.com/latk/yaxmldiff.py yaxmldiff`

## `compare_xml()`

Compare two XML documents.

If the documents are given as strings, they are parsed first.
Alternatively, the documents can be given as an `lxml.etree` object.

Args:

* left: an input document
* right: an input document
* context: how many lines of context to preserve around each change
* comments: whether comments and processing instructions will be diffed as well (default: true)

Returns: None if both are equal, a diff otherwise.

Signature:

``` python
def compare_xml(
    left: str | Element,
    right: str | Element,
    *,
    context: int = 3,
    comments: bool = True,
) -> str | None:
```

## Command line interface

Yaxmldiff can also be used as a command line tool.

Installation: The CLI is installed as part of the `yaxmldiff` package, see instructions above.

<!-- begin usage -->

Usage: `yaxmldiff LEFT RIGHT [--html, --no-html] [-U N] [--comments, --no-comments] [--exit-code, --no-exit-code] [--quiet, --no-quiet] [-h] [--completion COMPLETION]`

Compare two XML files via a structural diff.

The output is similar to an unified diff (like the one used by Git),
but the diff is performed structurally: element by element, not line by line.
Whitespace is generally ignored.

**Input Options:**

- `LEFT`

  A file to compare.

- `RIGHT`

  A file to compare.

- `[--html, --no-html]`

  Parse the files as HTML.

**Options:**

- `[-U, --context, --unified N]`

  How many lines of context to show around each change.

  The output will always use the "unified diff" format, never the "context" format.
  Where content is elided, the output cannot use the `@@ ... @@` markers due to the structural nature of the diff,
  and will instead insert a placeholder like `... skipped 12 lines`.

- `[--comments, --no-comments]`

  Whether comments and processing instructions will be diffed as well.

- `[--exit-code, --no-exit-code]`

  Exit with code 1 if files differ, just like the standard `diff` tool.

- `[--quiet, --no-quiet]`

  Don't print the diff, only check if the inputs differ. Implies `--exit-code`.

**Help:**

- `[-h, --help]`

  Show this message and exit.

- `[--completion COMPLETION]`

  Use `--completion generate` to print shell-specific completion source.

**Exit code:** exits with `0` on success, or `2` if there was a problem.
If `--exit-code` or `--quiet` were enabled, exit with code `1` if the files differ.

More info at the yaxmldiff website: <https://github.com/latk/yaxmldiff.py>

<!-- end usage -->

## Examples

Example: equal documents

```pycon
>>> print(compare_xml("<a/>", "<a/>"))
None

```

Example: different tag

```pycon
>>> print(compare_xml("<a/>", "<b x='2'/>"))
- <a/>
+ <b .../>

```

Example: changed text

```pycon
>>> print(compare_xml("<root><a/>foo</root>", "<root><a/>bar</root>"))
  <root>
    <a/>
-   foo
+   bar
  </root>

```

Example: nested changed text, collapses other nodes

```pycon
>>> print(compare_xml(
...     "<root><uninteresting a='b'>foo</uninteresting><scope>a</scope></root>",
...     "<root><uninteresting a='b'>foo</uninteresting><scope>b</scope></root>",
... ))
  <root>
    <uninteresting ...>...</uninteresting>
    <scope>
-     a
+     b
    </scope>
  </root>

```

Example: inserted and removed nodes

```pycon
>>> print(compare_xml("<r><a/><c/></r>", "<r><a/><b/><c/></r>"))
  <r>
    <a/>
+   <b/>
    <c/>
  </r>

```

```pycon
>>> print(compare_xml("<r><a/><b/><c/></r>", "<r><a/><c/></r>"))
  <r>
    <a/>
-   <b/>
    <c/>
  </r>

```


Example: changed attributes

```pycon
>>> print(compare_xml(
...     "<a onlya='1' both='2' changed='3'/>",
...     "<a onlyb='1' both='2' changed='4'/>",
... ))
  <a both="2"
-   changed="3"
-   onlya="1"
+   changed="4"
+   onlyb="1"
  />

```

Example: changed attrs collapse content

```pycon
>>> print(compare_xml("<a>content</a>", "<a attribute='value'>content</a>"))
  <a
+   attribute="value"
  >
    ...
  </a>

```

Example: collapse common context

```pycon
>>> print(compare_xml(
...     "<root><a/><b/><c/><d/><e/><f/><changed-left/></root>",
...     "<root><a/><b/><c/><d/><e/><f/><changed-right/></root>"))
  <root>
    ... skipped 3 lines
    <d/>
    <e/>
    <f/>
-   <changed-left/>
+   <changed-right/>
  </root>

```

Example: can hande encoding declarations

```pycon
>>> print(compare_xml(
...     "<?xml version='1.0' encoding='UTF-8'?><a/>",
...     "<a/>",
... ))
None

```

Example: comparison ignores surrounding space and newlines

```pycon
>>> print(compare_xml("<a>b<c/></a>", "\n <a> \n b \n <c \n/> \n </a> \n "))
None

```

Example: pre-parse documents

```pycon
>>> import lxml.etree
>>> print(compare_xml(lxml.etree.XML('<a parsed="yes"/>'), "<a parsed='no'/>"))
  <a
-   parsed="yes"
+   parsed="no"
  />

```

Example: can handle XML namespaces

```pycon
>>> print(compare_xml(
...  '<html:html xmlns:html="http://www.w3.org/1999/xhtml"><html:body>explicit namespaces</html:body></html:html>',
...  '<html xmlns="http://www.w3.org/1999/xhtml"><body>implicit namespaces</body></html>',
... ))
  <html ...>
    <body ...>
-     explicit namespaces
+     implicit namespaces
    </body>
  </html>

```

```pycon
>>> print(compare_xml(
...  '<html xmlns="http://www.w3.org/1999/xhtml"><body>implicit namespaces</body></html>',
...  '<html><body>no namespaces</body></html>',
... ))
- <html xmlns="http://www.w3.org/1999/xhtml">...</html>
+ <html>...</html>

```

Example: can optionally handle comments

```pycon
>>> print(compare_xml('<a><!-- foo --></a>', '<a><!-- bar --></a>'))
  <a>
    <!--
-     foo
+     bar
    -->
  </a>

```

```pycon
>>> print(compare_xml('<a><!-- same --><x/></a>', '<a><!-- same --><y/></a>'))
  <a>
    <!-- same -->
-   <x/>
+   <y/>
  </a>

```

```pycon
>>> print(compare_xml('<a><!-- foo --></a>', '<a><!-- bar --></a>', comments=False))
None
>>> print(compare_xml('<a><!-- same --><x/></a>', '<a><!-- same --><y/></a>', comments=False))
  <a>
-   <x/>
+   <y/>
  </a>

```

Example: can handle processing instructions

```pycon
>>> print(compare_xml('<a><?php echo 123; ?></a>', '<a><?php echo "abc"; ?></a>'))
  <a>
    <?php
-     echo 123;
+     echo "abc";
    ?>
  </a>

```

```pycon
>>> print(compare_xml('<a><?math 3*3 ?></a>', '<a><?php echo "abc"; ?></a>'))
  <a>
-   <?math 3*3?>
+   <?php echo "abc";?>
  </a>

```

Example: can diff nodes of different types

```pycon
>>> print(compare_xml('<a>text<!-- comment --></a>', '<a><element/><?pi?></a>'))
  <a>
-   text
+   <element/>
-   <!-- comment -->
+   <?pi ?>
  </a>

```

## Related software

There are tons of XML diffing tools.

Most closely related is [`lxml.doctestcompare`](https://lxml.de/apidoc/lxml.doctestcompare.html) which is specifically intended for Python doctests.
It has test-oriented features
such as ignoring subtrees with an `<any>` tag or content with an `...` ellipsis.
In contrast, yaxmldiff will compare two documents without further transformations.
Another big difference is in the output.
Whereas lxml will add inline annotations,
yaxmldiff tries to emulate a unified diff,
and will collapse uninteresting parts of the document.

The `xmldiff` tool (PyPI: [xmldiff](https://pypi.org/project/xmldiff/) GitHub: [Shoobx/xmldiff](https://github.com/Shoobx/xmldiff)) is a much better diff tool than `yaxmldiff`.
It can be used both as a Python library and as a CLI.
However, it produces an XML patch: XPath-based instructions on what to move, add, or delete.
This output is not particularly human-readable, as there's no context.
An alternative XML formatter renders the diff in XML form, but that will show the full document, plus diff instructions nodes from a `diff` XML-namespace.

<details><summary>xmldiff vs yaxmldiff output comparison</summary>

```console
$ uvx xmldiff --version
xmldiff 3.0

$ uvx xmldiff a.xml b.xml
[update-text, /foo[1], "right", "left"]

$ uvx xmldiff a.xml b.xml --pretty-print --formatter xml
<foo xmlns:diff="http://namespaces.shoobx.com/diff"><diff:delete>lef</diff:delete><diff:insert>righ</diff:insert>t</foo>

$ yaxmldiff a.xml b.xml
  <foo>
-   left
+   right
  </foo>
```

</details>

The [`difftastic` tool](https://difftastic.wilfred.me.uk/) has really good support for structural diffs across many languages.
However, it is purely a command line tool.
It cannot be used from Python as a library.
The output also relies on color, unlike the unified diff format.

<details><summary>difftastic vs yaxmldiff output comparison</summary>

```console
$ difftastic --version
Difftastic 0.69.0

Revision:  90a0f1b6a 2026-04-29
Toolchain: 1.85.0
System:    linux x86_64 Snap

$ difftastic a.xml b.xml --display=inline
b.xml --- XML
1    <foo>left</foo>
   1 <foo>right</foo>

$ yaxmldiff a.xml b.xml
  <foo>
-   left
+   right
  </foo>
```

</details>

**Recommendations:**

If you're looking for a Python-based XML diffing library or CLI tool:

* pick the `lxml` doctest features if you want to match XML output in a doctest
* pick `xmldiff` if you want to generate machine-readable diffs
* pick `yaxmldiff` if you want to generate plaintext human-readable diffs

If you're looking for a command-line tool:

* pick `difftastic` if you want human-readable output with best-in-class structural diffing, and can rely on colored output
* pick `yaxmldiff` if you want human-readable output that works as plaintext

## Contributing

Use [uv](https://docs.astral.sh/uv) for virtualenv management.
After installing uv, run `uv sync --all-extras --dev` to install dependencies.

Common development tasks are managed via the [`just` tasks runner](https://github.com/casey/just).
Install it via your package manager.
If in doubt, use `pipx install rust-just`.
Once installed, run `just` or `just qa` for a complete QA pipeline with linters+typechecking+tests.
Run `just -l` to get a list of all recipes.

## License

Copyright 2021-2026 Lukas Atkinson

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
