# Changelog

## unreleased

* minimum Python version is 3.10
* minimum lxml version is 5
* support XML documents with comments or processing instructions (default: include comments and PIs in the diff)
* improved support for XML namespaces
* collapse repeated context lines at the same level (default: show 3 lines around each change)
* smarted detection of inserted/deleted nodes
* new command line interface (usage: `yaxmldiff left.xml right.xml`)
* (internal) refactor diffing logic to support the new features
* (internal) packaging updates

## 0.2.0 – 2024-09-29

* minimum Python version is 3.8
* (internal) packaging modernization

## 0.1.0 - 2021-06-13

* initial release
