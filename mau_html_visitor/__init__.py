import html
import sys
from importlib.resources import files

from mau.environment.environment import Environment
from mau.visitors.jinja_visitor import JinjaVisitor, load_templates_from_path
from pygments import highlight
from pygments.formatters import get_formatter_by_name
from pygments.lexers import get_lexer_by_name

templates = {}

load_templates_from_path(files("templates"), templates)

DEFAULT_TEMPLATES = {
    "macro.html": "",
    "command.html": "",
    "content.html": "",
}


class HtmlVisitor(JinjaVisitor):
    format_code = "html"
    extension = "html"

    default_templates = Environment(templates)
    default_templates.update(DEFAULT_TEMPLATES)

    # default_templates = DEFAULT_TEMPLATES

    def _visit_text(self, node, *args, **kwargs):
        base = super()._visit_text(node, *args, **kwargs)

        base["data"]["value"] = html.escape(base["data"]["value"])

        return base

    def _visit_source__default(self, node, *args, **kwargs):
        base = super()._visit_source__default(node, *args, **kwargs)

        result = base["data"]

        # The Pygments lexer for the given language
        lexer = get_lexer_by_name(node.language)

        # Fetch global configuration for Pygments
        formatter_config = self.environment.getnamespace(
            "mau.visitor.pygments.html"
        ).asdict()

        # Get all the attributes of this specific block
        # that start with `pygments.`
        node_pygments_config = dict(
            (k.replace("pygments.", ""), v)
            for k, v in node.kwargs.items()
            if k.startswith("pygments.")
        )

        # Converting from text to Python might be tricky,
        # so for now I just update the formatter config with
        # 'hl_lines' which is a list of comma-separated integers
        hl_lines = node_pygments_config.get("hl_lines", "")
        hl_lines = [i for i in hl_lines.split(",") if i != ""]

        # There might be lines marked as highlighted using
        # Mau's syntax. Pygments starts counting from 1, Mau from 0,
        # so adjust that.
        highlight_markers = [i + 1 for i in node.highlights]

        # Merge the two
        hl_lines = list(set(hl_lines) | set(highlight_markers))

        # Tell Pygments which lines we want to highlight
        formatter_config["hl_lines"] = hl_lines

        # Create the formatter and pass the config
        formatter = get_formatter_by_name("html", **formatter_config)

        code = result["code"]

        # Merge code lines to hightlight them
        src = "\n".join(code)

        # Highlight the source with Pygments
        highlighted_src = highlight(src, lexer, formatter)

        # Split highlighted code again
        code = highlighted_src.split("\n")

        result["code"] = list(zip(code, result["markers"]))

        base["data"] = result

        return base
