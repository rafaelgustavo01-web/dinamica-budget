from __future__ import annotations

import unicodedata

from backend.core.exceptions import ValidationError

_MAX_SCAN_ROWS = 30
_MIN_SCORE = 2

_TARGET_ALIASES: dict[str, set[str]] = {
    "codigo": {"item", "codigo", "cod", "cod.", "id", "no", "num", "numero"},
    "descricao": {
        "descricao", "servico", "atividade",
        "descricao das atividades", "descricao do servico", "discriminacao",
    },
    "unidade": {"unidade", "unid", "unid.", "und", "und.", "un", "un.", "uom"},
    "quantidade": {"quantidade", "qtde", "qtd", "quant", "quant.", "coef", "coef.", "coeficiente"},
    "preco": {
        "preco", "preco unitario", "p.u.", "pu",
        "custo unitario", "valor unitario",
    },
    "valor": {"valor", "valor total", "total", "preco total", "subtotal"},
}


def _normalize(cell: object) -> str:
    if cell is None:
        return ""
    text = str(cell).strip().lower()
    text = " ".join(text.split())
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def _score_row(row: list) -> tuple[int, bool]:
    count = 0
    has_descricao = False
    seen_fields: set[str] = set()
    norm_aliases = {field: {_normalize(a) for a in aliases} for field, aliases in _TARGET_ALIASES.items()}
    for cell in row:
        norm = _normalize(cell)
        if not norm:
            continue
        for field, aliases in norm_aliases.items():
            if field in seen_fields:
                continue
            matched = False
            if norm in aliases:
                matched = True
            else:
                for alias in aliases:
                    if alias in norm or norm in alias:
                        matched = True
                        break
            if matched:
                count += 1
                seen_fields.add(field)
                if field == "descricao":
                    has_descricao = True
                break
    return count, has_descricao


class HeaderDetector:
    @staticmethod
    def detect(rows: list[list], profile_header_row: int | None = None) -> int:
        if profile_header_row is not None:
            if profile_header_row < 0 or profile_header_row >= len(rows):
                raise ValidationError("Linha de cabeçalho configurada está fora do intervalo da planilha.")
            return profile_header_row

        best_idx = -1
        best_score = 0
        best_has_descricao = False

        for idx, row in enumerate(rows[:_MAX_SCAN_ROWS]):
            score, has_descricao = _score_row(row)
            if score > best_score or (score == best_score and has_descricao and not best_has_descricao):
                best_score = score
                best_idx = idx
                best_has_descricao = has_descricao

        if best_idx == -1 or best_score < _MIN_SCORE:
            raise ValidationError(
                "Nao foi possivel identificar o cabecalho da planilha. "
                "Verifique se o arquivo contem colunas de Descricao e Quantidade."
            )

        return best_idx
