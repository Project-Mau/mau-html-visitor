import html
from importlib.resources import files
from typing import Callable

from bs4 import BeautifulSoup
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import get_lexer_by_name

from mau.environment.environment import Environment
from mau.nodes.node import Node
from mau.visitors.jinja_visitor import JinjaVisitor, load_templates_from_path
from mau.nodes.source import SourceLineNode, SourceNode


# This removes trailing spaces and newlines from
# HTML templates. This allows to save them in a
# pretty format without passing unnecessary
# spaces and indentations to the template engine.
def filter_html(text):
    dedent = [i.lstrip() for i in text.split("\n")]
    dedent = [i for i in dedent if i != ""]
    return "".join(dedent)


templates = load_templates_from_path(
    str(files(__package__).joinpath("templates")), filter_html
)


# Inspired by https://stackoverflow.com/a/39603382
# Posted by lorenzog
# See https://pygments-doc.readthedocs.io/en/latest/formatters/html.html
class MultiHighlightFormatter(HtmlFormatter):
    """Overriding formatter to highlight more than one kind of lines"""

    def __init__(self, **options):
        super().__init__(**options)

        # This is a dictionary of {line_number: highlight_style}.
        self.hl_line_styles = options.get("hl_line_styles", [])

        # Internally, Pygments calls _highlight_lines only
        # if hl_lines is set.
        self.hl_lines = list(self.hl_line_styles.keys())

    def _highlight_lines(self, tokensource):
        # tokensource is a generator of tuples
        # (line_type, line_content)
        # where line_type is either 0 for a non
        # formatted line and 1 for a line of
        # formatted source code.

        for i, (line_type, line_content) in enumerate(tokensource):
            # If the line is not formatted source code
            # leave it untouched.
            if line_type != 1:
                yield line_type, line_content

            # i is a Python index, so line 1 has index 0.
            # We also convert the index to a string,
            # as Mau line numbers are not integers.
            line_number = str(i + 1)

            # Get the style or None.
            line_style = self.hl_line_styles.get(line_number)

            if line_style:
                # Add the style as a CSS class in the form
                # `hll-STYLE` which mimics the standard Pygments
                # highlighting that uses the class `hll`.
                yield 1, f'<span class="hll-{line_style}">{line_content}</span>'
            else:
                # No style, no party. Just return the line as it is.
                yield 1, line_content


class HtmlVisitor(JinjaVisitor):
    format_code = "html"
    extension = "html"
    templates_preprocess: Callable[[str], str] | None = filter_html

    default_templates = Environment.from_dict(templates)

    def _postprocess(self, result, *args, **kwargs):
        # Check if the visitor settings enable
        # postprocessing of the resulting HTML.
        if not self.environment.get("mau.visitor.html.pretty", False):
            return result

        # The result is HTML code, let's
        # make it nice to read.
        soup = BeautifulSoup(result, "html.parser")
        pretty = soup.prettify()

        return pretty

    def _visit_text(self, node: Node, *args, **kwargs) -> dict:
        result = super()._visit_text(node, *args, **kwargs)

        result["value"] = html.escape(result["value"])

        return result

    def _visit_verbatim(self, node: Node, *args, **kwargs) -> dict:
        result = super()._visit_verbatim(node, *args, **kwargs)

        result["value"] = html.escape(result["value"])

        return result

    def _visit_source(self, node: Node, *args, **kwargs) -> dict:
        # Copy the source node and all source
        # line nodes to avoid changing them during
        # the process.
        # Without this, if a source node is visited
        # twice (which can happen if it's in a footnote)
        # the content of the second render
        # is the highlight of the highlight.
        content = []
        for line in node.content:
            new_line_node = SourceLineNode(
                line_number=line.line_number,
                line_content=line.line_content,
                highlight_style=line.highlight_style,
                marker=line.marker,
                parent=line.parent,
                arguments=line.arguments,
                info=line.info,
            )

            content.append(new_line_node)

        new_node = SourceNode(
            language=node.language,
            classes=node.classes,
            content=content,
            labels=node.labels,
            parent=node.parent,
            arguments=node.arguments,
            info=node.info,
        )

        # Collect all markers and remove them
        # from the source code.
        all_markers = []
        for line in content:
            # Save the marker.
            all_markers.append(line.marker)

            # Remove the marker.
            line.marker = None

        # Find all lines that are highlighted.
        highlighted_lines = [line for line in content if line.highlight_style]

        # Create a dictionary of {line_number: highlight_style}.
        # Convert the highlight_style using the aliases
        # loaded above.
        hl_line_styles: dict[str, str] = {}
        for line in highlighted_lines:
            # # Get the highlight style. Replace it
            # # with the aliased version if any.
            # highlight_style = style_aliases.get(
            #     line.highlight_style, line.highlight_style
            # )

            hl_line_styles[line.line_number] = line.highlight_style

        # Render the code without markers.
        code = self.visitlist(new_node, content, *args, **kwargs)

        # Find the highlighter set in the environment.
        highlighter_name = self.environment.get(
            "mau.visitor.html.highlighter", "pygments"
        )

        # Override the globally set highlighter if
        # this specific block has a different one.
        highlighter = new_node.arguments.named_args.pop("highlighter", highlighter_name)

        if highlighter == "pygments":
            # The Pygments lexer for the given language.
            lexer = get_lexer_by_name(new_node.language)

            # Fetch global configuration for Pygments.
            formatter_config = self.environment.get(
                "mau.visitor.html.pygments", Environment.from_dict({"nowrap": True})
            ).asdict()

            # Tell Pygments which lines we want to highlight
            # and which style we want for each.
            formatter_config["hl_line_styles"] = hl_line_styles

            # Create the formatter and pass the config.
            formatter = MultiHighlightFormatter(**formatter_config)
            # formatter = get_formatter_by_name("html", **formatter_config)

            # Highlight the source with Pygments
            highlighted_src = highlight(code, lexer, formatter)

        # Split highlighted code again into lines.
        highlighted_lines = highlighted_src.split("\n")

        # This is a list of tuples (node, highlighted_code, marker)
        # for each node in the original content.
        tmp_content_tuples = list(zip(content, highlighted_lines, all_markers))

        # Put everything together.
        for line_node, code, marker in tmp_content_tuples:
            line_node.line_content = code
            line_node.marker = marker

        result = super()._visit_source(new_node, *args, **kwargs)

        return result
