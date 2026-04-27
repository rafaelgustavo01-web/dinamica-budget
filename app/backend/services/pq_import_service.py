import csv
import io
import uuid
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

import openpyxl
from fastapi import UploadFile

from backend.core.exceptions import NotFoundError, ValidationError
from backend.models.enums import StatusImportacao, StatusMatch
from backend.models.proposta import PqImportacao, PqItem
from backend.repositories.associacao_repository import normalize_text
from backend.repositories.pq_importacao_repository import PqImportacaoRepository
from backend.repositories.pq_item_repository import PqItemRepository
from backend.repositories.proposta_repository import PropostaRepository

_HEADER_ALIASES = {
    "codigo": {"codigo", "código", "cod", "item", "item codigo"},
    "descricao": {
        "descricao", "descrição", "servico", "serviço",
        "item descricao", "item descrição",
        "descricao das atividades", "descrição das atividades",
    },
    "unidade": {"unidade", "unid", "unid.", "und", "und.", "unidade_medida", "unidade medida"},
    "quantidade": {"quantidade", "qtde", "qtd", "quant", "quant.", "coeficiente", "coef", "coef."},
}
_SUPPORTED_EXTENSIONS = {"csv", "xlsx"}


def _normalize_header(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    return " ".join(text.replace("_", " ").split())


def _decode_csv(contents: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return contents.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValidationError("Não foi possível decodificar o CSV informado.")


def _find_column_map(headers: list[object]) -> dict[str, int]:
    normalized = [_normalize_header(value) for value in headers]
    column_map: dict[str, int] = {}
    for canonical, aliases in _HEADER_ALIASES.items():
        for idx, header in enumerate(normalized):
            if header in aliases:
                column_map[canonical] = idx
                break
    if "descricao" not in column_map:
        raise ValidationError("A planilha deve conter uma coluna de descrição.")
    return column_map


def _find_column_map_from_layout(headers: list[object], layout_map: dict[str, str]) -> dict[str, int]:
    normalized = [_normalize_header(value) for value in headers]
    column_map: dict[str, int] = {}
    for campo, coluna_planilha in layout_map.items():
        coluna_norm = _normalize_header(coluna_planilha)
        for idx, header in enumerate(normalized):
            if header == coluna_norm:
                column_map[campo] = idx
                break
    if "descricao" not in column_map:
        raise ValidationError("A planilha deve conter uma coluna de descrição.")
    return column_map


def _parse_decimal(value: object, default: Decimal) -> Decimal:
    if value in (None, ""):
        return default
    normalized = str(value).strip()
    if "," in normalized and "." in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    elif "," in normalized:
        normalized = normalized.replace(",", ".")
    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise ValidationError("Quantidade inválida na planilha.", details={"valor": str(value)}) from exc


class PqImportService:
    def __init__(
        self,
        proposta_repo: PropostaRepository,
        importacao_repo: PqImportacaoRepository,
        item_repo: PqItemRepository,
        pq_layout_repo=None,
    ) -> None:
        self.proposta_repo = proposta_repo
        self.importacao_repo = importacao_repo
        self.item_repo = item_repo
        self._pq_layout_repo = pq_layout_repo

    async def _resolver_mapa_colunas(self, cliente_id: UUID) -> dict[str, str] | None:
        if self._pq_layout_repo is None:
            return None
        layout = await self._pq_layout_repo.get_by_cliente_id(cliente_id)
        if layout is None:
            return None
        return {m.campo_sistema.value: m.coluna_planilha for m in layout.mapeamentos}

    async def importar_planilha(self, proposta_id: uuid.UUID, arquivo: UploadFile) -> PqImportacao:
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta:
            raise NotFoundError("Proposta", str(proposta_id))
        if not arquivo.filename:
            raise ValidationError("Arquivo inválido.")

        ext = arquivo.filename.rsplit(".", 1)[-1].lower() if "." in arquivo.filename else ""
        if ext not in _SUPPORTED_EXTENSIONS:
            raise ValidationError("Somente arquivos .csv e .xlsx são suportados.")

        contents = await arquivo.read()
        if not contents:
            raise ValidationError("Arquivo vazio.")

        layout_map = await self._resolver_mapa_colunas(proposta.cliente_id)
        parsed_rows = self._parse_contents(contents, ext, layout_map=layout_map)
        importacao = PqImportacao(
            id=uuid.uuid4(),
            proposta_id=proposta_id,
            nome_arquivo=arquivo.filename,
            formato=ext,
            linhas_total=len(parsed_rows),
            linhas_importadas=0,
            linhas_com_erro=0,
            status=StatusImportacao.PROCESSANDO,
        )
        importacao = await self.importacao_repo.create(importacao)

        itens: list[PqItem] = []
        linhas_com_erro = 0
        for row in parsed_rows:
            descricao = str(row["descricao"] or "").strip()
            if not descricao:
                linhas_com_erro += 1
                continue

            try:
                quantidade = _parse_decimal(row["quantidade"], Decimal("1"))
            except ValidationError:
                linhas_com_erro += 1
                continue

            codigo = str(row["codigo"]).strip() if row["codigo"] not in (None, "") else None
            unidade = str(row["unidade"]).strip() if row["unidade"] not in (None, "") else None
            itens.append(
                PqItem(
                    proposta_id=proposta_id,
                    pq_importacao_id=importacao.id,
                    codigo_original=codigo,
                    descricao_original=descricao,
                    unidade_medida_original=unidade,
                    quantidade_original=quantidade,
                    descricao_tokens=normalize_text(descricao),
                    match_status=StatusMatch.PENDENTE,
                    linha_planilha=row["linha_planilha"],
                )
            )

        if itens:
            await self.item_repo.create_batch(itens)

        importacao.linhas_importadas = len(itens)
        importacao.linhas_com_erro = linhas_com_erro
        importacao.status = StatusImportacao.CONCLUIDO if linhas_com_erro == 0 else StatusImportacao.COM_ERROS
        await self.importacao_repo.update(importacao)
        return importacao

    def _parse_contents(self, contents: bytes, ext: str, layout_map: dict[str, str] | None = None) -> list[dict[str, Any]]:
        if ext == "csv":
            return self._parse_csv(contents, layout_map=layout_map)
        return self._parse_xlsx(contents, layout_map=layout_map)

    def _parse_csv(self, contents: bytes, layout_map: dict[str, str] | None = None) -> list[dict[str, Any]]:
        text = _decode_csv(contents)
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        if not rows:
            return []

        if layout_map:
            column_map = _find_column_map_from_layout(rows[0], layout_map)
        else:
            column_map = _find_column_map(rows[0])
        parsed_rows: list[dict[str, Any]] = []
        for line_number, row in enumerate(rows[1:], start=2):
            if not any(str(cell).strip() for cell in row if cell is not None):
                continue
            parsed_rows.append(self._build_parsed_row(row, column_map, line_number))
        return parsed_rows

    def _parse_xlsx(self, contents: bytes, layout_map: dict[str, str] | None = None) -> list[dict[str, Any]]:
        workbook = openpyxl.load_workbook(io.BytesIO(contents), read_only=True, data_only=True)
        worksheet = workbook.active

        header_row_number = None
        header_values: list[object] = []
        for row_number, row in enumerate(worksheet.iter_rows(values_only=True), start=1):
            values = list(row)
            try:
                if layout_map:
                    _find_column_map_from_layout(values, layout_map)
                else:
                    _find_column_map(values)
                header_row_number = row_number
                header_values = values
                break
            except ValidationError:
                continue

        if header_row_number is None:
            raise ValidationError("Não foi possível identificar o cabeçalho da planilha.")

        if layout_map:
            column_map = _find_column_map_from_layout(header_values, layout_map)
        else:
            column_map = _find_column_map(header_values)
        parsed_rows: list[dict[str, Any]] = []
        for row_number, row in enumerate(
            worksheet.iter_rows(min_row=header_row_number + 1, values_only=True),
            start=header_row_number + 1,
        ):
            values = list(row)
            if not any(str(cell).strip() for cell in values if cell is not None):
                continue
            parsed_rows.append(self._build_parsed_row(values, column_map, row_number))
        return parsed_rows

    def _build_parsed_row(
        self,
        row: list[object],
        column_map: dict[str, int],
        line_number: int,
    ) -> dict[str, Any]:
        def _value(field: str) -> object:
            idx = column_map.get(field)
            if idx is None or idx >= len(row):
                return None
            return row[idx]

        return {
            "codigo": _value("codigo"),
            "descricao": _value("descricao"),
            "unidade": _value("unidade"),
            "quantidade": _value("quantidade"),
            "linha_planilha": line_number,
        }

