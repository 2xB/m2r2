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
class M2R(mistune.Markdown):
    def __init__(self, renderer=None, block=None, inline=None, plugins=None):
        renderer = renderer or RestRenderer()
        block = block or RestBlockParser()
        inline = inline or RestInlineParser(renderer)
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
            return PROLOG + output
        else:
            return output


def convert(text, **kwargs):
    return M2R(**kwargs)(text)
