class GenericAdapter:

    def parse_file(self, parser, file_path, pipeline, language):
        """
        Generic languages use the shared pipeline directly.
        """
        return pipeline(parser, file_path, language)