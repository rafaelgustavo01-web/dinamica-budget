from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from backend.models.smart_import import SmartImportStatus
from backend.services.smart_import_service import SmartImportService


@pytest.fixture
def db():
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.flush = AsyncMock()
    return session


def _mock_profile(uso_count=0):
    from backend.models.import_profile import ImportProfile
    p = MagicMock(spec=ImportProfile)
    p.id = uuid4()
    p.header_row_strategy = {"mode": "scan"}
    p.column_aliases = {}
    p.aba_pattern = None
    p.uso_count = uso_count
    p.score_confianca = Decimal("0")
    return p


def _job_without_proposta():
    job = MagicMock()
    job.id = uuid4()
    job.cliente_id = uuid4()
    job.proposta_id = None
    job.arquivo_origem = "test.xlsx"
    job.status = SmartImportStatus.REVIEW_REQUIRED
    job.profile_id = None
    job.payload_staging = {"rows": []}
    return job


@pytest.mark.asyncio
async def test_commit_job_marks_completed_and_learns(db):
    mock_profile = _mock_profile()
    mock_repo = AsyncMock()
    mock_repo.get_by_cliente_id.return_value = mock_profile
    mock_repo.save_corrections.return_value = []

    job = _job_without_proposta()
    job.status = SmartImportStatus.REVIEW_REQUIRED

    with patch("backend.services.smart_import_service.ImportProfileRepository") as mock_cls:
        mock_cls.return_value = mock_repo
        svc = SmartImportService()
        result = await svc.commit_job(job, db, corrections=[
            {"tipo": "COLUMN_REMAP", "detalhe": {"campo": "quantidade", "header_text": "QUANT."}}
        ])

    assert result.status == SmartImportStatus.COMPLETED
    assert result.profile_id == mock_profile.id
    assert "QUANT." in mock_profile.column_aliases.get("quantidade", [])
    assert mock_profile.uso_count == 1


@pytest.mark.asyncio
async def test_commit_job_creates_profile_if_none_exists(db):
    new_profile = _mock_profile()
    mock_repo = AsyncMock()
    mock_repo.get_by_cliente_id.return_value = None
    mock_repo.create.return_value = new_profile
    mock_repo.save_corrections.return_value = []

    job = _job_without_proposta()

    with patch("backend.services.smart_import_service.ImportProfileRepository") as mock_cls:
        mock_cls.return_value = mock_repo
        svc = SmartImportService()
        result = await svc.commit_job(job, db, corrections=[])

    mock_repo.create.assert_called_once_with(job.cliente_id)
    assert result.status == SmartImportStatus.COMPLETED


@pytest.mark.asyncio
async def test_commit_job_clean_import_scores_higher_than_corrected(db):
    """Second commit with no corrections should yield higher score than first with corrections."""
    from backend.services.smart_import.profile_learner import _compute_score

    score_corrected = _compute_score(uso_count=1, correction_count=2)
    score_clean = _compute_score(uso_count=1, correction_count=0)
    assert score_clean > score_corrected


@pytest.mark.asyncio
async def test_commit_no_corrections_does_not_call_save_corrections(db):
    mock_profile = _mock_profile(uso_count=2)
    mock_repo = AsyncMock()
    mock_repo.get_by_cliente_id.return_value = mock_profile
    mock_repo.save_corrections.return_value = []

    job = _job_without_proposta()
    job.status = SmartImportStatus.COMPLETED

    with patch("backend.services.smart_import_service.ImportProfileRepository") as mock_cls:
        mock_cls.return_value = mock_repo
        await SmartImportService().commit_job(job, db, corrections=[])

    mock_repo.save_corrections.assert_not_called()


@pytest.mark.asyncio
async def test_commit_job_with_proposta_id_creates_pq_items(db):
    """When proposta_id is set, commit_job should db.add a PqImportacao and PqItems."""
    from backend.models.proposta import PqImportacao, PqItem as PqItemModel

    mock_profile = _mock_profile()
    mock_repo = AsyncMock()
    mock_repo.get_by_cliente_id.return_value = mock_profile
    mock_repo.save_corrections.return_value = []

    proposta_id = uuid4()
    job = MagicMock()
    job.id = uuid4()
    job.cliente_id = uuid4()
    job.proposta_id = proposta_id
    job.arquivo_origem = "planilha.xlsx"
    job.status = SmartImportStatus.REVIEW_REQUIRED
    job.profile_id = None
    job.payload_staging = {
        "rows": [
            {
                "idx": 0, "sheet_row": 2, "row_class": "ITEM",
                "codigo": "1.1", "descricao": "Escavacao manual",
                "unidade": "m2", "quantidade": "10", "preco": None, "valor": None,
            },
            {
                "idx": 1, "sheet_row": 3, "row_class": "SECAO",
                "codigo": None, "descricao": "SERVICOS PRELIMINARES",
                "unidade": None, "quantidade": None, "preco": None, "valor": None,
            },
        ]
    }

    added_objects = []
    db.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))

    with patch("backend.services.smart_import_service.ImportProfileRepository") as mock_cls:
        mock_cls.return_value = mock_repo
        await SmartImportService().commit_job(job, db, corrections=[])

    importacoes = [o for o in added_objects if isinstance(o, PqImportacao)]
    pq_items = [o for o in added_objects if isinstance(o, PqItemModel)]

    assert len(importacoes) == 1
    assert importacoes[0].proposta_id == proposta_id
    assert importacoes[0].nome_arquivo == "planilha.xlsx"
    assert importacoes[0].linhas_importadas == 1
    assert importacoes[0].linhas_ignoradas == 1

    assert len(pq_items) == 1
    assert pq_items[0].proposta_id == proposta_id
    assert pq_items[0].descricao_original == "Escavacao manual"
    assert pq_items[0].codigo_original == "1.1"
    assert pq_items[0].unidade_medida_original == "m2"
    assert pq_items[0].linha_planilha == 2


@pytest.mark.asyncio
async def test_commit_job_without_proposta_id_skips_pq_items(db):
    """When proposta_id is None, no PqImportacao or PqItem is created."""
    from backend.models.proposta import PqImportacao, PqItem as PqItemModel

    mock_profile = _mock_profile()
    mock_repo = AsyncMock()
    mock_repo.get_by_cliente_id.return_value = mock_profile
    mock_repo.save_corrections.return_value = []

    job = _job_without_proposta()
    job.payload_staging = {
        "rows": [
            {
                "idx": 0, "sheet_row": 2, "row_class": "ITEM",
                "codigo": "1.1", "descricao": "Escavacao",
                "unidade": "m2", "quantidade": "5", "preco": None, "valor": None,
            },
        ]
    }

    added_objects = []
    db.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))

    with patch("backend.services.smart_import_service.ImportProfileRepository") as mock_cls:
        mock_cls.return_value = mock_repo
        await SmartImportService().commit_job(job, db, corrections=[])

    assert not any(isinstance(o, PqImportacao) for o in added_objects)
    assert not any(isinstance(o, PqItemModel) for o in added_objects)
