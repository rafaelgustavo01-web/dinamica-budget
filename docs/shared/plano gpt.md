# Plano de Melhoria Revisado — Módulo de Propostas do Dinamica Budget

## 1. Objetivo deste documento

Este documento revisa o plano anterior do módulo de Propostas do **Dinamica Budget** à luz das novas definições funcionais e arquiteturais estabelecidas:

1. **Cada proposta deve possuir uma CPU persistida e recuperável**, com todas as linhas de serviços vindas da PQ e suas composições explodidas, inclusive de forma recursiva quando necessário.
2. **Cada proposta precisa gerar listas consolidadas próprias** de equipamentos, ferramentas, mão de obra e insumos, derivadas da CPU.
3. **Os preços dessas listas devem poder ser alterados dentro da proposta**, sem alterar as tabelas globais de apoio.
4. **Uma mesma proposta deve possuir múltiplas versões**, e essas versões precisam ser consultáveis tanto na UI web quanto por integração externa (Excel / Power Query / API).
5. **O RBAC de propostas não deve ser centrado em cliente**, e sim em papéis por proposta: proprietário, editor, visualizador e, adicionalmente, comprador.
6. **Deve existir um mini módulo de compras**, capaz de alterar preços das listas consolidadas da proposta sem modificar a estrutura da CPU.

A revisão principal deste documento é a seguinte:

> **Não será adotada uma tabela separada `proposta_versoes` como primeira opção.**  
> A recomendação revisada é utilizar **uma única tabela de propostas tratada como tabela de versões**, onde **cada linha representa uma versão concreta e imutável da proposta**, agrupada por um identificador lógico comum.

Essa mudança reduz complexidade estrutural, simplifica integração externa e mantém aderência total aos requisitos de negócio, desde que a modelagem seja feita com rigor.

---

## 2. Diagnóstico do estado atual do repositório

O repositório já avançou bastante e possui uma base relevante para o módulo de propostas. Entre os elementos já existentes:

- Entidade `Proposta` com status, cliente, título, totais e código.
- Importação de PQ via upload de planilhas.
- `PqItem` e `PqImportacao` para ingestão dos itens quantitativos.
- `PqMatchService` para sugerir associação entre itens da PQ e o catálogo/base.
- `CpuGeracaoService` para reconstruir itens da proposta, explodir composições e calcular custos.
- `PropostaItem` e `PropostaItemComposicao` como snapshots parciais da estrutura de CPU.
- Frontend com listagem, criação, detalhe, importação e página placeholder para CPU.

Apesar disso, o desenho atual ainda apresenta limitações importantes:

### 2.1 Limitações estruturais

1. **A proposta ainda está sendo tratada como registro mutável principal**, e não como snapshot versionado.
2. **A CPU não está modelada de forma suficientemente hierárquica** para reconstituir a estrutura completa no Excel/Power Query com fidelidade.
3. **As listas consolidadas derivadas da CPU ainda não existem como entidades próprias persistidas**.
4. **Não existe separação formal entre custo global de referência e custo ajustado da proposta**.
5. **O RBAC continua orientado a cliente**, quando o requisito correto para propostas é orientado a proposta/papel de usuário.
6. **Não existe módulo de compras** para ajuste de preços derivados da proposta.
7. **Não existe estratégia formal de exposição tabular para integração analítica**, especialmente Power Query.

### 2.2 Risco se o projeto continuar sem corrigir essa modelagem

Se o time continuar evoluindo endpoints e telas sobre a modelagem atual sem corrigir a arquitetura central do versionamento e dos snapshots, os efeitos mais prováveis serão:

- sobrescrita de versões anteriores;
- dificuldade de rastrear histórico real;
- inconsistência entre dados da UI e do Excel;
- dificuldade de auditar ajustes de custos;
- acoplamento indevido entre tabelas globais e dados específicos da proposta;
- explosão de complexidade no backend quando o mini módulo de compras entrar.

Por isso, a revisão do plano precisa começar pela base do modelo de dados.

---

## 3. Diretriz revisada de modelagem: **uma tabela única de propostas versionadas**

### 3.1 Decisão arquitetural revisada

A recomendação revisada é **não criar inicialmente uma tabela separada `proposta_versoes`**.

