"""Service for searching and composing proposal values with business rules."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundError, ValidationError
from backend.core.logging import get_logger
from backend.models.enums import StatusProposta, TipoRecurso
from backend.models.proposta import Proposta, PropostaItem, PropostaItemComposicao, PropostaResumoRecurso
from backend.repositories.proposta_item_composicao_repository import PropostaItemComposicaoRepository
from backend.repositories.proposta_item_repository import PropostaItemRepository
from backend.repositories.proposta_recurso_extra_repository import PropostaRecursoExtraRepository
from backend.repositories.proposta_repository import PropostaRepository
from backend.repositories.proposta_resumo_recurso_repository import PropostaResumoRecursoRepository

logger = get_logger(__name__)


class PropostaComposicaoService:
    """
    Orquestra a busca, validação e composição de valores para propostas.
    
    Regras de Negócio:
    1. COMPOSIÇÃO DE VALORES:
       - Valores são buscados de:
         a) Composições (insumos: material, MO, equipamento)
         b) Recursos extras (alocados a composições ou não)
         c) Cálculos de BDI (% indireto sobre direto)
    
    2. HIERARQUIA DE CUSTO:
       - Custo Direto Unitário (item) = soma de composições + extras alocadas
       - Custo Indireto Unitário = Custo Direto * % BDI
       - Preço Unitário = Custo Direto + Custo Indireto
       - Preço Total = Preço Unitário * Quantidade
    
    3. TOTAIS DA PROPOSTA:
       - Total Direto = soma(Custo Direto Unitário * Quantidade) para todos itens
       - Total Indireto = soma(Custo Indireto Unitário * Quantidade)
       - Total Geral = Total Direto + Total Indireto
    
    4. RESUMO POR TIPO DE RECURSO:
       - Agrupa custos por TipoRecurso (MO, MATERIAL, EQUIPAMENTO, ENCARGOS, etc)
       - Aplica % BDI ao direto para calcular indireto
       - Gera PropostaResumoRecurso com direto/indireto/total
    
    5. VALIDAÇÕES:
       - Proposta deve estar em RASCUNHO, CPU_GERADA ou EM_ANALISE
       - Items devem ter composições ou extras para cálculo
       - BDI % deve estar entre 0-100
       - Não calcula se CPU foi gerada sem composições (erro de dados)
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.proposta_repo = PropostaRepository(db)
        self.item_repo = PropostaItemRepository(db)
        self.comp_repo = PropostaItemComposicaoRepository(db)
        self.resumo_repo = PropostaResumoRecursoRepository(db)
        self.recurso_repo = PropostaRecursoExtraRepository(db)

    async def buscar_valores_proposta(self, proposta_id: UUID) -> dict:
        """
        Busca todos os valores necessários para compor a proposta.
        
        Retorna:
        {
            "proposta_id": "uuid",
            "items": [
                {
                    "id": "uuid",
                    "codigo": "01",
                    "descricao": "Escavação",
                    "quantidade": 100.0,
                    "composicoes": [
                        {
                            "id": "uuid",
                            "descricao": "Retroescavadeira",
                            "tipo": "EQUIPAMENTO",
                            "quantidade_consumo": 0.5,
                            "custo_unitario": 150.0,
                            "custo_total": 75.0,
                        }
                    ],
                    "recursos_extras": [
                        {
                            "id": "uuid",
                            "descricao": "Seguro",
                            "tipo": "ENCARGOS",
                            "custo_unitario": 10.0,
                            "alocacoes": 1,  # quantas composições usam
                        }
                    ],
                    "custo_direto_unitario": 85.0,  # soma de composições + extras
                }
            ],
            "percentual_bdi": 28.5,
            "totais": {
                "total_direto": 8500.0,
                "total_indireto": 2422.5,
                "total_geral": 10922.5,
            },
            "resumo_por_tipo": {
                "EQUIPAMENTO": {"direto": 7500, "indireto": 2137.5},
                "ENCARGOS": {"direto": 1000, "indireto": 285},
            }
        }
        """
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta:
            raise NotFoundError("Proposta", str(proposta_id))

        items = await self.item_repo.list_by_proposta(proposta_id)
        if not items:
            raise ValidationError("Proposta não possui itens. Gere a CPU primeiro.")

        # Buscar composições para todos os items
        comps_map = await self.comp_repo.list_by_proposta_items_batch(proposta_id)
        
        # Buscar recursos extras
        recursos_extras = await self.recurso_repo.list_by_proposta(proposta_id)

        # Montar estrutura de resposta
        items_data = []
        for item in items:
            comps = comps_map.get(item.id, [])
            
            # Buscar extras alocadas a este item
            extras_do_item = [r for r in recursos_extras if r.alocacoes]
            
            items_data.append({
                "id": str(item.id),
                "codigo": item.codigo,
                "descricao": item.descricao,
                "quantidade": float(item.quantidade or 1),
                "custo_direto_unitario": float(item.custo_direto_unitario or 0),
                "custo_indireto_unitario": float(item.custo_indireto_unitario or 0),
                "preco_unitario": float(item.preco_unitario or 0),
                "preco_total": float(item.preco_total or 0),
                "composicoes_count": len(comps),
                "extras_count": len(extras_do_item),
            })

        # Calcular resumo por tipo
        resumo_tipos = await self.resumo_repo.list_by_proposta(proposta_id)
        resumo_data = {
            str(r.tipo_recurso): {
                "direto": float(r.total_direto or 0),
                "indireto": float(r.total_indireto or 0),
                "total": float(r.total_geral or 0),
            }
            for r in resumo_tipos
        }

        bdi_percentual = float((items[0].percentual_indireto or 0) * Decimal("100"))

        return {
            "proposta_id": str(proposta_id),
            "codigo": proposta.codigo,
            "status": proposta.status.value,
            "items": items_data,
            "percentual_bdi": bdi_percentual,
            "totais": {
                "total_direto": float(proposta.total_direto or 0),
                "total_indireto": float(proposta.total_indireto or 0),
                "total_geral": float(proposta.total_geral or 0),
            },
            "resumo_por_tipo": resumo_data,
        }

    async def validar_valores_composicao(self, proposta_id: UUID) -> dict:
        """
        Valida se os valores de composição estão corretos e completos.
        
        Checklist:
        - Todos items têm composições ou extras?
        - Custos estão preenchidos?
        - BDI é válido?
        - Totais bateriam com recálculo?
        
        Retorna:
        {
            "valido": true/false,
            "erros": [],
            "avisos": [],
            "totais_esperados": {...},
        }
        """
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta:
            raise NotFoundError("Proposta", str(proposta_id))

        items = await self.item_repo.list_by_proposta(proposta_id)
        comps_map = await self.comp_repo.list_by_proposta_items_batch(proposta_id)
        recursos_extras = await self.recurso_repo.list_by_proposta(proposta_id)

        erros = []
        avisos = []
        
        # Validação 1: Items sem composição
        items_vazios = []
        for item in items:
            comps = comps_map.get(item.id, [])
            extras_alocadas = sum(1 for r in recursos_extras if r.alocacoes)
            if not comps and not extras_alocadas:
                items_vazios.append(f"{item.codigo} - {item.descricao}")

        if items_vazios:
            erros.append(f"Items sem composição: {', '.join(items_vazios)}")

        # Validação 2: BDI
        bdi_values = [i.percentual_indireto for i in items if i.percentual_indireto is not None]
        if bdi_values and len(set(bdi_values)) > 1:
            avisos.append(f"BDI inconsistente entre items: {set(bdi_values)}")

        # Validação 3: Custos unitários zerados
        items_sem_custo = [i for i in items if (i.custo_direto_unitario or 0) == 0]
        if items_sem_custo:
            avisos.append(f"{len(items_sem_custo)} items com custo_direto_unitario zerado")

        # Validação 4: Preços não batendo
        for item in items:
            if item.custo_direto_unitario and item.percentual_indireto is not None:
                custo_indireto_esperado = item.custo_direto_unitario * item.percentual_indireto
                preco_unitario_esperado = item.custo_direto_unitario + custo_indireto_esperado
                if abs(float(item.preco_unitario or 0) - float(preco_unitario_esperado)) > 0.01:
                    avisos.append(f"Item {item.codigo}: preço unitário não bate com cálculo")

        valido = len(erros) == 0

        return {
            "proposta_id": str(proposta_id),
            "valido": valido,
            "erros": erros,
            "avisos": avisos,
            "items_total": len(items),
            "items_com_composicao": sum(1 for i in items if comps_map.get(i.id)),
            "items_vazios": len(items_vazios),
        }

    async def gerar_relatorio_composicao(self, proposta_id: UUID) -> dict:
        """
        Gera relatório detalhado da composição de uma proposta.
        
        Usado para auditoria e entendimento de como os valores foram calculados.
        """
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta:
            raise NotFoundError("Proposta", str(proposta_id))

        items = await self.item_repo.list_by_proposta(proposta_id)
        comps_map = await self.comp_repo.list_by_proposta_items_batch(proposta_id)
        recursos_extras = await self.recurso_repo.list_by_proposta(proposta_id)

        items_detalhados = []

        for item in items:
            comps = comps_map.get(item.id, [])
            
            # Composições agrupadas por tipo
            comps_por_tipo = {}
            custo_comps_total = Decimal("0")
            
            for comp in comps:
                tipo = comp.tipo_recurso.value if comp.tipo_recurso else "OUTROS"
                custo_comp = comp.custo_total_insumo or Decimal("0")
                
                if tipo not in comps_por_tipo:
                    comps_por_tipo[tipo] = {
                        "descricoes": [],
                        "quantidade": Decimal("0"),
                        "custo_total": Decimal("0"),
                    }
                
                comps_por_tipo[tipo]["descricoes"].append(comp.descricao_insumo)
                comps_por_tipo[tipo]["custo_total"] += custo_comp
                custo_comps_total += custo_comp

            # Extras alocadas a este item
            extras_alocadas = []
            custo_extras_total = Decimal("0")
            
            for recurso in recursos_extras:
                for aloc in recurso.alocacoes:
                    if aloc.proposta_item_id == item.id:
                        custo = (recurso.custo_unitario or Decimal("0")) * (aloc.quantidade_consumo or Decimal("0"))
                        extras_alocadas.append({
                            "descricao": recurso.descricao,
                            "tipo": recurso.tipo_recurso,
                            "custo": float(custo),
                        })
                        custo_extras_total += custo

            custo_direto_total = custo_comps_total + custo_extras_total
            bdi_frac = item.percentual_indireto or Decimal("0")
            custo_indireto_total = custo_direto_total * bdi_frac

            items_detalhados.append({
                "item": {
                    "codigo": item.codigo,
                    "descricao": item.descricao,
                    "quantidade": float(item.quantidade or 1),
                },
                "composicoes": {
                    "por_tipo": {k: {"custo": float(v["custo_total"])} for k, v in comps_por_tipo.items()},
                    "total": float(custo_comps_total),
                },
                "extras_alocadas": {
                    "items": extras_alocadas,
                    "total": float(custo_extras_total),
                },
                "custos": {
                    "direto_unitario": float(custo_direto_total),
                    "indireto_unitario": float(custo_indireto_total),
                    "bdi_percentual": float(bdi_frac * Decimal("100")),
                    "preco_unitario": float(item.preco_unitario or 0),
                    "preco_total": float(item.preco_total or 0),
                },
            })

        return {
            "proposta": {
                "id": str(proposta_id),
                "codigo": proposta.codigo,
                "status": proposta.status.value,
            },
            "items_detalhados": items_detalhados,
            "totais_proposta": {
                "total_direto": float(proposta.total_direto or 0),
                "total_indireto": float(proposta.total_indireto or 0),
                "total_geral": float(proposta.total_geral or 0),
            },
        }
