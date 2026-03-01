def extract_framework_signals(root, source, symbols):

    def get_text(node):
        return source[node.start_byte:node.end_byte].decode(errors="ignore")

    def walk(node):

        text = get_text(node)

        # FastAPI / Flask decorators
        if node.type == "decorator":
            if "app." in text or "router." in text:
                for s in symbols:
                    s.framework_tags.append("api_route")

        # Express / fetch style routes
        if node.type == "call_expression":
            if any(keyword in text for keyword in [
                "app.get",
                "app.post",
                "router.get",
                "router.post",
                "fetch(",
                "axios."
            ]):
                for s in symbols:
                    s.framework_tags.append("api_call")

        for child in node.children:
            walk(child)

    walk(root)