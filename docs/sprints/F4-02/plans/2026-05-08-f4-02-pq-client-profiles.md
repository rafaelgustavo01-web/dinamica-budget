# F4-02 — PQ Client Profiles + Learning Loop

## Objetivo
Criar padronizações por cliente para importação de PQ.

## Escopo
- Detectar padrões por cliente: abas, linha de cabeçalho, aliases de colunas, unidades, campos ignoráveis.
- Salvar perfil aprovado pelo usuário.
- Reutilizar perfil nas próximas importações.
- Permitir correção humana virar aprendizado controlado.

## Fora do escopo
- Importação pesada de BASES/BCUs.
- CRUD completo de BASE.
- Alteração de regra de preço/custo sem aprovação humana.

## Aceite
- Uma PQ fora do padrão pode ser mapeada com preview.
- O mapeamento aprovado vira perfil do cliente.
- Nova PQ do mesmo cliente reaproveita perfil com score de confiança.
