# Dinamica Budget — Guia do Smart Import para Usuários

> Documento explicativo para usuários não-técnicos
> Data: 2026-05-18

---

## 1. O que é o Smart Import?

O **Smart Import** é a ferramenta que permite você enviar uma planilha de quantitativos (PQ) e o sistema automaticamente:

1. **Lê** a planilha
2. **Identifica** os itens de obra
3. **Procura** no catálogo os serviços correspondentes
4. **Sugere** matches para você confirmar

---

## 2. Como Funciona a Busca?

Quando o sistema procura um item no catálogo, ele usa um **motor de busca em camadas** (como uma busca em vários andares de um prédio):

### Andar 1 — Código Exato
- O sistema primeiro verifica se você digitou um código que existe no catálogo
- Se encontrar, retorna imediatamente (100% de acerto)

### Andar 2 — Itens do Seu Cliente
- Procura em itens que já foram cadastrados especificamente para o seu cliente
- Só mostra itens já aprovados

### Andar 3 — Associações Inteligentes
- O sistema "lembra" de matches anteriores que você confirmou
- Se você já disse que "Concreto Fck 25" = item X, ele sugere item X automaticamente
- Quanto mais você usa, mais ele aprende

### Andar 4 — Busca por Semelhança (IA)
- Usa inteligência artificial para encontrar itens com descrições similares
- Funciona mesmo quando o texto não é igual

### Andar 5 — Busca Fuzzy (Último Recurso)
- Se nada funcionar, faz uma busca mais ampla e tolerante
- Aceita erros de digitação e variações

---

## 3. Por que Alguns Itens Não Encontram Match?

### 3.1 Serviços TCPO

Serviços de obra (mão de obra, concreto, alvenaria, etc.) geralmente são encontrados porque:
- Existem no catálogo base TCPO
- São bem descritos
- Outros usuários já fizeram matches similares

### 3.2 Equipamentos, Ferramentas e Insumos

Itens como:
- **Equipamentos**: betoneira, compactador, andaime...
- **Ferramentas**: martelo, nível, trena...
- **Insumos**: cimento, areia, brita...

**Podem não ser encontrados** porque:
1. O catálogo principal é de **serviços**, não de materiais/equipamentos
2. A descrição na planilha pode ser muito diferente do catálogo
3. O sistema ainda não "aprendeu" que tipo de item é esse

### 3.3 O que Fazer Quando Não Encontra?

Quando um item fica como **"Pendente"** ou **"Sem Match"**, você pode:

1. **Buscar manualmente**: clique no item e digite uma descrição mais curta/simples
2. **Criar item próprio**: se o item não existe no catálogo, cadastre para seu cliente
3. **Confirmar similar**: se apareceu uma sugestão "próxima", confirme e o sistema aprende

---

## 4. Como Melhorar o Match?

### 4.1 Prepare Bem a Planilha

✅ **Faça:**
- Use cabeçalhos claros: "Descrição", "Unidade", "Quantidade"
- Descreva itens de forma completa: "Concreto usinado Fck 25 MPa" em vez de só "Concreto"
- Use unidades padrão: m², m³, kg, un, etc.
- Separe bem os capítulos/títulos das linhas de item

❌ **Evite:**
- Abreviações muito curtas: "Conc." em vez de "Concreto"
- Descrições genéricas: "Mão de obra" em vez de "Pedreiro para alvenaria"
- Misturar serviço e material na mesma descrição
- Deixar células de quantidade ou unidade em branco

### 4.2 Use Códigos Quando Possível

Se você souber o código do item no catálogo, coloque na coluna de código:
- O sistema encontra **imediatamente** por código
- É o match mais preciso possível

### 4.3 Confirme Matches Corretos

Quando o sistema sugere algo certo:
- **Confirme** — isso ensina o sistema que aquela descrição = aquele item
- Depois de 3 confirmações, o match vira automático!

### 4.4 Corrija Matches Errados

Se o sistema sugeriu algo errado:
- **Rejeite** — isso evita que ele sugira de novo
- Busque o item correto manualmente
- Confirme o correto

---

## 5. Configurações do Sistema

### 5.1 Threshold (Limiar de Confiança)

O sistema só sugere um match se tiver confiança mínima de **55%**.

Se você quer mais precisão (menos sugestões, mas mais certeiras), pode pedir para aumentar.
Se você quer mais sugestões (mesmo arriscando erros), pode pedir para diminuir.

### 5.2 Quantidade de Resultados

Por padrão, o sistema mostra até **10 sugestões** por item.
Você pode pedir para mostrar mais ou menos.

### 5.3 Perfis de Importação

Se você sempre importa planilhas do mesmo formato (mesmo cliente, mesma estrutura), o sistema pode **aprender o padrão**:
- Qual linha é o cabeçalho
- Quais colunas correspondem a quais campos
- Isso evita erros de mapeamento

---

## 6. Fluxo de Status dos Itens

```
PENDENTE     → Item importado, aguardando match
   ↓
BUSCANDO    → Sistema está procurando no catálogo
   ↓
SUGERIDO    → Sistema encontrou algo (aguardando sua confirmação)
   ↓
CONFIRMADO  → Você confirmou o match (vai para a proposta)
   ↓
MANUAL      → Você fez match manualmente
   ↓
SEM MATCH   → Sistema não encontrou nada (você precisa criar/cadastrar)
```

---

## 7. Dicas Avançadas

### 7.1 Itens de Equipamento

Para itens como betoneira, martelete, andaime:
- Descreva incluindo a função: "Locação de betoneira 400L"
- Use unidade "h" (hora) ou "d" (dia) para equipamentos
- Se não encontrar, considere criar como "item próprio" do cliente

### 7.2 Itens de Insumo

Para materiais como cimento, areia, aço:
- Inclua especificações: "Cimento Portland CPII-32,5 50kg"
- O sistema pode não encontrar insumos no catálogo de serviços
- Use a função de "item próprio" para materiais específicos

### 7.3 Capítulos e Seções

O sistema automaticamente ignora linhas que são:
- Títulos de capítulo: "CAPÍTULO 1 — FUNDAÇÃO"
- Subtotais: "TOTAL DO CAPÍTULO"
- Linhas em branco

Se um título de capítulo foi identificado como item por engano:
- Delete-o ou marque como seção

---

## 8. Glossário

| Termo | Significado |
|-------|-------------|
| **PQ** | Planilha de Quantitativos — lista de itens de obra com quantidades |
| **Match** | Associação entre um item da PQ e um item do catálogo |
| **Threshold** | Limiar mínimo de confiança para sugerir um match |
| **TCPO** | Tabela de Composição de Preços de Obra — catálogo de serviços |
| **Item Próprio** | Item cadastrado especificamente para um cliente |
| **Associação** | Link aprendido entre uma descrição e um item do catálogo |
| **Fuzzy** | Busca tolerante a erros de digitação |
| **Embedding** | Representação numérica de texto para busca por semelhança |

---

*Documento gerado em 2026-05-18. Para dúvidas técnicas, consulte o documento técnico.*
