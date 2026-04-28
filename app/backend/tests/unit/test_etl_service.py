"""
Unit tests for EtlService.parse_tcpo_pini.
"""
import pytest
from unittest.mock import MagicMock, patch

from backend.services.etl_service import etl_service


def _make_cell(value, bold=None, indent=None):
    """Helper to build a mock openpyxl Cell."""
    cell = MagicMock()
    cell.value = value
    if bold is not None:
        cell.font = MagicMock()
        cell.font.bold = bold
    else:
        cell.font = None
    if indent is not None:
        cell.alignment = MagicMock()
        cell.alignment.indent = indent
    else:
        cell.alignment = None
    return cell


def _make_row(
    codigo, descricao, classe, unidade, coef, preco, descricao_bold=None, codigo_indent=None
):
    """Build a row tuple of mock cells matching TCPO column order."""
    return (
        _make_cell(codigo, indent=codigo_indent),
        _make_cell(descricao, bold=descricao_bold),
        _make_cell(classe),
        _make_cell(unidade),
        _make_cell(coef),
        _make_cell(preco),
    )


class _MockWorkbook:
    """Simple mock of openpyxl.Workbook for TCPO parsing tests."""

    def __init__(self, ws):
        self._ws = ws

    def __getitem__(self, key):
        if key == "Composições analíticas":
            return self._ws
        raise KeyError(key)

    def close(self):
        pass


def _mock_workbook(rows):
    """Return a mock openpyxl Workbook that yields the given rows."""
    mock_ws = MagicMock()
    mock_ws.iter_rows.return_value = iter(rows)
    return _MockWorkbook(mock_ws)


@pytest.fixture(autouse=True)
def clear_cache():
    """Ensure ETL cache is clean before/after each test."""
    etl_service._cache.clear()
    yield
    etl_service._cache.clear()


