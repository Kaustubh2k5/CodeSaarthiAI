class TypeScriptAdapter:
    """
    Adapter for TypeScript / TSX files.

    Uses shared parsing pipeline but allows
    TypeScript-specific enhancements later.
    """

    language = "typescript"

    def parse_file(self, parser, file_path, pipeline, language):
        """
        parser   : cached tree-sitter parser
        file_path: file to parse
        pipeline : parsing pipeline function
        language : language string
        """

        # Run shared parsing pipeline
        symbols = pipeline(parser, file_path, language)

        # ---- Future TypeScript-specific enrichments ----
        # (keep minimal for now)
        #
        # Example later:
        # - detect React components
        # - detect Express routes
        # - detect Next.js pages

        return symbols