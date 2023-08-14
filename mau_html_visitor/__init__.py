import html

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import get_formatter_by_name

from mau.visitors.jinja_visitor import JinjaVisitor


DEFAULT_TEMPLATES = {
    "caret.html": "<sup>{{ content }}</sup>",
    "class.html": """<span class="{{ classes | join(' ') }}">{{ content }}</span>""",
    "image.html": (
        '<span class="image">'
        '<img src="{{ uri }}"{%if alt_text %} alt="{{ alt_text }}"{% endif %}>'
        "</span>"
    ),
    "link.html": '<a href="{{ target }}">{{ text }}</a>',
    "macro.html": "",
    "sentence.html": "{{ content }}",
    "star.html": "<strong>{{ content }}</strong>",
    "text.html": "{{ value }}",
    "tilde.html": "<sub>{{ content }}</sub>",
    "underscore.html": "<em>{{ content }}</em>",
    "verbatim.html": "<code>{{ value }}</code>",
    ########################################
    "block-admonition.html": (
        '<div class="admonition {{ kwargs.class }}">'
        '<i class="{{ kwargs.icon }}"></i>'
        '<div class="content">'
        '<div class="title">{{ kwargs.label }}</div>'
        "<div>{{ content }}</div>"
        "</div></div>"
    ),
    "block.html": (
        '<div class="{{ blocktype }}{% if classes %} {{ classes }}{% endif %}">'
        '{% if title %}<div class="title">{{ title }}</div>{% endif %}'
        '<div class="content">{{ content }}</div>'
        "</div>"
    ),
    "block-quote.html": (
        "<blockquote>"
        "{{ content }}"
        "<cite>{{ secondary_content }}</cite>"
        "</blockquote>"
    ),
    ########################################
    "source.html": (
        '<div class="{{ blocktype }}">'
        '{% if title %}<div class="title">{{ title }}</div>{% endif %}'
        '<div class="content">{% for line, callout in code %}'
        "{{ line }}{% if callout %} {{ callout }}{% endif %}\n"
        "{% endfor %}</div>"
        '{% if callouts %}<div class="callouts">'
        "<table><tbody>"
        "{% for callout_entry in callouts %}{{ callout_entry }}{% endfor %}"
        "</tbody></table>"
        "</div>{% endif %}"
        "</div>"
    ),
    "callouts_entry.html": (
        "<tr>"
        '<td><span class="callout">{{ marker }}</span></td>'
        "<td>{{ value }}</td>"
        "</tr>"
    ),
    "callout.html": '<span class="callout">{{ marker }}</span>',
    ########################################
    "command.html": "",
    "container.html": "{{ content }}",
    "document.html": "<html><head></head><body>{{ content }}</body></html>",
    "header.html": '<h{{ level }} id="{{ anchor }}">{{ value }}</h{{ level }}>',
    "horizontal_rule.html": "<hr>",
    "content.html": "",
    "content_image.html": (
        '<div class="imageblock">'
        '<div class="content">'
        '<img src="{{ uri }}"{% if alt_text %} alt="{{ alt_text }}"{% endif %} />'
        '{% if title %}<div class="title">{{ title }}</div>{% endif %}'
        "</div></div>"
    ),
    "paragraph.html": "<p>{{ content }}</p>",
    "raw.html": "{{ content }}",
    ########################################
    "list_item.html": "<li>{{ content }}</li>",
    "list.html": (
        "<{% if ordered %}ol{% else %}ul{% endif %}"
        "{% if kwargs.start %}start={{ kwargs.start }}{% endif %}>"
        "{{ items }}"
        "</{% if ordered %}ol{% else %}ul{% endif %}>"
    ),
    ########################################
    "toc_entry.html": (
        "<li>"
        '<a href="#{{ anchor }}">{{ value }}</a>'
        "{% if children %}<ul>{{ children }}</ul>{% endif %}"
        "</li>"
    ),
    "toc.html": "<div>{% if entries%}<ul>{{ entries }}</ul>{% endif %}</div>",
    ########################################
    "footnote.html": (
        "<sup>"
        '[<a id="{{ reference_anchor }}" href="#{{ definition_anchor }}">{{ number }}</a>]'
        "</sup>"
    ),
    "footnotes_entry.html": (
        '<div id="{{ definition_anchor }}">'
        '<a href="#{{ reference_anchor }}">{{ number }}</a> {{ content }}</div>'
    ),
    "footnotes.html": '<div id="_footnotes">{{ entries }}</div>',
    ########################################
    "reference.html": (
        '[<a id="{{ reference_anchor }}" href="#{{ content_anchor }}">{{ number }}</a>]'
    ),
    "references_entry.html": (
        '<div id="{{ content_anchor }}">'
        '<a href="#{{ reference_anchor }}">{{ number }}</a> {{ content }}</div>'
    ),
    "references.html": '<div id="_references">{{ entries }}</div>',
}


class HtmlVisitor(JinjaVisitor):
    format_code = "html"
    extension = "html"

    default_templates = DEFAULT_TEMPLATES

    def _visit_text(self, node):
        base = super()._visit_text(node)

        base["data"]["value"] = html.escape(base["data"]["value"])

        return base

    def _visit_source__default(self, node):
        base = super()._visit_source__default(node)

        result = base["data"]

        # The Pygments lexer for the given language
        lexer = get_lexer_by_name(node.language)

        # Fetch global configuration for Pygments and for the HtmlFormatter
        pygments_config = self.config.get("pygments", {})
        formatter_config = pygments_config.get("html", {})

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
