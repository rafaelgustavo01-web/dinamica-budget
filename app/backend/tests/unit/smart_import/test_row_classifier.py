import pytest

from backend.services.smart_import.row_classifier import RowClassifier, RowClass


def _row(descricao=None, unidade=None, quantidade=None, preco=None, valor=None, codigo=None):
    return {
        "descricao": descricao,
        "unidade": unidade,
        "quantidade": quantidade,
        "preco": preco,
        "valor": valor,
        "codigo": codigo,
    }


def test_item_with_qtd_and_unidade():
    result = RowClassifier.classify(_row("Escavacao manual", "m2", 10.5, 50.0))
    assert result == RowClass.ITEM


def test_item_with_qtd_only():
    result = RowClassifier.classify(_row("Concreto C-25", None, 5.0))
    assert result == RowClass.ITEM


def test_secao_no_qtd_no_unidade():
    result = RowClassifier.classify(_row("1 - SERVICOS PRELIMINARES"))
    assert result == RowClass.SECAO


def test_secao_all_caps_short():
    result = RowClassifier.classify(_row("CAPITULO 1"))
    assert result == RowClass.SECAO


def test_secao_numbering_only():
    result = RowClassifier.classify(_row("1.2.3"))
    assert result == RowClass.SECAO


def test_total_keyword_in_descricao():
    result = RowClassifier.classify(_row("TOTAL GERAL", None, None, None, 500000))
    assert result == RowClass.TOTAL


def test_total_subtotal_keyword():
    result = RowClassifier.classify(_row("Subtotal Capitulo 1", None, None, None, 100000))
    assert result == RowClass.TOTAL


def test_vazia_all_none():
    result = RowClassifier.classify(_row())
    assert result == RowClass.VAZIA


def test_vazia_empty_strings():
    result = RowClassifier.classify(_row("", "", ""))
    assert result == RowClass.VAZIA


def test_item_not_falsely_classified_when_has_both():
    result = RowClassifier.classify(_row("Forma metalica", "m2", 120, 35.0, 4200))
    assert result == RowClass.ITEM
