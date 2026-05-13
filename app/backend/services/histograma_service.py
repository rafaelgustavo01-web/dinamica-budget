"""Service for per-proposal cost snapshot (Histograma)."""

import asyncio
import uuid
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundError, UnprocessableEntityError, ValidationError
from backend.core.logging import get_logger
from backend.models.bcu import (
    BcuCabecalho,
    BcuEncargoItem,
    BcuEpiItem,
    BcuEquipamentoItem,
    BcuEquipamentoPremissa,
    BcuFerramentaItem,
    BcuMaoObraItem,
    BcuMobilizacaoItem,
    BcuMobilizacaoQuantidadeFuncao,
    BcuTableType,
)
from backend.models.proposta import Proposta, PropostaItem, PropostaItemComposicao
from backend.models.proposta_pc import (
    PropostaPcEncargo,
    PropostaPcEpi,
    PropostaPcEquipamento,
    PropostaPcEquipamentoPremissa,
    PropostaPcFerramenta,
    PropostaPcMaoObra,
    PropostaPcMobilizacao,
    PropostaPcMobilizacaoQuantidade,
)
from backend.models.proposta_recurso_extra import PropostaRecursoExtra
from backend.repositories.base_tcpo_repository import BaseTcpoRepository
from backend.repositories.bcu_de_para_repository import BcuDeParaRepository
from backend.repositories.bcu_repository import BcuRepository
from backend.repositories.proposta_pc_repository import ProposalPcRepository
from backend.repositories.proposta_repository import PropostaRepository
from backend.repositories.proposta_recurso_extra_repository import PropostaRecursoExtraRepository

logger = get_logger(__name__)

EDITABLE_FIELDS = {
    "mao-obra": {
        "quantidade",
        "salario",
        "previsao_reajuste",
        "encargos_percent",
        "periculosidade_insalubridade",
        "refeicao",
        "agua_potavel",
        "vale_alimentacao",
        "plano_saude",
        "ferramentas_val",
        "seguro_vida",
        "abono_ferias",
        "uniforme_val",
        "epi_val",
        "custo_unitario_h",
        "custo_mensal",
        "mobilizacao",
    },
    "equipamento": {
        "combustivel_utilizado",
        "consumo_l_h",
        "aluguel_r_h",
        "combustivel_r_h",
        "mao_obra_r_h",
        "hora_produtiva",
        "hora_improdutiva",
        "mes",
        "aluguel_mensal",
    },
    "equipamento-premissa": {"horas_mes", "preco_gasolina_l", "preco_diesel_l"},
    "encargo": {"taxa_percent", "grupo", "codigo_grupo", "discriminacao_encargo"},
    "epi": {"unidade", "custo_unitario", "quantidade", "vida_util_meses", "custo_epi_mes"},
    "ferramenta": {"item", "unidade", "quantidade", "preco", "preco_total"},
    "mobilizacao": {"descricao", "funcao", "tipo_mao_obra"},
}


def _tipo_recurso_value(tipo: Any) -> str | None:
    return tipo.value if hasattr(tipo, "value") else tipo


