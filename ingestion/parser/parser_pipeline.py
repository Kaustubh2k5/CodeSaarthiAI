from ingestion.parser.levels.level1_registry import extract_structure
from ingestion.parser.levels.level2_dependencies import extract_dependencies
from ingestion.parser.levels.level3_calls import extract_calls
from ingestion.parser.levels.level4_frameworks import extract_framework_signals


def parse_file(parser, file_path, language):

    with open(file_path, "rb") as f:
        source = f.read()

    tree = parser.parse(source)
    root = tree.root_node

    symbols = extract_structure(root, source, file_path, language)

    extract_dependencies(root, source, symbols)
    extract_calls(root, source, symbols)
    extract_framework_signals(root, source, symbols)

    return symbols