Em vez disso, a solução deve tratar a tabela `propostas` como **tabela de versões físicas da proposta**, adotando o seguinte princípio:

> **Cada linha da tabela `propostas` representa uma versão concreta, fechada e identificável do orçamento.**

Isso significa que a tabela deixa de representar “a proposta abstrata” e passa a representar:

- proposta X versão 1
- proposta X versão 2
- proposta X versão 3

Todas essas versões coexistem como registros independentes.

### 3.2 Motivo da mudança

Essa abordagem foi escolhida porque:

1. **reduz a complexidade estrutural imediata**;
2. **facilita o consumo por Power Query / Excel**, pois cada versão já é um registro consultável diretamente;
3. **simplifica o relacionamento das listas e snapshots**, que podem apontar diretamente para o UUID da versão;
4. **evita duplicidade semântica entre “proposta” e “proposta_versao”**, que costuma gerar confusão operacional no time;
5. **mantém aderência funcional total**, desde que a tabela seja bem desenhada com identificador lógico de agrupamento.

### 3.3 Condição obrigatória para essa abordagem funcionar

Essa abordagem **só funciona corretamente** se o time adotar explicitamente dois níveis de identidade:

#### A. Identidade lógica da proposta
É o agrupador que diz que várias versões pertencem à mesma proposta comercial.

#### B. Identidade física da versão
É o UUID da linha concreta que representa uma revisão específica.

Sem essa separação conceitual, a tabela única vira apenas uma tabela mutável com um campo de versão — e isso não resolve o problema.

---

## 4. Nova modelagem recomendada para a tabela `propostas`

### 4.1 Papel da tabela

A tabela `propostas` passa a armazenar **versões**.

Cada linha será uma fotografia fechada da proposta naquele momento.

### 4.2 Campos recomendados

#### Identidade e agrupamento
- `id` UUID — identificador único da versão.
- `proposta_root_id` UUID — identificador lógico comum entre todas as versões da mesma proposta.
- `numero_versao` INTEGER — número sequencial da versão.
- `versao_anterior_id` UUID NULL — referência opcional à versão anterior.

#### Vínculo de negócio
- `cliente_id` UUID — cliente da proposta.
- `codigo_proposta` VARCHAR — código comercial reutilizável entre versões.
- `titulo` VARCHAR
- `descricao` TEXT

#### Estado da versão
- `status` ENUM / VARCHAR
- `is_versao_atual` BOOLEAN
- `is_fechada` BOOLEAN
- `motivo_revisao` TEXT NULL

#### Parâmetros de cálculo
- `bdi_percentual` NUMERIC
- `pc_cabecalho_id` UUID NULL

#### Totais da versão
- `total_direto` NUMERIC
- `total_indireto` NUMERIC
- `total_geral` NUMERIC
- `total_materiais` NUMERIC
- `total_mao_obra` NUMERIC
- `total_equipamentos` NUMERIC
- `total_ferramentas` NUMERIC

#### Auditoria
- `criado_por_id` UUID
- `created_at` TIMESTAMP
- `updated_at` TIMESTAMP

### 4.3 Constraints recomendadas

- `UNIQUE (proposta_root_id, numero_versao)`
- Index em `proposta_root_id`
- Index em `(proposta_root_id, is_versao_atual)`
- Index em `cliente_id`
- Index em `status`

### 4.4 Motivo técnico dessa modelagem

Essa modelagem resolve simultaneamente:

- agrupamento de histórico;
- recuperação de versões;
- relação direta das tabelas filhas com a versão concreta;
- simplificação das consultas para integração externa;
- controle de versão sem necessidade de tabela intermediária.

---

## 5. Estratégia de criação de nova versão

### 5.1 Regra recomendada

Versões fechadas **não devem ser sobrescritas estruturalmente**.

Mudanças relevantes devem gerar **nova linha em `propostas`**.

#### Mudanças que devem gerar nova versão
- nova importação de PQ;
- alteração manual relevante de match;
- regeneração da CPU;
- alteração aprovada de listas consolidadas;
- rodada formal de compras com impacto nos totais;
- revisão comercial relevante.

#### Mudanças que podem ser update da versão corrente
- metadados superficiais antes do fechamento;
- correções textuais ainda em rascunho;
- observações administrativas sem impacto no orçamento.

### 5.2 Motivo

