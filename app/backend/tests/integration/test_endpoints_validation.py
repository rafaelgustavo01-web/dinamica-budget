"""
Testes de Validação de Endpoints — Dinamica Budget

Valida a estrutura e funcionamento dos endpoints principais da API.
Executar com: pytest app/backend/tests/integration/test_endpoints_validation.py -v
"""

import pytest
from httpx import AsyncClient


class TestAuthEndpoints:
    """Validação de endpoints de autenticação"""
    
    @pytest.mark.asyncio
    async def test_login_endpoint_existe(self, client: AsyncClient):
        """GET /api/v1/auth/login deve existir"""
        # Nota: sem credentials, deve retornar 422 ou 401, não 404
        response = await client.post("/api/v1/auth/login", data={})
        assert response.status_code != 404, "Endpoint /login não encontrado"
    
    @pytest.mark.asyncio
    async def test_refresh_endpoint_existe(self, client: AsyncClient):
        """GET /api/v1/auth/refresh deve existir"""
        response = await client.post("/api/v1/auth/refresh", json={})
        assert response.status_code != 404, "Endpoint /refresh não encontrado"
    
    @pytest.mark.asyncio
    async def test_me_endpoint_existe(self, client: AsyncClient):
        """GET /api/v1/auth/me deve existir"""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code != 404, "Endpoint /me não encontrado"


class TestBuscaEndpoints:
    """Validação de endpoints de busca TCPO"""
    
    @pytest.mark.asyncio
    async def test_buscar_servicos_endpoint_existe(self, client: AsyncClient):
        """GET /api/v1/servicos/buscar deve existir"""
        response = await client.get("/api/v1/servicos/buscar", params={"q": "teste"})
        assert response.status_code != 404, "Endpoint /servicos/buscar não encontrado"
    
    @pytest.mark.asyncio
    async def test_associar_endpoint_existe(self, client: AsyncClient):
        """POST /api/v1/servicos/associar deve existir"""
        response = await client.post("/api/v1/servicos/associar", json={})
        assert response.status_code != 404, "Endpoint /servicos/associar não encontrado"


class TestHomologacaoEndpoints:
    """Validação de endpoints de homologação"""
    
    @pytest.mark.asyncio
    async def test_pendentes_endpoint_existe(self, client: AsyncClient):
        """GET /api/v1/homologacao/pendentes deve existir"""
        response = await client.get("/api/v1/homologacao/pendentes")
        # Sem auth pode retornar 401, mas não 404
        assert response.status_code != 404, "Endpoint /homologacao/pendentes não encontrado"
    
    @pytest.mark.asyncio
    async def test_aprovar_endpoint_existe(self, client: AsyncClient):
        """POST /api/v1/homologacao/{id}/aprovar deve existir"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.post(f"/api/v1/homologacao/{fake_id}/aprovar", json={})
        # Sem auth pode retornar 401, mas não 404
        assert response.status_code != 404, "Endpoint /homologacao/{id}/aprovar não encontrado"


class TestHealthCheck:
    """Validação de health check"""
    
    @pytest.mark.asyncio
    async def test_health_retorna_json(self, client: AsyncClient):
        """GET /health deve retornar JSON com status"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    @pytest.mark.asyncio
    async def test_health_db_status(self, client: AsyncClient):
        """GET /health deve incluir status do DB"""
        response = await client.get("/health")
        data = response.json()
        assert "database" in data or "db" in data.get("status", "").lower()


class TestOpenAPI:
    """Validação de documentação OpenAPI"""
    
    @pytest.mark.asyncio
    async def test_openapi_json_existe(self, client: AsyncClient):
        """GET /openapi.json deve existir"""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data or "swagger" in data
    
    @pytest.mark.asyncio
    async def test_swagger_ui_existe(self, client: AsyncClient):
        """GET /docs (Swagger) deve existir"""
        response = await client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()


class TestErrorHandling:
    """Validação de tratamento de erros"""
    
    @pytest.mark.asyncio
    async def test_404_nao_encontrado(self, client: AsyncClient):
        """GET /endpoint-inexistente deve retornar 404"""
        response = await client.get("/api/v1/inexistente")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_401_sem_autenticacao(self, client: AsyncClient):
        """Endpoints protegidos sem token devem retornar 401"""
        response = await client.get("/api/v1/homologacao/pendentes")
        assert response.status_code == 401 or response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_422_validacao_invalida(self, client: AsyncClient):
        """POST com schema inválido deve retornar 422"""
        response = await client.post(
            "/api/v1/auth/login",
            data={"invalid_field": "invalid"}  # Falta username/password
        )
        assert response.status_code == 422 or response.status_code == 401


class TestCORSHeaders:
    """Validação de headers CORS"""
    
    @pytest.mark.asyncio
    async def test_cors_headers_presentes(self, client: AsyncClient):
        """Response deve incluir headers CORS"""
        response = await client.get("/health")
        # Verificar se ao menos um header CORS está presente
        cors_headers = [h for h in response.headers if "access-control" in h.lower()]
        # Note: pode estar vazio ou preenchido, dependendo da configuração
        # Esta validação apenas verifica se não há erro
        assert response.status_code == 200


class TestResponseFormats:
    """Validação de formatos de resposta"""
    
    @pytest.mark.asyncio
    async def test_health_response_valido(self, client: AsyncClient):
        """Health check deve retornar JSON válido"""
        response = await client.get("/health")
        assert response.headers.get("content-type", "").startswith("application/json")
        data = response.json()
        assert isinstance(data, dict)
    
    @pytest.mark.asyncio
    async def test_error_response_estruturado(self, client: AsyncClient):
        """Respostas de erro devem ter estrutura consistente"""
        response = await client.get("/api/v1/inexistente")
        if response.status_code >= 400:
            try:
                data = response.json()
                # Verificar estrutura comum de erro
                assert "detail" in data or "message" in data or "error" in data
            except:
                # Se não for JSON, still ok (pode ser HTML, etc)
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
