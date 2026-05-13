# Validação do Fluxo PQ + Match + Histograma

## Problemas Corrigidos

### 1. **Erro 502 no endpoint `/api/v1/propostas/{id}/pq/match`** ✅
**Problema**: Exceções não eram capturadas e logadas adequadamente
**Solução**: Adicionado try/except com logging detalhado no endpoint

**Arquivo**: `backend/api/v1/endpoints/pq_importacao.py`
- Adicionado import `get_logger`
- Envolvido match com try/except
- Adicionado log de erro com contexto (proposta_id, usuario_id, erro)

---

### 2. **Histograma compartilhado entre propostas do mesmo cliente** ✅
**Problema**: Cada proposta herdava histograma de outra porque:
- `bulk_upsert` com constraint `(proposta_id, bcu_item_id)` permite duplicatas quando `bcu_item_id` é NULL
- Não havia DELETE prévio para limpar dados antigos
- Logo, dados de proposta anterior permaneciam

**Solução**: 
1. Implementar lógica de DELETE antes de INSERT em todas as tabelas de histograma
2. Adicionar métodos de limpeza no repositório:
   - `clear_mao_obra(proposta_id)`
   - `clear_equipamentos(proposta_id)`
   - `clear_epi(proposta_id)`
   - `clear_ferramentas(proposta_id)`

**Arquivos alterados**:
- `backend/repositories/proposta_pc_repository.py`: Adicionados 4 métodos de limpeza
- `backend/services/histograma_service.py`: Substituído `bulk_upsert` por DELETE + INSERT

**Diferença importante**:
```python
# ANTES (problemático):
await self.repo.bulk_upsert(PropostaPcMaoObra, mo_items, ["proposta_id", "bcu_item_id"])

# DEPOIS (correto):
await self.repo.clear_mao_obra(proposta_id)  # Limpa dados antigos
await self.repo.bulk_insert(PropostaPcMaoObra, mo_items)  # Insere novos
```

---

### 3. **Falta de UniqueConstraint em PropostaPcEncargo** ✅
**Problema**: `PropostaPcEncargo` não tinha constraint definida, permitindo duplicatas

**Solução**: Adicionado `UniqueConstraint("proposta_id", "bcu_item_id")`

**Arquivo**: `backend/models/proposta_pc.py`
```python
class PropostaPcEncargo(Base):
    __tablename__ = "proposta_pc_encargo"
    __table_args__ = (
        UniqueConstraint("proposta_id", "bcu_item_id", name="uq_proposta_pc_encargo"),
        {"schema": "operacional"},
    )
```

---

## Roteiro de Testes

### Teste 1: Importação de PQ funciona
```bash
1. Criar proposta A (Cliente X)
2. Criar proposta B (Cliente X)
3. Upload de PQ.xlsx em Proposta A
4. Verificar que apenas Proposta A tem itens importados
5. Verificar que Proposta B permanece vazia
```

### Teste 2: Match de itens gera sugestões
```bash
1. Com Proposta A tendo PQ importado
2. Chamar POST /api/v1/propostas/{A_id}/pq/match
3. Verificar resposta com estrutura: {"processados": N, "sugeridos": M, "sem_match": K}
4. Se receber 502, verificar logs em backend (agora terá stack trace completo)
```

### Teste 3: Histograma isolado por proposta
```bash
1. Com Proposta A tendo match confirmado
2. Chamar POST /api/v1/propostas/{A_id}/montar-histograma
3. Verificar GET /api/v1/propostas/{A_id}/histograma contém dados corretos
4. Verificar que GET /api/v1/propostas/{B_id}/histograma está VAZIO (não herda de A)
5. Repetir com Proposta B
```

### Teste 4: Regeneração de histograma limpa dados antigos
```bash
1. Montar histograma de Proposta A (gera X itens de Mão de Obra)
2. Verificar contagem: GET /api/v1/propostas/{A_id}/histograma mao_obra
3. Montar histograma novamente (deve gerar mesma estrutura)
4. Verificar que não há duplicatas (contagem = X, não 2X)
```

---

## Erro 401 (Unauthorized)

Este erro é **separado** do fluxo PQ e relacionado à expiração de token de autenticação no frontend.

**Solução de curto prazo**: Fazer login novamente no frontend

**Solução de longo prazo**: Implementar refresh de token automático no frontend

---

## Próximas Ações Recomendadas

1. **Executar testes acima** para confirmar correções
2. **Verificar logs** quando receber 502 (agora terá stack trace completo)
3. **Considerar migração de banco** se `PropostaPcEncargo` já tem dados históricos (pode quebrar constraint)
4. **Monitorar performance** do histograma com múltiplas propostas

---

## Resumo das Mudanças

| Arquivo | Mudança | Impacto |
|---------|---------|--------|
| `proposta_pc_repository.py` | +4 métodos clear_* | Evita dados compartilhados |
| `histograma_service.py` | DELETE antes de INSERT | Garante isolamento por proposta |
| `proposta_pc.py` | +UniqueConstraint | Consistency com outras tabelas |
| `pq_importacao.py` (endpoint) | +try/except +logging | Melhor debug de erros 502 |
