"""Service for managing proposal items (add, remove, update)."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundError, ValidationError
from backend.core.logging import get_logger
from backend.models.enums import StatusProposta
from backend.models.proposta import PropostaItem
from backend.repositories.proposta_item_repository import PropostaItemRepository
from backend.repositories.proposta_repository import PropostaRepository

logger = get_logger(__name__)


class PropostaItemService:
    """
    Orquestra operações de CRUD em items de propostas.
    
    Regras:
    - Items podem ser adicionados em status RASCUNHO ou CPU_GERADA
    - Items só podem ser removidos se a proposta estiver em RASCUNHO
    - Remover item remove suas composições automaticamente
    - Após add/remove, proposta marcada como cpu_desatualizada = True
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.proposta_repo = PropostaRepository(db)
        self.item_repo = PropostaItemRepository(db)

    async def adicionar_item(
        self,
        proposta_id: UUID,
        codigo: str,
        descricao: str,
        unidade_medida: str,
        quantidade: Decimal,
    ) -> dict:
        """
        Adiciona um novo item à proposta.
        
        Args:
            proposta_id: ID da proposta
            codigo: Código do item (ex: "01", "01.1")
            descricao: Descrição do item
            unidade_medida: Unidade (m, m², m³, un, etc)
            quantidade: Quantidade do item
        
        Returns:
            {"id": "uuid", "codigo": "01", "descricao": "...", "proposta_id": "..."}
        
        Validações:
            - Proposta deve existir
            - Proposta não pode estar APROVADA/ARQUIVADA
            - Código deve ser único por proposta
            - Quantidade > 0
        """
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta:
            raise NotFoundError("Proposta", str(proposta_id))

        # Validar status
        if proposta.status not in {
            StatusProposta.RASCUNHO,
            StatusProposta.CPU_GERADA,
        }:
            raise ValidationError(
                f"Não é possível adicionar items em status {proposta.status.value}. "
                "Estados permitidos: RASCUNHO, CPU_GERADA"
            )

        # Validar quantidade
        if quantidade <= 0:
            raise ValidationError("Quantidade deve ser maior que zero")

        # Verificar código único
        items_existentes = await self.item_repo.list_by_proposta(proposta_id)
        if any(i.codigo == codigo for i in items_existentes):
            raise ValidationError(f"Código {codigo} já existe nesta proposta")

        # Encontrar próxima ordem
        max_ordem = max((i.ordem for i in items_existentes), default=0)
        
        # Criar novo item
        novo_item = PropostaItem(
            proposta_id=proposta_id,
            codigo=codigo,
            descricao=descricao,
            unidade_medida=unidade_medida,
            quantidade=quantidade,
            ordem=max_ordem + 1,
        )
        
        self.db.add(novo_item)
        await self.db.flush()

        # Marcar proposta como desatualizada
        proposta.cpu_desatualizada = True
        self.db.add(proposta)
        
        logger.info(
            "item_added",
            proposta_id=str(proposta_id),
            item_id=str(novo_item.id),
            codigo=codigo,
        )

        return {
            "id": str(novo_item.id),
            "proposta_id": str(proposta_id),
            "codigo": novo_item.codigo,
            "descricao": novo_item.descricao,
            "unidade_medida": novo_item.unidade_medida,
            "quantidade": float(novo_item.quantidade),
            "ordem": novo_item.ordem,
            "custo_direto_unitario": None,
            "preco_total": None,
        }

    async def remover_item(self, proposta_id: UUID, item_id: UUID) -> None:
        """
        Remove um item da proposta.
        
        Validações:
            - Proposta deve existir
            - Item deve existir e pertencer à proposta
            - Proposta deve estar em RASCUNHO (mais restritivo)
            - Remove composições automaticamente (cascade)
        
        Throws:
            NotFoundError: Se proposta ou item não existem
            ValidationError: Se status não permite remoção
        """
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta:
            raise NotFoundError("Proposta", str(proposta_id))

        item = await self.item_repo.get_by_id(item_id)
        if not item or item.proposta_id != proposta_id:
            raise NotFoundError("PropostaItem", str(item_id))

        # Validação: só em RASCUNHO
        if proposta.status != StatusProposta.RASCUNHO:
            raise ValidationError(
                f"Items só podem ser removidos em status RASCUNHO. "
                f"Status atual: {proposta.status.value}"
            )

        # Remover item (cascade remove composições)
        await self.item_repo.delete(item_id)

        # Marcar proposta como desatualizada
        proposta.cpu_desatualizada = True
        self.db.add(proposta)

        logger.info(
            "item_removed",
            proposta_id=str(proposta_id),
            item_id=str(item_id),
            codigo=item.codigo,
        )

    async def atualizar_item(
        self,
        proposta_id: UUID,
        item_id: UUID,
        **kwargs
    ) -> dict:
        """
        Atualiza dados de um item.
        
        Campos atualizáveis:
            - descricao
            - quantidade
            - unidade_medida
        
        Campos NÃO atualizáveis:
            - codigo (identificador imutável)
            - custos (recalculados pelo rebuild)
        """
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta:
            raise NotFoundError("Proposta", str(proposta_id))

        item = await self.item_repo.get_by_id(item_id)
        if not item or item.proposta_id != proposta_id:
            raise NotFoundError("PropostaItem", str(item_id))

        if proposta.status != StatusProposta.RASCUNHO:
            raise ValidationError(
                f"Items só podem ser editados em status RASCUNHO. "
                f"Status atual: {proposta.status.value}"
            )

        # Whitelist de campos atualizáveis
        allowed_fields = {"descricao", "quantidade", "unidade_medida"}
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}

        # Validar quantidade se sendo atualizada
        if "quantidade" in update_data and update_data["quantidade"] <= 0:
            raise ValidationError("Quantidade deve ser maior que zero")

        # Aplicar atualizações
        for key, value in update_data.items():
            setattr(item, key, value)

        self.db.add(item)
        proposta.cpu_desatualizada = True
        self.db.add(proposta)

        await self.db.flush()

        logger.info(
            "item_updated",
            proposta_id=str(proposta_id),
            item_id=str(item_id),
            fields=list(update_data.keys()),
        )

        return {
            "id": str(item.id),
            "proposta_id": str(proposta_id),
            "codigo": item.codigo,
            "descricao": item.descricao,
            "unidade_medida": item.unidade_medida,
            "quantidade": float(item.quantidade),
            "ordem": item.ordem,
            "custo_direto_unitario": float(item.custo_direto_unitario or 0),
            "preco_total": float(item.preco_total or 0),
        }

    async def listar_items(self, proposta_id: UUID) -> list[dict]:
        """Lista todos os items de uma proposta, ordenados."""
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta:
            raise NotFoundError("Proposta", str(proposta_id))

        items = await self.item_repo.list_by_proposta(proposta_id)
        
        return [
            {
                "id": str(item.id),
                "proposta_id": str(proposta_id),
                "codigo": item.codigo,
                "descricao": item.descricao,
                "unidade_medida": item.unidade_medida,
                "quantidade": float(item.quantidade),
                "ordem": item.ordem,
                "custo_direto_unitario": float(item.custo_direto_unitario or 0) if item.custo_direto_unitario else None,
                "custo_indireto_unitario": float(item.custo_indireto_unitario or 0) if item.custo_indireto_unitario else None,
                "preco_unitario": float(item.preco_unitario or 0) if item.preco_unitario else None,
                "preco_total": float(item.preco_total or 0) if item.preco_total else None,
                "composicoes_count": len(item.composicoes) if item.composicoes else 0,
            }
            for item in items
        ]

    async def reordenar_items(self, proposta_id: UUID, items_ids: list[UUID]) -> dict:
        """
        Reordena items da proposta.
        
        Args:
            proposta_id: ID da proposta
            items_ids: Lista de IDs em nova ordem
        
        Returns:
            {"items_reordenados": count}
        """
        proposta = await self.proposta_repo.get_by_id(proposta_id)
        if not proposta:
            raise NotFoundError("Proposta", str(proposta_id))

        if proposta.status != StatusProposta.RASCUNHO:
            raise ValidationError(
                f"Reordenação permitida apenas em RASCUNHO. "
                f"Status atual: {proposta.status.value}"
            )

        items = await self.item_repo.list_by_proposta(proposta_id)
        items_map = {item.id: item for item in items}

        # Validar que todos os IDs pertencem à proposta
        if not all(item_id in items_map for item_id in items_ids):
            raise ValidationError("Um ou mais IDs não pertencem a esta proposta")

        # Atualizar ordem
        for ordem, item_id in enumerate(items_ids, start=1):
            items_map[item_id].ordem = ordem
            self.db.add(items_map[item_id])

        proposta.cpu_desatualizada = True
        self.db.add(proposta)

        await self.db.flush()

        logger.info(
            "items_reordered",
            proposta_id=str(proposta_id),
            count=len(items_ids),
        )

        return {
            "proposta_id": str(proposta_id),
            "items_reordenados": len(items_ids),
        }
