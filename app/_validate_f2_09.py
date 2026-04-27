import os
os.environ["DEBUG"] = "True"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://x:x@localhost/x"
os.environ["SECRET_KEY"] = "a" * 32

import sys
sys.path.insert(0, ".")

# ── migration syntax ──────────────────────────────────────────────────────────
import ast
with open("alembic/versions/022_proposta_versionamento.py", encoding="utf-8") as f:
    src = f.read()
ast.parse(src)
assert "autocommit_block" in src, "autocommit_block missing"
assert "AGUARDANDO_APROVACAO" in src
assert "proposta_root_id" in src
assert "uq_proposta_versao" in src
print("OK: migration 022 syntax valid, autocommit_block present")

# ── route ordering (React) ────────────────────────────────────────────────────
with open("frontend/src/features/proposals/routes.tsx", encoding="utf-8") as f:
    routes_src = f.read()
aprovacoes_pos = routes_src.find("aprovacoes")
id_pos = routes_src.find('path=":id"')
assert aprovacoes_pos < id_pos, f"aprovacoes must come before :id ({aprovacoes_pos} vs {id_pos})"
print("OK: /aprovacoes route declared before /:id in routes.tsx")

# ── route ordering (FastAPI) ──────────────────────────────────────────────────
with open("backend/api/v1/endpoints/propostas.py", encoding="utf-8") as f:
    ep_src = f.read()
aprovacoes_ep = ep_src.find('"/aprovacoes"')
root_versoes_ep = ep_src.find('"/root/{root_id}/versoes"')
proposta_id_ep = ep_src.find('"/{proposta_id}"')
assert aprovacoes_ep < proposta_id_ep, "FastAPI: /aprovacoes must be before /{proposta_id}"
assert root_versoes_ep < proposta_id_ep, "FastAPI: /root/{root_id}/versoes must be before /{proposta_id}"
print("OK: FastAPI static routes before /{proposta_id}")

# ── require_proposta_role resolves via root_id ────────────────────────────────
with open("backend/core/dependencies.py", encoding="utf-8") as f:
    dep_src = f.read()
assert "proposta_root_id" in dep_src, "require_proposta_role must resolve via proposta_root_id"
assert "acl_id = proposta_root_id if proposta_root_id is not None else proposta_id" in dep_src
print("OK: require_proposta_role resolves ACL via proposta_root_id")

# ── PropostaResponse has versioning fields ────────────────────────────────────
with open("backend/schemas/proposta.py", encoding="utf-8") as f:
    schema_src = f.read()
for field in ["proposta_root_id", "numero_versao", "is_versao_atual", "is_fechada", "requer_aprovacao", "aprovado_por_id", "motivo_revisao"]:
    assert field in schema_src, f"PropostaResponse missing field: {field}"
print("OK: PropostaResponse has all versioning/approval fields")

# ── frontend proposalsApi has new methods ─────────────────────────────────────
with open("frontend/src/shared/services/api/proposalsApi.ts", encoding="utf-8") as f:
    api_src = f.read()
for method in ["novaVersao", "enviarAprovacao", "aprovar", "rejeitar", "filaAprovacoes", "listarVersoes"]:
    assert method in api_src, f"proposalsApi missing method: {method}"
print("OK: proposalsApi has all F2-09 methods")

# ── ApprovalQueuePage and ProposalHistoryPanel exist ─────────────────────────
import os
assert os.path.exists("frontend/src/features/proposals/pages/ApprovalQueuePage.tsx")
assert os.path.exists("frontend/src/features/proposals/components/ProposalHistoryPanel.tsx")
print("OK: ApprovalQueuePage and ProposalHistoryPanel exist")

# ── repo has new methods ──────────────────────────────────────────────────────
with open("backend/repositories/proposta_repository.py", encoding="utf-8") as f:
    repo_src = f.read()
assert "max_numero_versao" in repo_src
assert "list_by_root" in repo_src
assert "list_aguardando_aprovacao" in repo_src
print("OK: PropostaRepository has max_numero_versao, list_by_root, list_aguardando_aprovacao")

print("\n✅ All F2-09 structural validations passed")
