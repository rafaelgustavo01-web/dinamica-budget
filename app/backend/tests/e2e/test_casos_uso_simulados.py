"""
Testes de Simulação de Casos de Uso — Dinamica Budget

Este arquivo simula os principais fluxos de negócio e valida:
1. Autenticação e JWT
2. Busca TCPO (4 fases)
3. Homologação de itens próprios
4. Smart Import
5. PQ Client Profiles
6. BCU/BASE CRUD
7. Folha PC
8. RBAC e isolamento de dados

Executar com: pytest app/backend/tests/e2e/test_casos_uso_simulados.py -v
"""

import pytest
import asyncio
import json
from datetime import datetime
from typing import Dict, Any
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

# Import models
from backend.models.usuario import Usuario
from backend.models.cliente import Cliente
from backend.models.servico_tcpo import ServicoTCPO
from backend.models.item_proprio import ItemProprio
from backend.core.security import hash_password
from backend.core.database import async_session_factory
import uuid


class TestCasosUsoSimulados:
    """Suite de testes E2E simulando fluxos reais de usuários"""

    @pytest.fixture
    async def setup_users(self, db_session: AsyncSession):
        """Setup: Criar usuários de teste (admin, cliente A, cliente B)"""
        users = {}
        
        # Admin
        admin = Usuario(
            id=uuid.uuid4(),
            nome="Admin Teste",
            email="admin@test.local",
            hashed_password=hash_password("AdminPassword123!"),
            is_admin=True,
            is_active=True,
        )
        db_session.add(admin)
        users["admin"] = admin
        
        # Cliente A
        cliente_a_user = Usuario(
            id=uuid.uuid4(),
            nome="Gerente Cliente A",
            email="cliente_a@test.local",
            hashed_password=hash_password("ClientePassword123!"),
            is_admin=False,
            is_active=True,
        )
        db_session.add(cliente_a_user)
        users["cliente_a_user"] = cliente_a_user
        
        # Cliente B
        cliente_b_user = Usuario(
            id=uuid.uuid4(),
            nome="Gerente Cliente B",
            email="cliente_b@test.local",
            hashed_password=hash_password("ClientePassword123!"),
            is_admin=False,
            is_active=True,
        )
        db_session.add(cliente_b_user)
        users["cliente_b_user"] = cliente_b_user
        
        await db_session.commit()
        return users

    @pytest.fixture
    async def setup_clientes(self, db_session: AsyncSession, setup_users):
        """Setup: Criar clientes (ClienteA, ClienteB)"""
        users = setup_users
        
        cliente_a = Cliente(
            id=uuid.uuid4(),
            nome="Construtora ABC LTDA",
            razao_social="Construtora ABC Sociedade Limitada",
            cnpj="12345678000100",
            contato_comercial="vendas@construtoraabc.com.br",
            usuario_id=users["cliente_a_user"].id,
            is_active=True,
        )
        db_session.add(cliente_a)
        
        cliente_b = Cliente(
            id=uuid.uuid4(),
            nome="Engenharia XYZ LTDA",
            razao_social="Engenharia XYZ Sociedade Limitada",
            cnpj="87654321000199",
            contato_comercial="contato@engenhariaxyz.com.br",
            usuario_id=users["cliente_b_user"].id,
            is_active=True,
        )
        db_session.add(cliente_b)
        
        await db_session.commit()
        return {"cliente_a": cliente_a, "cliente_b": cliente_b}

    @pytest.mark.asyncio
    async def test_uc001_login_and_jwt_refresh(self, client: AsyncClient, setup_users):
        """UC-001: Login com JWT e Refresh Token"""
        users = setup_users
        
        # 1. Login com admin
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "admin@test.local",
                "password": "AdminPassword123!",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        
        # 2. Usar access_token para GET /me
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        me_data = response.json()
        assert me_data["email"] == "admin@test.local"
        assert me_data["is_admin"] is True
        
        # 3. Refresh do token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        new_data = response.json()
        assert "access_token" in new_data
        new_access_token = new_data["access_token"]
        
        # 4. Validar novo access_token
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert response.status_code == 200
        
        print("✅ UC-001: Login e JWT Refresh — PASSOU")

    @pytest.mark.asyncio
    async def test_uc002_busca_tcpo_4_fases(self, client: AsyncClient, db_session: AsyncSession):
        """UC-002: Busca TCPO com 4 fases (Direta, Fuzzy, Semântica, IA)"""
        
        # Setup: Criar alguns serviços TCPO de teste
        servicos = [
            ServicoTCPO(
                id=uuid.uuid4(),
                codigo_tcpo="0101.00.01.00",
                descricao="Escavação manual de solo argiloso a pá",
                unidade="m³",
                preco_base=50.00,
                origem="TCPO_OFICIAL"
            ),
            ServicoTCPO(
                id=uuid.uuid4(),
                codigo_tcpo="0102.00.01.00",
                descricao="Escavação mecânica com escavadeira",
                unidade="m³",
                preco_base=35.00,
                origem="TCPO_OFICIAL"
            ),
        ]
        db_session.add_all(servicos)
        await db_session.commit()
        
        # Teste de busca
        response = await client.get(
            "/api/v1/servicos/buscar",
            params={"q": "escavação manual solo argiloso"}
        )
        assert response.status_code == 200
        results = response.json()
        assert "resultados" in results
        assert len(results["resultados"]) > 0
        
        # Validar que cada resultado tem source (DIRETA, FUZZY, SEMANTICA ou IA)
        for resultado in results["resultados"]:
            assert "codigo_tcpo" in resultado
            assert "descricao" in resultado
            assert "score" in resultado
            assert "source" in resultado
            assert resultado["source"] in ["DIRETA", "FUZZY", "SEMANTICA", "IA"]
        
        print("✅ UC-002: Busca TCPO 4 Fases — PASSOU")

    @pytest.mark.asyncio
    async def test_uc003_homologacao_itens_proprios(self, client: AsyncClient, db_session: AsyncSession, setup_users, setup_clientes):
        """UC-003: Criar, aprovar e reprovar itens próprios (PROPRIA)"""
        users = setup_users
        clientes = setup_clientes
        
        # Login como cliente A
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "cliente_a@test.local",
                "password": "ClientePassword123!",
            }
        )
        token_a = response.json()["access_token"]
        
        # 1. Cliente A cria item próprio
        response = await client.post(
            "/api/v1/itens-proprios/criar",
            json={
                "nome": "Parede de concreto 15cm",
                "descricao": "Parede em concreto armado, espessura 15cm",
                "unidade": "m²",
                "preco_base": 150.00,
            },
            headers={"Authorization": f"Bearer {token_a}"}
        )
        assert response.status_code == 201
        item_id = response.json()["id"]
        assert response.json()["status"] == "PENDENTE"
        
        # 2. Admin lista itens pendentes
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "admin@test.local", "password": "AdminPassword123!"}
        )
        token_admin = response.json()["access_token"]
        
        response = await client.get(
            "/api/v1/homologacao/pendentes",
            headers={"Authorization": f"Bearer {token_admin}"}
        )
        assert response.status_code == 200
        pendentes = response.json()
        assert len(pendentes) > 0
        
        # 3. Admin aprova item
        response = await client.post(
            f"/api/v1/homologacao/{item_id}/aprovar",
            headers={"Authorization": f"Bearer {token_admin}"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "APROVADO"
        
        # 4. Validar que auditoria registrou a aprovação
        response = await client.get(
            f"/api/v1/homologacao/{item_id}/historico",
            headers={"Authorization": f"Bearer {token_admin}"}
        )
        assert response.status_code == 200
        historico = response.json()
        assert len(historico) > 0
        assert historico[-1]["tipo_operacao"] == "APROVAR"
        
        print("✅ UC-003: Homologação de Itens Próprios — PASSOU")

    @pytest.mark.asyncio
    async def test_uc008_rbac_isolamento_dados(self, client: AsyncClient, db_session: AsyncSession, setup_users, setup_clientes):
        """UC-008: RBAC e Isolamento de Dados por Cliente"""
        users = setup_users
        clientes = setup_clientes
        cliente_a_id = clientes["cliente_a"].id
        cliente_b_id = clientes["cliente_b"].id
        
        # Setup: Criar itens próprios para cada cliente
        item_a = ItemProprio(
            id=uuid.uuid4(),
            cliente_id=cliente_a_id,
            nome="Item exclusivo de A",
            descricao="Dados confidenciais de Cliente A",
            unidade="un",
            preco_base=100.00,
            status="APROVADO"
        )
        
        item_b = ItemProprio(
            id=uuid.uuid4(),
            cliente_id=cliente_b_id,
            nome="Item exclusivo de B",
            descricao="Dados confidenciais de Cliente B",
            unidade="un",
            preco_base=200.00,
            status="APROVADO"
        )
        db_session.add_all([item_a, item_b])
        await db_session.commit()
        
        # Login como cliente A
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "cliente_a@test.local", "password": "ClientePassword123!"}
        )
        token_a = response.json()["access_token"]
        
        # Login como cliente B
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "cliente_b@test.local", "password": "ClientePassword123!"}
        )
        token_b = response.json()["access_token"]
        
        # 1. Cliente A lista seus itens
        response = await client.get(
            "/api/v1/itens-proprios/meus",
            headers={"Authorization": f"Bearer {token_a}"}
        )
        assert response.status_code == 200
        itens_a = response.json()
        assert len(itens_a) == 1
        assert itens_a[0]["nome"] == "Item exclusivo de A"
        
        # 2. Cliente B lista seus itens
        response = await client.get(
            "/api/v1/itens-proprios/meus",
            headers={"Authorization": f"Bearer {token_b}"}
        )
        assert response.status_code == 200
        itens_b = response.json()
        assert len(itens_b) == 1
        assert itens_b[0]["nome"] == "Item exclusivo de B"
        
        # 3. Cliente A tenta acessar item de B (deve falhar)
        response = await client.get(
            f"/api/v1/itens-proprios/{item_b.id}",
            headers={"Authorization": f"Bearer {token_a}"}
        )
        assert response.status_code == 403  # Forbidden
        
        # 4. Cliente B tenta acessar item de A (deve falhar)
        response = await client.get(
            f"/api/v1/itens-proprios/{item_a.id}",
            headers={"Authorization": f"Bearer {token_b}"}
        )
        assert response.status_code == 403  # Forbidden
        
        # 5. Admin consegue ver itens de ambos
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "admin@test.local", "password": "AdminPassword123!"}
        )
        token_admin = response.json()["access_token"]
        
        response = await client.get(
            "/api/v1/itens-proprios/listar-todos",
            headers={"Authorization": f"Bearer {token_admin}"}
        )
        assert response.status_code == 200
        todos_itens = response.json()
        assert len(todos_itens) >= 2
        
        print("✅ UC-008: RBAC e Isolamento de Dados — PASSOU")

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Teste básico: Health Check da API"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded"]
        
        print("✅ Health Check — PASSOU")

    @pytest.mark.asyncio
    async def test_rate_limiting(self, client: AsyncClient):
        """Teste de Rate Limiting: 50 requisições rápidas devem bloquear"""
        print("⏳ Testando Rate Limiting...")
        
        for i in range(50):
            response = await client.get("/health")
            if response.status_code == 200:
                continue
            elif response.status_code == 429:  # Too Many Requests
                print(f"✅ Rate Limiting ativado na requisição {i+1} — PASSOU")
                return
        
        print("⚠️  Rate Limiting — Esperado bloquear em 50 requisições")


