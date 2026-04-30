"""API endpoints for BCU (Base de Custos Unitarios)."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.dependencies import get_current_active_user, get_current_admin_user, get_db
from backend.core.exceptions import NotFoundError, ValidationError
from backend.core.logging import get_logger

logger = get_logger(__name__)
from backend.models.bcu import (
    BcuCabecalho,
    BcuEncargoItem,
    BcuEquipamentoItem,
    BcuEquipamentoPremissa,
    BcuEpiItem,
    BcuFerramentaItem,
    BcuMaoObraItem,
    BcuMobilizacaoItem,
    BcuTableType,
    DeParaTcpoBcu,
)
from backend.schemas.bcu import (
    BcuCabecalhoOut,
    BcuEncargoItemOut,
    BcuEquipamentosOut,
    BcuEquipamentoItemOut,
    BcuEquipamentoPremissaOut,
    BcuEpiItemOut,
    BcuFerramentaItemOut,
    BcuMaoObraItemOut,
    BcuMobilizacaoItemOut,
    DeParaCreate,
    DeParaOut,
    DeParaListItemOut,
)
from backend.services.bcu_service import BcuService
from backend.services.bcu_de_para_service import BcuDeParaService

router = APIRouter(prefix="/bcu", tags=["bcu"])


async def _get_cabecalho(db: AsyncSession, cabecalho_id: UUID) -> BcuCabecalho:
    result = await db.execute(select(BcuCabecalho).where(BcuCabecalho.id == cabecalho_id))
    cab = result.scalar_one_or_none()
    if not cab:
        raise NotFoundError("BCU cabecalho", str(cabecalho_id))
    return cab


# ── Static routes BEFORE /{cabecalho_id}/ to avoid UUID capture ───────────────

@router.get("/cabecalhos", response_model=list[BcuCabecalhoOut])
async def listar_cabecalhos(
    _=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[BcuCabecalhoOut]:
    result = await db.execute(select(BcuCabecalho).order_by(BcuCabecalho.criado_em.desc()))
    return [BcuCabecalhoOut.model_validate(c) for c in result.scalars().all()]


@router.get("/cabecalho-ativo", response_model=BcuCabecalhoOut | None)
async def get_cabecalho_ativo(
    _=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> BcuCabecalhoOut | None:
    result = await db.execute(
        select(BcuCabecalho).where(BcuCabecalho.is_ativo == True).limit(1)
    )
    cab = result.scalar_one_or_none()
    return BcuCabecalhoOut.model_validate(cab) if cab else None


@router.post("/importar", response_model=BcuCabecalhoOut)
async def importar_bcu(
    file: UploadFile = File(...),
    current_user=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BcuCabecalhoOut:
    if not file.filename:
        raise ValidationError("Arquivo invalido.")
    if not file.filename.lower().endswith(".xlsx"):
        raise ValidationError("Somente arquivos .xlsx sao suportados.")

    payload = await file.read()
    if not payload:
        raise ValidationError("Arquivo vazio.")

    svc = BcuService(db)
    try:
        cab = await svc.importar_bcu(payload, file.filename, current_user.id)
    except (IndexError, KeyError, AttributeError) as exc:
        # Parser falhou ao acessar coluna/aba esperada — arquivo provavelmente nao e a planilha BCU oficial.
        raise ValidationError(
            "Estrutura da planilha invalida. Verifique se o arquivo e a 'BCU tabelas.xlsx' oficial "
            f"(detalhe tecnico: {exc.__class__.__name__}: {exc})"
        ) from exc
    return BcuCabecalhoOut.model_validate(cab)


@router.post("/importar-converter", response_model=BcuCabecalhoOut)
async def importar_converter(
    file: UploadFile = File(...),
    current_user=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BcuCabecalhoOut:
    """
    Importa 'Converter em Data Center.xlsx' (6 abas) → bcu.* + sync referencia.base_tcpo.

    Aceita: Mão de Obra, Equipamentos, Encargos, EPI/Uniforme, Ferramentas, Exames.
    Avisos sobre abas ausentes ou EXAMES (sem tabela alvo) são salvos em cabecalho.observacao.
    """
    if not file.filename:
        raise ValidationError("Arquivo invalido.")
    if not file.filename.lower().endswith(".xlsx"):
        raise ValidationError("Somente arquivos .xlsx sao suportados.")

    payload = await file.read()
    if not payload:
        raise ValidationError("Arquivo vazio.")

    svc = BcuService(db)
    try:
        cab = await svc.importar_converter(payload, file.filename, current_user.id)
    except (IndexError, KeyError, AttributeError, ValueError) as exc:
        raise ValidationError(
            "Estrutura da planilha invalida para o formato Converter (6 abas). "
            f"Detalhe: {exc.__class__.__name__}: {exc}"
        ) from exc
    except Exception as exc:
        logger.error(
            "bcu.importar_converter.unexpected_error",
            arquivo=file.filename,
            error=str(exc),
            exc_info=True,
        )
        raise ValidationError(
            f"Erro inesperado ao importar BCU: {exc.__class__.__name__}: {exc}"
        ) from exc
    return BcuCabecalhoOut.model_validate(cab)


# ── De/Para — must be before /{cabecalho_id}/ ─────────────────────────────────

@router.get("/de-para", response_model=list[DeParaListItemOut])
async def listar_de_para(
    only_unmapped: bool = False,
    search: str | None = None,
    _=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> list[DeParaListItemOut]:
    svc = BcuDeParaService(db)
    items = await svc.listar(search=search, only_unmapped=only_unmapped)
    return [DeParaListItemOut.model_validate(i) for i in items]


@router.post("/de-para", response_model=DeParaOut, status_code=201)
async def criar_de_para(
    body: DeParaCreate,
    current_user=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> DeParaOut:
    svc = BcuDeParaService(db)
    de_para = await svc.criar(
        base_tcpo_id=body.base_tcpo_id,
        bcu_table_type=BcuTableType(body.bcu_table_type),
        bcu_item_id=body.bcu_item_id,
        criador_id=current_user.id,
    )
    return DeParaOut.model_validate(de_para)


@router.patch("/de-para/{de_para_id}", response_model=DeParaOut)
async def atualizar_de_para(
    de_para_id: UUID,
    body: DeParaCreate,
    _=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> DeParaOut:
    svc = BcuDeParaService(db)
    de_para = await svc.atualizar(
        de_para_id=de_para_id,
        bcu_table_type=BcuTableType(body.bcu_table_type),
        bcu_item_id=body.bcu_item_id,
    )
    return DeParaOut.model_validate(de_para)


@router.delete("/de-para/{de_para_id}", status_code=204)
async def deletar_de_para(
    de_para_id: UUID,
    _=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    svc = BcuDeParaService(db)
    await svc.deletar(de_para_id)


# ── Parameterized /{cabecalho_id}/ routes ─────────────────────────────────────

@router.post("/cabecalhos/{cabecalho_id}/ativar", response_model=BcuCabecalhoOut)
async def ativar_cabecalho(
    cabecalho_id: UUID,
    _=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BcuCabecalhoOut:
    svc = BcuService(db)
    cab = await svc.ativar_cabecalho(cabecalho_id)
    return BcuCabecalhoOut.model_validate(cab)


@router.get("/{cabecalho_id}/mao-obra", response_model=list[BcuMaoObraItemOut])
async def listar_mao_obra(
    cabecalho_id: UUID,
    _=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[BcuMaoObraItemOut]:
    await _get_cabecalho(db, cabecalho_id)
    result = await db.execute(
        select(BcuMaoObraItem)
        .where(BcuMaoObraItem.cabecalho_id == cabecalho_id)
        .order_by(BcuMaoObraItem.descricao_funcao)
    )
    return [BcuMaoObraItemOut.model_validate(r) for r in result.scalars().all()]


@router.get("/{cabecalho_id}/equipamentos", response_model=BcuEquipamentosOut)
async def listar_equipamentos(
    cabecalho_id: UUID,
    _=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> BcuEquipamentosOut:
    await _get_cabecalho(db, cabecalho_id)
    res_p = await db.execute(
        select(BcuEquipamentoPremissa).where(BcuEquipamentoPremissa.cabecalho_id == cabecalho_id).limit(1)
    )
    premissa = res_p.scalar_one_or_none()
    res_i = await db.execute(
        select(BcuEquipamentoItem)
        .where(BcuEquipamentoItem.cabecalho_id == cabecalho_id)
        .order_by(BcuEquipamentoItem.equipamento)
    )
    items = res_i.scalars().all()
    return BcuEquipamentosOut(
        premissa=BcuEquipamentoPremissaOut.model_validate(premissa) if premissa else None,
        items=[BcuEquipamentoItemOut.model_validate(i) for i in items],
    )


@router.get("/{cabecalho_id}/encargos", response_model=list[BcuEncargoItemOut])
async def listar_encargos(
    cabecalho_id: UUID,
    tipo: str | None = None,
    _=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[BcuEncargoItemOut]:
    await _get_cabecalho(db, cabecalho_id)
    q = select(BcuEncargoItem).where(BcuEncargoItem.cabecalho_id == cabecalho_id)
    if tipo:
        q = q.where(BcuEncargoItem.tipo_encargo == tipo.upper())
    result = await db.execute(q)
    return [BcuEncargoItemOut.model_validate(r) for r in result.scalars().all()]


@router.get("/{cabecalho_id}/epi", response_model=list[BcuEpiItemOut])
async def listar_epi(
    cabecalho_id: UUID,
    _=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[BcuEpiItemOut]:
    await _get_cabecalho(db, cabecalho_id)
    result = await db.execute(
        select(BcuEpiItem)
        .where(BcuEpiItem.cabecalho_id == cabecalho_id)
        .order_by(BcuEpiItem.epi)
    )
    return [BcuEpiItemOut.model_validate(r) for r in result.scalars().all()]


@router.get("/{cabecalho_id}/ferramentas", response_model=list[BcuFerramentaItemOut])
async def listar_ferramentas(
    cabecalho_id: UUID,
    _=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[BcuFerramentaItemOut]:
    await _get_cabecalho(db, cabecalho_id)
    result = await db.execute(
        select(BcuFerramentaItem)
        .where(BcuFerramentaItem.cabecalho_id == cabecalho_id)
        .order_by(BcuFerramentaItem.descricao)
    )
    return [BcuFerramentaItemOut.model_validate(r) for r in result.scalars().all()]


@router.get("/{cabecalho_id}/mobilizacao", response_model=list[BcuMobilizacaoItemOut])
async def listar_mobilizacao(
    cabecalho_id: UUID,
    _=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[BcuMobilizacaoItemOut]:
    await _get_cabecalho(db, cabecalho_id)
    result = await db.execute(
        select(BcuMobilizacaoItem)
        .where(BcuMobilizacaoItem.cabecalho_id == cabecalho_id)
        .options(selectinload(BcuMobilizacaoItem.quantidades_funcao))
    )
    return [BcuMobilizacaoItemOut.model_validate(r) for r in result.scalars().all()]
