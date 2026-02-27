class PythonAdapter:

    def parse_file(self, parser, file_path, pipeline, language):

        # run normal parsing
        symbols = pipeline(parser, file_path, language)

        # future: python-specific enhancements
        # detect decorators, async patterns, etc.

        return symbols