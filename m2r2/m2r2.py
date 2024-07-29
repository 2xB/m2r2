#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

import os
import re
from urllib.parse import urlparse

import mistune
from docutils import io, nodes, statemachine, utils
from docutils.parsers import rst
from docutils.utils import column_width
from mistune.renderers import BaseRenderer
from pkg_resources import get_distribution

__version__ = get_distribution("m2r2").version

PROLOG = """\
.. role:: raw-html-m2r(raw)
   :format: html

"""


class RestRenderer(BaseRenderer):
    _include_raw_html = False
    list_indent_re = re.compile(r"^(\s*(#\.|\*)\s)")
    indent = " " * 3
    list_marker = "{#__rest_list_mark__#}"
    hmarks = {
        1: "=",
        2: "-",
        3: "^",
        4: "~",
        5: '"',
        6: "#",
    }

    def __init__(self, **kwargs):
        self.parse_relative_links = kwargs.pop("parse_relative_links", False)
        self.anonymous_references = kwargs.pop("anonymous_references", False)
        self.use_mermaid = kwargs.pop("use_mermaid", False)
        super().__init__(**kwargs)

    def finalize(self, data):
        return "".join(filter(lambda x: x is not None, data))

    def _indent_block(self, block):
        return "\n".join(
            self.indent + line if line else "" for line in block.splitlines()
        )

    def _raw_html(self, html):
        self._include_raw_html = True
        return r"\ :raw-html-m2r:`{}`\ ".format(html)

    def block_text(self, text) -> str:
        print(f"block_text={text}")
        return f"{text}\n"

    def newline(self):
        return ""

    def block_code(self, children, info=None):
        print(f"block_code={children=}, {info=}")
        lang = info.strip() if info else None
        if lang == "math":
            first_line = "\n.. math::\n\n"
        elif lang == "mermaid" and self.use_mermaid:
            first_line = "\n.. mermaid::\n\n"
        elif lang:
            first_line = "\n.. code-block:: {}\n\n".format(lang)
        else:
            first_line = "\n.. code-block::\n\n"
        return first_line + self._indent_block(children) + "\n"

    def block_quote(self, text):
        return "\n..\n\n{}\n\n".format(self._indent_block(text.strip("\n")))

    def block_html(self, html):
        return "\n\n.. raw:: html\n\n" + self._indent_block(html) + "\n\n"

    def heading(self, text, level):
        return "\n{0}\n{1}\n".format(text, self.hmarks[level] * len(text))

    def thematic_break(self):
        return "\n----\n"

    def list(self, text, ordered, level, start=None):
        mark = "#. " if ordered else "* "
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line and not line.startswith(self.list_marker):
                lines[i] = " " * len(mark) + line
        return "\n{}\n".format("\n".join(lines)).replace(self.list_marker, mark)

    def list_item(self, text, level):
        return "\n" + self.list_marker + text

    def paragraph(self, text):
        print(f"paragraph={text}")
        if text[-2:] == "::":
            text = text[:-1]
        return f"\n{text}\n"

    def table(self, text):
        table = "\n.. list-table::\n"
        rows = text.split("\n")
        if rows and not rows[0].isspace():
            table = (
                table
                + self.indent
                + ":header-rows: 1\n\n"
                + self._indent_block(rows[0])
                + "\n"
            )
            rows = rows[1:]
        else:
            table = table + "\n"
        table = table + self._indent_block("\n".join(rows)) + "\n\n"
        return table

    def table_row(self, text):
        contents = text.splitlines()
        if not contents:
            return ""
        clist = ["* " + contents[0]]
        if len(contents) > 1:
            for c in contents[1:]:
                clist.append("  " + c)
        return "\n".join(clist) + "\n"

    def table_cell(self, text, align=None, is_head=False):
        return "- " + text + "\n"

    def strong(self, text):
        return r"\ **{}**\ ".format(text)

    def emphasis(self, text):
        return r"\ *{}*\ ".format(text)

    def codespan(self, text):
        if "``" not in text:
            return r"\ ``{}``\ ".format(text)
        else:
            # actually, docutils split spaces in literal
            return self._raw_html(
                '<code class="docutils literal">'
                '<span class="pre">{}</span>'
                "</code>".format(text.replace("`", "&#96;"))
            )

    def linebreak(self):
        return self._raw_html("<br>") + "\n"

    def strikethrough(self, text):
        return self._raw_html("<del>{}</del>".format(text))

    def text(self, text):
        return text

    def link(self, link, children=None, title=None):
        if self.anonymous_references:
            underscore = "__"
        else:
            underscore = "_"
        if title:
            return self._raw_html(
                '<a href="{link}" title="{title}">{text}</a>'.format(
                    link=link, title=title, text=children or link
                )
            )
        if not self.parse_relative_links:
            return r"\ `{text} <{target}>`{underscore}\ ".format(
                target=link, text=children or link, underscore=underscore
            )
        else:
            url_info = urlparse(link)
            if url_info.scheme:
                return r"\ `{text} <{target}>`{underscore}\ ".format(
                    target=link, text=children or link, underscore=underscore
                )
            else:
                link_type = "doc"
                anchor = url_info.fragment
                if url_info.fragment:
                    if url_info.path:
                        anchor = ""
                    else:
                        link_type = "ref"
                doc_link = "{doc_name}{anchor}".format(
                    doc_name=os.path.splitext(url_info.path)[0],
                    anchor=anchor,
                )
                return r"\ :{link_type}:`{text} <{doc_link}>`\ ".format(
                    link_type=link_type, doc_link=doc_link, text=children or link
                )

    def image(self, src, alt="", title=None):
        return "\n".join(
            [
                "",
                ".. image:: {}".format(src),
                "   :target: {}".format(src),
                "   :alt: {}".format(alt),
                "",
            ]
        )

    def inline_html(self, html):
        return self._raw_html(html)

    def footnote_ref(self, key, index):
        return r"\ [#fn-{}]_\ ".format(key)

    def footnote_item(self, key, text):
        return ".. [#fn-{0}] {1}\n".format(key, text.strip())

    def footnotes(self, text):
        return "\n\n" + text if text else ""

    """Below outputs are for rst."""

    def image_link(self, url, target, alt):
        return "\n".join(
            [
                "",
                ".. image:: {}".format(url),
                "   :target: {}".format(target),
                "   :alt: {}".format(alt),
                "",
            ]
        )

    def rest_role(self, text):
        return text

    def rest_link(self, text):
        return text

    def inline_math(self, math):
        """Extension of recommonmark."""
        return r":math:`{}`".format(math)

    def eol_literal_marker(self, marker):
        """Extension of recommonmark."""
        return marker

    def directive(self, text):
        return "\n" + text

    def rest_code_block(self, text):
        return "\n\n"


