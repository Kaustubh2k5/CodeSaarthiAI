# graph/graph_builder.py
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from .resolver import resolve_symbols
from .enricher import enrich_symbol
from .graph_store import GraphStore


class GraphBuilder:

    def __init__(self, workers=None):
        self.store = GraphStore()
        self.workers = int(
            workers or os.getenv("ENRICH_WORKERS", 8)
        )

    # --------------------------------------------------
    # PARALLEL ENRICHMENT
    # --------------------------------------------------

    def _parallel_enrich(self, symbols):

        enriched = []

        with ThreadPoolExecutor(max_workers=self.workers) as executor:

            futures = {
                executor.submit(enrich_symbol, s): s
                for s in symbols
            }

            for future in as_completed(futures):
                try:
                    enriched.append(future.result())
                except Exception as e:
                    print("Enrichment failed:", e)

        return enriched

    # --------------------------------------------------
    # BUILD PIPELINE
    # --------------------------------------------------

    def build(self, symbols):

        print("Resolving symbols...")
        symbols = resolve_symbols(symbols)

        print("Parallel enrichment starting...")
        symbols = self._parallel_enrich(symbols)

        print("Writing graph batches...")

        for symbol in symbols:
            self.store.save_node(symbol)
            self.store.save_edges(symbol)

        # FINAL FLUSH
        self.store.flush_all()

        print("Graph build complete.")