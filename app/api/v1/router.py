from fastapi import APIRouter

<<<<<<< HEAD
from app.api.v1.endpoints import admin, auth, busca, clientes, composicoes, extracao, homologacao, servicos, usuarios, versoes
=======
from app.api.v1.endpoints import admin, auth, busca, clientes, composicoes, homologacao, pc_tabelas, servicos, usuarios, versoes
>>>>>>> 5f0973541797732f99516ee792729f7f3cef10c2

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
<<<<<<< HEAD
router.include_router(extracao.router)
=======
router.include_router(pc_tabelas.router)
>>>>>>> 5f0973541797732f99516ee792729f7f3cef10c2