Isso preserva histórico, evita perda de rastreabilidade e permite comparação real entre revisões.

---

## 6. Persistência da CPU como snapshot hierárquico e recursivo

### 6.1 Problema a resolver

A CPU da proposta precisa ser recuperável em estrutura semelhante a:

- Serviço 1 — quantidade 10
  - Materiais — unitário 2 — total 20
  - Mão de Obra — unitário 1 — total 10
  - Equipamentos — unitário 4 — total 40

Mas isso é apenas o nível visual resumido.  
Na prática, o banco precisa armazenar a árvore completa da composição, inclusive quando existirem subcomposições recursivas.

### 6.2 Proposta de modelagem

Recomenda-se separar a CPU em duas camadas persistidas:

#### 6.2.1 Tabela de serviços raiz da CPU
Sugestão: `proposta_cpu_servicos`

Campos:
- `id`
- `proposta_id` → aponta para a versão em `propostas`
- `pq_item_id`
- `ordem`
- `codigo_servico`
- `descricao_servico`
- `unidade_medida`
- `quantidade`
- `servico_origem_id`
- `servico_origem_tipo`
- `custo_direto_unitario`
- `custo_indireto_unitario`
- `preco_unitario`
- `preco_total`
- `composicao_fonte`

#### 6.2.2 Tabela de linhas da CPU explodida
Sugestão: `proposta_cpu_linhas`

Campos:
- `id`
- `proposta_id`
- `cpu_servico_id`
- `parent_linha_id` NULL
- `nivel`
- `ordem`
- `path_hierarquico`
- `tipo_linha` (`SERVICO`, `COMPOSICAO`, `INSUMO`)
- `tipo_recurso` (`MATERIAL`, `MO`, `EQUIPAMENTO`, `FERRAMENTA`, etc.)
- `item_global_id` NULL
- `item_proprio_id` NULL
- `descricao`
- `unidade_medida`
- `quantidade_consumo`
- `custo_unitario`
- `custo_total`
- `fonte_custo`
- `origem_snapshot`

### 6.3 Motivo dessa separação

A separação entre serviço raiz e linhas explodidas melhora:

- legibilidade do modelo;
- recuperação de dados para UI;
- recuperação tabular para Power Query;
- consolidação posterior das listas;
- auditoria da origem do cálculo.

### 6.4 Persistência recursiva obrigatória

O backend precisa salvar:

- o serviço raiz;
- todas as linhas derivadas da explosão;
- a relação pai-filho;
- o nível hierárquico;
- a ordem dentro da estrutura.

Sem isso, o Excel não conseguirá reconstruir a composição corretamente.

---

## 7. Listas consolidadas por versão da proposta

### 7.1 Objetivo

Cada proposta precisa possuir listas consolidadas próprias de:

- insumos;
- mão de obra;
- equipamentos;
- ferramentas.

Essas listas devem ser o **somatório das composições de todos os serviços da CPU daquela versão**.

### 7.2 Proposta de modelagem

#### 7.2.1 `proposta_lista_insumos`
- `id`
- `proposta_id`
- `codigo_referencia`
- `descricao`
- `unidade_medida`
- `quantidade_total`
- `custo_unitario_base`
- `custo_unitario_ajustado`
- `custo_total_base`
- `custo_total_ajustado`
- `origem_global_id` NULL
- `origem_proprio_id` NULL
- `fornecedor` NULL
- `observacao` NULL

#### 7.2.2 `proposta_lista_mao_obra`
Estrutura semelhante, com campos adicionais como categoria/função.

#### 7.2.3 `proposta_lista_equipamentos`
Estrutura semelhante, com campos de identificação do equipamento.

#### 7.2.4 `proposta_lista_ferramentas`
Estrutura semelhante.

### 7.3 Regra de negócio

Essas tabelas **não são espelhos das tabelas globais**.

Elas são **snapshots consolidados e editáveis da proposta**.

Ou seja:

- a tabela global fornece o custo base;
- a proposta gera sua lista;
- a lista da proposta vira entidade própria;
- ajustes nessa lista não retornam para a base global.

### 7.4 Motivo

Essa separação é indispensável porque o processo real de orçamento exige:

- cálculo técnico inicial;
- refinamento comercial;
- cotação específica;
- rastreamento de custo original versus custo ajustado.