from typing import Any, Dict, Match, Tuple

import mistune

from m2r2.typing import Element, State, Token


class RestBlockParser(mistune.BlockParser):
    DIRECTIVE = re.compile(
        r"^( *\.\..*?)\n(?=\S)",
        re.DOTALL | re.MULTILINE,
    )
    ONELINE_DIRECTIVE = re.compile(
        r"^( *\.\..*?)$",
        re.DOTALL | re.MULTILINE,
    )
    REST_CODE_BLOCK = re.compile(
        r"^::\s*$",
        re.DOTALL | re.MULTILINE,
    )
    RULE_NAMES = mistune.BlockParser.RULE_NAMES + (
        "directive",
        "oneline_directive",
        "rest_code_block",
    )

    def parse_directive(self, match: Match, state: State) -> Token:
        return {"type": "directive", "text": match.group(1)}

    def parse_oneline_directive(self, match: Match, state: State) -> Token:
        # reuse directive output
        return {"type": "directive", "text": match.group(1)}

    def parse_rest_code_block(self, match: Match, state: State) -> Token:
        return {"type": "rest_code_block", "text": ""}


class RestInlineParser(mistune.InlineParser):
    IMAGE_LINK = re.compile(
        r"\[!\[(?P<alt>.*?)\]\((?P<url>.*?)\).*?\]\((?P<target>.*?)\)"
    )
    REST_ROLE = re.compile(r":.*?:`.*?`|`[^`]+`:.*?:")
    REST_LINK = re.compile(r"`[^`]*?`_")
    INLINE_MATH = re.compile(r"`\$(.*?)\$`")
    EOL_LITERAL_MARKER = re.compile(r"(\s+)?::\s*$")
    # add colon and space as special text
    TEXT = re.compile(r"^[\s\S]+?(?=[\\<!\[:_*`~ ]|https?://| {2,}\n|$)")
    # __word__ or **word**
    DOUBLE_EMPHASIS = re.compile(r"^([_*]){2}(?P<text>[\s\S]+?)\1{2}(?!\1)")
    # _word_ or *word*
    EMPHASIS = re.compile(
        r"^\b_((?:__|[^_])+?)_\b"  # _word_
        r"|"
        r"^\*(?P<text>(?:\*\*|[^\*])+?)\*(?!\*)"  # *word*
    )

    RUlE_NAMES = (
        "inline_math",
        "image_link",
        "rest_role",
        "rest_link",
        "eol_literal_marker",
    ) + mistune.InlineParser.RULE_NAMES

    def parse_double_emphasis(self, match: Match, state: State) -> Element:
        # may include code span
        return "double_emphasis", match.group("text")

    def parse_emphasis(self, match: Match, state: State) -> Element:
        # may include code span
        return "emphasis", match.group("text") or match.group(1)

    def parse_image_link(self, match: Match, state: State) -> Element:
        """Pass through rest role."""
        alt, src, target = match.groups()
        return "image_link", src, target, alt

    def parse_rest_role(self, match: Match, state: State) -> Element:
        """Pass through rest role."""
        return "rest_role", match.group(0)

    def parse_rest_link(self, match: Match, state: State) -> Element:
        """Pass through rest link."""
        return "rest_link", match.group(0)

    def parse_inline_math(self, match: Match, state: State) -> Element:
        """Pass through rest link."""
        return "inline_math", match.group(2)

    def parse_eol_literal_marker(self, match: Match, state: State) -> Element:
        """Pass through rest link."""
        marker = ":" if match.group(1) is None else ""
        return "eol_literal_marker", marker

    def no_underscore_emphasis(self):
        self.DOUBLE_EMPHASIS = re.compile(
            r"^\*{2}(?P<text>[\s\S]+?)\*{2}(?!\*)"  # **word**
        )
        self.EMPHASIS = re.compile(r"^\*(?P<text>(?:\*\*|[^\*])+?)\*(?!\*)")  # *word*

    def __init__(self, renderer, *args, **kwargs):
        # no_underscore_emphasis = kwargs.pop("no_underscore_emphasis", False)
        disable_inline_math = kwargs.pop("disable_inline_math", False)
        super().__init__(renderer, *args, **kwargs)
        # if not _is_sphinx:
        #    parse_options()
        # if no_underscore_emphasis or getattr(options, "no_underscore_emphasis", False):
        #    self.rules.no_underscore_emphasis()
        inline_maths = "inline_math" in self.RULE_NAMES
        if disable_inline_math:  # or getattr(options, "disable_inline_math", False):
            if inline_maths:
                self.RULE_NAMES = tuple(
                    x for x in self.RUlE_NAMES if x != "inline_math"
                )
        elif not inline_maths:
            self.RUlE_NAMES = ("inline_math", *self.RUlE_NAMES)


