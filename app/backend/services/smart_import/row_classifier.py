from __future__ import annotations

import enum
import re
import unicodedata
from decimal import Decimal, InvalidOperation


class RowClass(str, enum.Enum):
    ITEM = "ITEM"
    SECAO = "SECAO"
    TOTAL = "TOTAL"
    VAZIA = "VAZIA"


_SECTION_KEYWORDS = {
    "capitulo", "secao", "titulo", "etapa", "fase", "disciplina",
    "grupo", "subgrupo", "empreitada", "contrato", "obra", "projeto",
    "relatorio", "resumo", "sumario",
}
_TOTAL_KEYWORDS = {"total", "subtotal", "soma", "geral"}
_SECTION_NUMBERING_RE = re.compile(r"^\d+(\.\d+)*\s*[\.:)\-]?\s*$")


def _norm(text: object) -> str:
    if text is None:
        return ""
    s = str(text).strip().lower()
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _to_decimal(value: object) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        s = str(value).strip().replace(",", ".")
        return Decimal(s)
    except InvalidOperation:
        return None


class RowClassifier:
    @staticmethod
    def classify(row: dict) -> RowClass:
        descricao = _norm(row.get("descricao"))
        unidade = _norm(row.get("unidade"))
        qtd = _to_decimal(row.get("quantidade"))
        preco = _to_decimal(row.get("preco"))
        valor = _to_decimal(row.get("valor"))

        if not descricao and not unidade and qtd is None and preco is None and valor is None:
            return RowClass.VAZIA

        has_qtd = qtd is not None and qtd > 0
        has_unidade = bool(unidade)

        first_word = descricao.split()[0] if descricao.split() else ""
        if first_word in _TOTAL_KEYWORDS or any(kw in descricao for kw in _TOTAL_KEYWORDS):
            if not has_qtd:
                return RowClass.TOTAL

        if has_qtd:
            return RowClass.ITEM
        if has_unidade and descricao:
            return RowClass.ITEM

        if _SECTION_NUMBERING_RE.match(descricao):
            return RowClass.SECAO
        if len(descricao) <= 5:
            return RowClass.SECAO
        if descricao.isupper() and len(descricao) <= 60:
            return RowClass.SECAO
        if first_word in _SECTION_KEYWORDS:
            return RowClass.SECAO

        return RowClass.SECAO
