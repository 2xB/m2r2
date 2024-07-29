#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

import mistune
from pkg_resources import get_distribution

from m2r2.constants import PROLOG
from m2r2.rst.parser import RestBlockParser, RestInlineParser
from m2r2.rst.renderer import RestRenderer

__version__ = get_distribution("m2r2").version


# TODO: check this
class M2R2(mistune.Markdown):
    def __init__(
        self,
        renderer=None,
        block=None,
        inline=None,
        plugins=None,
        use_mermaid: bool = False,
        parse_relative_links: bool = False,
        anonymous_references: bool = False,
        disable_inline_math: bool = True,
        no_underscore_emphasis: bool = True,
    ):
        renderer = renderer or RestRenderer(
            use_mermaid=use_mermaid,
            parse_relative_links=parse_relative_links,
            anonymous_references=anonymous_references,
        )
        block = block or RestBlockParser()
        inline = inline or RestInlineParser(
            renderer,
            disable_inline_math=disable_inline_math,
            no_underscore_emphasis=no_underscore_emphasis,
        )
        super().__init__(renderer=renderer, block=block, inline=inline, plugins=plugins)

    def parse(self, s, state=None):
        output = super().parse(s, state)
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
            return PROLOG + output
        return output


def convert(text, **kwargs):
    return M2R2(**kwargs)(text)
