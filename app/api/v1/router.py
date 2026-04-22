from fastapi import APIRouter

from app.api.v1.endpoints import admin, auth, busca, clientes, composicoes, extracao, homologacao, servicos, usuarios, versoes

router = APIRouter()

router.include_router(auth.router)
router.include_router(busca.router)
router.include_router(servicos.router)
router.include_router(composicoes.router)
router.include_router(versoes.router)
router.include_router(homologacao.router)
router.include_router(admin.router)
router.include_router(usuarios.router)
router.include_router(clientes.router)
router.include_router(extracao.router)
