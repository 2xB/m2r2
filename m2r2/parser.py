from docutils import statemachine
from docutils.parsers import rst

from m2r2 import M2R


class M2RParser(rst.Parser):
    # Explicitly tell supported formats to sphinx
    supported = ("markdown", "md", "mkd")

    def parse(self, inputstring, document):
        """Parse `inputstring` and populate `document`, a document tree."""
        config = document.settings.env.config
        converter = M2R(
            no_underscore_emphasis=config.no_underscore_emphasis,
            parse_relative_links=config.m2r_parse_relative_links,
            anonymous_references=config.m2r_anonymous_references,
            disable_inline_math=config.m2r_disable_inline_math,
            use_mermaid=config.m2r_use_mermaid,
        )
        super(M2RParser, self).parse(converter(inputstring), document)
