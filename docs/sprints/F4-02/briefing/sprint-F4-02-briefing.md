# Briefing — F4-02 PQ Client Profiles + Learning Loop

## Objetivo
Implementar perfis de importação de PQ por cliente para reaproveitar mapeamentos aprovados pelo usuário.

## Escopo
- Modelo/tabela para perfil de PQ por cliente, aliases de colunas, aba, linha de cabeçalho e regras aprovadas.
- Preview e aplicação de perfil no importador de PQ.
- Correção humana vira aprendizado controlado, nunca automático sem aprovação.
- Testes unitários e, se houver schema, migration Alembic segura.

## Critérios de aceite
- Cliente pode ter perfil de PQ persistido.
- Nova importação do mesmo cliente reutiliza perfil com confiança/preview.
- Importação fora do padrão não grava dados inválidos.

## Regras obrigatórias de execução
- Seguir estritamente o project-pipeline: briefing, plano, implementação, technical review, walkthrough, QA handoff.
- NÃO fazer push direto. Trabalhar em worktree isolada e entregar diff/commit local para consolidação.
- Pode instalar dependências locais necessárias para implementar/testar, preferindo venv local e sem tocar produção.
- Atenção total a Alembic/migrations: toda mudança de schema exige migration reversível, down_revision correto, teste/validação de upgrade, preocupação com dados existentes e unicidade.
- Banco protegido: leitura/importação pode ser flexível; gravação sempre validada, transacional e auditável.
- Não incluir segredos nem dados reais sensíveis em fixtures/docs.
- Atualizar documentação da sprint. README geral será atualizado ao final da Fase 4 consolidada.
