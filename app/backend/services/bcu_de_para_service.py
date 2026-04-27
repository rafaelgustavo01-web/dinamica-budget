"""Service for BCU De/Para explicit mapping between base_tcpo and bcu.*"""

import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundError, UnprocessableEntityError
from backend.models.base_tcpo import BaseTcpo
from backend.models.bcu import (
    BcuCabecalho,
    BcuEquipamentoItem,
    BcuEpiItem,
    BcuFerramentaItem,
    BcuMaoObraItem,
    BcuTableType,
    DeParaTcpoBcu,
)
from backend.repositories.bcu_de_para_repository import BcuDeParaRepository


TIPO_COERENCIA = {
    "MO": ["MO"],
    "EQUIPAMENTO": ["EQP"],
    "INSUMO": ["EPI", "FER"],
    "FERRAMENTA": ["FER"],
}


class BcuDeParaService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = BcuDeParaRepository(db)

    async def listar(
        self, search: str | None = None, only_unmapped: bool = False
    ) -> list[dict]:
        """
        Retorna todas as entradas com join em base_tcpo.
        Se only_unmapped=True, retorna BaseTcpo sem mapeamento.
        """
        if only_unmapped:
            subq = select(DeParaTcpoBcu.base_tcpo_id).subquery()
            q = select(BaseTcpo).where(BaseTcpo.id.notin_(select(subq.c.base_tcpo_id)))
            if search:
                q = q.where(BaseTcpo.descricao.ilike(f"%{search}%"))
            result = await self.db.execute(q.order_by(BaseTcpo.descricao))
            return [
                {
                    "id": None,
                    "base_tcpo_id": row.id,
                    "base_tcpo_codigo": row.codigo_origem,
                    "base_tcpo_descricao": row.descricao,
                    "base_tcpo_tipo_recurso": (row.tipo_recurso.value if hasattr(row.tipo_recurso, "value") else row.tipo_recurso) if row.tipo_recurso else None,
                    "bcu_table_type": None,
                    "bcu_item_id": None,
                    "bcu_item_descricao": None,
                }
                for row in result.scalars().all()
            ]

        q = (
            select(
                DeParaTcpoBcu.id,
                DeParaTcpoBcu.base_tcpo_id,
                BaseTcpo.codigo_origem,
                BaseTcpo.descricao,
                BaseTcpo.tipo_recurso,
                DeParaTcpoBcu.bcu_table_type,
                DeParaTcpoBcu.bcu_item_id,
            )
            .join(BaseTcpo, DeParaTcpoBcu.base_tcpo_id == BaseTcpo.id)
        )
        if search:
            q = q.where(BaseTcpo.descricao.ilike(f"%{search}%"))
        q = q.order_by(BaseTcpo.descricao)
        result = await self.db.execute(q)
        rows = result.all()

        # Resolve bcu_item_descricao dinamicamente
        out: list[dict] = []
        for row in rows:
            bcu_desc = await self._resolve_bcu_descricao(row.bcu_table_type, row.bcu_item_id)
            out.append({
                "id": row.id,
                "base_tcpo_id": row.base_tcpo_id,
                "base_tcpo_codigo": row.codigo_origem,
                "base_tcpo_descricao": row.descricao,
                "base_tcpo_tipo_recurso": row.tipo_recurso.value if row.tipo_recurso else None,
                "bcu_table_type": row.bcu_table_type.value,
                "bcu_item_id": row.bcu_item_id,
                "bcu_item_descricao": bcu_desc,
            })
        return out

    async def _resolve_bcu_descricao(self, table_type: BcuTableType, item_id: UUID) -> str | None:
        if table_type == BcuTableType.MO:
            r = await self.db.execute(select(BcuMaoObraItem.descricao_funcao).where(BcuMaoObraItem.id == item_id))
        elif table_type == BcuTableType.EQP:
            r = await self.db.execute(select(BcuEquipamentoItem.equipamento).where(BcuEquipamentoItem.id == item_id))
        elif table_type == BcuTableType.EPI:
            r = await self.db.execute(select(BcuEpiItem.epi).where(BcuEpiItem.id == item_id))
        elif table_type == BcuTableType.FER:
            r = await self.db.execute(select(BcuFerramentaItem.descricao).where(BcuFerramentaItem.id == item_id))
        else:
            return None
        return r.scalar_one_or_none()

    async def criar(
        self, base_tcpo_id: UUID, bcu_table_type: BcuTableType, bcu_item_id: UUID, criador_id: UUID
    ) -> DeParaTcpoBcu:
        # 1. base_tcpo existe
        bt = await self.db.get(BaseTcpo, base_tcpo_id)
        if not bt:
            raise NotFoundError("BaseTcpo", str(base_tcpo_id))

        # 2. bcu_item_id existe na tabela correspondente
        await self._validar_bcu_item_existe(bcu_table_type, bcu_item_id)

        # 3. Tipo coerente
        tr = bt.tipo_recurso.value if hasattr(bt.tipo_recurso, "value") else bt.tipo_recurso
        self._validar_tipo_coerente(tr if bt.tipo_recurso else None, bcu_table_type)

        # 4. UniqueConstraint
        existing = await self.repo.get_by_base_tcpo_id(base_tcpo_id)
        if existing:
            raise UnprocessableEntityError(
                f"BaseTcpo {base_tcpo_id} ja possui mapeamento. Use PATCH para atualizar."
            )

        de_para = DeParaTcpoBcu(
            id=uuid.uuid4(),
            base_tcpo_id=base_tcpo_id,
            bcu_table_type=bcu_table_type,
            bcu_item_id=bcu_item_id,
            criado_por_id=criador_id,
        )
        return await self.repo.create(de_para)

    async def atualizar(
        self, de_para_id: UUID, bcu_table_type: BcuTableType, bcu_item_id: UUID
    ) -> DeParaTcpoBcu:
        de_para = await self.repo.get_by_id(de_para_id)
        if not de_para:
            raise NotFoundError("DePara", str(de_para_id))

        bt = await self.db.get(BaseTcpo, de_para.base_tcpo_id)
        await self._validar_bcu_item_existe(bcu_table_type, bcu_item_id)
        tr = bt.tipo_recurso.value if hasattr(bt.tipo_recurso, "value") else bt.tipo_recurso
        self._validar_tipo_coerente(tr if bt.tipo_recurso else None, bcu_table_type)

        de_para.bcu_table_type = bcu_table_type
        de_para.bcu_item_id = bcu_item_id
        self.db.add(de_para)
        await self.db.flush()
        await self.db.refresh(de_para)
        return de_para

    async def deletar(self, de_para_id: UUID) -> None:
        de_para = await self.repo.get_by_id(de_para_id)
        if not de_para:
            raise NotFoundError("DePara", str(de_para_id))
        await self.repo.delete(de_para)

    async def lookup_bcu_para_base_tcpo(self, base_tcpo_id: UUID) -> tuple[BcuTableType, UUID] | None:
        de_para = await self.repo.get_by_base_tcpo_id(base_tcpo_id)
        if de_para:
            return (de_para.bcu_table_type, de_para.bcu_item_id)
        return None

    async def _validar_bcu_item_existe(self, table_type: BcuTableType, item_id: UUID) -> None:
        if table_type == BcuTableType.MO:
            r = await self.db.execute(select(BcuMaoObraItem.id).where(BcuMaoObraItem.id == item_id))
        elif table_type == BcuTableType.EQP:
            r = await self.db.execute(select(BcuEquipamentoItem.id).where(BcuEquipamentoItem.id == item_id))
        elif table_type == BcuTableType.EPI:
            r = await self.db.execute(select(BcuEpiItem.id).where(BcuEpiItem.id == item_id))
        elif table_type == BcuTableType.FER:
            r = await self.db.execute(select(BcuFerramentaItem.id).where(BcuFerramentaItem.id == item_id))
        elif table_type == BcuTableType.MOB:
            r = await self.db.execute(select(BcuCabecalho.id).where(BcuCabecalho.id == item_id))
        else:
            raise UnprocessableEntityError(f"Tipo BCU invalido: {table_type}")

        if r.scalar_one_or_none() is None:
            raise NotFoundError(f"Item BCU ({table_type.value})", str(item_id))

    def _validar_tipo_coerente(self, tcpo_tipo: str | None, bcu_table_type: BcuTableType) -> None:
        if tcpo_tipo is None:
            raise UnprocessableEntityError("BaseTcpo sem tipo_recurso nao pode ser mapeado.")
        validos = TIPO_COERENCIA.get(tcpo_tipo, [])
        if bcu_table_type.value not in validos:
            raise UnprocessableEntityError(
                f"Tipo incoerente: TCPO {tcpo_tipo} nao pode mapear para BCU {bcu_table_type.value}"
            )
