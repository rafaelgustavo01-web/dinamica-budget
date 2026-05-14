import pytest

from backend.services.smart_import.column_mapper import ColumnMapper


def test_maps_standard_portuguese_headers():
    headers = ["ITEM", "DESCRICAO", "UNID.", "QUANT.", "PRECO UNITARIO", "VALOR TOTAL"]
    cm = ColumnMapper.from_headers(headers)
    assert cm["codigo"] == 0
    assert cm["descricao"] == 1
    assert cm["unidade"] == 2
    assert cm["quantidade"] == 3
    assert cm["preco"] == 4
    assert cm["valor"] == 5


def test_maps_verbose_qqp_headers():
    headers = [None, None, "Item", "Descricao", "%Subcont.", "%Proprio", "Unid.", "Quant.", "BDI", "Preco Unitario", "Valor Total"]
    cm = ColumnMapper.from_headers(headers)
    assert cm["codigo"] == 2
    assert cm["descricao"] == 3
    assert cm["unidade"] == 6
    assert cm["quantidade"] == 7
    assert cm["preco"] == 9
    assert cm["valor"] == 10


def test_maps_planilha_style_headers():
    headers = ["ITEM", "", "", "", "", "", "", "", "", "DESCRICAO DAS ATIVIDADES", "UNID.", "", "", "", "", "", "QUANT.", "PRECO", "TOTAL"]
    cm = ColumnMapper.from_headers(headers)
    assert cm["codigo"] == 0
    assert cm["descricao"] == 9
    assert cm["unidade"] == 10
    assert cm["quantidade"] == 16
    assert cm["preco"] == 17
    assert cm["valor"] == 18


def test_raises_when_descricao_not_found():
    from backend.core.exceptions import ValidationError
    headers = ["XPTO", "AAAA", "ZZZZ"]
    with pytest.raises(ValidationError, match="descricao"):
        ColumnMapper.from_headers(headers)


def test_profile_aliases_override_global():
    profile_aliases = {"quantidade": ["criterio de medicao"]}
    headers = ["ITEM", "ATIVIDADE", "UNID.", "CRITERIO DE MEDICAO", "VALOR"]
    cm = ColumnMapper.from_headers(headers, profile_aliases=profile_aliases)
    assert cm["quantidade"] == 3


def test_returns_empty_for_optional_fields_not_found():
    headers = ["ITEM", "DESCRICAO", "UNIDADE"]
    cm = ColumnMapper.from_headers(headers)
    assert cm["codigo"] == 0
    assert cm["descricao"] == 1
    assert cm["unidade"] == 2
    assert "quantidade" not in cm
    assert "preco" not in cm
    assert "valor" not in cm
