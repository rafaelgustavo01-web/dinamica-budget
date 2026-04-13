from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usuario import Usuario, UsuarioPerfil
from app.repositories.base_repository import BaseRepository


class UsuarioRepository(BaseRepository[Usuario]):
    model = Usuario

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def get_by_email(self, email: str) -> Usuario | None:
        result = await self.db.execute(
            select(Usuario).where(Usuario.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, id: UUID) -> Usuario | None:  # type: ignore[override]
        result = await self.db.execute(select(Usuario).where(Usuario.id == id))
        return result.scalar_one_or_none()

    async def update_refresh_token(self, user_id: UUID, token_hash: str | None) -> None:
        user = await self.get_by_id(user_id)
        if user:
            user.refresh_token_hash = token_hash
            await self.db.flush()

    async def update_nome(self, user_id: UUID, nome: str) -> Usuario | None:
        user = await self.get_by_id(user_id)
        if user:
            user.nome = nome
            await self.db.flush()
        return user

    async def update_hashed_password(self, user_id: UUID, hashed_password: str) -> None:
        user = await self.get_by_id(user_id)
        if user:
            user.hashed_password = hashed_password
            await self.db.flush()

    async def list_paginated(
        self,
        offset: int,
        limit: int,
        is_active: bool | None = None,
    ) -> tuple[list[Usuario], int]:
        filters = []
        if is_active is not None:
            filters.append(Usuario.is_active == is_active)

        count_result = await self.db.execute(
            select(func.count()).select_from(Usuario).where(*filters)
        )
        total = count_result.scalar_one()

        items_result = await self.db.execute(
            select(Usuario).where(*filters).order_by(Usuario.nome).offset(offset).limit(limit)
        )
        return list(items_result.scalars().all()), total

    async def get_perfis(self, usuario_id: UUID) -> list[UsuarioPerfil]:
        result = await self.db.execute(
            select(UsuarioPerfil).where(UsuarioPerfil.usuario_id == usuario_id)
        )
        return list(result.scalars().all())

    async def set_perfis_cliente(
        self,
        usuario_id: UUID,
        cliente_id: UUID,
        perfis: list[str],
    ) -> list[UsuarioPerfil]:
        """
        Replace all perfis for a user on a specific client.
        Deletes existing entries for (usuario_id, cliente_id) and inserts the new ones.
        """
        # Remove existing
        existing = await self.db.execute(
            select(UsuarioPerfil).where(
                UsuarioPerfil.usuario_id == usuario_id,
                UsuarioPerfil.cliente_id == cliente_id,
            )
        )
        for row in existing.scalars().all():
            await self.db.delete(row)
        await self.db.flush()

        # Insert new
        new_perfis = []
        for perfil in perfis:
            up = UsuarioPerfil(
                usuario_id=usuario_id,
                cliente_id=cliente_id,
                perfil=perfil.upper(),
            )
            self.db.add(up)
            new_perfis.append(up)

        await self.db.flush()
        return new_perfis