Sem listas próprias por proposta, o sistema fica preso à base global e não suporta negociação.

---

## 8. Separação formal entre custo global e custo da proposta

### 8.1 Problema

Hoje, o custo de apoio tende a ser recuperado das tabelas corporativas e usado diretamente no cálculo.

Isso é insuficiente para o processo real porque o orçamento precisa conviver com dois universos:

#### Universo 1 — custo corporativo de referência
Vem das tabelas globais.

#### Universo 2 — custo efetivo daquela proposta
Vem das listas consolidadas e dos ajustes de compras.

### 8.2 Regra obrigatória

Cada linha consolidada da proposta deve guardar no mínimo:

- custo unitário base;
- custo unitário ajustado;
- custo total base;
- custo total ajustado;
- origem do preço;
- data da última atualização;
- usuário responsável pela alteração.

### 8.3 Motivo

Sem essa separação, o sistema não consegue:

- explicar divergências entre orçamento e base corporativa;
- mostrar economia ou aumento de custo;
- auditar decisões de compra;
- manter rastreabilidade entre engenharia e suprimentos.

---

## 9. Mini módulo de compras

### 9.1 Objetivo

Permitir que compradores atuem **sobre as listas consolidadas da proposta**, sem alterar a estrutura da CPU.

### 9.2 Regra funcional

Compras não muda:

- composição;
- quantidades técnicas;
- estrutura da CPU;
- match do serviço.

Compras muda apenas:

- custo ajustado;
- fornecedor;
- observação;
- eventual data de cotação;
- origem da cotação.

### 9.3 Proposta mínima de modelagem

Além dos campos nas listas, pode existir tabela complementar:

#### `proposta_compras_cotacoes`
- `id`
- `proposta_id`
- `tipo_lista`
- `lista_item_id`
- `fornecedor`
- `valor_unitario`
- `prazo_entrega`
- `condicao_pagamento`
- `observacao`
- `selecionada`
- `created_at`
- `created_by`

### 9.4 Motivo

Esse módulo viabiliza a participação de suprimentos no fluxo orçamentário sem corromper a engenharia da composição.

Também permite construir futuramente:

- mapa de cotações;
- histórico de negociação;
- comparativos por fornecedor.

---

## 10. RBAC revisado: acesso por proposta, não por cliente

### 10.1 Problema atual

O repositório atual está orientado a `require_cliente_access`, o que faz sentido para cadastros por cliente, mas não para o novo processo de propostas.

O requisito correto agora é:

- qualquer usuário pode atuar em propostas de qualquer cliente, conforme seu papel na proposta.

### 10.2 Proposta revisada

Não amarrar RBAC operacional da proposta ao cliente.

#### Tabela recomendada: `proposta_acl`
Campos:
- `id`
- `proposta_root_id`
- `usuario_id`
- `papel`

Papéis:
- `OWNER`
- `EDITOR`
- `VIEWER`
- `COMPRADOR`

### 10.3 Herança de permissão

A permissão deve ser aplicada ao `proposta_root_id`, não a cada versão isoladamente.

Isso significa:

- se o usuário é `EDITOR` da proposta root,
- ele é editor das versões dessa proposta.

### 10.4 Motivo

Se a permissão fosse por versão, o sistema ficaria difícil de administrar e cada nova revisão exigiria replicação de ACL.

A ACL por proposta lógica é mais consistente com o processo real.

---

## 11. APIs e integração com Excel / Power Query

### 11.1 Objetivo

A estrutura da proposta precisa ser consultável fora da UI, principalmente no Excel.

### 11.2 Estratégia

As APIs devem expor datasets tabulares ligados ao UUID da versão (`propostas.id`).

#### Endpoints recomendados
- `GET /propostas/{proposta_root_id}/versoes`
- `GET /propostas/{proposta_id}/cpu-servicos`
- `GET /propostas/{proposta_id}/cpu-linhas`
- `GET /propostas/{proposta_id}/lista-insumos`
- `GET /propostas/{proposta_id}/lista-mao-obra`
- `GET /propostas/{proposta_id}/lista-equipamentos`
- `GET /propostas/{proposta_id}/lista-ferramentas`
- `GET /propostas/{proposta_id}/resumo-financeiro`
- `GET /propostas/{proposta_id}/comparativo-base-vs-ajustado`

