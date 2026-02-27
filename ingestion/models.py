class Symbol:
    def __init__(self, id, name, type, file, language,
                 tenant_id=None, repo_id=None):
        self.id = id
        self.name = name
        self.type = type
        self.file = file
        self.language = language

        # optional but future-proof
        self.tenant_id = tenant_id
        self.repo_id = repo_id

        self.imports = []
        self.calls = []
        self.framework_tags = []

        self.description = ""
        self.embedding_text = ""
        self.keywords = []