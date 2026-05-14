from __future__ import annotations

import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.import_profile import ImportCorrectionType, ImportProfile, ImportProfileCorrection


class ImportProfileRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_cliente_id(self, cliente_id: UUID) -> ImportProfile | None:
        result = await self._db.execute(
            select(ImportProfile).where(ImportProfile.cliente_id == cliente_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, profile_id: UUID) -> ImportProfile | None:
        result = await self._db.execute(
            select(ImportProfile).where(ImportProfile.id == profile_id)
        )
        return result.scalar_one_or_none()

    async def create(self, cliente_id: UUID) -> ImportProfile:
        profile = ImportProfile(id=uuid.uuid4(), cliente_id=cliente_id)
        self._db.add(profile)
        await self._db.flush()
        return profile

    async def save_corrections(
        self,
        profile_id: UUID,
        job_id: UUID,
        corrections: list[dict],
    ) -> list[ImportProfileCorrection]:
        saved = []
        for c in corrections:
            corr = ImportProfileCorrection(
                id=uuid.uuid4(),
                profile_id=profile_id,
                job_id=job_id,
                tipo=ImportCorrectionType(c["tipo"]),
                detalhe=c.get("detalhe"),
                aplicada=False,
            )
            self._db.add(corr)
            saved.append(corr)
        await self._db.flush()
        return saved