### 11.3 Motivo técnico

Essa separação em datasets tabulares simplifica:

- Power Query;
- relatórios gerenciais;
- exportações;
- auditorias;
- reconciliação financeira.

Uma API genérica de detalhe não é suficiente para analytics.

---

## 12. Ajustes necessários no backend atual

### 12.1 Refatorar o serviço de proposta
O serviço de proposta deve deixar de operar como entidade mutável e passar a operar com:

- criação de proposta root;
- criação de novas versões;
- marcação da versão atual;
- clonagem controlada de snapshots.

### 12.2 Refatorar `CpuGeracaoService`
O serviço atual já explode composições e calcula custos, mas precisa passar a:

1. operar em cima de uma versão específica;
2. gerar `cpu_servicos`;
3. gerar `cpu_linhas` hierárquicas;
4. consolidar listas;
5. recalcular totais por categoria;
6. salvar tudo como snapshot da versão.

### 12.3 Refatorar `PqMatchService`
O match precisa continuar funcionando, mas a persistência deve ficar associada à versão da proposta.

### 12.4 Adicionar serviços de consolidação
Novos serviços:
- `ListaConsolidacaoService`
- `ComprasService`
- `PropostaVersionamentoService`
- `PropostaAclService`

### 12.5 Motivo

Esses serviços deixam o domínio mais explícito e evitam colocar regras demais em um único service.

---

## 13. Ajustes necessários no frontend

### 13.1 Módulo de versões
A UI deve permitir:

- visualizar histórico da proposta;
- abrir versões antigas;
- criar nova versão a partir da atual;
- comparar versões.

### 13.2 Tela de CPU real
A página de CPU precisa deixar de ser placeholder e passar a mostrar:

- serviços raiz;
- expansão das composições;
- totais por serviço;
- origem de custo.

### 13.3 Módulo de listas consolidadas
Telas para:
- insumos;
- mão de obra;
- equipamentos;
- ferramentas.

### 13.4 Módulo de compras
Telas para:
- ajuste de preços;
- seleção de fornecedor;
- comparação base x ajustado.

### 13.5 Motivo

Sem isso, o backend continuará mais avançado que a operação real do usuário, gerando dependência excessiva de Excel ou consultas manuais.

---

## 14. Estratégia de implementação recomendada

### Fase 1 — base estrutural
1. Revisar a tabela `propostas` para suportar versão por linha.
2. Adicionar `proposta_root_id`, `numero_versao`, `versao_anterior_id`, `is_versao_atual`, `is_fechada`.
3. Criar ACL por proposta root.

### Fase 2 — CPU persistida corretamente
4. Criar `proposta_cpu_servicos`.
5. Criar `proposta_cpu_linhas`.
6. Refatorar geração de CPU para salvar árvore completa.

### Fase 3 — listas consolidadas
7. Criar tabelas de listas por tipo de recurso.
8. Criar serviço de consolidação.
9. Recalcular totais por categoria.

### Fase 4 — compras
10. Criar campos ajustados nas listas.
11. Criar cotação/compras.
12. Recalcular totais ajustados da proposta.

### Fase 5 — integração e UI
13. Expor endpoints analíticos.
14. Entregar UI de versões.
15. Entregar UI de CPU.
16. Entregar UI de compras e listas.

---

## 15. Conclusão revisada

A principal revisão deste plano é:

> **o versionamento pode e deve ser implementado sem tabela separada `proposta_versoes`, desde que a tabela `propostas` passe a representar versões concretas da proposta, agrupadas por `proposta_root_id`.**

Essa abordagem é tecnicamente sólida, mais simples para o time e melhor para integração externa.

Mas ela **não é apenas “colocar um campo de versão”**.  
Ela exige uma mudança conceitual completa:

- a proposta lógica passa a ser o agrupamento;
- a linha da tabela passa a ser a versão;
- CPU, listas e compras passam a apontar para o UUID da versão;
- ACL passa a apontar para o root da proposta;
- o custo da proposta deixa de depender diretamente da base global e passa a viver em snapshots próprios.

Com isso, o Dinamica Budget passa a ter uma base muito mais aderente ao fluxo real de orçamento, engenharia, compras e integração analítica.
