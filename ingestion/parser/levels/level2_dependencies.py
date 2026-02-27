def extract_dependencies(root, source, symbols):

    imports_found = []

    def get_text(node):
        return source[node.start_byte:node.end_byte].decode(errors="ignore")

    def walk(node):

        if node.type in (
            "import_statement",
            "import_from_statement",
            "import_clause",
        ):
            imports_found.append(get_text(node))

        for child in node.children:
            walk(child)

    walk(root)

    # attach imports to all file symbols
    for symbol in symbols:
        symbol.imports.extend(imports_found)