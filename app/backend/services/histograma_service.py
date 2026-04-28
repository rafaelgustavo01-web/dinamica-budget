"""Service for per-proposal cost snapshot (Histograma)."""

import uuid
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundError, UnprocessableEntityError, ValidationError
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
from backend.models.proposta import Proposta, PropostaItemComposicao
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

        # Extrair composicoes para obter insumos unicos
        comp_result = await self.db.execute(
            select(PropostaItemComposicao)
            .join(PropostaItemComposicao.proposta_item)
            .where(PropostaItemComposicao.proposta_item.has(proposta_id=proposta_id))
        )
        composicoes = comp_result.scalars().all()

        insumos_unicos = set()
        for c in composicoes:
            if c.insumo_base_id:
                insumos_unicos.add(c.insumo_base_id)

        # Buscar todos os De/Para relevantes
        mapeamento = {}
        for insumo_id in insumos_unicos:
            de_para = await self.de_para_repo.get_by_base_tcpo_id(insumo_id)
            if de_para:
                mapeamento[insumo_id] = de_para

        mo_items = []
        eqp_items = []
        epi_items = []
        fer_items = []

        for insumo_id in insumos_unicos:
            tcpo = await self.tcpo_repo.get_by_id(insumo_id)
            if not tcpo:
                continue

            de_para = mapeamento.get(insumo_id)
            if de_para:
                if de_para.bcu_table_type == BcuTableType.MO:
                    bcu_item = await self.db.get(BcuMaoObraItem, de_para.bcu_item_id)
                    if bcu_item:
                        mo_items.append({
                            "id": uuid.uuid4(),
                            "proposta_id": proposta_id,
                            "bcu_item_id": bcu_item.id,
                            "descricao_funcao": bcu_item.descricao_funcao,
                            "codigo_origem": bcu_item.codigo_origem,
                            "quantidade": bcu_item.quantidade,
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
                    bcu_item = await self.db.get(BcuEquipamentoItem, de_para.bcu_item_id)
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
                    bcu_item = await self.db.get(BcuEpiItem, de_para.bcu_item_id)
                    if bcu_item:
                        epi_items.append({
                            "id": uuid.uuid4(),
                            "proposta_id": proposta_id,
                            "bcu_item_id": bcu_item.id,
                            "codigo_origem": bcu_item.codigo_origem,
                            "epi": bcu_item.epi,
                            "unidade": bcu_item.unidade,
                            "custo_unitario": bcu_item.custo_unitario,
                            "quantidade": bcu_item.quantidade,
                            "vida_util_meses": bcu_item.vida_util_meses,
                            "custo_epi_mes": bcu_item.custo_epi_mes,
                            "valor_bcu_snapshot": bcu_item.custo_unitario,
                            "editado_manualmente": False,
                        })
                elif de_para.bcu_table_type == BcuTableType.FER:
                    bcu_item = await self.db.get(BcuFerramentaItem, de_para.bcu_item_id)
                    if bcu_item:
                        fer_items.append({
                            "id": uuid.uuid4(),
                            "proposta_id": proposta_id,
                            "bcu_item_id": bcu_item.id,
                            "codigo_origem": bcu_item.codigo_origem,
                            "item": bcu_item.item,
                            "descricao": bcu_item.descricao,
                            "unidade": bcu_item.unidade,
                            "quantidade": bcu_item.quantidade,
                            "preco": bcu_item.preco,
                            "preco_total": bcu_item.preco_total,
                            "valor_bcu_snapshot": bcu_item.preco,
                            "editado_manualmente": False,
                        })
            else:
                # Não mapeado (sem BCU)
                if tcpo.tipo_recurso and tcpo.tipo_recurso.value == "MO":
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
                elif tcpo.tipo_recurso and tcpo.tipo_recurso.value == "EQUIPAMENTO":
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
                elif tcpo.tipo_recurso and tcpo.tipo_recurso.value == "INSUMO":
                    # Assume EPI for insumo fallback if not mapped, or skip? We'll put in EPI.
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

        # Upsert
        await self.repo.bulk_upsert(PropostaPcMaoObra, mo_items, ["proposta_id", "bcu_item_id"])
        await self.repo.bulk_upsert(PropostaPcEquipamento, eqp_items, ["proposta_id", "bcu_item_id"])
        await self.repo.bulk_upsert(PropostaPcEpi, epi_items, ["proposta_id", "bcu_item_id"])
        await self.repo.bulk_upsert(PropostaPcFerramenta, fer_items, ["proposta_id", "bcu_item_id"])

        # Equipamento Premissa (se existir no BCU ativo, copia 1:1)
        premissas = await self.bcu_repo.list_equipamento_premissas(cabecalho.id)
        if premissas:
            p = premissas[0]
            existing_premissa = await self.repo.list_equipamento_premissas(proposta_id)
            if not existing_premissa:
                await self.repo.bulk_insert(PropostaPcEquipamentoPremissa, [{
                    "id": uuid.uuid4(),
                    "proposta_id": proposta_id,
                    "bcu_item_id": p.id,
                    "horas_mes": p.horas_mes,
                    "preco_gasolina_l": p.preco_gasolina_l,
                    "preco_diesel_l": p.preco_diesel_l,
                    "editado_manualmente": False,
                }])

        # Encargos (Integral)
        await self.repo.clear_encargos(proposta_id)
        bcu_encargos = await self.bcu_repo.list_encargos(cabecalho.id)
        encargos_items = []
        for e in bcu_encargos:
            encargos_items.append({
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
            })
        await self.repo.bulk_insert(PropostaPcEncargo, encargos_items)

        # Mobilizacao (Integral)
        await self.repo.clear_mobilizacao(proposta_id)
        bcu_mob = await self.bcu_repo.list_mobilizacao_items(cabecalho.id)
        mob_items = []
        mob_qtd_items = []
        
        mob_ids = [m.id for m in bcu_mob]
        bcu_mob_qtds = []
        if mob_ids:
            result_qtd = await self.db.execute(
                select(BcuMobilizacaoQuantidadeFuncao)
                .where(BcuMobilizacaoQuantidadeFuncao.mobilizacao_item_id.in_(mob_ids))
            )
            bcu_mob_qtds = result_qtd.scalars().all()
            
        qtds_by_mob = {}
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

        premissa = await self.repo.list_equipamento_premissas(proposta_id)
        encargos = await self.repo.list_encargos(proposta_id)
        
        recurso_repo = PropostaRecursoExtraRepository(self.db)
        recursos_extras = await recurso_repo.list_by_proposta(proposta_id)

        return {
            "proposta_id": str(proposta_id),
            "bcu_cabecalho_id": str(proposta.bcu_cabecalho_id) if proposta.bcu_cabecalho_id else None,
            "mao_obra": await self.repo.list_mao_obra(proposta_id),
            "equipamento_premissa": premissa[0] if premissa else None,
            "equipamentos": await self.repo.list_equipamentos(proposta_id),
            "encargos_horista": [e for e in encargos if e.tipo_encargo == "HORISTA"],
            "encargos_mensalista": [e for e in encargos if e.tipo_encargo == "MENSALISTA"],
            "epis": await self.repo.list_epi(proposta_id),
            "ferramentas": await self.repo.list_ferramentas(proposta_id),
            "mobilizacao": await self.repo.list_mobilizacao(proposta_id),
            "recursos_extras": recursos_extras,
            "divergencias": await self.detectar_divergencias(proposta_id),
            "cpu_desatualizada": proposta.cpu_desatualizada,
        }

    async def detectar_divergencias(self, proposta_id: UUID) -> list[dict]:
        divergencias = []
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta or not proposta.bcu_cabecalho_id:
            return divergencias

        # Mao de obra
        r_mo = await self.db.execute(
            select(PropostaPcMaoObra.id, PropostaPcMaoObra.valor_bcu_snapshot, BcuMaoObraItem.custo_unitario_h)
            .join(BcuMaoObraItem, PropostaPcMaoObra.bcu_item_id == BcuMaoObraItem.id)
            .where(PropostaPcMaoObra.proposta_id == proposta_id)
        )
        for p_id, snapshot, atual in r_mo:
            if snapshot != atual:
                divergencias.append({
                    "tabela": "mao-obra",
                    "item_id": str(p_id),
                    "campo": "custo_unitario_h",
                    "valor_snapshot": float(snapshot) if snapshot is not None else None,
                    "valor_atual_bcu": float(atual) if atual is not None else None,
                    "valor_proposta": None
                })

        # Equipamento
        r_eqp = await self.db.execute(
            select(PropostaPcEquipamento.id, PropostaPcEquipamento.valor_bcu_snapshot, BcuEquipamentoItem.aluguel_r_h)
            .join(BcuEquipamentoItem, PropostaPcEquipamento.bcu_item_id == BcuEquipamentoItem.id)
            .where(PropostaPcEquipamento.proposta_id == proposta_id)
        )
        for p_id, snapshot, atual in r_eqp:
            if snapshot != atual:
                divergencias.append({
                    "tabela": "equipamento",
                    "item_id": str(p_id),
                    "campo": "aluguel_r_h",
                    "valor_snapshot": float(snapshot) if snapshot is not None else None,
                    "valor_atual_bcu": float(atual) if atual is not None else None,
                    "valor_proposta": None
                })
                
        # EPI
        r_epi = await self.db.execute(
            select(PropostaPcEpi.id, PropostaPcEpi.valor_bcu_snapshot, BcuEpiItem.custo_unitario)
            .join(BcuEpiItem, PropostaPcEpi.bcu_item_id == BcuEpiItem.id)
            .where(PropostaPcEpi.proposta_id == proposta_id)
        )
        for p_id, snapshot, atual in r_epi:
            if snapshot != atual:
                divergencias.append({
                    "tabela": "epi",
                    "item_id": str(p_id),
                    "campo": "custo_unitario",
                    "valor_snapshot": float(snapshot) if snapshot is not None else None,
                    "valor_atual_bcu": float(atual) if atual is not None else None,
                    "valor_proposta": None
                })
                
        # Ferramenta
        r_fer = await self.db.execute(
            select(PropostaPcFerramenta.id, PropostaPcFerramenta.valor_bcu_snapshot, BcuFerramentaItem.preco)
            .join(BcuFerramentaItem, PropostaPcFerramenta.bcu_item_id == BcuFerramentaItem.id)
            .where(PropostaPcFerramenta.proposta_id == proposta_id)
        )
        for p_id, snapshot, atual in r_fer:
            if snapshot != atual:
                divergencias.append({
                    "tabela": "ferramenta",
                    "item_id": str(p_id),
                    "campo": "preco",
                    "valor_snapshot": float(snapshot) if snapshot is not None else None,
                    "valor_atual_bcu": float(atual) if atual is not None else None,
                    "valor_proposta": None
                })
                
        # Encargo
        r_enc = await self.db.execute(
            select(PropostaPcEncargo.id, PropostaPcEncargo.valor_bcu_snapshot, BcuEncargoItem.taxa_percent)
            .join(BcuEncargoItem, PropostaPcEncargo.bcu_item_id == BcuEncargoItem.id)
            .where(PropostaPcEncargo.proposta_id == proposta_id)
        )
        for p_id, snapshot, atual in r_enc:
            if snapshot != atual:
                divergencias.append({
                    "tabela": "encargo",
                    "item_id": str(p_id),
                    "campo": "taxa_percent",
                    "valor_snapshot": float(snapshot) if snapshot is not None else None,
                    "valor_atual_bcu": float(atual) if atual is not None else None,
                    "valor_proposta": None
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

        for k, v in payload.items():
            if hasattr(item, k):
                setattr(item, k, v)
        
        item.editado_manualmente = True
        
        proposta = await self.proposta_repo.get_by_id(item.proposta_id)
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
        proposta.cpu_desatualizada = True
        
        self.db.add(item_pc)
        self.db.add(proposta)
        await self.db.flush()
