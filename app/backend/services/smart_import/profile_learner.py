from __future__ import annotations

import copy


def _compute_score(uso_count: int, correction_count: int) -> float:
    """Score rises with uso_count, penalized 2x per correction."""
    if uso_count == 0:
        return 0.0
    raw = uso_count / (uso_count + correction_count * 2)
    return min(round(raw, 4), 1.0)


class ProfileLearner:
    @staticmethod
    def apply(profile: dict, corrections: list[dict]) -> dict:
        """Return an updated copy of the profile dict after applying corrections.

        profile keys: header_row_strategy, column_aliases, aba_pattern, uso_count, score_confianca
        correction item keys: tipo (str), detalhe (dict | None)
        """
        p = copy.deepcopy(profile)
        aliases: dict[str, list[str]] = p.setdefault("column_aliases", {})

        for c in corrections:
            tipo = c.get("tipo", "")
            detail = c.get("detalhe") or {}

            if tipo == "COLUMN_REMAP":
                campo = detail.get("campo")
                header_text = detail.get("header_text")
                if campo and header_text:
                    field_aliases = aliases.setdefault(campo, [])
                    if header_text not in field_aliases:
                        field_aliases.append(header_text)

            elif tipo == "HEADER_ROW_FIX":
                corrected_row = detail.get("corrected")
                if corrected_row is not None:
                    p["header_row_strategy"] = {"mode": "fixed", "row": int(corrected_row)}

            elif tipo == "SHEET_CHANGE":
                sheet_name = detail.get("sheet_name")
                if sheet_name:
                    p["aba_pattern"] = sheet_name

            # ROW_RECLASSIFY — logged for audit only, no structural profile change

        uso_count = p.get("uso_count", 0) + 1
        p["uso_count"] = uso_count
        p["score_confianca"] = _compute_score(uso_count, len(corrections))
        return p