class TestParseTcpoPini:
    def test_parent_bold_and_subservice_nonbold(self):
        """
        Parent service (bold SER.CG) followed by a subservice (non-bold SER.CG)
        and a normal child insumo.
        """
        rows = [
            _make_row("S-001", "Serviço Pai", "SER.CG", "UN", None, 100.0, descricao_bold=True, codigo_indent=0),
            _make_row("S-002", "Subserviço", "SER.CG", "UN", 1.0, 50.0, descricao_bold=False, codigo_indent=1),
            _make_row("MAT-001", "Cimento", "MAT.", "KG", 10.0, 25.0),
        ]

        with patch("backend.services.etl_service.openpyxl.load_workbook", return_value=_mock_workbook(rows)):
            resp = etl_service.parse_tcpo_pini(b"dummy")

        assert resp.parse_preview.total_itens == 3
        assert resp.parse_preview.total_relacoes == 2

        # Both subservice and insumo are children of S-001
        rels = resp.parse_preview.relacoes_amostra
        assert any(r.pai_codigo == "S-001" and r.filho_codigo == "S-002" for r in rels)
        assert any(r.pai_codigo == "S-001" and r.filho_codigo == "MAT-001" for r in rels)

    def test_two_separate_parents(self):
        """
        Two bold SER.CG rows create two distinct parents; each has its own children.
        """
        rows = [
            _make_row("S-001", "Serviço A", "SER.CG", "UN", None, 100.0, descricao_bold=True, codigo_indent=0),
            _make_row("MAT-001", "Cimento A", "MAT.", "KG", 5.0, 20.0),
            _make_row("S-002", "Serviço B", "SER.CG", "UN", None, 200.0, descricao_bold=True, codigo_indent=0),
            _make_row("MAT-002", "Cimento B", "MAT.", "KG", 3.0, 15.0),
        ]

        with patch("backend.services.etl_service.openpyxl.load_workbook", return_value=_mock_workbook(rows)):
            resp = etl_service.parse_tcpo_pini(b"dummy")

        assert resp.parse_preview.total_itens == 4
        assert resp.parse_preview.total_relacoes == 2

        rels = resp.parse_preview.relacoes_amostra
        assert any(r.pai_codigo == "S-001" and r.filho_codigo == "MAT-001" for r in rels)
        assert any(r.pai_codigo == "S-002" and r.filho_codigo == "MAT-002" for r in rels)

    def test_subservice_without_parent_warns(self):
        """
        A non-bold SER.CG before any bold parent should generate a warning.
        """
        rows = [
            _make_row("S-002", "Subserviço Órfão", "SER.CG", "UN", 1.0, 50.0, descricao_bold=False, codigo_indent=1),
        ]

        with patch("backend.services.etl_service.openpyxl.load_workbook", return_value=_mock_workbook(rows)):
            resp = etl_service.parse_tcpo_pini(b"dummy")

        assert resp.parse_preview.total_itens == 0
        assert resp.parse_preview.total_relacoes == 0
        assert any("subserviço sem pai" in a for a in resp.parse_preview.avisos)

    def test_child_without_parent_warns(self):
        """
        A MAT. row before any SER.CG parent should generate a warning.
        """
        rows = [
            _make_row("MAT-001", "Cimento", "MAT.", "KG", 10.0, 25.0),
        ]

        with patch("backend.services.etl_service.openpyxl.load_workbook", return_value=_mock_workbook(rows)):
            resp = etl_service.parse_tcpo_pini(b"dummy")

        assert resp.parse_preview.total_itens == 0
        assert resp.parse_preview.total_relacoes == 0
        assert any("filho sem pai" in a for a in resp.parse_preview.avisos)

    def test_mixed_mo_eqp_fer_children(self):
        """
        Parent with M.O., EQP. and FER. children.
        """
        rows = [
            _make_row("S-001", "Serviço Misto", "SER.CG", "UN", None, 100.0, descricao_bold=True, codigo_indent=0),
            _make_row("MO-001", "Pedreiro", "M.O.", "H", 8.0, 35.0),
            _make_row("EQP-001", "Betoneira", "EQP.", "H", 2.0, 15.0),
            _make_row("FER-001", "Espátula", "FER.", "UN", 1.0, 5.0),
        ]

        with patch("backend.services.etl_service.openpyxl.load_workbook", return_value=_mock_workbook(rows)):
            resp = etl_service.parse_tcpo_pini(b"dummy")

        assert resp.parse_preview.total_itens == 4
        assert resp.parse_preview.total_relacoes == 3

        rels = resp.parse_preview.relacoes_amostra
        assert any(r.pai_codigo == "S-001" and r.filho_codigo == "MO-001" for r in rels)
        assert any(r.pai_codigo == "S-001" and r.filho_codigo == "EQP-001" for r in rels)
        assert any(r.pai_codigo == "S-001" and r.filho_codigo == "FER-001" for r in rels)

    def test_parent_with_subservice_and_grandchildren(self):
        """
        Parent -> subservice -> insumo under subservice.
        The subservice does NOT become a new parent, so the insumo is a child
        of the original parent (not the subservice). This matches the TCPO
        analytical sheet semantics where subservices are consumed, not exploded.
        """
        rows = [
            _make_row("S-001", "Serviço Pai", "SER.CG", "UN", None, 100.0, descricao_bold=True, codigo_indent=0),
            _make_row("S-002", "Subserviço", "SER.CG", "UN", 1.0, 50.0, descricao_bold=False, codigo_indent=1),
            _make_row("MAT-001", "Cimento", "MAT.", "KG", 10.0, 25.0),
        ]

        with patch("backend.services.etl_service.openpyxl.load_workbook", return_value=_mock_workbook(rows)):
            resp = etl_service.parse_tcpo_pini(b"dummy")

        # All relations point to S-001 (the bold parent)
        for rel in resp.parse_preview.relacoes_amostra:
            assert rel.pai_codigo == "S-001"

    def test_ser_prefix_variations(self):
        """
        Any class starting with 'SER.' should be treated as service/subservice,
        not just SER.CG. Test SER.MO and SER.CH.
        """
        rows = [
            _make_row("S-001", "Serviço Pai", "SER.CH", "UN", None, 100.0, descricao_bold=True, codigo_indent=0),
            _make_row("S-002", "Subserviço", "SER.MO", "UN", 1.0, 50.0, descricao_bold=False, codigo_indent=1),
            _make_row("MAT-001", "Cimento", "MAT.", "KG", 10.0, 25.0),
        ]

        with patch("backend.services.etl_service.openpyxl.load_workbook", return_value=_mock_workbook(rows)):
            resp = etl_service.parse_tcpo_pini(b"dummy")

        assert resp.parse_preview.total_itens == 3
        assert resp.parse_preview.total_relacoes == 2

        rels = resp.parse_preview.relacoes_amostra
        assert any(r.pai_codigo == "S-001" and r.filho_codigo == "S-002" for r in rels)
        assert any(r.pai_codigo == "S-001" and r.filho_codigo == "MAT-001" for r in rels)

    def test_non_ser_class_treated_as_insumo(self):
        """
        Classes that do not start with 'SER.' are treated as direct children,
        even if they look like services (e.g., SRV.CG).
        """
        rows = [
            _make_row("S-001", "Serviço Pai", "SER.CG", "UN", None, 100.0, descricao_bold=True, codigo_indent=0),
            _make_row("X-001", "Item Estranho", "SRV.CG", "UN", 2.0, 30.0),
        ]

        with patch("backend.services.etl_service.openpyxl.load_workbook", return_value=_mock_workbook(rows)):
            resp = etl_service.parse_tcpo_pini(b"dummy")

        assert resp.parse_preview.total_itens == 2
        assert resp.parse_preview.total_relacoes == 1

        rel = resp.parse_preview.relacoes_amostra[0]
        assert rel.pai_codigo == "S-001"
        assert rel.filho_codigo == "X-001"
