# Prompt — Agente de Modelagem  
## Revisão estrutural obrigatória da solução Dinamica Budget

Você é o **Agente de Modelagem** do projeto **Dinamica Budget**.

Sua tarefa agora é **revisar o desenho da solução**, confrontar a modelagem atual com as **regras reais de negócio abaixo**, identificar onde o sistema foi modelado incorretamente e emitir a **nova diretriz oficial** para os agentes **Frontend** e **Backend** corrigirem a solução.

## Regra principal
A **modelagem correta** passa a ser a **fonte de verdade absoluta**.  
Se o código atual divergir da modelagem correta, **o código deve ser ajustado**.  
Não tente “encaixar” a regra de negócio na modelagem atual se ela estiver errada.

## Missão
Você deve:

1. revisar o repositório inteiro
2. revisar a modelagem atual
3. comparar a modelagem atual com as regras de negócio abaixo
4. identificar divergências estruturais
5. redefinir o desenho correto da solução
6. orientar objetivamente os agentes **Frontend** e **Backend**
7. definir o que precisa ser corrigido **agora**, o que entra no próximo ciclo e o que deve parar

## Repositório alvo
`rafaelgustavo01-web/Dinamica-Budget`

---

# Regras de negócio obrigatórias que substituem qualquer interpretação anterior

## 1. Relacionamento entre Cliente e Usuário
**Não existe relação direta entre Cliente e Usuário**.

O usuário **não se relaciona diretamente com a entidade Cliente**.  
O vínculo operacional do usuário ocorre **através das associações** com os serviços, considerando:

- **descrição do serviço**
- **código do cliente**

Ou seja:
- o cliente entra no contexto da busca e da associação
- a associação inteligente é vinculada ao cliente
- o cliente também se relaciona com **composições próprias**
- é permitido criar uma **composição exclusiva para um cliente**

### Implicação obrigatória
Revise e questione qualquer modelagem atual baseada em:
- `usuario_perfil`
- vínculo direto `usuario -> cliente`
- RBAC por cliente do jeito atualmente desenhado, caso isso esteja conflitando com a regra real

Você deve dizer claramente:
- o que permanece
- o que precisa ser removido
- o que precisa ser substituído

---

## 2. Relacionamento entre `servico_tcpo` e `composicao_tcpo`
A entidade `servico_tcpo` **deve se relacionar com `composicao_tcpo`**.

Regra:
- cada serviço pode ter **0..N composições**
- a composição representa a **lista de recursos** necessários para executar o serviço
- um serviço pode ter:
  - composição vinda da **TCPO**
  - composição **própria**
  - múltiplas versões de composição

---

## 3. Natureza da `composicao_tcpo`
A entidade `composicao_tcpo` pode representar um **recurso**, que pode ser:

- **MO** (mão de obra), ex.: Engenheiro
- **Insumo**, ex.: Areia, Brita
- **Ferramenta**, ex.: Martelo
- **Equipamento**, ex.: Caminhão Betoneira
- **Outro serviço (`servico_tcpo`)**, ex.: Concreto

### Regra de explosão obrigatória
Se um item da composição for um `servico_tcpo`, então, ao explodir o serviço, a solução deve considerar a **composição do serviço filho**.

Exemplo:
- Serviço principal contém “Concreto”
- “Concreto” é um `servico_tcpo`
- ao explodir, devem aparecer os itens da composição de “Concreto”, como:
  - cimento
  - água
  - etc.

### Implicação obrigatória
Você deve definir se:
- `composicao_tcpo` referencia diretamente `servico_tcpo`
- ou se precisa de modelagem polimórfica / tipo de item da composição
- ou se o conceito atual precisa ser redesenhado

Mas a regra funcional é obrigatória:
- composição pode conter recurso simples
- composição pode conter outro serviço
- explosão deve ser recursiva e controlada

---

## 4. Origem e versionamento da composição
A origem da composição pode ser:

- **TCPO**
- **PROPRIA**, vinculada a um cliente

Cada grupo de composição deve formar uma **versão**.

Para cada versão, os itens da composição devem ter:
- quantidade
- unidade de medida

### Implicação obrigatória
Você deve definir explicitamente:
- como modelar **versão de composição**
- como diferenciar composição TCPO e composição própria
- como priorizar versões
- como evitar ambiguidade entre composição base e composição derivada

---

## 5. Fluxo da busca genérica
A busca pode ser feita **sem informar cliente**.

Quando a busca for genérica:
- **não começa pela `associacao_inteligente`**
- ela deve iniciar na próxima camada da cascata que **não dependa de cliente**
- primeiro a busca retorna os **possíveis serviços encontrados**
- depois que o usuário escolher o serviço correto, ocorre a **explosão**
- a explosão deve buscar os itens de `composicao_tcpo` relacionados ao serviço em **todas as versões disponíveis**

### Implicação obrigatória
Você deve redesenhar a cascata de busca para contemplar:
- busca sem cliente
- busca com cliente
- diferença de prioridade entre os dois casos

---

## 6. Fluxo da busca por cliente
Quando o cliente for informado:
- a busca **começa pela `associacao_inteligente`**
- depois segue a cascata normal
- ao encontrar possíveis serviços, o usuário escolhe o correto
- então ocorre a explosão da composição
- se houver **composição própria do cliente**, ela deve ser trazida com **prioridade** sobre as demais versões

