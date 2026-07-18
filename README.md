# yaxmldiff – Yet Another XML Diff Library

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

## `compare_xml()`

Compare two XML documents.

If the documents are given as strings, they are parsed first.
Alternatively, the documents can be given as an `lxml.etree` object.

Returns: None if both are equal, a diff otherwise.

Signature:

``` python
def compare_xml(
    left: str | Element,
    right: str | Element,
) -> str | None:
```

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

There are tons of XML diffing tools for Python.

Most closely related is [`lxml.doctestcompare`](https://lxml.de/apidoc/lxml.doctestcompare.html).
The lxml variant has lots of useful tools for doctests,
such as ignoring subtrees with an `<any>` tag or content with an `...` ellipsis.
In contrast, yaxmldiff will compare two documents without further transformations.
Another big difference is in the output.
Whereas lxml will add inline annotations,
yaxmldiff tries to emulate a unified diff,
and will collapse uninteresting parts of the document.

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
