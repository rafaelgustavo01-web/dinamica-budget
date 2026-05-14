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


@pytest.mark.asyncio
async def test_commit_job_marks_completed_and_learns(db):
    mock_profile = _mock_profile()
    mock_repo = AsyncMock()
    mock_repo.get_by_cliente_id.return_value = mock_profile
    mock_repo.save_corrections.return_value = []

    job = MagicMock()
    job.id = uuid4()
    job.cliente_id = uuid4()
    job.status = SmartImportStatus.REVIEW_REQUIRED
    job.profile_id = None

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

    job = MagicMock()
    job.id = uuid4()
    job.cliente_id = uuid4()
    job.status = SmartImportStatus.REVIEW_REQUIRED
    job.profile_id = None

    with patch("backend.services.smart_import_service.ImportProfileRepository", return_value=mock_repo):
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

    job = MagicMock()
    job.id = uuid4()
    job.cliente_id = uuid4()
    job.status = SmartImportStatus.COMPLETED
    job.profile_id = None

    with patch("backend.services.smart_import_service.ImportProfileRepository", return_value=mock_repo):
        await SmartImportService().commit_job(job, db, corrections=[])

    mock_repo.save_corrections.assert_not_called()
