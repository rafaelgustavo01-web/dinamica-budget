# Briefing — F3-05 Hotfix PQ Match + TCPO Recursive Tree

## Contexto
Rafael testou a solução e encontrou dois bugs funcionais:
- Importação de PQ não libera o passo **2. Match Inteligente**.
- Catálogo TCPO mostra árvore, mas não explode recursivamente serviços compostos por outros serviços.

## Instrução operacional
Aplicar correções mínimas e validadas, preservando comportamento atual. Não incluir Smart Import/Docling nesta sprint; isso será tratado nas F4.

## Agentes consultados
- Claude: diagnóstico frontend/UX.
- Codex: diagnóstico/backend patch.
- Kimi: hardening e riscos.
- Gemini: estratégia de inteligência/Smart Import.
