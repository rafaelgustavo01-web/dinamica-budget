"""API endpoints for PC Tabelas (Planilha de Custos)."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_active_user, get_current_admin_user, get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.models.pc_tabelas import (
    PcCabecalho,
    PcEncargoItem,
    PcEquipamentoItem,
    PcEquipamentoPremissa,
    PcEpiItem,
    PcFerramentaItem,
    PcMaoObraItem,
    PcMobilizacaoItem,
)
from app.schemas.pc_tabelas import (
    PcCabecalhoOut,
    PcEncargoItemOut,
    PcEquipamentosOut,
    PcEquipamentoItemOut,
    PcEquipamentoPremissaOut,
    PcEpiItemOut,
    PcFerramentaItemOut,
    PcMaoObraItemOut,
    PcMobilizacaoItemOut,
)
from app.services.pc_tabelas_service import importar_pc_tabelas

router = APIRouter(prefix="/pc-tabelas", tags=["pc-tabelas"])


# ── Helper ───────────────────────────────────────────────────────────────────

async def _get_cabecalho(db: AsyncSession, cabecalho_id: UUID) -> PcCabecalho:
    result = await db.execute(select(PcCabecalho).where(PcCabecalho.id == cabecalho_id))
    cab = result.scalar_one_or_none()
    if not cab:
        raise NotFoundError("PC Tabela não encontrada.")
    return cab


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/cabecalhos", response_model=list[PcCabecalhoOut])
async def listar_cabecalhos(
    _=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[PcCabecalhoOut]:
    result = await db.execute(select(PcCabecalho).order_by(PcCabecalho.criado_em.desc()))
    return [PcCabecalhoOut.model_validate(c) for c in result.scalars().all()]


@router.get("/{cabecalho_id}/mao-obra", response_model=list[PcMaoObraItemOut])
async def listar_mao_obra(
    cabecalho_id: UUID,
    _=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[PcMaoObraItemOut]:
    await _get_cabecalho(db, cabecalho_id)
    result = await db.execute(
        select(PcMaoObraItem)
        .where(PcMaoObraItem.pc_cabecalho_id == cabecalho_id)
        .order_by(PcMaoObraItem.descricao_funcao)
    )
    return [PcMaoObraItemOut.model_validate(r) for r in result.scalars().all()]


@router.get("/{cabecalho_id}/equipamentos", response_model=PcEquipamentosOut)
async def listar_equipamentos(
    cabecalho_id: UUID,
    _=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PcEquipamentosOut:
    await _get_cabecalho(db, cabecalho_id)
    res_p = await db.execute(
        select(PcEquipamentoPremissa).where(PcEquipamentoPremissa.pc_cabecalho_id == cabecalho_id).limit(1)
    )
    premissa = res_p.scalar_one_or_none()
    res_i = await db.execute(
        select(PcEquipamentoItem)
        .where(PcEquipamentoItem.pc_cabecalho_id == cabecalho_id)
        .order_by(PcEquipamentoItem.equipamento)
    )
    items = res_i.scalars().all()
    return PcEquipamentosOut(
        premissa=PcEquipamentoPremissaOut.model_validate(premissa) if premissa else None,
        items=[PcEquipamentoItemOut.model_validate(i) for i in items],
    )


@router.get("/{cabecalho_id}/encargos", response_model=list[PcEncargoItemOut])
async def listar_encargos(
    cabecalho_id: UUID,
    tipo: str | None = None,
    _=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[PcEncargoItemOut]:
    await _get_cabecalho(db, cabecalho_id)
    q = select(PcEncargoItem).where(PcEncargoItem.pc_cabecalho_id == cabecalho_id)
    if tipo:
        q = q.where(PcEncargoItem.tipo_encargo == tipo.upper())
    result = await db.execute(q)
    return [PcEncargoItemOut.model_validate(r) for r in result.scalars().all()]


@router.get("/{cabecalho_id}/epi", response_model=list[PcEpiItemOut])
async def listar_epi(
    cabecalho_id: UUID,
    _=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[PcEpiItemOut]:
    await _get_cabecalho(db, cabecalho_id)
    result = await db.execute(
        select(PcEpiItem)
        .where(PcEpiItem.pc_cabecalho_id == cabecalho_id)
        .order_by(PcEpiItem.epi)
    )
    return [PcEpiItemOut.model_validate(r) for r in result.scalars().all()]


@router.get("/{cabecalho_id}/ferramentas", response_model=list[PcFerramentaItemOut])
async def listar_ferramentas(
    cabecalho_id: UUID,
    _=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[PcFerramentaItemOut]:
    await _get_cabecalho(db, cabecalho_id)
    result = await db.execute(
        select(PcFerramentaItem)
        .where(PcFerramentaItem.pc_cabecalho_id == cabecalho_id)
        .order_by(PcFerramentaItem.descricao)
    )
    return [PcFerramentaItemOut.model_validate(r) for r in result.scalars().all()]


@router.get("/{cabecalho_id}/mobilizacao", response_model=list[PcMobilizacaoItemOut])
async def listar_mobilizacao(
    cabecalho_id: UUID,
    _=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[PcMobilizacaoItemOut]:
    await _get_cabecalho(db, cabecalho_id)
    result = await db.execute(
        select(PcMobilizacaoItem)
        .where(PcMobilizacaoItem.pc_cabecalho_id == cabecalho_id)
        .options(selectinload(PcMobilizacaoItem.quantidades_funcao))
    )
    return [PcMobilizacaoItemOut.model_validate(r) for r in result.scalars().all()]


@router.post("/importar", response_model=PcCabecalhoOut)
async def importar_planilha(
    file: UploadFile = File(...),
    _=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> PcCabecalhoOut:
    if not file.filename:
        raise ValidationError("Arquivo inválido.")
    if not file.filename.lower().endswith(".xlsx"):
        raise ValidationError("Somente arquivos .xlsx são suportados.")

    payload = await file.read()
    if not payload:
        raise ValidationError("Arquivo vazio.")

    cab = await importar_pc_tabelas(db=db, file_bytes=payload, nome_arquivo=file.filename)
    return PcCabecalhoOut.model_validate(cab)
