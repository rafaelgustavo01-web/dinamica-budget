"""
Benchmark fuzzy vs semantic search using the current repository code paths.

Outputs:
- logs/benchmark_search_results.csv
- logs/benchmark_search_summary.json
"""

from __future__ import annotations

import asyncio
import csv
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_ROOT = ROOT / "app"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import async_session_factory
from backend.ml.embedder import embedder
from backend.repositories.base_tcpo_repository import BaseTcpoRepository
from backend.repositories.tcpo_embeddings_repository import TcpoEmbeddingsRepository

TEST_QUERIES = [
    "escavacao manual em terra",
    "concreto usinado para laje",
    "reboco em parede de tijolo",
    "instalacao hidraulica residencial",
    "pintura latex em gesso",
    "demolicao de alvenaria",
    "terraplanagem mecanizada",
    "argamassa para assentamento",
    "impermeabilizacao de laje",
    "estrutura metalica",
]

FUZZY_THRESHOLD = 0.30
SEMANTIC_THRESHOLD = 0.30
LIMIT = 10


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * p)))
    return ordered[index]


async def benchmark_fuzzy(session: AsyncSession, query: str) -> tuple[float, int]:
    repo = BaseTcpoRepository(session)
    started = time.perf_counter()
    rows = await repo.fuzzy_search(query, threshold=FUZZY_THRESHOLD, limit=LIMIT)
    elapsed_ms = (time.perf_counter() - started) * 1000
    return elapsed_ms, len(rows)


async def benchmark_semantic(session: AsyncSession, query: str) -> tuple[float, int]:
    if not embedder.ready:
        embedder.load()

    repo = TcpoEmbeddingsRepository(session)
    started = time.perf_counter()
    vector = embedder.encode(query)
    rows = await repo.vector_search(
        query_vector=vector,
        threshold=SEMANTIC_THRESHOLD,
        limit=LIMIT,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000
    return elapsed_ms, len(rows)


async def main() -> None:
    csv_path = Path("logs/benchmark_search_results.csv")
    summary_path = Path("logs/benchmark_search_summary.json")
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    fuzzy_times: list[float] = []
    semantic_times: list[float] = []
    rows_for_csv: list[list[object]] = []

    async with async_session_factory() as session:
        for query in TEST_QUERIES:
            fuzzy_ms, fuzzy_count = await benchmark_fuzzy(session, query)
            semantic_ms, semantic_count = await benchmark_semantic(session, query)
            fuzzy_times.append(fuzzy_ms)
            semantic_times.append(semantic_ms)
            rows_for_csv.append(
                [query, round(fuzzy_ms, 2), fuzzy_count, round(semantic_ms, 2), semantic_count]
            )
            print(
                f"{query:<32} | fuzzy={fuzzy_ms:8.2f}ms ({fuzzy_count:>2}) | "
                f"semantic={semantic_ms:8.2f}ms ({semantic_count:>2})"
            )

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["query", "fuzzy_ms", "fuzzy_count", "semantic_ms", "semantic_count"])
        writer.writerows(rows_for_csv)

    summary = {
        "queries": len(TEST_QUERIES),
        "fuzzy": {
            "average_ms": round(statistics.mean(fuzzy_times), 2),
            "median_ms": round(statistics.median(fuzzy_times), 2),
            "p95_ms": round(percentile(fuzzy_times, 0.95), 2),
        },
        "semantic": {
            "average_ms": round(statistics.mean(semantic_times), 2),
            "median_ms": round(statistics.median(semantic_times), 2),
            "p95_ms": round(percentile(semantic_times, 0.95), 2),
        },
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"\nCSV saved to {csv_path}")
    print(f"Summary saved to {summary_path}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
