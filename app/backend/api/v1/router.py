from fastapi import APIRouter

from backend.api.v1.endpoints import (
    admin,
    auth,
    busca,
    clientes,
    composicoes,
    cpu_geracao,
    extracao,
    homologacao,
    pc_tabelas,
    pq_importacao,
    pq_layout,
    proposta_acl,
    proposta_export,
    propostas,
    servicos,
    usuarios,
    versoes,
)

router = APIRouter()

router.include_router(auth.router)
router.include_router(busca.router)
router.include_router(servicos.router)
router.include_router(composicoes.router)
router.include_router(cpu_geracao.router)
router.include_router(versoes.router)
router.include_router(homologacao.router)
router.include_router(admin.router)
router.include_router(usuarios.router)
router.include_router(clientes.router)
router.include_router(extracao.router)
router.include_router(pc_tabelas.router)
router.include_router(propostas.router)
router.include_router(proposta_export.router)
router.include_router(pq_importacao.router)
router.include_router(pq_layout.router)
router.include_router(proposta_acl.router)
