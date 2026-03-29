=========
Changelog
=========

Version 3.0.0
=============

- [enhancement] Compatibility with Mau 5
- [fix] Use node.deepcopy() instead of manual node reconstruction
- [fix] Use .get() instead of .pop() on node arguments to avoid mutation
- [fix] Handle non-Pygments highlighters without crashing
- [fix] Fixed default value of hl_line_styles in MultiHighlightFormatter

Version 2.0.2
=============

- [fix] Fixed missing `nowrap` in Pygments configuration
- [fix] Fixed usage and positioning of callouts in `source.html` template

Version 2.0.1
=============

- [internal] Added end-to-end tests for HtmlVisitor()

Version 2.0.0
=============

- [enhancement] Templates have been adapted to match Mau v4
- [enhancement] Templates have been moved to files to simplify development

Version 1.1.1
=============

- [fix] Fixed retrieval of Pygments parameters from Mau configuration

Version 1.1.0
=============

- [enhancement] Added template for RawNode nodes
- [fix] Accept *args and **kwargs in visit functions

Version 1.0.0
=============

- A working initial implementation

