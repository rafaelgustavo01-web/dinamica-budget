# Walkthrough — F2-10: BCU Unificada + De/Para

**Data:** 2026-04-27  
**Sprint:** F2-10  
**Status:** TESTED

## Objetivo

Consolidar a base global de custos em um único schema `bcu.*`, eliminando o legado `pc_*` e os pipelines duplicados (Converter ETL + Carga inteligente PC). Implementar mapeamento explícito De/Para entre o catálogo TCPO e a BCU.

## O que mudou para o usuário

### 1. Upload unificado
- **Antes:** três uploads separados (TCPO, Converter, PC Tabelas).
- **Depois:** dois uploads (TCPO e BCU). A planilha "Converter em Data Center.xlsx" foi descontinuada.

### 2. Tela BCU
- **Antes:** `/pc-tabelas` mostrava dados da planilha PC.
- **Depois:** `/bcu` mostra a Base de Custos Unitários com 7 abas (Mão de Obra, Equipamentos, Encargos Horista/Mensalista, EPI, Ferramentas, Mobilização).
- Cabeçalhos múltiplos suportados; o ativo é destacado com badge "Base ativa".

### 3. Mapeamento De/Para (novo)
- Nova rota `/bcu/de-para` acessível via menu "De/Para BCU" (apenas admins).
- Permite vincular cada item do catálogo TCPO a um item correspondente na BCU.
- Validação de tipo: não é possível mapear um TCPO do tipo "EQUIPAMENTO" para um item de "Mão de Obra" na BCU.
- Cada item TCPO pode ter no máximo 1 mapeamento (1:1).

### 4. Cálculo de custos na CPU
- **Antes:** heurística baseada em nome/descrição.
- **Depois:** lookup direto pelo De/Para. Se não houver mapeamento, usa o custo base do catálogo TCPO com warning no log.

## Como usar

### Importar uma BCU
1. Acesse **Governança → Upload**.
2. Na seção "BCU", selecione o arquivo `.xlsx` com as 7 abas.
3. Clique em "Importar BCU".
4. Após importar, ative o cabeçalho desejado via endpoint ou futura UI de ativação.

### Criar um mapeamento De/Para
1. Acesse **Operação → De/Para BCU**.
2. Use o filtro "Mostrar não mapeados" para ver itens TCPO sem vínculo.
3. Clique em "Novo Mapeamento" (ou edite um existente).
4. Informe o ID do item TCPO, o tipo BCU (MO/EQP/EPI/FER) e o ID do item na BCU.
5. Salve. O sistema valida coerência de tipo e existência do item.

## Verificação técnica rápida

```bash
# Migration aplicada
alembic upgrade head

# Schema bcu existe com 11 tabelas
psql -c "\dt bcu.*"

# Schema public não tem mais pc_*
psql -c "\dt public.pc_*"  # deve retornar vazio

# pytest
pytest backend/tests/unit/test_bcu_service.py backend/tests/unit/test_bcu_de_para_service.py -v

# TypeScript
cd app/frontend && npx tsc --noEmit
```

## Decisões de produto

- **Encargos e Mobilização não entram no De/Para:** são valores globais aplicados em fórmulas (percentual sobre folha, exames por função). Não são itens de catálogo.
- **De/Para é manual:** sugestões por similaridade (IA) ficam fora do escopo desta sprint.
- **Reset do banco autorizado:** sem dados legados em produção; `bcu.*` nasce vazio.
