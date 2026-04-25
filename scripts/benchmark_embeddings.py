"""
Benchmark the current embedding model on CPU-only environments.

Outputs:
- logs/benchmark_embeddings_results.json
"""

from __future__ import annotations

import gc
import json
import os
import platform
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_ROOT = ROOT / "app"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

import psutil
from sentence_transformers import SentenceTransformer

from backend.core.config import settings

TEST_TEXTS = [
    "escavacao manual em terra",
    "concreto usinado para laje de concreto armado",
    "reboco em parede de alvenaria",
    "instalacao de tubulacao hidraulica em pvc",
    "pintura latex em teto de gesso",
] * 40


def get_ram_mb() -> float:
    return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)


def benchmark_model(model_name: str) -> dict:
    gc.collect()
    before_mb = get_ram_mb()
    started = time.perf_counter()
    model = SentenceTransformer(
        model_name,
        cache_folder=settings.SENTENCE_TRANSFORMERS_HOME,
        device="cpu",
    )
    load_time_s = time.perf_counter() - started
    after_load_mb = get_ram_mb()

    single_runs = []
    for _ in range(8):
        tick = time.perf_counter()
        model.encode("concreto usinado para laje", normalize_embeddings=True)
        single_runs.append((time.perf_counter() - tick) * 1000)

    batch_results = {}
    for batch_size in (1, 8, 32, 64):
        batch = TEST_TEXTS[:batch_size]
        tick = time.perf_counter()
        model.encode(batch, batch_size=batch_size, normalize_embeddings=True)
        elapsed_ms = (time.perf_counter() - tick) * 1000
        batch_results[str(batch_size)] = {
            "total_ms": round(elapsed_ms, 2),
            "per_item_ms": round(elapsed_ms / batch_size, 2),
        }

    return {
        "model": model_name,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "load_time_s": round(load_time_s, 2),
        "ram_before_mb": round(before_mb, 2),
        "ram_after_load_mb": round(after_load_mb, 2),
        "ram_delta_mb": round(after_load_mb - before_mb, 2),
        "single_encode_avg_ms": round(statistics.mean(single_runs), 2),
        "single_encode_median_ms": round(statistics.median(single_runs), 2),
        "batch_results": batch_results,
    }


def main() -> None:
    results = [benchmark_model(settings.EMBEDDING_MODEL_NAME)]
    output_path = Path("logs/benchmark_embeddings_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
