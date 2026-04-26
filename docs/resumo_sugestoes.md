# Resumo das Sugestões — Dinamica Budget

## Contexto consolidado

Com base na proposta comercial e no documento técnico inicial, o escopo originalmente pensado para a solução tinha três pilares:

1. **Data Center corporativo**
   - Base TCPO centralizada
   - Cadastro de clientes
   - Serviços específicos por cliente
   - Associações inteligentes por cliente
   - Histórico de orçamentos

2. **Interface de orçamento**
   - Busca inteligente de composições
   - Explosão automática de CPU
   - Folha de rosto da proposta
   - Automação de histograma baseada em cronograma e CPU

3. **Motores de inteligência**
   - Motor de associação por cliente
   - Busca fuzzy / similaridade textual

---

## Síntese das sugestões

## 1. Reforçar o modelo de domínio centrado em cliente

A relação principal do sistema deve ficar explícita no domínio:

- **Propostas comerciais** pertencem a um cliente
- **Itens próprios** pertencem a um cliente
- **Associações inteligentes** pertencem a um cliente
- Cada cliente deve possuir seu próprio conjunto de dados relevantes

### Sugestão prática
Formalizar isso no modelo principal do sistema e na documentação funcional, para evitar ambiguidades futuras.

---

## 2. Criar o módulo de Propostas Comerciais como entidade de primeira classe

Hoje esse ponto precisa existir como módulo próprio, e não apenas como consequência da busca ou da CPU.

### Sugestão prática
Implementar:

- `propostas` / `orcamentos` como entidade principal
- vínculo obrigatório com `cliente_id`
- cabeçalho da proposta
- dados específicos da proposta
- responsável, data, status e valor total
- itens da proposta vinculados à proposta

### Resultado esperado
O sistema passa a refletir melhor o processo comercial real.

---

## 3. Separar corretamente os domínios de dados

O projeto original sugere domínios diferentes que não devem ficar misturados:

- catálogo global de referência (TCPO)
- dados próprios do cliente
- associações inteligentes
- propostas/orçamentos
- composições e recursos operacionais

### Sugestão prática
Revisar o modelo de dados para garantir separação clara entre:

- **referência global**
- **dados customizados por cliente**
- **dados transacionais da proposta**

---

## 4. Completar o escopo funcional originalmente prometido

Pelos documentos iniciais, ainda faltam blocos importantes para aderir ao que foi proposto.

### Itens a priorizar
- módulo de propostas/orçamentos
- folha de rosto da proposta
- tabela de aplicabilidade
- CPU a partir dos itens da PQ
- automação de histograma
- cálculo de recursos por serviço
- cálculo total da CPU
- definição de prazo por recursos
- definição de recursos por prazo
- relatórios operacionais e executivos
- histórico consolidado de orçamentos

---

## 5. Decidir oficialmente a estratégia de interface

Os documentos iniciais propõem **Excel + VBA + Power Query** como interface.  
A aplicação atual evoluiu para uma abordagem web.

### Sugestão prática
O time precisa decidir e documentar oficialmente uma destas opções:

### Opção A — manter a estratégia web como oficial
Nesse caso, adaptar formalmente o escopo original para web e abandonar a dependência conceitual do Excel.

### Opção B — manter integração híbrida
Nesse caso, definir claramente:
- o que fica na aplicação web
- o que continua no Excel
- como ocorre a integração entre ambos

### Recomendação
Evitar zona cinzenta arquitetural. A decisão precisa constar em documentação oficial.

---

## 6. Ampliar o Data Center além de cliente + serviço

A proposta inicial fala em tabelas específicas para apoio operacional.

### Sugestão prática
Planejar backlog para incluir, quando fizer sentido de negócio:

- mão de obra
- equipamentos
- encargos
- EPI / uniforme
- ferramentas
- mobilização
- tabelas auxiliares de composição e produtividade

Isso é importante principalmente se a proposta comercial exigir cálculo avançado de histograma, curva e recursos.

---

## 7. Evoluir o sistema para ciclo completo de orçamento

Hoje a inteligência de busca resolve apenas parte do problema. O escopo original é maior.

### Sugestão prática
Organizar a evolução em fluxo fim a fim:

1. cliente
2. proposta
3. itens da proposta
4. busca/associação
5. composição/CPU
6. recursos
7. cronograma
8. histograma
9. relatórios
10. emissão final

---

## 8. Priorizar backlog por valor de negócio

### Prioridade alta
- propostas comerciais por cliente
- itens da proposta
- folha de rosto
- dados específicos da proposta
- persistência completa do orçamento

### Prioridade média
- tabela de aplicabilidade
- histórico consolidado
- CRUD ampliado do Data Center
- integrações externas e migração de dados

### Prioridade evolutiva
- histograma
- cronograma
- relatórios avançados
- curvas e análises gerenciais

---

## 9. Revisar a documentação oficial do projeto

Atualmente existe risco de desalinhamento entre:
- escopo vendido
- arquitetura inicialmente pensada
- solução efetivamente implementada

### Sugestão prática
Criar um documento oficial de alinhamento com três colunas:

- **Escopo original**
- **Implementado hoje**
- **Pendente / replanejado**

Isso reduz ruído com time, cliente e implantação.

---

## 10. Recomendações objetivas para o próximo ciclo

### Recomendação 1
Formalizar o domínio:
- cliente
- proposta
- item da proposta
- item próprio
- associação

### Recomendação 2
Entregar o módulo de proposta comercial ponta a ponta.

### Recomendação 3
Definir oficialmente se o produto final será:
- web
- Excel
- híbrido

### Recomendação 4
Replanejar o backlog conforme o escopo vendido, para não deixar itens críticos fora da entrega percebida.

---

## Resumo executivo

A principal sugestão é **reposicionar o sistema em torno do cliente e da proposta comercial**, porque esse é o vínculo central do processo de negócio.

Hoje a solução já cobre bem:
- cliente
- item próprio
- associação inteligente
- busca

Mas, para aderir melhor ao escopo original, ainda precisa evoluir principalmente em:
- **propostas comerciais**
- **estrutura completa do orçamento**
- **histograma / cronograma**
- **relatórios e consolidação operacional**
- **clareza arquitetural entre web e Excel**

