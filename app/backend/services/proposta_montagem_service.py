"""Service for rebuilding/consolidating a proposal after histogram edits and extra resources."""

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


class PropostaMontagemService:
    """Consolidates proposal values after CPU generation, histogram edits, and extra resources."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.proposta_repo = PropostaRepository(db)
        self.item_repo = PropostaItemRepository(db)
        self.comp_repo = PropostaItemComposicaoRepository(db)
        self.resumo_repo = PropostaResumoRecursoRepository(db)
        self.recurso_repo = PropostaRecursoExtraRepository(db)

    async def rebuild(self, proposta_id: UUID) -> dict:
        """
        Rebuild proposal totals and resource summary.

        Flow:
          1. Load proposal + items + compositions
          2. Load extra resources + allocations
          3. Recalculate item costs (including allocated extras)
          4. Recalculate proposal totals (direct + indirect + grand)
          5. Update resource summary (compositions + extras by type)
          6. Mark cpu_desatualizada = False
        """
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta:
            raise NotFoundError("Proposta", str(proposta_id))

        if proposta.status not in {
            StatusProposta.RASCUNHO,
            StatusProposta.CPU_GERADA,
            StatusProposta.EM_ANALISE,
        }:
            raise ValidationError(
                "Proposta não pode ser remontada neste status. "
                f"Status atual: {proposta.status.value}"
            )

        items = await self.item_repo.list_by_proposta(proposta_id)
        if not items:
            raise ValidationError(
                "Proposta não possui itens. Gere a CPU primeiro."
            )

        # Load all compositions for this proposal
        comps_map = await self.comp_repo.list_by_proposta_items_batch(proposta_id)

        # Load extra resources with allocations
        recursos_extras = await self.recurso_repo.list_by_proposta(proposta_id)
        extras_cost_by_comp: dict[UUID, Decimal] = {}
        extras_cost_total: Decimal = Decimal("0")
        extras_by_tipo: dict[str, Decimal] = {}

        for recurso in recursos_extras:
            for aloc in recurso.alocacoes:
                comp_id = aloc.composicao_id
                cost = (recurso.custo_unitario or Decimal("0")) * (aloc.quantidade_consumo or Decimal("0"))
                extras_cost_by_comp[comp_id] = extras_cost_by_comp.get(comp_id, Decimal("0")) + cost
                extras_cost_total += cost
                tipo = recurso.tipo_recurso or "OUTROS"
                extras_by_tipo[tipo] = extras_by_tipo.get(tipo, Decimal("0")) + cost

        # Recalculate each item
        total_direto = Decimal("0")
        total_indireto = Decimal("0")

        # Determine BDI fraction from first item that has it, or zero
        bdi_frac = Decimal("0")
        for item in items:
            if item.percentual_indireto is not None:
                bdi_frac = item.percentual_indireto
                break

        resumo_map: dict[str, Decimal] = {}

        for item in items:
            comps = comps_map.get(item.id, [])
            item_direto = Decimal("0")

            for comp in comps:
                # Base composition cost
                comp_cost = comp.custo_total_insumo or Decimal("0")
                # Add extra resources allocated to this composition
                extra_cost = extras_cost_by_comp.get(comp.id, Decimal("0"))
                comp_total = comp_cost + extra_cost
                item_direto += comp_total

                # Aggregate for resource summary
                tipo = comp.tipo_recurso.value if comp.tipo_recurso else "OUTROS"
                # Multiply by parent item quantity for total project cost
                item_qtd = item.quantidade or Decimal("1")
                resumo_map[tipo] = resumo_map.get(tipo, Decimal("0")) + (comp_total * item_qtd)

            # Apply BDI
            item_indireto = item_direto * bdi_frac
            item_preco_unitario = item_direto + item_indireto
            item_preco_total = item_preco_unitario * (item.quantidade or Decimal("1"))

            # Update item
            item.custo_direto_unitario = item_direto
            item.custo_indireto_unitario = item_indireto
            item.preco_unitario = item_preco_unitario
            item.preco_total = item_preco_total
            self.db.add(item)

            total_direto += item_direto * (item.quantidade or Decimal("1"))
            total_indireto += item_indireto * (item.quantidade or Decimal("1"))

        # Add extra resources that aren't allocated to any composition
        # (standalone extras — count towards OUTROS)
        unallocated_extras = Decimal("0")
        for recurso in recursos_extras:
            if not recurso.alocacoes:
                cost = recurso.custo_unitario or Decimal("0")
                unallocated_extras += cost
                tipo = recurso.tipo_recurso or "OUTROS"
                extras_by_tipo[tipo] = extras_by_tipo.get(tipo, Decimal("0")) + cost

        total_direto += unallocated_extras
        total_indireto += unallocated_extras * bdi_frac

        # Merge extras into resumo_map
        for tipo, cost in extras_by_tipo.items():
            resumo_map[tipo] = resumo_map.get(tipo, Decimal("0")) + cost

        # Update proposal totals
        proposta.total_direto = total_direto
        proposta.total_indireto = total_indireto
        proposta.total_geral = total_direto + total_indireto
        proposta.cpu_desatualizada = False
        self.db.add(proposta)

        # Update resource summary
        await self.resumo_repo.delete_by_proposta(proposta_id)
        resumos: list[PropostaResumoRecurso] = []
        for tipo, tipo_direto in resumo_map.items():
            tipo_indireto = tipo_direto * bdi_frac
            resumos.append(
                PropostaResumoRecurso(
                    proposta_id=proposta_id,
                    tipo_recurso=tipo,
                    total_direto=tipo_direto,
                    total_indireto=tipo_indireto,
                    total_geral=tipo_direto + tipo_indireto,
                )
            )
        if resumos:
            await self.resumo_repo.create_batch(resumos)

        await self.db.flush()

        logger.info(
            "proposta_rebuilt",
            proposta_id=str(proposta_id),
            total_direto=float(total_direto),
            total_indireto=float(total_indireto),
            total_geral=float(proposta.total_geral),
            itens=len(items),
        )

        return {
            "proposta_id": str(proposta_id),
            "total_direto": float(total_direto),
            "total_indireto": float(total_indireto),
            "total_geral": float(proposta.total_geral),
            "bdi_percentual": float(bdi_frac * Decimal("100")),
            "itens_processados": len(items),
            "cpu_desatualizada": False,
        }
