from ingestion.repo_loader import load_repo
from ingestion.language_detector import detect_languages
from ingestion.parser.ast_parser import parse_files
import os
from ingestion.graph.graph_builder import GraphBuilder


def index_repo(repo_url, neptune_endpoint):

    # -----------------------------------
    # STEP 1 — Load repository
    # -----------------------------------
    repo_path = load_repo(repo_url)

    # -----------------------------------
    # STEP 2 — Detect languages
    # -----------------------------------
    language_files = detect_languages(repo_path)

    # -----------------------------------
    # STEP 3 — Parse AST → Symbols
    # -----------------------------------
    symbols = parse_files(language_files)

    print(f"\nExtracted {len(symbols)} symbols")

    # -----------------------------------
    # STEP 4 — Build Graph
    # -----------------------------------
    builder = GraphBuilder(os.getenv("ENRICH_WORKERS", 8))

    builder.build(symbols)

    print("Graph successfully built.")

    return symbols