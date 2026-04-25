from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from backend.core.dependencies import get_current_active_user, get_db


@pytest.mark.asyncio
async def test_criar_proposta_importar_pq_match_e_gerar_cpu():
    from backend.api.v1.endpoints import cpu_geracao, pq_importacao, propostas
    from backend.main import create_app

    now = datetime.now(timezone.utc)
    cliente_id = uuid4()
    proposta_id = uuid4()
    pq_item_id = uuid4()
    importacao_id = uuid4()
    servico_id = uuid4()
    cpu_item_id = uuid4()

    current_user = SimpleNamespace(
        id=uuid4(),
        email="worker-smoke@example.com",
        nome="Worker Smoke",
        is_active=True,
        is_admin=True,
    )

    store = {
        "proposta": None,
        "pq_items": [],
        "cpu_items": [],
    }

    class FakePropostaService:
        async def criar_proposta(self, _cliente_id, usuario_id, data):
            store["proposta"] = SimpleNamespace(
                id=proposta_id,
                cliente_id=_cliente_id,
                criado_por_id=usuario_id,
                codigo="PROP-2026-0001",
                titulo=data.titulo,
                descricao=data.descricao,
                status="RASCUNHO",
                versao_cpu=1,
                pc_cabecalho_id=None,
                total_direto=None,
                total_indireto=None,
                total_geral=None,
                data_finalizacao=None,
                created_at=now,
                updated_at=now,
            )
            return store["proposta"]

        async def listar_propostas(self, _cliente_id, page=1, page_size=20):
            return ([store["proposta"]] if store["proposta"] else [], 1 if store["proposta"] else 0)

        async def obter_por_id(self, _proposta_id):
            return store["proposta"]

        async def atualizar_metadados(self, _proposta_id, _cliente_id, data):
            if data.titulo is not None:
                store["proposta"].titulo = data.titulo
            if data.descricao is not None:
                store["proposta"].descricao = data.descricao
            return store["proposta"]

        async def soft_delete(self, _proposta_id, _cliente_id):
            return None

    class FakeImportService:
        def __init__(self, *args, **kwargs):
            pass

        async def importar_planilha(self, _proposta_id, arquivo):
            await arquivo.read()
            store["pq_items"] = [
                SimpleNamespace(
                    id=pq_item_id,
                    proposta_id=_proposta_id,
                    descricao_original="Escavacao manual",
                    quantidade_original=3,
                    servico_match_id=None,
                    servico_match_tipo=None,
                    match_status="PENDENTE",
                )
            ]
            return SimpleNamespace(
                id=importacao_id,
                status=SimpleNamespace(value="CONCLUIDO"),
                linhas_total=1,
                linhas_importadas=1,
                linhas_com_erro=0,
            )

    class FakeMatchService:
        def __init__(self, *args, **kwargs):
            pass

        async def executar_match_para_proposta(self, _proposta_id, _usuario_id):
            item = store["pq_items"][0]
            item.servico_match_id = servico_id
            item.servico_match_tipo = "BASE_TCPO"
            item.match_status = "CONFIRMADO"
            return {"processados": 1, "sugeridos": 1, "sem_match": 0}

    class FakeCpuService:
        def __init__(self, *args, **kwargs):
            pass

        async def gerar_cpu_para_proposta(self, proposta_id=None, pc_cabecalho_id=None, percentual_bdi=0, **kwargs):
            store["proposta"].status = "CPU_GERADA"
            store["proposta"].pc_cabecalho_id = pc_cabecalho_id
            store["proposta"].total_direto = 75.0
            store["proposta"].total_indireto = 0.0
            store["proposta"].total_geral = 75.0
            store["cpu_items"] = [
                SimpleNamespace(
                    id=cpu_item_id,
                    proposta_id=proposta_id,
                    pq_item_id=pq_item_id,
                    servico_id=servico_id,
                    servico_tipo="BASE_TCPO",
                    codigo="TCPO-001",
                    descricao="Escavacao manual",
                    unidade_medida="m2",
                    quantidade=3,
                    custo_material_unitario=25,
                    custo_mao_obra_unitario=0,
                    custo_equipamento_unitario=0,
                    custo_direto_unitario=25,
                    percentual_indireto=0,
                    custo_indireto_unitario=0,
                    preco_unitario=25,
                    preco_total=75,
                    composicao_fonte="custo_base",
                    pc_cabecalho_id=pc_cabecalho_id,
                    ordem=0,
                    created_at=now,
                    updated_at=now,
                )
            ]
            return {
                "proposta_id": str(proposta_id),
                "total_direto": 75.0,
                "total_indireto": 0.0,
                "total_geral": 75.0,
                "detalhe": {"processados": 1, "erros": 0},
            }

        async def listar_cpu_itens(self, _proposta_id):
            return store["cpu_items"]

    async def _override_user():
        return current_user

    async def _override_db():
        yield AsyncMock()

    async def _override_service():
        return FakePropostaService()

    app = create_app()
    app.dependency_overrides[get_current_active_user] = _override_user
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[propostas._get_service] = _override_service

    original_import_service = pq_importacao.PqImportService
    original_match_service = pq_importacao.PqMatchService
    original_cpu_service = cpu_geracao.CpuGeracaoService
    original_pq_lookup = pq_importacao._get_proposta_or_404
    original_cpu_lookup = cpu_geracao._get_proposta_or_404
    pq_importacao.PqImportService = FakeImportService
    pq_importacao.PqMatchService = FakeMatchService
    cpu_geracao.CpuGeracaoService = FakeCpuService
    pq_importacao._get_proposta_or_404 = AsyncMock(side_effect=lambda *_args, **_kwargs: store["proposta"])
    cpu_geracao._get_proposta_or_404 = AsyncMock(side_effect=lambda *_args, **_kwargs: store["proposta"])

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post(
                "/api/v1/propostas/",
                json={
                    "cliente_id": str(cliente_id),
                    "titulo": "Smoke Proposta",
                    "descricao": "Fluxo completo",
                },
            )
            assert create_resp.status_code == 201, create_resp.text

            upload_resp = await client.post(
                f"/api/v1/propostas/{proposta_id}/pq/importar",
                files={
                    "arquivo": (
                        "pq.csv",
                        b"codigo,descricao,unidade,quantidade\n001,Escavacao manual,m2,3\n",
                        "text/csv",
                    )
                },
            )
            assert upload_resp.status_code == 201, upload_resp.text
            assert upload_resp.json()["linhas_importadas"] == 1

            match_resp = await client.post(f"/api/v1/propostas/{proposta_id}/pq/match")
            assert match_resp.status_code == 200, match_resp.text
            assert match_resp.json()["sugeridos"] == 1

            cpu_resp = await client.post(f"/api/v1/propostas/{proposta_id}/cpu/gerar")
            assert cpu_resp.status_code == 200, cpu_resp.text
            assert cpu_resp.json()["detalhe"]["processados"] == 1

            proposta_resp = await client.get(f"/api/v1/propostas/{proposta_id}")
            assert proposta_resp.status_code == 200, proposta_resp.text
            assert proposta_resp.json()["status"] == "CPU_GERADA"

            itens_resp = await client.get(f"/api/v1/propostas/{proposta_id}/cpu/itens")
            assert itens_resp.status_code == 200, itens_resp.text
            itens = itens_resp.json()
            assert len(itens) == 1
            assert itens[0]["codigo"] == "TCPO-001"
    finally:
        pq_importacao.PqImportService = original_import_service
        pq_importacao.PqMatchService = original_match_service
        cpu_geracao.CpuGeracaoService = original_cpu_service
        pq_importacao._get_proposta_or_404 = original_pq_lookup
        cpu_geracao._get_proposta_or_404 = original_cpu_lookup

