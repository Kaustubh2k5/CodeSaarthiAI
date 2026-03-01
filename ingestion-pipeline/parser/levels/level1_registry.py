from ingestion.models import Symbol


STRUCTURE_NODE_TYPES = {
    "function_definition",
    "function_declaration",
    "method_definition",
    "class_definition",
    "class_declaration",
}


def extract_structure(root, source, file_path, language):

    symbols = []

    def get_text(node):
        return source[node.start_byte:node.end_byte].decode(errors="ignore")

    def walk(node):

        if node.type in STRUCTURE_NODE_TYPES:

            name_node = node.child_by_field_name("name")

            if name_node:
                name = get_text(name_node)

                symbol_type = (
                    "class" if "class" in node.type else "function"
                )

                symbols.append(
                    Symbol(
                        id=f"{file_path}::{name}",
                        name=name,
                        type=symbol_type,
                        file=file_path,
                        language=language,
                    )
                )

        # Detect arrow functions (TypeScript/JS)
        if node.type == "arrow_function":
            symbols.append(
                Symbol(
                    id=f"{file_path}::anonymous_arrow",
                    name="anonymous_arrow",
                    type="function",
                    file=file_path,
                    language=language,
                )
            )

        for child in node.children:
            walk(child)

    walk(root)
    return symbols