from tree_sitter_language_pack import get_parser

PARSER_CACHE = {}


def get_cached_parser(language):

    if language not in PARSER_CACHE:
        PARSER_CACHE[language] = get_parser(language)

    return PARSER_CACHE[language]