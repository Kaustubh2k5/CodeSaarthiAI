def extract_calls(root, source, symbols):

    # Map symbol name → symbol object
    symbol_map = {s.name: s for s in symbols}

    def get_text(node):
        return source[node.start_byte:node.end_byte].decode(
            errors="ignore"
        )

    current_function = None

    def walk(node):
        nonlocal current_function

        # ----------------------------
        # Enter function scope
        # ----------------------------
        if node.type in (
            "function_definition",
            "function_declaration",
            "method_definition",
        ):
            name_node = node.child_by_field_name("name")
            if name_node:
                fn_name = get_text(name_node)
                current_function = symbol_map.get(fn_name)

        # ----------------------------
        # Detect calls
        # ----------------------------
        if node.type in ("call", "call_expression"):

            if current_function:
                call_text = get_text(node)

                # extract simple function name
                call_name = call_text.split("(")[0].split(".")[-1]

                current_function.calls.append(call_name)

        # recurse
        for child in node.children:
            walk(child)

        # ----------------------------
        # Exit scope
        # ----------------------------
        if node.type in (
            "function_definition",
            "function_declaration",
            "method_definition",
        ):
            current_function = None

    walk(root)