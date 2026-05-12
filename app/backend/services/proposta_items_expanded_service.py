"""
Service para gerenciar items de propostas com suporte a múltiplos tipos
(genéricos, EPI, Mão de Obra, Equipamentos, Ferramentas)
"""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.proposta import Proposta, PropostaItem
from backend.models.proposta_pc import PropostaPcEpi, PropostaPcMaoObra, PropostaPcEquipamento, PropostaPcFerramenta
from backend.models.bcu import BcuEpiItem, BcuMaoObraItem, BcuEquipamentoItem, BcuFerramentaItem
from backend.repositories.proposta_repository import PropostaRepository
from backend.repositories.proposta_item_repository import PropostaItemRepository


class PropostaItemsExpandedService:
    """Serviço expandido de items com suporte a múltiplos tipos."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.proposta_repo = PropostaRepository(db)
        self.item_repo = PropostaItemRepository(db)

    async def listar_tipos_disponiveis(self, proposta_id: UUID) -> dict:
        """Retorna tipos de items que podem ser adicionados."""
        return {
            "tipos": [
                {
                    "id": "generico",
                    "label": "Item Genérico",
                    "descricao": "Descreva manualmente o item",
                    "campos": ["codigo", "descricao", "quantidade", "unidade_medida"],
                },
                {
                    "id": "mao_obra",
                    "label": "Mão de Obra",
                    "descricao": "Selecione da base de custos",
                    "campos": ["bcu_item_id", "quantidade"],
                },
                {
                    "id": "epi",
                    "label": "EPI (Equipamento de Proteção)",
                    "descricao": "Selecione equipamento de proteção",
                    "campos": ["bcu_item_id", "quantidade"],
                },
                {
                    "id": "equipamento",
                    "label": "Equipamento",
                    "descricao": "Selecione equipamento",
                    "campos": ["bcu_item_id", "quantidade"],
                },
                {
                    "id": "ferramenta",
                    "label": "Ferramenta",
                    "descricao": "Selecione ferramenta",
                    "campos": ["bcu_item_id", "quantidade"],
                },
            ]
        }

    async def listar_bcu_mao_obra(self) -> list[dict]:
        """Lista mão de obra disponível na base BCU."""
        stmt = select(BcuMaoObraItem).limit(100)
        result = await self.db.execute(stmt)
        items = result.scalars().all()
        return [
            {
                "id": str(item.id),
                "codigo": item.codigo_origem,
                "descricao": item.descricao_funcao,
                "valor": float(item.salario_base or 0),
            }
            for item in items
        ]

    async def listar_bcu_epi(self) -> list[dict]:
        """Lista EPI disponível na base BCU."""
        stmt = select(BcuEpiItem).limit(100)
        result = await self.db.execute(stmt)
        items = result.scalars().all()
        return [
            {
                "id": str(item.id),
                "codigo": item.codigo_origem,
                "descricao": item.descricao,
                "valor": float(item.valor or 0),
            }
            for item in items
        ]

    async def listar_bcu_equipamento(self) -> list[dict]:
        """Lista equipamentos disponíveis na base BCU."""
        stmt = select(BcuEquipamentoItem).limit(100)
        result = await self.db.execute(stmt)
        items = result.scalars().all()
        return [
            {
                "id": str(item.id),
                "codigo": item.codigo_origem,
                "descricao": item.descricao,
                "valor": float(item.custo_diario or 0),
            }
            for item in items
        ]

    async def listar_bcu_ferramenta(self) -> list[dict]:
        """Lista ferramentas disponíveis na base BCU."""
        stmt = select(BcuFerramentaItem).limit(100)
        result = await self.db.execute(stmt)
        items = result.scalars().all()
        return [
            {
                "id": str(item.id),
                "codigo": item.codigo_origem,
                "descricao": item.descricao,
                "valor": float(item.valor or 0),
            }
            for item in items
        ]

    async def adicionar_item_generico(
        self,
        proposta_id: UUID,
        codigo: str,
        descricao: str,
        unidade_medida: str,
        quantidade: float,
    ) -> dict:
        """Adiciona item genérico à proposta."""
        return await self.item_repo.adicionar_item(
            proposta_id=proposta_id,
            codigo=codigo,
            descricao=descricao,
            unidade_medida=unidade_medida,
            quantidade=quantidade,
        )

    async def adicionar_mao_obra(
        self,
        proposta_id: UUID,
        bcu_item_id: UUID,
        quantidade: float,
    ) -> dict:
        """Adiciona mão de obra da base BCU."""
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta:
            raise ValueError("Proposta não encontrada")

        # Buscar item da base BCU
        stmt = select(BcuMaoObraItem).where(BcuMaoObraItem.id == bcu_item_id)
        result = await self.db.execute(stmt)
        bcu_item = result.scalar_one_or_none()
        if not bcu_item:
            raise ValueError("Item de mão de obra não encontrado na base")

        # Criar item PropostaPc
        pc_item = PropostaPcMaoObra(
            proposta_id=proposta_id,
            bcu_item_id=bcu_item_id,
            descricao_funcao=bcu_item.descricao_funcao,
            codigo_origem=bcu_item.codigo_origem,
            quantidade=quantidade,
            salario=bcu_item.salario_base,
            encargos_percent=bcu_item.encargos_percent,
        )
        self.db.add(pc_item)
        await self.db.flush()

        return {
            "id": str(pc_item.id),
            "tipo": "mao_obra",
            "descricao": pc_item.descricao_funcao,
            "quantidade": float(pc_item.quantidade or 0),
            "valor_unitario": float(pc_item.salario or 0),
        }

    async def adicionar_epi(
        self,
        proposta_id: UUID,
        bcu_item_id: UUID,
        quantidade: float,
    ) -> dict:
        """Adiciona EPI da base BCU."""
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta:
            raise ValueError("Proposta não encontrada")

        # Buscar item da base BCU
        stmt = select(BcuEpiItem).where(BcuEpiItem.id == bcu_item_id)
        result = await self.db.execute(stmt)
        bcu_item = result.scalar_one_or_none()
        if not bcu_item:
            raise ValueError("EPI não encontrado na base")

        # Criar item PropostaPc
        pc_item = PropostaPcEpi(
            proposta_id=proposta_id,
            bcu_item_id=bcu_item_id,
            descricao=bcu_item.descricao,
            codigo_origem=bcu_item.codigo_origem,
            quantidade=quantidade,
            valor_unitario=bcu_item.valor,
        )
        self.db.add(pc_item)
        await self.db.flush()

        return {
            "id": str(pc_item.id),
            "tipo": "epi",
            "descricao": pc_item.descricao,
            "quantidade": float(pc_item.quantidade or 0),
            "valor_unitario": float(pc_item.valor_unitario or 0),
        }

    async def adicionar_equipamento(
        self,
        proposta_id: UUID,
        bcu_item_id: UUID,
        quantidade: float,
    ) -> dict:
        """Adiciona equipamento da base BCU."""
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta:
            raise ValueError("Proposta não encontrada")

        # Buscar item da base BCU
        stmt = select(BcuEquipamentoItem).where(BcuEquipamentoItem.id == bcu_item_id)
        result = await self.db.execute(stmt)
        bcu_item = result.scalar_one_or_none()
        if not bcu_item:
            raise ValueError("Equipamento não encontrado na base")

        # Criar item PropostaPc
        pc_item = PropostaPcEquipamento(
            proposta_id=proposta_id,
            bcu_item_id=bcu_item_id,
            descricao=bcu_item.descricao,
            codigo_origem=bcu_item.codigo_origem,
            quantidade=quantidade,
            custo_diario=bcu_item.custo_diario,
        )
        self.db.add(pc_item)
        await self.db.flush()

        return {
            "id": str(pc_item.id),
            "tipo": "equipamento",
            "descricao": pc_item.descricao,
            "quantidade": float(pc_item.quantidade or 0),
            "valor_unitario": float(pc_item.custo_diario or 0),
        }

    async def adicionar_ferramenta(
        self,
        proposta_id: UUID,
        bcu_item_id: UUID,
        quantidade: float,
    ) -> dict:
        """Adiciona ferramenta da base BCU."""
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta:
            raise ValueError("Proposta não encontrada")

        # Buscar item da base BCU
        stmt = select(BcuFerramentaItem).where(BcuFerramentaItem.id == bcu_item_id)
        result = await self.db.execute(stmt)
        bcu_item = result.scalar_one_or_none()
        if not bcu_item:
            raise ValueError("Ferramenta não encontrada na base")

        # Criar item PropostaPc
        pc_item = PropostaPcFerramenta(
            proposta_id=proposta_id,
            bcu_item_id=bcu_item_id,
            descricao=bcu_item.descricao,
            codigo_origem=bcu_item.codigo_origem,
            quantidade=quantidade,
            valor_unitario=bcu_item.valor,
        )
        self.db.add(pc_item)
        await self.db.flush()

        return {
            "id": str(pc_item.id),
            "tipo": "ferramenta",
            "descricao": pc_item.descricao,
            "quantidade": float(pc_item.quantidade or 0),
            "valor_unitario": float(pc_item.valor_unitario or 0),
        }