class M2R2(mistune.Markdown):
    def __init__(self, renderer=None, block=None, inline=None, plugins=None, **kwargs):
        disable_inline_math = kwargs.pop("disable_inline_math", False)
        renderer = renderer or RestRenderer(**kwargs)
        block = block or RestBlockParser()
        inline = inline or RestInlineParser(renderer, disable_inline_math)
        super().__init__(renderer=renderer, block=block, inline=inline, plugins=plugins)

    def parse(self, text):
        output = super().parse(text)
        return self.post_process(output)

    def post_process(self, text):
        output = (
            text.replace("\\ \n", "\n")
            .replace("\n\\ ", "\n")
            .replace(" \\ ", " ")
            .replace("\\  ", " ")
            .replace("\\ .", ".")
        )
        if self.renderer._include_raw_html:
            return (
                PROLOG + output
            )  # You might need to define 'prolog' if it's used in your original code
        else:
            return output


class M2R2Parser(rst.Parser, object):
    # Explicitly tell supported formats to sphinx
    supported = ("markdown", "md", "mkd")

    def parse(self, inputstrings, document):
        if isinstance(inputstrings, statemachine.StringList):
            inputstring = "\n".join(inputstrings)
        else:
            inputstring = inputstrings
        config = document.settings.env.config
        converter = M2R2(
            no_underscore_emphasis=config.no_underscore_emphasis,
            parse_relative_links=config.m2r_parse_relative_links,
            anonymous_references=config.m2r_anonymous_references,
            disable_inline_math=config.m2r_disable_inline_math,
            use_mermaid=config.m2r_use_mermaid,
        )
        super(M2R2Parser, self).parse(converter(inputstring), document)