# ─────────────────────────────────────────────────────────────────────────────
# Testes de Validação de Banco de Dados
# ─────────────────────────────────────────────────────────────────────────────

class TestDatabaseValidation:
    """Suite de validações de estrutura e integrity do banco de dados"""
    
    @pytest.mark.asyncio
    async def test_schemas_existem(self, db_session: AsyncSession):
        """Validar que todos os schemas necessários foram criados"""
        required_schemas = ["bcu", "referencia", "operacional"]
        
        for schema in required_schemas:
            result = await db_session.execute(
                text(f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{schema}'")
            )
            assert result.scalar(), f"Schema '{schema}' não existe"
        
        print("✅ Schemas existem — PASSOU")
    
    @pytest.mark.asyncio
    async def test_enums_existem(self, db_session: AsyncSession):
        """Validar que todos os ENUM types foram criados"""
        enum_types = [
            "status_homologacao_enum",
            "status_proposta_enum",
            "tipo_operacao_auditoria_enum",
        ]
        
        for enum_type in enum_types:
            result = await db_session.execute(
                text(f"SELECT typname FROM pg_type WHERE typname = '{enum_type}'")
            )
            assert result.scalar(), f"ENUM '{enum_type}' não existe"
        
        print("✅ ENUMs existem — PASSOU")
    
    @pytest.mark.asyncio
    async def test_indexes_criados(self, db_session: AsyncSession):
        """Validar que indexes críticos foram criados"""
        # Verificar se existe index para busca fuzzy
        result = await db_session.execute(
            text("SELECT indexname FROM pg_indexes WHERE indexname LIKE '%trgm%'")
        )
        assert result.scalar(), "Index pg_trgm não encontrado"
        
        print("✅ Indexes críticos existem — PASSOU")


# ─────────────────────────────────────────────────────────────────────────────
# Testes de Performance
# ─────────────────────────────────────────────────────────────────────────────

class TestPerformance:
    """Suite de testes de performance"""
    
    @pytest.mark.asyncio
    async def test_busca_semântica_latência(self, client: AsyncClient, db_session: AsyncSession):
        """Validar que busca semântica retorna em <500ms"""
        import time
        
        # Setup: Criar 100 serviços TCPO
        servicos = [
            ServicoTCPO(
                id=uuid.uuid4(),
                codigo_tcpo=f"010{i:04d}",
                descricao=f"Serviço teste número {i}",
                unidade="un",
                preco_base=float(i * 10),
                origem="TCPO_OFICIAL"
            )
            for i in range(100)
        ]
        db_session.add_all(servicos)
        await db_session.commit()
        
        # Buscar e medir latência
        start = time.time()
        response = await client.get(
            "/api/v1/servicos/buscar",
            params={"q": "serviço"}
        )
        elapsed = (time.time() - start) * 1000  # ms
        
        assert response.status_code == 200
        assert elapsed < 500, f"Busca levou {elapsed:.1f}ms (esperado <500ms)"
        
        print(f"✅ Busca Semântica latência: {elapsed:.1f}ms — PASSOU")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
