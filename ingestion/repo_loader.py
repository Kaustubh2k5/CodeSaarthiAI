import git
import os
import hashlib

BASE_DIR = ".repos"

"""
this module is responsible for loading a git repository from a given URL and commit hash.
It uses the GitPython library to clone the repository if it doesn't exist locally, and checks out the 
specified commit if provided. The repository is stored in a local directory named ".repos" 
with a unique identifier based on the repository URL.
"""

def repo_id(url):
    return hashlib.md5(url.encode()).hexdigest()

def load_repo(repo_source):
    """
    Accepts either:
    - git URL
    - local folder path
    """

    # ✅ CASE 1 — Local folder (YOUR CURRENT TEST)
    if os.path.isdir(repo_source):
        print("Using local repository (no clone needed).")
        return os.path.abspath(repo_source)

    # ✅ CASE 2 — Remote git repo
    os.makedirs(BASE_DIR, exist_ok=True)

    path = os.path.join(BASE_DIR, repo_id(repo_source))

    if not os.path.exists(path):
        print("Cloning repository...")
        git.Repo.clone_from(repo_source, path)

    return path