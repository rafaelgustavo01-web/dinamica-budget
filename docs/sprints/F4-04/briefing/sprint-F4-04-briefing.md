# Briefing — F4-04 Cadastro de Clientes para Folha PC

## Objetivo
Enriquecer cadastro de Clientes com dados necessários para Proposta Comercial/Folha PC, com UI limpa e sem IDs técnicos expostos.

## Escopo
- Campos empresariais/comerciais úteis para folha de rosto/PC.
- Backend schemas/endpoints/repositórios e migration Alembic se houver novos campos.
- Frontend UX com tips leves, labels amigáveis e validação.
- Preparar integração futura com exportação/folha de rosto, sem quebrar export atual.

## Critérios de aceite
- Cliente possui dados adicionais persistidos e editáveis.
- UI clara para cadastro/edição.
- Export/PC consegue consumir dados ou tem contrato documentado para próxima etapa.

## Regras obrigatórias de execução
- Seguir estritamente o project-pipeline: briefing, plano, implementação, technical review, walkthrough, QA handoff.
- NÃO fazer push direto. Trabalhar em worktree isolada e entregar diff/commit local para consolidação.
- Pode instalar dependências locais necessárias para implementar/testar, preferindo venv local e sem tocar produção.
- Atenção total a Alembic/migrations: toda mudança de schema exige migration reversível, down_revision correto, teste/validação de upgrade, preocupação com dados existentes e unicidade.
- Banco protegido: leitura/importação pode ser flexível; gravação sempre validada, transacional e auditável.
- Não incluir segredos nem dados reais sensíveis em fixtures/docs.
- Atualizar documentação da sprint. README geral será atualizado ao final da Fase 4 consolidada.
