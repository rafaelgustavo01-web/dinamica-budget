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
    BcuEncargoItemCreate,
    BcuEncargoItemOut,
    BcuEncargoItemUpdate,
    BcuEquipamentosOut,
    BcuEquipamentoItemCreate,
    BcuEquipamentoItemOut,
    BcuEquipamentoItemUpdate,
    BcuEquipamentoPremissaOut,
    BcuEpiItemCreate,
    BcuEpiItemOut,
    BcuEpiItemUpdate,
    BcuFerramentaItemCreate,
    BcuFerramentaItemOut,
    BcuFerramentaItemUpdate,
    BcuMaoObraItemCreate,
    BcuMaoObraItemOut,
    BcuMaoObraItemUpdate,
    BcuMobilizacaoItemCreate,
    BcuMobilizacaoItemOut,
    BcuMobilizacaoItemUpdate,
    BcuUploadConfirmOut,
    BcuUploadPreviewOut,
    BcuUploadPreviewRow,
    DeParaCreate,
    DeParaOut,
    DeParaListItemOut,
)
from backend.services.bcu_service import BcuService
from backend.services.bcu_de_para_service import BcuDeParaService
from backend.services.bcu_upload_service import BcuUploadService
from backend.services.bcu_crud_service import BcuCrudService

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

