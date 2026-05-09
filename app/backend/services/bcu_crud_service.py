"""CRUD seguro para itens BCU individuais."""

from __future__ import annotations

import uuid
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundError, UnprocessableEntityError
from backend.core.logging import get_logger
from backend.models.base_tcpo import BaseTcpo
from backend.models.bcu import (
    BcuCabecalho,
    BcuEncargoItem,
    BcuEquipamentoItem,
    BcuEpiItem,
    BcuFerramentaItem,
    BcuMaoObraItem,
    BcuMobilizacaoItem,
)

logger = get_logger(__name__)

_ITEM_MAP = {
    "mo": (BcuMaoObraItem, "descricao_funcao", "MO"),
    "equipamentos": (BcuEquipamentoItem, "equipamento", "EQUIPAMENTO"),
    "encargos": (BcuEncargoItem, "discriminacao_encargo", None),
    "epi": (BcuEpiItem, "epi", "INSUMO"),
    "ferramentas": (BcuFerramentaItem, "descricao", "FERRAMENTA"),
    "mobilizacao": (BcuMobilizacaoItem, "descricao", None),
}


def _tipo_to_prefix(tipo: str) -> str:
    return {"mo": "MO", "equipamentos": "EQP", "epi": "EPI", "ferramentas": "FER"}.get(tipo, tipo.upper()[:3])


class BcuCrudService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _assert_cabecalho(self, cabecalho_id: UUID) -> BcuCabecalho:
        cab = await self.db.get(BcuCabecalho, cabecalho_id)
        if not cab:
            raise NotFoundError("BCU cabecalho", str(cabecalho_id))
        return cab

    async def _get_next_seq(self, tipo: str, cabecalho_id: UUID) -> int:
        from sqlalchemy import func, select
        model = _ITEM_MAP[tipo][0]
        result = await self.db.execute(
            select(func.count(model.id)).where(model.cabecalho_id == cabecalho_id)
        )
        return (result.scalar() or 0) + 1

    async def criar(self, tipo: str, cabecalho_id: UUID, data: dict, criador_id: UUID | None = None) -> Any:
        tipo = tipo.lower()
        if tipo not in _ITEM_MAP:
            raise UnprocessableEntityError(f"Tipo BCU inválido: {tipo}")
        await self._assert_cabecalho(cabecalho_id)

        model, desc_field, base_tcpo_tipo = _ITEM_MAP[tipo]
        item = model(cabecalho_id=cabecalho_id, **data)

        # Auto-generate codigo_origem for types that support it
        if hasattr(item, "codigo_origem"):
            seq = await self._get_next_seq(tipo, cabecalho_id)
            item.codigo_origem = f"BCU-{_tipo_to_prefix(tipo)}-{seq:03d}"

        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)

        # Sync base_tcpo for types that map to it
        if base_tcpo_tipo and hasattr(item, "codigo_origem"):
            desc = getattr(item, desc_field)
            unidade = getattr(item, "unidade", None) or getattr(item, "unidade_medida", None) or "UN"
            custo = getattr(item, "custo_unitario_h", None) or getattr(item, "aluguel_r_h", None) or getattr(item, "custo_unitario", None) or getattr(item, "preco", None) or 0
            bt = BaseTcpo(
                id=uuid.uuid4(),
                codigo_origem=item.codigo_origem,
                descricao=desc,
                unidade_medida=unidade,
                custo_base=float(custo or 0),
                tipo_recurso=base_tcpo_tipo,
            )
            self.db.add(bt)
            await self.db.flush()

        logger.info("bcu.crud.criar", tipo=tipo, cabecalho_id=str(cabecalho_id), item_id=str(item.id))
        return item

    async def atualizar(self, tipo: str, cabecalho_id: UUID, item_id: UUID, data: dict) -> Any:
        tipo = tipo.lower()
        if tipo not in _ITEM_MAP:
            raise UnprocessableEntityError(f"Tipo BCU inválido: {tipo}")
        await self._assert_cabecalho(cabecalho_id)

        model = _ITEM_MAP[tipo][0]
        item = await self.db.get(model, item_id)
        if not item or item.cabecalho_id != cabecalho_id:
            raise NotFoundError(f"Item BCU ({tipo})", str(item_id))

        for key, value in data.items():
            if value is not None or key in ("codigo", "grupo", "codigo_grupo", "funcao", "tipo_mao_obra"):
                setattr(item, key, value)

        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)

        # Update base_tcpo if applicable
        desc_field = _ITEM_MAP[tipo][1]
        base_tcpo_tipo = _ITEM_MAP[tipo][2]
        if base_tcpo_tipo and hasattr(item, "codigo_origem") and item.codigo_origem:
            from sqlalchemy import select, update
            bt = await self.db.execute(
                select(BaseTcpo).where(BaseTcpo.codigo_origem == item.codigo_origem)
            )
            bt = bt.scalar_one_or_none()
            if bt:
                desc = getattr(item, desc_field)
                unidade = getattr(item, "unidade", None) or getattr(item, "unidade_medida", None) or "UN"
                custo = getattr(item, "custo_unitario_h", None) or getattr(item, "aluguel_r_h", None) or getattr(item, "custo_unitario", None) or getattr(item, "preco", None) or 0
                await self.db.execute(
                    update(BaseTcpo)
                    .where(BaseTcpo.codigo_origem == item.codigo_origem)
                    .values(
                        descricao=desc,
                        unidade_medida=unidade,
                        custo_base=float(custo or 0),
                    )
                )

        logger.info("bcu.crud.atualizar", tipo=tipo, item_id=str(item_id))
        return item

    async def deletar(self, tipo: str, cabecalho_id: UUID, item_id: UUID) -> None:
        tipo = tipo.lower()
        if tipo not in _ITEM_MAP:
            raise UnprocessableEntityError(f"Tipo BCU inválido: {tipo}")
        await self._assert_cabecalho(cabecalho_id)

        model = _ITEM_MAP[tipo][0]
        item = await self.db.get(model, item_id)
        if not item or item.cabecalho_id != cabecalho_id:
            raise NotFoundError(f"Item BCU ({tipo})", str(item_id))

        # If item has codigo_origem, remove from base_tcpo as well
        if hasattr(item, "codigo_origem") and item.codigo_origem:
            from sqlalchemy import delete
            await self.db.execute(
                delete(BaseTcpo).where(BaseTcpo.codigo_origem == item.codigo_origem)
            )

        await self.db.delete(item)
        await self.db.flush()
        logger.info("bcu.crud.deletar", tipo=tipo, item_id=str(item_id))