class HistogramaService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ProposalPcRepository(db)
        self.proposta_repo = PropostaRepository(db)
        self.bcu_repo = BcuRepository(db)
        self.de_para_repo = BcuDeParaRepository(db)
        self.tcpo_repo = BaseTcpoRepository(db)

    async def montar_histograma(self, proposta_id: UUID) -> dict[str, int]:
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta:
            raise NotFoundError("Proposta", str(proposta_id))

        cabecalho = await self.bcu_repo.get_cabecalho_ativo()
        if not cabecalho:
            raise UnprocessableEntityError("Nenhum cabecalho BCU ativo encontrado.")

        # Extrair composicoes para obter insumos unicos — join direto evita subquery do .has()
        comp_result = await self.db.execute(
            select(PropostaItemComposicao)
            .join(PropostaItem, PropostaItem.id == PropostaItemComposicao.proposta_item_id)
            .where(PropostaItem.proposta_id == proposta_id)
        )
        composicoes = comp_result.scalars().all()

        insumos_unicos = {c.insumo_base_id for c in composicoes if c.insumo_base_id}
        insumos_list = list(insumos_unicos)

        # Batch fetch De/Para and BaseTcpo in parallel (eliminates N+1)
        mapeamento, tcpo_map = await asyncio.gather(
            self.de_para_repo.get_by_base_tcpo_ids(insumos_list),
            self.tcpo_repo.get_by_ids(insumos_list),
        )

        # Batch fetch all BCU items referenced by the De/Para mapping in parallel
        mo_ids = [dp.bcu_item_id for dp in mapeamento.values() if dp.bcu_table_type == BcuTableType.MO]
        eqp_ids = [dp.bcu_item_id for dp in mapeamento.values() if dp.bcu_table_type == BcuTableType.EQP]
        epi_ids = [dp.bcu_item_id for dp in mapeamento.values() if dp.bcu_table_type == BcuTableType.EPI]
        fer_ids = [dp.bcu_item_id for dp in mapeamento.values() if dp.bcu_table_type == BcuTableType.FER]

        async def _batch_get(model, ids):
            if not ids:
                return {}
            r = await self.db.execute(select(model).where(model.id.in_(ids)))
            return {item.id: item for item in r.scalars().all()}

        bcu_mo_map, bcu_eqp_map, bcu_epi_map, bcu_fer_map = await asyncio.gather(
            _batch_get(BcuMaoObraItem, mo_ids),
            _batch_get(BcuEquipamentoItem, eqp_ids),
            _batch_get(BcuEpiItem, epi_ids),
            _batch_get(BcuFerramentaItem, fer_ids),
        )

        mo_items: list[dict] = []
        eqp_items: list[dict] = []
        epi_items: list[dict] = []
        fer_items: list[dict] = []

        for insumo_id in insumos_list:
            tcpo = tcpo_map.get(insumo_id)
            if not tcpo:
                continue

            de_para = mapeamento.get(insumo_id)
            if de_para:
                if de_para.bcu_table_type == BcuTableType.MO:
                    bcu_item = bcu_mo_map.get(de_para.bcu_item_id)
                    if bcu_item:
                        mo_items.append({
                            "id": uuid.uuid4(),
                            "proposta_id": proposta_id,
                            "bcu_item_id": bcu_item.id,
                            "descricao_funcao": bcu_item.descricao_funcao,
                            "codigo_origem": bcu_item.codigo_origem,
                            "quantidade": max(1, int(bcu_item.quantidade or 1)),
                            "salario": bcu_item.salario,
                            "previsao_reajuste": bcu_item.previsao_reajuste,
                            "encargos_percent": bcu_item.encargos_percent,
                            "periculosidade_insalubridade": bcu_item.periculosidade_insalubridade,
                            "refeicao": bcu_item.refeicao,
                            "agua_potavel": bcu_item.agua_potavel,
                            "vale_alimentacao": bcu_item.vale_alimentacao,
                            "plano_saude": bcu_item.plano_saude,
                            "ferramentas_val": bcu_item.ferramentas_val,
                            "seguro_vida": bcu_item.seguro_vida,
                            "abono_ferias": bcu_item.abono_ferias,
                            "uniforme_val": bcu_item.uniforme_val,
                            "epi_val": bcu_item.epi_val,
                            "custo_unitario_h": bcu_item.custo_unitario_h,
                            "custo_mensal": bcu_item.custo_mensal,
                            "mobilizacao": bcu_item.mobilizacao,
                            "valor_bcu_snapshot": bcu_item.custo_unitario_h,
                            "editado_manualmente": False,
                        })
                elif de_para.bcu_table_type == BcuTableType.EQP:
                    bcu_item = bcu_eqp_map.get(de_para.bcu_item_id)
                    if bcu_item:
                        eqp_items.append({
                            "id": uuid.uuid4(),
                            "proposta_id": proposta_id,
                            "bcu_item_id": bcu_item.id,
                            "codigo": bcu_item.codigo,
                            "codigo_origem": bcu_item.codigo_origem,
                            "equipamento": bcu_item.equipamento,
                            "combustivel_utilizado": bcu_item.combustivel_utilizado,
                            "consumo_l_h": bcu_item.consumo_l_h,
                            "aluguel_r_h": bcu_item.aluguel_r_h,
                            "combustivel_r_h": bcu_item.combustivel_r_h,
                            "mao_obra_r_h": bcu_item.mao_obra_r_h,
                            "hora_produtiva": bcu_item.hora_produtiva,
                            "hora_improdutiva": bcu_item.hora_improdutiva,
                            "mes": bcu_item.mes,
                            "aluguel_mensal": bcu_item.aluguel_mensal,
                            "valor_bcu_snapshot": bcu_item.aluguel_r_h,
                            "editado_manualmente": False,
                        })
                elif de_para.bcu_table_type == BcuTableType.EPI:
                    bcu_item = bcu_epi_map.get(de_para.bcu_item_id)
                    if bcu_item:
                        epi_items.append({
                            "id": uuid.uuid4(),
                            "proposta_id": proposta_id,
                            "bcu_item_id": bcu_item.id,
                            "codigo_origem": bcu_item.codigo_origem,
                            "epi": bcu_item.epi,
                            "unidade": bcu_item.unidade,
                            "custo_unitario": bcu_item.custo_unitario,
                            "quantidade": max(1, int(bcu_item.quantidade or 1)),
                            "vida_util_meses": bcu_item.vida_util_meses,
                            "custo_epi_mes": bcu_item.custo_epi_mes,
                            "valor_bcu_snapshot": bcu_item.custo_unitario,
                            "editado_manualmente": False,
                        })
                elif de_para.bcu_table_type == BcuTableType.FER:
                    bcu_item = bcu_fer_map.get(de_para.bcu_item_id)
                    if bcu_item:
                        fer_items.append({
                            "id": uuid.uuid4(),
                            "proposta_id": proposta_id,
                            "bcu_item_id": bcu_item.id,
                            "codigo_origem": bcu_item.codigo_origem,
                            "item": bcu_item.item,
                            "descricao": bcu_item.descricao,
                            "unidade": bcu_item.unidade,
                            "quantidade": max(1, int(bcu_item.quantidade or 1)),
                            "preco": bcu_item.preco,
                            "preco_total": bcu_item.preco_total,
                            "valor_bcu_snapshot": bcu_item.preco,
                            "editado_manualmente": False,
                        })
            else:
                # Não mapeado (sem BCU)
                tipo_recurso = _tipo_recurso_value(tcpo.tipo_recurso)
                if tipo_recurso == "MO":
                    mo_items.append({
                        "id": uuid.uuid4(),
                        "proposta_id": proposta_id,
                        "bcu_item_id": None,
                        "descricao_funcao": tcpo.descricao,
                        "codigo_origem": tcpo.codigo_origem,
                        "custo_unitario_h": tcpo.custo_base,
                        "valor_bcu_snapshot": tcpo.custo_base,
                        "editado_manualmente": False,
                    })
                elif tipo_recurso == "EQUIPAMENTO":
                    eqp_items.append({
                        "id": uuid.uuid4(),
                        "proposta_id": proposta_id,
                        "bcu_item_id": None,
                        "equipamento": tcpo.descricao,
                        "codigo_origem": tcpo.codigo_origem,
                        "aluguel_r_h": tcpo.custo_base,
                        "valor_bcu_snapshot": tcpo.custo_base,
                        "editado_manualmente": False,
                    })
                elif tipo_recurso == "INSUMO":
                    codigo_origem = (tcpo.codigo_origem or "").upper()
                    if codigo_origem.startswith("FER-"):
                        fer_items.append({
                            "id": uuid.uuid4(),
                            "proposta_id": proposta_id,
                            "bcu_item_id": None,
                            "codigo_origem": tcpo.codigo_origem,
                            "descricao": tcpo.descricao,
                            "preco": tcpo.custo_base,
                            "valor_bcu_snapshot": tcpo.custo_base,
                            "editado_manualmente": False,
                        })
                    elif codigo_origem.startswith("EPI-"):
                        epi_items.append({
                            "id": uuid.uuid4(),
                            "proposta_id": proposta_id,
                            "bcu_item_id": None,
                            "codigo_origem": tcpo.codigo_origem,
                            "epi": tcpo.descricao,
                            "custo_unitario": tcpo.custo_base,
                            "valor_bcu_snapshot": tcpo.custo_base,
                            "editado_manualmente": False,
                        })
                    else:
                        logger.warning(
                            "histograma.insumo_sem_de_para_ignorado",
                            proposta_id=str(proposta_id),
                            base_tcpo_id=str(tcpo.id),
                            codigo_origem=tcpo.codigo_origem,
                        )

        # Limpar dados antigos em paralelo (garante que cada proposta tem apenas seu histograma)
        await asyncio.gather(
            self.repo.clear_mao_obra(proposta_id),
            self.repo.clear_equipamentos(proposta_id),
            self.repo.clear_epi(proposta_id),
            self.repo.clear_ferramentas(proposta_id),
        )

        # Inserir novos dados em paralelo (4 tabelas independentes)
        await asyncio.gather(
            self.repo.bulk_insert(PropostaPcMaoObra, mo_items),
            self.repo.bulk_insert(PropostaPcEquipamento, eqp_items),
            self.repo.bulk_insert(PropostaPcEpi, epi_items),
            self.repo.bulk_insert(PropostaPcFerramenta, fer_items),
        )

        # Equipamento Premissa (se existir no BCU ativo, copia 1:1)
        premissas = await self.bcu_repo.list_equipamento_premissas(cabecalho.id)
        if premissas:
            existing_premissa = await self.repo.list_equipamento_premissas(proposta_id)
            if not existing_premissa:
                p = premissas[0]
                await self.repo.bulk_insert(PropostaPcEquipamentoPremissa, [{
                    "id": uuid.uuid4(),
                    "proposta_id": proposta_id,
                    "bcu_item_id": p.id,
                    "horas_mes": p.horas_mes,
                    "preco_gasolina_l": p.preco_gasolina_l,
                    "preco_diesel_l": p.preco_diesel_l,
                    "editado_manualmente": False,
                }])

        # Encargos (Integral) — clear + insert em nested transaction
        bcu_encargos = await self.bcu_repo.list_encargos(cabecalho.id)
        encargos_items = [
            {
                "id": uuid.uuid4(),
                "proposta_id": proposta_id,
                "bcu_item_id": e.id,
                "tipo_encargo": e.tipo_encargo,
                "grupo": e.grupo,
                "codigo_grupo": e.codigo_grupo,
                "discriminacao_encargo": e.discriminacao_encargo,
                "taxa_percent": e.taxa_percent,
                "valor_bcu_snapshot": e.taxa_percent,
                "editado_manualmente": False,
            }
            for e in bcu_encargos
        ]
        async with self.db.begin_nested():
            await self.repo.clear_encargos(proposta_id)
            await self.repo.bulk_insert(PropostaPcEncargo, encargos_items)

        # Mobilizacao (Integral) — batch fetch quantidades, then clear + insert
        await self.repo.clear_mobilizacao(proposta_id)
        bcu_mob = await self.bcu_repo.list_mobilizacao_items(cabecalho.id)
        mob_items: list[dict] = []
        mob_qtd_items: list[dict] = []

        mob_ids = [m.id for m in bcu_mob]
        bcu_mob_qtds = []
        if mob_ids:
            result_qtd = await self.db.execute(
                select(BcuMobilizacaoQuantidadeFuncao)
                .where(BcuMobilizacaoQuantidadeFuncao.mobilizacao_item_id.in_(mob_ids))
            )
            bcu_mob_qtds = result_qtd.scalars().all()

        qtds_by_mob: dict[UUID, list] = {}
        for q in bcu_mob_qtds:
            qtds_by_mob.setdefault(q.mobilizacao_item_id, []).append(q)

        for m in bcu_mob:
            mob_id = uuid.uuid4()
            mob_items.append({
                "id": mob_id,
                "proposta_id": proposta_id,
                "bcu_item_id": m.id,
                "descricao": m.descricao,
                "funcao": m.funcao,
                "tipo_mao_obra": m.tipo_mao_obra,
                "editado_manualmente": False,
            })
            for q in qtds_by_mob.get(m.id, []):
                mob_qtd_items.append({
                    "id": uuid.uuid4(),
                    "mobilizacao_id": mob_id,
                    "coluna_funcao": q.coluna_funcao,
                    "quantidade": q.quantidade,
                })

        await self.repo.bulk_insert(PropostaPcMobilizacao, mob_items)
        if mob_qtd_items:
            await self.repo.bulk_insert(PropostaPcMobilizacaoQuantidade, mob_qtd_items)

        # Fixar cabecalho
        proposta.bcu_cabecalho_id = cabecalho.id
        proposta.cpu_desatualizada = True
        self.db.add(proposta)
        await self.db.flush()

        return {
            "mao_obra": len(mo_items),
            "equipamento_premissa": 1 if premissas else 0,
            "equipamentos": len(eqp_items),
            "encargos": len(encargos_items),
            "epis": len(epi_items),
            "ferramentas": len(fer_items),
            "mobilizacao": len(mob_items),
        }

    async def get_histograma(self, proposta_id: UUID) -> dict:
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta:
            raise NotFoundError("Proposta", str(proposta_id))

        # Paraleliza todas as queries independentes do histograma
        recurso_repo = PropostaRecursoExtraRepository(self.db)
        (
            premissa,
            encargos,
            recursos_extras,
            mao_obra,
            equipamentos,
            epis,
            ferramentas,
            mobilizacao,
            divergencias,
        ) = await asyncio.gather(
            self.repo.list_equipamento_premissas(proposta_id),
            self.repo.list_encargos(proposta_id),
            recurso_repo.list_by_proposta(proposta_id),
            self.repo.list_mao_obra(proposta_id),
            self.repo.list_equipamentos(proposta_id),
            self.repo.list_epi(proposta_id),
            self.repo.list_ferramentas(proposta_id),
            self.repo.list_mobilizacao(proposta_id),
            self.detectar_divergencias(proposta_id),
        )

        return {
            "proposta_id": str(proposta_id),
            "bcu_cabecalho_id": str(proposta.bcu_cabecalho_id) if proposta.bcu_cabecalho_id else None,
            "mao_obra": mao_obra,
            "equipamento_premissa": premissa[0] if premissa else None,
            "equipamentos": equipamentos,
            "encargos_horista": [e for e in encargos if e.tipo_encargo == "HORISTA"],
            "encargos_mensalista": [e for e in encargos if e.tipo_encargo == "MENSALISTA"],
            "epis": epis,
            "ferramentas": ferramentas,
            "mobilizacao": mobilizacao,
            "recursos_extras": recursos_extras,
            "divergencias": divergencias,
            "cpu_desatualizada": proposta.cpu_desatualizada,
        }

    async def detectar_divergencias(self, proposta_id: UUID) -> list[dict]:
        divergencias: list[dict] = []
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta or not proposta.bcu_cabecalho_id:
            return divergencias

        # Dispara todas as queries de divergência em paralelo
        r_mo, r_eqp, r_epi, r_fer, r_enc = await asyncio.gather(
            self.db.execute(
                select(PropostaPcMaoObra.id, PropostaPcMaoObra.valor_bcu_snapshot, BcuMaoObraItem.custo_unitario_h)
                .join(BcuMaoObraItem, PropostaPcMaoObra.bcu_item_id == BcuMaoObraItem.id)
                .where(PropostaPcMaoObra.proposta_id == proposta_id)
            ),
            self.db.execute(
                select(PropostaPcEquipamento.id, PropostaPcEquipamento.valor_bcu_snapshot, BcuEquipamentoItem.aluguel_r_h)
                .join(BcuEquipamentoItem, PropostaPcEquipamento.bcu_item_id == BcuEquipamentoItem.id)
                .where(PropostaPcEquipamento.proposta_id == proposta_id)
            ),
            self.db.execute(
                select(PropostaPcEpi.id, PropostaPcEpi.valor_bcu_snapshot, BcuEpiItem.custo_unitario)
                .join(BcuEpiItem, PropostaPcEpi.bcu_item_id == BcuEpiItem.id)
                .where(PropostaPcEpi.proposta_id == proposta_id)
            ),
            self.db.execute(
                select(PropostaPcFerramenta.id, PropostaPcFerramenta.valor_bcu_snapshot, BcuFerramentaItem.preco)
                .join(BcuFerramentaItem, PropostaPcFerramenta.bcu_item_id == BcuFerramentaItem.id)
                .where(PropostaPcFerramenta.proposta_id == proposta_id)
            ),
            self.db.execute(
                select(PropostaPcEncargo.id, PropostaPcEncargo.valor_bcu_snapshot, BcuEncargoItem.taxa_percent)
                .join(BcuEncargoItem, PropostaPcEncargo.bcu_item_id == BcuEncargoItem.id)
                .where(PropostaPcEncargo.proposta_id == proposta_id)
            ),
        )

        for p_id, snapshot, atual in r_mo:
            if snapshot != atual:
                divergencias.append({
                    "tabela": "mao-obra",
                    "item_id": str(p_id),
                    "campo": "custo_unitario_h",
                    "valor_snapshot": float(snapshot) if snapshot is not None else None,
                    "valor_atual_bcu": float(atual) if atual is not None else None,
                    "valor_proposta": None,
                })

        for p_id, snapshot, atual in r_eqp:
            if snapshot != atual:
                divergencias.append({
                    "tabela": "equipamento",
                    "item_id": str(p_id),
                    "campo": "aluguel_r_h",
                    "valor_snapshot": float(snapshot) if snapshot is not None else None,
                    "valor_atual_bcu": float(atual) if atual is not None else None,
                    "valor_proposta": None,
                })

        for p_id, snapshot, atual in r_epi:
            if snapshot != atual:
                divergencias.append({
                    "tabela": "epi",
                    "item_id": str(p_id),
                    "campo": "custo_unitario",
                    "valor_snapshot": float(snapshot) if snapshot is not None else None,
                    "valor_atual_bcu": float(atual) if atual is not None else None,
                    "valor_proposta": None,
                })

        for p_id, snapshot, atual in r_fer:
            if snapshot != atual:
                divergencias.append({
                    "tabela": "ferramenta",
                    "item_id": str(p_id),
                    "campo": "preco",
                    "valor_snapshot": float(snapshot) if snapshot is not None else None,
                    "valor_atual_bcu": float(atual) if atual is not None else None,
                    "valor_proposta": None,
                })

        for p_id, snapshot, atual in r_enc:
            if snapshot != atual:
                divergencias.append({
                    "tabela": "encargo",
                    "item_id": str(p_id),
                    "campo": "taxa_percent",
                    "valor_snapshot": float(snapshot) if snapshot is not None else None,
                    "valor_atual_bcu": float(atual) if atual is not None else None,
                    "valor_proposta": None,
                })

        return divergencias

    async def editar_item(self, tabela: str, item_id: UUID, payload: dict) -> None:
        model_map = {
            "mao-obra": PropostaPcMaoObra,
            "equipamento": PropostaPcEquipamento,
            "equipamento-premissa": PropostaPcEquipamentoPremissa,
            "encargo": PropostaPcEncargo,
            "epi": PropostaPcEpi,
            "ferramenta": PropostaPcFerramenta,
            "mobilizacao": PropostaPcMobilizacao,
        }
        model = model_map.get(tabela)
        if not model:
            raise ValidationError(f"Tabela inválida: {tabela}")

        item = await self.repo.get_item(model, item_id)
        if not item:
            raise NotFoundError("Item", str(item_id))

        allowed = EDITABLE_FIELDS[tabela]
        invalid_fields = sorted(set(payload) - allowed)
        if invalid_fields:
            raise ValidationError(f"Campo(s) não editável(is): {', '.join(invalid_fields)}")

        for k, v in payload.items():
            if hasattr(item, k):
                setattr(item, k, v)
        
        item.editado_manualmente = True
        
        proposta = await self.proposta_repo.get_by_id(item.proposta_id)
        if not proposta:
            raise NotFoundError("Proposta", str(item.proposta_id))
        proposta.cpu_desatualizada = True

        self.db.add(item)
        self.db.add(proposta)
        await self.db.flush()

    async def aceitar_valor_bcu(self, tabela: str, item_id: UUID) -> None:
        model_map = {
            "mao-obra": (PropostaPcMaoObra, BcuMaoObraItem, "custo_unitario_h", "custo_unitario_h"),
            "equipamento": (PropostaPcEquipamento, BcuEquipamentoItem, "aluguel_r_h", "aluguel_r_h"),
            "epi": (PropostaPcEpi, BcuEpiItem, "custo_unitario", "custo_unitario"),
            "ferramenta": (PropostaPcFerramenta, BcuFerramentaItem, "preco", "preco"),
            "encargo": (PropostaPcEncargo, BcuEncargoItem, "taxa_percent", "taxa_percent"),
        }
        
        mapping = model_map.get(tabela)
        if not mapping:
            raise ValidationError(f"Tabela inválida ou não suportada: {tabela}")
            
        model_pc, model_bcu, campo_pc, campo_bcu = mapping
        
        item_pc = await self.repo.get_item(model_pc, item_id)
        if not item_pc:
            raise NotFoundError("Item", str(item_id))
            
        if not item_pc.bcu_item_id:
            raise UnprocessableEntityError("Item não possui vínculo com BCU.")
            
        item_bcu = await self.db.get(model_bcu, item_pc.bcu_item_id)
        if not item_bcu:
            raise UnprocessableEntityError("Item BCU vinculado não encontrado.")
            
        novo_valor = getattr(item_bcu, campo_bcu)
        
        setattr(item_pc, campo_pc, novo_valor)
        item_pc.valor_bcu_snapshot = novo_valor
        item_pc.editado_manualmente = False
        
        proposta = await self.proposta_repo.get_by_id(item_pc.proposta_id)
        if not proposta:
            raise NotFoundError("Proposta", str(item_pc.proposta_id))
        proposta.cpu_desatualizada = True
        
        self.db.add(item_pc)
        self.db.add(proposta)
        await self.db.flush()
