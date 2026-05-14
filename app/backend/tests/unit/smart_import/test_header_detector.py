import pytest

from backend.services.smart_import.header_detector import HeaderDetector


def _sheet_rows(header_at: int, header: list, data: list[list], total_rows: int = 15) -> list[list]:
    rows = [[] for _ in range(header_at)]
    rows.append(header)
    rows.extend(data)
    while len(rows) < total_rows:
        rows.append([])
    return rows


def test_detects_header_at_row_0():
    rows = _sheet_rows(
        header_at=0,
        header=["ITEM", "DESCRICAO", "UNID", "QUANT"],
        data=[["1.1", "Mobilizacao", "vb", 1]],
    )
    idx = HeaderDetector.detect(rows)
    assert idx == 0


def test_detects_header_at_row_10():
    rows = _sheet_rows(
        header_at=10,
        header=["Item", "Descricao", "Unidade", "Qtd", "Preco Unitario", "Valor Total"],
        data=[["1.1.1", "Escavacao manual", "m2", 10.5, 50.0, 525.0]],
    )
    idx = HeaderDetector.detect(rows)
    assert idx == 10


def test_detects_header_at_row_7_with_partial_matches():
    rows = _sheet_rows(
        header_at=7,
        header=["ITEM", "DESCRICAO DAS ATIVIDADES", "", "UNID.", "CRITERIO", "QUANT.", "PRECO", "TOTAL"],
        data=[["1.1.1.1", "Canteiro de obras", "", "vb", "", 1, 3100, 3100]],
    )
    idx = HeaderDetector.detect(rows)
    assert idx == 7


def test_returns_first_non_empty_row_with_descricao():
    rows = [
        [],
        ["Codigo", "Servico", "Un.", "Qtde.", "P.U.", "Total"],
        ["001", "Limpeza", "m2", 100, 5.5, 550],
    ]
    idx = HeaderDetector.detect(rows)
    assert idx == 1


def test_raises_when_no_header_found():
    rows = [["1", "2", "3", "4"]] * 35
    from backend.core.exceptions import ValidationError
    with pytest.raises(ValidationError, match="cabecalho"):
        HeaderDetector.detect(rows)


def test_respects_profile_fixed_row():
    rows = _sheet_rows(
        header_at=5,
        header=["Codigo", "Descricao", "Un.", "Qtd."],
        data=[["1", "Obra", "vb", 1]],
    )
    idx = HeaderDetector.detect(rows, profile_header_row=5)
    assert idx == 5