class MdInclude(rst.Directive):
    """Directive class to include markdown in sphinx.

    Load a file and convert it to rst and insert as a node. Currently
    directive-specific options are not implemented.
    """

    required_arguments = 1
    optional_arguments = 0
    option_spec = {
        "start-line": int,
        "end-line": int,
    }

    def run(self):
        """Most of this method is from ``docutils.parser.rst.Directive``.

        docutils version: 0.12
        """
        if not self.state.document.settings.file_insertion_enabled:
            raise self.warning('"%s" directive disabled.' % self.name)
        source = self.state_machine.input_lines.source(
            self.lineno - self.state_machine.input_offset - 1
        )
        source_dir = os.path.dirname(os.path.abspath(source))
        path = rst.directives.path(self.arguments[0])
        path = os.path.normpath(os.path.join(source_dir, path))
        path = utils.relative_path(None, path)
        path = nodes.reprunicode(path)

        # get options (currently not use directive-specific options)
        encoding = self.options.get(
            "encoding", self.state.document.settings.input_encoding
        )
        e_handler = self.state.document.settings.input_encoding_error_handler
        tab_width = self.options.get(
            "tab-width", self.state.document.settings.tab_width
        )

        # open the including file
        try:
            self.state.document.settings.record_dependencies.add(path)
            include_file = io.FileInput(
                source_path=path, encoding=encoding, error_handler=e_handler
            )
        except UnicodeEncodeError:
            raise self.severe(
                'Problems with "%s" directive path:\n'
                'Cannot encode input file path "%s" '
                "(wrong locale?)." % (self.name, str(path))
            )
        except IOError as error:
            raise self.severe(
                'Problems with "%s" directive path:\n%s.'
                % (self.name, io.error_string(error))
            )

        # read from the file
        startline = self.options.get("start-line", None)
        endline = self.options.get("end-line", None)
        try:
            if startline or (endline is not None):
                lines = include_file.readlines()
                rawtext = "".join(lines[startline:endline])
            else:
                rawtext = include_file.read()
        except UnicodeError as error:
            raise self.severe(
                'Problem with "%s" directive:\n%s' % (self.name, io.error_string(error))
            )

        config = self.state.document.settings.env.config
        converter = M2R2(
            no_underscore_emphasis=config.no_underscore_emphasis,
            parse_relative_links=config.m2r_parse_relative_links,
            anonymous_references=config.m2r_anonymous_references,
            disable_inline_math=config.m2r_disable_inline_math,
            use_mermaid=config.m2r_use_mermaid,
        )
        include_lines = statemachine.string2lines(
            converter(rawtext), tab_width, convert_whitespace=True
        )
        self.state_machine.insert_input(include_lines, path)
        return []


def convert(text, **kwargs):
    return M2R2(**kwargs)(text)
