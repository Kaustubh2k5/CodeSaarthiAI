import os
from collections import defaultdict

# ---------------------------------------------------
# Extension → Language Mapping
# (extend gradually as needed)
# ---------------------------------------------------
EXTENSION_MAP = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".cpp": "cpp",
    ".c": "c",
    ".cs": "csharp",
    ".php": "php",
}

# ---------------------------------------------------
# Directories we NEVER want to index
# (massive performance improvement)
# ---------------------------------------------------
SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
    "out",
    ".venv",
    "venv",
    ".idea",
    ".vscode",
    "target",
}


def should_skip_dir(path: str) -> bool:
    """
    Returns True if directory should be ignored.
    """
    parts = set(path.split(os.sep))
    return not parts.isdisjoint(SKIP_DIRS)


# ---------------------------------------------------
# MAIN FUNCTION
# ---------------------------------------------------
def detect_languages(repo_path: str) -> dict:
    """
    Scan repository and group files by language.

    Returns:
        {
            "python": [file1.py, file2.py],
            "typescript": [file3.ts]
        }
    """

    language_files = defaultdict(list)

    for root, dirs, files in os.walk(repo_path):

        # Remove skipped directories from traversal
        dirs[:] = [
            d for d in dirs
            if not should_skip_dir(os.path.join(root, d))
        ]

        for file in files:

            ext = os.path.splitext(file)[1].lower()

            if ext not in EXTENSION_MAP:
                continue

            language = EXTENSION_MAP[ext]
            full_path = os.path.join(root, file)

            language_files[language].append(full_path)

    return dict(language_files)