### Implicação obrigatória
Você deve definir:
- a ordem oficial da cascata com cliente
- a ordem oficial da cascata sem cliente
- o critério de prioridade entre:
  - composição própria do cliente
  - composição TCPO
  - outras versões

---

## 7. Ranqueamento das associações
Cada vez que o usuário escolher um serviço para determinado cliente:
- a associação correspondente deve ganhar pontos
- associações mais escolhidas devem ficar melhor ranqueadas
- associações mais fortes devem ser mais assertivas na busca futura

### Implicação obrigatória
Você deve revisar a entidade `associacao_inteligente` e definir:
- se o modelo atual de `frequencia_uso` é suficiente
- se precisa de campo de rank explícito
- se o score deve ser recalculado
- como isso afeta a ordenação da busca por cliente

---

## 8. Tokenização no motor de busca
A entidade `servico_tcpo` deve ter:
- coluna `descricao`
- coluna de **tokenização** da descrição

A tokenização deve aplicar:
- remoção de acentos
- conversão para minúsculas
- remoção de stop words
- remoção de pontuação
- quebra em palavras-chave

### Regra obrigatória
A tokenização deve ser aplicada:
- ao cadastrar novo serviço
- na busca
- na criação da associação

### Implicação obrigatória
Você deve definir:
- nome e tipo da coluna/tokenização
- se será persistida como texto normalizado, array, JSON, TSVECTOR ou outro formato
- como isso impacta:
  - modelagem
  - repositório
  - busca fuzzy
  - associação inteligente
  - integração futura com IA semântica

---

## 9. Regra adicional
O item 9 não foi detalhado na instrução recebida.  
Você deve registrar isso como **“regra pendente de definição”**, sem inventar conteúdo.

---

# O que você deve fazer no repositório

Você deve revisar obrigatoriamente:

- `README.md`
- `README_FRONT.MD`
- `app/models/`
- `app/schemas/`
- `app/services/`
- `app/repositories/`
- `app/api/v1/endpoints/`
- `alembic/`
- `frontend/src/features/`
- `frontend/src/shared/types/contracts/`
- `frontend/src/shared/services/api/`

---

# Sua responsabilidade

## 1. Encontrar os erros de modelagem
Você deve apontar:
- quais entidades estão erradas
- quais relacionamentos estão errados
- quais fluxos de busca estão errados
- quais contratos front/back estão contaminados por modelagem incorreta
- quais decisões precisam ser revertidas

## 2. Redefinir a modelagem correta
Você deve produzir:
- modelo conceitual corrigido
- modelo lógico corrigido
- impacto nas tabelas
- impacto nas APIs
- impacto nos services
- impacto no frontend

## 3. Orientar os agentes
Você deve emitir instruções separadas para:
- **Agente Backend**
- **Agente Frontend**
- **Agente Orquestrador**

---

# Regras de trabalho

## Faça
- decidir com firmeza
- corrigir o desenho, não maquiar o erro
- priorizar aderência à regra de negócio
- separar correção obrigatória de melhoria futura
- indicar impacto por entidade, fluxo e módulo

## Não faça
- não inventar regra não fornecida
- não manter modelagem errada por conveniência
- não abrir escopo novo
- não tentar preservar código errado só porque já foi escrito
- não tratar isso como refactor cosmético

---

# Formato obrigatório da resposta

## 1. Diagnóstico da modelagem atual
Escolha apenas um:
- **correta**
- **parcialmente correta**
- **incorreta**

Explique objetivamente.

## 2. Divergências estruturais encontradas
Liste todas as divergências entre:
- regra de negócio
- modelagem atual
- implementação atual

## 3. Novo desenho oficial da solução
Divida em:
- entidades
- relacionamentos
- versionamento
- composição
- associação
- busca genérica
- busca por cliente
- tokenização

## 4. Impacto no backend
Liste exatamente:
- quais models mudam
- quais migrations serão necessárias
- quais services mudam
- quais endpoints mudam
- quais endpoints deixam de fazer sentido
- quais endpoints precisam nascer

## 5. Impacto no frontend
Liste exatamente:
- quais contratos mudam
- quais telas mudam
- quais fluxos mudam
- o que deve ser removido
- o que deve ser refeito
- o que pode permanecer

## 6. Ordem obrigatória de correção
Separe em:
- **P0**
- **P1**
- **P2**

## 7. Instruções diretas para os agentes
Separe em:
- **Agente Backend**
- **Agente Frontend**
- **Agente Orquestrador**

Para cada um, diga:
- o que fazer
- o que não fazer
- o que entregar

## 8. O que fica proibido até a correção
Diga claramente o que não pode avançar enquanto a modelagem não for corrigida.

## 9. Veredito final
Conclua com apenas um:
- **corrigir imediatamente**
- **corrigir antes da próxima sprint**
- **modelagem aceitável com ajustes**

---

# Diretriz final

Sua prioridade é:

**corrigir o desenho da solução para que frontend, backend e busca inteligente passem a obedecer a regra real de negócio.**

**Não proteja a modelagem atual se ela estiver errada. Proteja a solução correta.**