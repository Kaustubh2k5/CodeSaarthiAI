from ingestion.parser.adapter_registry import get_adapter
from ingestion.parser.parser_cache import get_cached_parser
from ingestion.parser.parser_pipeline import parse_file as run_pipeline


def parse_files(language_files):

    all_symbols = []

    total_files = sum(len(v) for v in language_files.values())
    processed = 0

    for language, files in language_files.items():

        print(f"\nParsing language: {language}")

        adapter = get_adapter(language)
        parser = get_cached_parser(language)

        for file_path in files:

            try:
                symbols = adapter.parse_file(
                    parser,
                    file_path,
                    run_pipeline,
                    language
                )

                all_symbols.extend(symbols)

            except Exception as e:
                print(f"⚠ Failed parsing {file_path}: {e}")

            processed += 1
            print(f"Progress: {processed}/{total_files}", end="\r")

    print("\nParsing complete.")

    return all_symbols