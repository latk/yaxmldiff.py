# yaxmldiff – Yet Another XML Diff Library

This library checks if two XML documents seem semantically equivalent.
If not, it produces something similar to a unified diff.

Example:

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

## `compare_xml()`

Compare two XML documents.

If the documents are given as strings, they are parsed first.

Returns: None if both are equal, a diff otherwise.

Signature:

``` python
def compare_xml(
    left: Union[str, Element],
    right: Union[str, Element],
) -> Optional[str]:
```

## Examples

Example: equal documents

    >>> print(compare_xml("<a/>", "<a/>"))
    None

Example: different tag

    >>> print(compare_xml("<a/>", "<b x='2'/>"))
    - <a/>
    + <b .../>

Example: changed text

    >>> print(compare_xml("<root><a/>foo</root>", "<root><a/>bar</root>"))
      <root>
        <a/>
    -   foo
    +   bar
      </root>

Example: nested changed text, collapses other nodes

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

Example: inserted node

    >>> print(compare_xml("<r><a/></r>", "<r><a/><b/></r>"))
      <r>
        <a/>
    +   <b/>
      </r>

Example: changed attributes

    >>> print(compare_xml(
    ...     "<a onlya='1' both='2' changed='3'/>",
    ...     "<a onlyb='1' both='2' changed='4'/>",
    ... ))
      <a both="2"
    -   onlya="1"
    -   changed="3"
    +   changed="4"
    +   onlyb="1"
      />

Example: can hande encoding declarations

    >>> print(compare_xml(
    ...     "<?xml version='1.0' encoding='UTF-8'?><a/>",
    ...     "<a/>",
    ... ))
    None

Example: comparison ignores surrounding space and newlines

    >>> print(compare_xml("<a>b<c/></a>", "\n <a> \n b \n <c \n/> \n </a> \n "))
    None

Example: pre-parse documents

    >>> import lxml.etree
    >>> print(compare_xml(lxml.etree.XML('<a parsed="yes"/>'), "<a parsed='no'/>"))
      <a
    -   parsed="yes"
    +   parsed="no"
      />

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

Automation is based on [Nox](https://nox.thea.codes/).
See `nox --list` for various tasks.
You can run `nox -s test` for particular targets,
or just `nox` for a complete QA pipeline.

## License

Copyright 2021 Lukas Atkinson

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
