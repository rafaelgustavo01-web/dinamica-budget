import pytest
from backend.services.smart_import.profile_learner import ProfileLearner, _compute_score


def _base_profile():
    return {
        "header_row_strategy": {"mode": "scan"},
        "column_aliases": {},
        "aba_pattern": None,
        "uso_count": 0,
        "score_confianca": 0.0,
    }


def test_column_remap_adds_alias():
    profile = _base_profile()
    corrections = [
        {"tipo": "COLUMN_REMAP", "detalhe": {"campo": "quantidade", "header_text": "QUANT."}}
    ]
    result = ProfileLearner.apply(profile, corrections)
    assert "QUANT." in result["column_aliases"].get("quantidade", [])


def test_column_remap_does_not_duplicate_alias():
    profile = _base_profile()
    profile["column_aliases"] = {"quantidade": ["QUANT."]}
    corrections = [
        {"tipo": "COLUMN_REMAP", "detalhe": {"campo": "quantidade", "header_text": "QUANT."}}
    ]
    result = ProfileLearner.apply(profile, corrections)
    assert result["column_aliases"]["quantidade"].count("QUANT.") == 1


def test_header_row_fix_updates_strategy_to_fixed():
    profile = _base_profile()
    corrections = [
        {"tipo": "HEADER_ROW_FIX", "detalhe": {"detected": 0, "corrected": 10}}
    ]
    result = ProfileLearner.apply(profile, corrections)
    assert result["header_row_strategy"]["mode"] == "fixed"
    assert result["header_row_strategy"]["row"] == 10


def test_sheet_change_updates_aba_pattern():
    profile = _base_profile()
    corrections = [
        {"tipo": "SHEET_CHANGE", "detalhe": {"sheet_name": "QQP"}}
    ]
    result = ProfileLearner.apply(profile, corrections)
    assert result["aba_pattern"] == "QQP"


def test_uso_count_increments_on_apply():
    profile = _base_profile()
    profile["uso_count"] = 2
    result = ProfileLearner.apply(profile, [])
    assert result["uso_count"] == 3


def test_score_increases_with_clean_import():
    # With corrections present, more uso_count means higher score
    score_low = _compute_score(uso_count=1, correction_count=2)
    score_high = _compute_score(uso_count=5, correction_count=2)
    assert score_high > score_low


def test_score_penalized_by_corrections():
    clean = _compute_score(uso_count=5, correction_count=0)
    corrected = _compute_score(uso_count=5, correction_count=3)
    assert corrected < clean


def test_score_capped_at_one():
    score = _compute_score(uso_count=1000, correction_count=0)
    assert score <= 1.0


def test_row_reclassify_does_not_crash():
    profile = _base_profile()
    corrections = [
        {"tipo": "ROW_RECLASSIFY", "detalhe": {"descricao": "Limpeza de terreno", "de": "SECAO", "para": "ITEM"}}
    ]
    result = ProfileLearner.apply(profile, corrections)
    assert result is not None


def test_apply_does_not_mutate_original():
    profile = _base_profile()
    original_aliases = profile["column_aliases"]
    ProfileLearner.apply(profile, [
        {"tipo": "COLUMN_REMAP", "detalhe": {"campo": "quantidade", "header_text": "QTD."}}
    ])
    assert original_aliases == {}
