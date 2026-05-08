# F4-01 — Smart Import Architecture

## Objetivo
Projetar a camada **Smart Import** com leitura flexível e gravação rígida.

## Princípio central
**Entrada tolerante. Núcleo rigoroso. Banco protegido.**

## Decisão de produto
- PQ recebe inteligência pesada/adaptativa por cliente.
- Docling é candidato principal para interpretação de documentos variados.
- Pydantic/Pandas/OpenPyXL continuam como camada determinística de normalização/validação.
- BASES/BCUs internas seguem importação rígida/simples.
- TCPO recebe flexibilidade moderada, principalmente em hierarquia e cabeçalhos.

## Entregáveis
- Arquitetura de pipeline: parser flexível → normalizador → staging → validação rígida → confirmação humana → gravação transacional.
- Modelo de `ImportJob`/staging com score de confiança e auditoria por linha.
- Prova técnica com Docling em arquivos reais.
- Critérios para aceitar/rejeitar dados antes do banco.

## Segurança
- LLM/Docling não grava no banco.
- Toda gravação passa por schema Pydantic e transação.
- Campos ambíguos exigem revisão humana.
- Logs sem segredos e com rastreabilidade de arquivo/aba/linha/regra.
