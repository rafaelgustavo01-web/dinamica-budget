# Briefing — F4-03 BASES/BCUs Upload Individual + CRUD

## Objetivo
Permitir upload individual e manutenção CRUD das bases BASE/BCU internas, mantendo importação rígida, preview, validação forte e auditoria.

## Escopo
- Backend: endpoints/serviços para upload individual e CRUD de entidades BCU/BASE existentes.
- Frontend: telas/ações para upload individual, listagem, edição e validação amigável.
- Migration Alembic apenas se indispensável; preferir reuso do schema `bcu.*` existente.
- Testes unitários e build frontend.

## Critérios de aceite
- Upload individual por tabela/base com preview e erro claro.
- CRUD básico seguro e auditável.
- Nenhuma gravação sem validação rígida.

## Regras obrigatórias de execução
- Seguir estritamente o project-pipeline: briefing, plano, implementação, technical review, walkthrough, QA handoff.
- NÃO fazer push direto. Trabalhar em worktree isolada e entregar diff/commit local para consolidação.
- Pode instalar dependências locais necessárias para implementar/testar, preferindo venv local e sem tocar produção.
- Atenção total a Alembic/migrations: toda mudança de schema exige migration reversível, down_revision correto, teste/validação de upgrade, preocupação com dados existentes e unicidade.
- Banco protegido: leitura/importação pode ser flexível; gravação sempre validada, transacional e auditável.
- Não incluir segredos nem dados reais sensíveis em fixtures/docs.
- Atualizar documentação da sprint. README geral será atualizado ao final da Fase 4 consolidada.
