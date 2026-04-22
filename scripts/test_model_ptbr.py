"""
Compare current and multilingual SentenceTransformers models on PT-BR examples.

Outputs:
- logs/model_ptbr_evaluation.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sentence_transformers import SentenceTransformer

from app.core.config import settings

TEST_PAIRS = [
    ("escavar buraco para fundacao", "escavacao manual em fundacao"),
    ("concreto para laje", "concreto usinado para laje de concreto armado"),
    ("rebocar parede", "reboco em parede de alvenaria"),
    ("tubo pvc agua", "instalacao de tubulacao hidraulica em pvc"),
    ("pintar teto", "pintura latex em teto de gesso"),
    ("demolicao parede", "demolicao de alvenaria com ferramenta manual"),
    ("estrutura metalica", "montagem de estrutura metalica"),
]

DISTRACTORS = [
    "limpeza de caixa dagua",
    "instalacao de sistema de alarme",
    "paisagismo e jardinagem",
]

CURRENT_MODEL = settings.EMBEDDING_MODEL_NAME
CANDIDATE_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


def evaluate_model(model_name: str) -> dict:
    model = SentenceTransformer(
        model_name,
        cache_folder=settings.SENTENCE_TRANSFORMERS_HOME,
        device="cpu",
    )
    details = []

    for query, expected in TEST_PAIRS:
        candidates = [expected] + DISTRACTORS
        embeddings = model.encode([query] + candidates, normalize_embeddings=True)
        query_vec = embeddings[0]
        similarities = [float(query_vec @ candidate_vec) for candidate_vec in embeddings[1:]]
        best_idx = max(range(len(similarities)), key=lambda idx: similarities[idx])
        details.append(
            {
                "query": query,
                "expected": expected,
                "expected_similarity": round(similarities[0], 4),
                "best_similarity": round(similarities[best_idx], 4),
                "expected_rank": 1 if best_idx == 0 else best_idx + 1,
                "all_similarities": [round(value, 4) for value in similarities],
            }
        )

    avg_similarity = sum(item["expected_similarity"] for item in details) / len(details)
    top1_hits = sum(1 for item in details if item["expected_rank"] == 1)
    return {
        "model": model_name,
        "avg_expected_similarity": round(avg_similarity, 4),
        "correct_top1": top1_hits,
        "total": len(details),
        "details": details,
    }


def main() -> None:
    report = [
        evaluate_model(CURRENT_MODEL),
        evaluate_model(CANDIDATE_MODEL),
    ]
    output_path = Path("logs/model_ptbr_evaluation.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nReport saved to {output_path}")


if __name__ == "__main__":
    main()
