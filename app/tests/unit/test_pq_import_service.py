from io import BytesIO
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import openpyxl
import pytest

from app.core.exceptions import ValidationError
from app.models.enums import StatusImportacao
from app.services.pq_import_service import PqImportService


def _build_upload(filename: str, payload: bytes):
    arquivo = MagicMock()
    arquivo.filename = filename
    arquivo.read = AsyncMock(return_value=payload)
    return arquivo


@pytest.mark.asyncio
async def test_importar_planilha_csv_cria_itens_e_normaliza_tokens():
    proposta = MagicMock()
    proposta.id = uuid4()

    proposta_repo = AsyncMock()
    proposta_repo.get_by_id.return_value = proposta
    importacao_repo = AsyncMock()
    importacao_repo.create.side_effect = lambda imp: imp
    importacao_repo.update.side_effect = lambda imp: imp
    item_repo = AsyncMock()
    item_repo.create_batch.side_effect = lambda items: items

    svc = PqImportService(proposta_repo, importacao_repo, item_repo)
    arquivo = _build_upload(
        "pq.csv",
        b"codigo,descricao,unidade,quantidade\n001,Escavacao manual,m2,10.5\n",
    )

    resultado = await svc.importar_planilha(proposta.id, arquivo)

    assert resultado.status == StatusImportacao.CONCLUIDO
    assert resultado.linhas_total == 1
    assert resultado.linhas_importadas == 1
    created_items = item_repo.create_batch.await_args.args[0]
    assert created_items[0].descricao_tokens == "escavacao manual"


@pytest.mark.asyncio
async def test_importar_planilha_xlsx_reconhece_aliases_de_coluna():
    proposta = MagicMock()
    proposta.id = uuid4()

    proposta_repo = AsyncMock()
    proposta_repo.get_by_id.return_value = proposta
    importacao_repo = AsyncMock()
    importacao_repo.create.side_effect = lambda imp: imp
    importacao_repo.update.side_effect = lambda imp: imp
    item_repo = AsyncMock()
    item_repo.create_batch.side_effect = lambda items: items

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Código", "Descrição", "Unidade", "Quantidade"])
    ws.append(["A-01", "Concreto estrutural", "m3", 12])
    payload = BytesIO()
    wb.save(payload)

    svc = PqImportService(proposta_repo, importacao_repo, item_repo)
    arquivo = _build_upload("pq.xlsx", payload.getvalue())

    resultado = await svc.importar_planilha(proposta.id, arquivo)

    assert resultado.status == StatusImportacao.CONCLUIDO
    created_items = item_repo.create_batch.await_args.args[0]
    assert created_items[0].codigo_original == "A-01"
    assert str(created_items[0].quantidade_original) == "12"


@pytest.mark.asyncio
async def test_importar_planilha_rejeita_extensao_nao_suportada():
    proposta = MagicMock()
    proposta.id = uuid4()

    proposta_repo = AsyncMock()
    proposta_repo.get_by_id.return_value = proposta
    svc = PqImportService(proposta_repo, AsyncMock(), AsyncMock())
    arquivo = _build_upload("pq.txt", b"teste")

    with pytest.raises(ValidationError, match="Somente arquivos"):
        await svc.importar_planilha(proposta.id, arquivo)
