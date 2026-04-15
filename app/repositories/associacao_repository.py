import re
import unicodedata
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.associacao_inteligente import AssociacaoInteligente, CONSOLIDACAO_THRESHOLD
from app.models.enums import OrigemAssociacao, StatusValidacaoAssociacao
from app.repositories.base_repository import BaseRepository


_STOP_WORDS_PT = {
    "de", "do", "da", "dos", "das", "e", "em", "com", "para", "por",
    "a", "o", "as", "os", "um", "uma", "no", "na", "nos", "nas",
    "ao", "aos", "à", "às", "se", "que", "ou", "mas", "mais",
}


def normalize_text(text: str) -> str:
    """
    Full normalization pipeline:
      1. Strip + lowercase
      2. Remove diacritics/accents (NFD + strip Mn)
      3. Remove punctuation (non-alphanumeric chars → space)
      4. Remove Portuguese stop words
      5. Dedup tokens + sort (canonical form for embedding/search)
    """
    text = text.strip().lower()
    nfkd = unicodedata.normalize("NFD", text)
    text = "".join(c for c in nfkd if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = [t for t in text.split() if t not in _STOP_WORDS_PT]
    tokens = sorted(set(tokens))
    return " ".join(tokens)


class AssociacaoRepository(BaseRepository[AssociacaoInteligente]):
    model = AssociacaoInteligente

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def find_by_cliente_and_text(
        self,
        cliente_id: UUID,
        texto_normalizado: str,
    ) -> AssociacaoInteligente | None:
        """
        Exact normalized-text lookup for Phase 1 (Associação Direta).
        Returns the best (highest frequencia_uso) match for this client+text.
        """
        result = await self.db.execute(
            select(AssociacaoInteligente)
            .where(
                AssociacaoInteligente.cliente_id == cliente_id,
                AssociacaoInteligente.texto_busca_normalizado == texto_normalizado,
            )
            .order_by(AssociacaoInteligente.frequencia_uso.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def fortalecer(self, associacao: AssociacaoInteligente) -> AssociacaoInteligente:
        """
        Increment frequencia_uso and elevate status_validacao.
        Calls the domain method on the model to keep business logic in one place.
        """
        associacao.fortalecer()
        await self.db.flush()
        await self.db.refresh(associacao)
        return associacao

    async def upsert_associacao(
        self,
        cliente_id: UUID,
        texto_busca_original: str,
        servico_tcpo_id: UUID,
        origem: OrigemAssociacao,
        confiabilidade_score: Decimal | None = None,
    ) -> AssociacaoInteligente:
        """
        Upsert: find existing association and strengthen it, or create a new one.
        Used by busca_service.criar_associacao after user selects a result.
        """
        texto_norm = normalize_text(texto_busca_original)
        existing = await self.find_by_cliente_and_text(cliente_id, texto_norm)

        if existing and existing.servico_tcpo_id == servico_tcpo_id:
            return await self.fortalecer(existing)

        # New association
        nova = AssociacaoInteligente(
            cliente_id=cliente_id,
            texto_busca_normalizado=texto_norm,
            servico_tcpo_id=servico_tcpo_id,
            origem_associacao=origem,
            confiabilidade_score=confiabilidade_score,
            frequencia_uso=1,
            status_validacao=StatusValidacaoAssociacao.VALIDADA,  # user explicitly selected
        )
        self.db.add(nova)
        await self.db.flush()
        await self.db.refresh(nova)
        return nova

    async def list_by_cliente(
        self,
        cliente_id: UUID,
        offset: int,
        limit: int,
    ) -> tuple[list[AssociacaoInteligente], int]:
        base_filter = [AssociacaoInteligente.cliente_id == cliente_id]

        count_result = await self.db.execute(
            select(func.count()).select_from(AssociacaoInteligente).where(*base_filter)
        )
        total = count_result.scalar_one()

        items_result = await self.db.execute(
            select(AssociacaoInteligente)
            .where(*base_filter)
            .order_by(AssociacaoInteligente.frequencia_uso.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(items_result.scalars().all()), total
