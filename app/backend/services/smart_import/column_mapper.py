from __future__ import annotations

import unicodedata

from backend.core.exceptions import ValidationError

_GLOBAL_ALIASES: dict[str, set[str]] = {
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

_REQUIRED = {"descricao"}

ColumnMap = dict[str, int]


def _normalize(text: object) -> str:
    if text is None:
        return ""
    s = str(text).strip().lower()
    s = " ".join(s.split())
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _jaccard(a: str, b: str) -> float:
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _match_score(norm_header: str, aliases: set[str]) -> float:
    if norm_header in aliases:
        return 1.0
    for alias in aliases:
        if alias in norm_header or norm_header in alias:
            return 0.85
    best = max((_jaccard(norm_header, alias) for alias in aliases), default=0.0)
    return best * 0.8 if best >= 0.5 else 0.0


class ColumnMapper:
    @staticmethod
    def from_headers(
        headers: list,
        profile_aliases: dict[str, list[str]] | None = None,
    ) -> ColumnMap:
        merged: dict[str, set[str]] = {field: set(aliases) for field, aliases in _GLOBAL_ALIASES.items()}
        if profile_aliases:
            for field, extra in profile_aliases.items():
                if field in merged:
                    merged[field].update(_normalize(a) for a in extra)
                else:
                    merged[field] = {_normalize(a) for a in extra}

        norm_headers = [_normalize(h) for h in headers]
        scores: list[tuple[float, str, int]] = []
        for field, aliases in merged.items():
            norm_aliases = {_normalize(a) for a in aliases}
            for col_idx, norm in enumerate(norm_headers):
                if not norm:
                    continue
                score = _match_score(norm, norm_aliases)
                if score > 0:
                    scores.append((score, field, col_idx))

        scores.sort(key=lambda x: -x[0])

        result: ColumnMap = {}
        assigned_cols: set[int] = set()
        assigned_fields: set[str] = set()
        for score, field, col_idx in scores:
            if field in assigned_fields or col_idx in assigned_cols:
                continue
            result[field] = col_idx
            assigned_fields.add(field)
            assigned_cols.add(col_idx)

        for req in _REQUIRED:
            if req not in result:
                raise ValidationError(
                    "A planilha deve conter uma coluna de descricao identificavel. "
                    "Verifique os cabecalhos do arquivo."
                )

        return result
