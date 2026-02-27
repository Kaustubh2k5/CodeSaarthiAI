"""
Simple end-to-end test runner for repository indexing + graph build.
"""
from dotenv import load_dotenv
load_dotenv()
import os
import sys
import time

sys.path.insert(0, os.path.abspath("."))

from ingestion.index_repo import index_repo


# --------------------------------------------------
# CONFIG
# --------------------------------------------------

PROJECT_PATH = r"/projects/work-dir/Hackathon/CodeSaarthiAI/CodeSaarthiAI/ingestion"

# AWS Neptune endpoint (CHANGE AFTER SETUP)
NEPTUNE_ENDPOINT = os.getenv("NEPTUNE_WRITE_ENDPOINT")


def main():

    if not os.path.exists(PROJECT_PATH):
        print("❌ Project path does not exist.")
        return

    print("=" * 60)
    print(" REPOSITORY INDEXER + GRAPH TEST ")
    print("=" * 60)

    start_time = time.time()

    # -----------------------------------
    # RUN FULL PIPELINE
    # -----------------------------------
    symbols = index_repo(
        PROJECT_PATH,
        neptune_endpoint=NEPTUNE_ENDPOINT
    )

    elapsed = time.time() - start_time

    print("\n" + "=" * 60)
    print(" PIPELINE COMPLETE ")
    print("=" * 60)

    print(f"⏱ Time taken: {elapsed:.2f}s")
    print(f"📦 Symbols extracted: {len(symbols)}")

    print("\nSample symbols:\n")

    for s in symbols[:10]:
        print({
            "id": s.id,
            "type": s.type,
            "calls": len(s.calls),
            "framework_tags": s.framework_tags,
        })

    print("\n✅ Test finished successfully.")


if __name__ == "__main__":
    main()