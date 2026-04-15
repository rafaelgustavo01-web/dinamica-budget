"""
Audit logging is handled explicitly in services (homologacao_service, etc.)
where the user context (usuario_id, cliente_id) is available.

This module keeps register_audit_hooks() as a no-op so main.py startup
does not need to be changed, but the fragile SQLAlchemy private-API hook
(session.identity_map._modified) has been removed.

Audited events (done in services):
  - servico_tcpo creation (PROPRIA item) → homologacao_service.criar_item_proprio
  - servico_tcpo approval/rejection      → homologacao_service.aprovar
  - servico_tcpo price change            → servico_catalog_service (when implemented)
  - soft delete                          → servico_catalog_service.soft_delete_servico
"""

from app.core.logging import get_logger

logger = get_logger(__name__)


def register_audit_hooks() -> None:
    """No-op: audit logging is handled explicitly in service layer."""
    logger.info("audit_hooks_registered_noop")