@router.delete("/cabecalhos/{cabecalho_id}", status_code=204)
async def deletar_cabecalho(
    cabecalho_id: UUID,
    _=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    cab = await _get_cabecalho(db, cabecalho_id)
    if cab.is_ativo:
        raise ValidationError("Não é possível remover a BCU ativa. Ative outra versão primeiro.")
    await db.delete(cab)
    await db.commit()

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


# ── Upload individual por tipo ────────────────────────────────────────────────

@router.post("/upload-individual/{tipo}/preview", response_model=BcuUploadPreviewOut)
async def preview_upload_individual(
    tipo: str,
    file: UploadFile = File(...),
    _=Depends(get_current_admin_user),
) -> BcuUploadPreviewOut:
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise ValidationError("Somente arquivos .xlsx são suportados.")
    payload = await file.read()
    if not payload:
        raise ValidationError("Arquivo vazio.")

    svc = BcuUploadService(None)  # db not needed for preview
    result = await svc.preview(tipo, payload, file.filename)
    return BcuUploadPreviewOut(
        tipo=result.tipo,
        total_rows=result.total_rows,
        valid_rows=result.valid_rows,
        invalid_rows=result.invalid_rows,
        rows=[
            BcuUploadPreviewRow(
                row_number=r.row_number,
                data=r.data,
                errors=r.errors,
            )
            for r in result.rows
        ],
    )


@router.post("/upload-individual/{tipo}/confirmar", response_model=BcuUploadConfirmOut)
async def confirmar_upload_individual(
    tipo: str,
    cabecalho_id: UUID,
    file: UploadFile = File(...),
    current_user=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BcuUploadConfirmOut:
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise ValidationError("Somente arquivos .xlsx são suportados.")
    payload = await file.read()
    if not payload:
        raise ValidationError("Arquivo vazio.")

    svc = BcuUploadService(db)
    result = await svc.importar(tipo, payload, file.filename, cabecalho_id, current_user.id)
    await db.commit()
    return BcuUploadConfirmOut(
        tipo=result.tipo,
        cabecalho_id=cabecalho_id,
        imported_rows=result.valid_rows,
        warnings=None,
    )


# ── CRUD seguro por tipo ──────────────────────────────────────────────────────

@router.post("/{cabecalho_id}/mao-obra", response_model=BcuMaoObraItemOut, status_code=201)
async def criar_mao_obra(
    cabecalho_id: UUID,
    body: BcuMaoObraItemCreate,
    current_user=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BcuMaoObraItemOut:
    svc = BcuCrudService(db)
    item = await svc.criar("mo", cabecalho_id, body.model_dump(), current_user.id)
    await db.commit()
    return BcuMaoObraItemOut.model_validate(item)


@router.patch("/{cabecalho_id}/mao-obra/{item_id}", response_model=BcuMaoObraItemOut)
async def atualizar_mao_obra(
    cabecalho_id: UUID,
    item_id: UUID,
    body: BcuMaoObraItemUpdate,
    _=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BcuMaoObraItemOut:
    svc = BcuCrudService(db)
    item = await svc.atualizar("mo", cabecalho_id, item_id, body.model_dump(exclude_unset=True))
    await db.commit()
    return BcuMaoObraItemOut.model_validate(item)


@router.delete("/{cabecalho_id}/mao-obra/{item_id}", status_code=204)
async def deletar_mao_obra(
    cabecalho_id: UUID,
    item_id: UUID,
    _=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    svc = BcuCrudService(db)
    await svc.deletar("mo", cabecalho_id, item_id)
    await db.commit()


@router.post("/{cabecalho_id}/equipamentos", response_model=BcuEquipamentoItemOut, status_code=201)
async def criar_equipamento(
    cabecalho_id: UUID,
    body: BcuEquipamentoItemCreate,
    current_user=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BcuEquipamentoItemOut:
    svc = BcuCrudService(db)
    item = await svc.criar("equipamentos", cabecalho_id, body.model_dump(), current_user.id)
    await db.commit()
    return BcuEquipamentoItemOut.model_validate(item)


@router.patch("/{cabecalho_id}/equipamentos/{item_id}", response_model=BcuEquipamentoItemOut)
async def atualizar_equipamento(
    cabecalho_id: UUID,
    item_id: UUID,
    body: BcuEquipamentoItemUpdate,
    _=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BcuEquipamentoItemOut:
    svc = BcuCrudService(db)
    item = await svc.atualizar("equipamentos", cabecalho_id, item_id, body.model_dump(exclude_unset=True))
    await db.commit()
    return BcuEquipamentoItemOut.model_validate(item)


@router.delete("/{cabecalho_id}/equipamentos/{item_id}", status_code=204)
async def deletar_equipamento(
    cabecalho_id: UUID,
    item_id: UUID,
    _=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    svc = BcuCrudService(db)
    await svc.deletar("equipamentos", cabecalho_id, item_id)
    await db.commit()


@router.post("/{cabecalho_id}/encargos", response_model=BcuEncargoItemOut, status_code=201)
async def criar_encargo(
    cabecalho_id: UUID,
    body: BcuEncargoItemCreate,
    current_user=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BcuEncargoItemOut:
    svc = BcuCrudService(db)
    item = await svc.criar("encargos", cabecalho_id, body.model_dump(), current_user.id)
    await db.commit()
    return BcuEncargoItemOut.model_validate(item)


@router.patch("/{cabecalho_id}/encargos/{item_id}", response_model=BcuEncargoItemOut)
async def atualizar_encargo(
    cabecalho_id: UUID,
    item_id: UUID,
    body: BcuEncargoItemUpdate,
    _=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BcuEncargoItemOut:
    svc = BcuCrudService(db)
    item = await svc.atualizar("encargos", cabecalho_id, item_id, body.model_dump(exclude_unset=True))
    await db.commit()
    return BcuEncargoItemOut.model_validate(item)


@router.delete("/{cabecalho_id}/encargos/{item_id}", status_code=204)
async def deletar_encargo(
    cabecalho_id: UUID,
    item_id: UUID,
    _=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    svc = BcuCrudService(db)
    await svc.deletar("encargos", cabecalho_id, item_id)
    await db.commit()


@router.post("/{cabecalho_id}/epi", response_model=BcuEpiItemOut, status_code=201)
async def criar_epi(
    cabecalho_id: UUID,
    body: BcuEpiItemCreate,
    current_user=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BcuEpiItemOut:
    svc = BcuCrudService(db)
    item = await svc.criar("epi", cabecalho_id, body.model_dump(), current_user.id)
    await db.commit()
    return BcuEpiItemOut.model_validate(item)


@router.patch("/{cabecalho_id}/epi/{item_id}", response_model=BcuEpiItemOut)
async def atualizar_epi(
    cabecalho_id: UUID,
    item_id: UUID,
    body: BcuEpiItemUpdate,
    _=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BcuEpiItemOut:
    svc = BcuCrudService(db)
    item = await svc.atualizar("epi", cabecalho_id, item_id, body.model_dump(exclude_unset=True))
    await db.commit()
    return BcuEpiItemOut.model_validate(item)


@router.delete("/{cabecalho_id}/epi/{item_id}", status_code=204)
async def deletar_epi(
    cabecalho_id: UUID,
    item_id: UUID,
    _=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    svc = BcuCrudService(db)
    await svc.deletar("epi", cabecalho_id, item_id)
    await db.commit()


@router.post("/{cabecalho_id}/ferramentas", response_model=BcuFerramentaItemOut, status_code=201)
async def criar_ferramenta(
    cabecalho_id: UUID,
    body: BcuFerramentaItemCreate,
    current_user=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BcuFerramentaItemOut:
    svc = BcuCrudService(db)
    item = await svc.criar("ferramentas", cabecalho_id, body.model_dump(), current_user.id)
    await db.commit()
    return BcuFerramentaItemOut.model_validate(item)


@router.patch("/{cabecalho_id}/ferramentas/{item_id}", response_model=BcuFerramentaItemOut)
async def atualizar_ferramenta(
    cabecalho_id: UUID,
    item_id: UUID,
    body: BcuFerramentaItemUpdate,
    _=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BcuFerramentaItemOut:
    svc = BcuCrudService(db)
    item = await svc.atualizar("ferramentas", cabecalho_id, item_id, body.model_dump(exclude_unset=True))
    await db.commit()
    return BcuFerramentaItemOut.model_validate(item)


@router.delete("/{cabecalho_id}/ferramentas/{item_id}", status_code=204)
async def deletar_ferramenta(
    cabecalho_id: UUID,
    item_id: UUID,
    _=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    svc = BcuCrudService(db)
    await svc.deletar("ferramentas", cabecalho_id, item_id)
    await db.commit()


@router.post("/{cabecalho_id}/mobilizacao", response_model=BcuMobilizacaoItemOut, status_code=201)
async def criar_mobilizacao(
    cabecalho_id: UUID,
    body: BcuMobilizacaoItemCreate,
    current_user=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BcuMobilizacaoItemOut:
    svc = BcuCrudService(db)
    item = await svc.criar("mobilizacao", cabecalho_id, body.model_dump(), current_user.id)
    await db.commit()
    return BcuMobilizacaoItemOut.model_validate(item)


@router.patch("/{cabecalho_id}/mobilizacao/{item_id}", response_model=BcuMobilizacaoItemOut)
async def atualizar_mobilizacao(
    cabecalho_id: UUID,
    item_id: UUID,
    body: BcuMobilizacaoItemUpdate,
    _=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> BcuMobilizacaoItemOut:
    svc = BcuCrudService(db)
    item = await svc.atualizar("mobilizacao", cabecalho_id, item_id, body.model_dump(exclude_unset=True))
    await db.commit()
    return BcuMobilizacaoItemOut.model_validate(item)


@router.delete("/{cabecalho_id}/mobilizacao/{item_id}", status_code=204)
async def deletar_mobilizacao(
    cabecalho_id: UUID,
    item_id: UUID,
    _=Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    svc = BcuCrudService(db)
    await svc.deletar("mobilizacao", cabecalho_id, item_id)
    await db.commit()
