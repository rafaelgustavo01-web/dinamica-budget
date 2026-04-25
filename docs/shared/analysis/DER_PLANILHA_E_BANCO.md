# Mapa visual: Planilha x Banco

Objetivo: visualizar em um formato mais claro e rapido o modelo da planilha e o modelo do banco, no mesmo documento.

Fontes:
- Planilha: tabelas/PC tabelas.xlsx
- Banco: app/models e app/alembic/versions

---

## 1) Visao executiva (lado a lado)

```mermaid
flowchart LR
    subgraph P[Dominio da Planilha]
        P0[Arquivo Excel]
        P1[MAO DE OBRA]
        P2[EQUIPAMENTOS]
        P3[ENCARGOS]
        P4[EPI / UNIFORME]
        P5[FERRAMENTAS]
        P6[MOBILIZACAO]
        P0 --> P1
        P0 --> P2
        P0 --> P3
        P0 --> P4
        P0 --> P5
        P0 --> P6
    end

    subgraph B[Dominio do Banco]
        B0[CLIENTES]
        B1[USUARIOS]
        B2[SERVICO_TCPO]
        B3[VERSAO_COMPOSICAO]
        B4[COMPOSICAO_TCPO]
        B5[CATEGORIA_RECURSO]
        B6[ASSOCIACAO_INTELIGENTE]
        B7[HISTORICO / AUDITORIA]

        B0 --> B2
        B1 --> B2
        B2 --> B3
        B3 --> B4
        B5 --> B2
        B0 --> B6
        B2 --> B6
        B0 --> B7
        B1 --> B7
    end

    P1 -. ETL .-> B2
    P2 -. ETL .-> B2
    P5 -. ETL .-> B2
    P3 -. ETL com tabela de parametros .-> B5
    P4 -. ETL com despivotamento .-> B2
    P6 -. ETL com modelagem de rateio .-> B3

    X[Sem mapeamento direto coluna a coluna hoje]
    X --- P
    X --- B

    classDef plan fill:#E6F4FF,stroke:#2A6FB0,stroke-width:1px,color:#0D2A44;
    classDef banco fill:#EAF7E8,stroke:#2D7D46,stroke-width:1px,color:#11321B;
    classDef alerta fill:#FFF4E5,stroke:#CC7A00,stroke-width:1px,color:#5A3400;

    class P0,P1,P2,P3,P4,P5,P6 plan;
    class B0,B1,B2,B3,B4,B5,B6,B7 banco;
    class X alerta;
```

---

## 2) DER da planilha (focado no que existe no Excel)

```mermaid
erDiagram
    PLANILHA_ARQUIVO ||--o{ PLANILHA_ABA : contem

    PLANILHA_ARQUIVO {
        string arquivo_id PK
        string nome_arquivo
        datetime data_referencia
    }

    PLANILHA_ABA {
        string aba_id PK
        string arquivo_id FK
        string nome_aba
        int header_row
    }

    PLANILHA_ABA ||--o{ MO_ITEM : possui
    PLANILHA_ABA ||--o{ EQUIPAMENTO_ITEM : possui
    PLANILHA_ABA ||--o{ ENCARGO_ITEM : possui
    PLANILHA_ABA ||--o{ EPI_ITEM : possui
    PLANILHA_ABA ||--o{ FERRAMENTA_ITEM : possui
    PLANILHA_ABA ||--o{ MOBILIZACAO_ITEM : possui

    PLANILHA_ABA ||--o{ EQUIPAMENTO_PREMISSA : define
    EPI_ITEM ||--o{ EPI_DISTRIBUICAO_FUNCAO : distribui
    MOBILIZACAO_ITEM ||--o{ MOBILIZACAO_QUANTIDADE_FUNCAO : rateia

    MO_ITEM {
        string mo_item_id PK
        string aba_id FK
        string descricao_funcao
        decimal quantidade
        decimal salario
        decimal custo_unitario_h
        decimal custo_mensal
    }

    EQUIPAMENTO_PREMISSA {
        string premissa_id PK
        string aba_id FK
        decimal horas_mes
        decimal preco_gasolina_l
        decimal preco_diesel_l
    }

    EQUIPAMENTO_ITEM {
        string equipamento_item_id PK
        string aba_id FK
        string codigo
        string equipamento
        decimal consumo_l_h
        decimal aluguel_r_h
        decimal aluguel_mensal
    }

    ENCARGO_ITEM {
        string encargo_item_id PK
        string aba_id FK
        string tipo_encargo
        string grupo
        string discriminacao_encargo
        decimal taxa_percent
    }

    EPI_ITEM {
        string epi_item_id PK
        string aba_id FK
        string epi
        decimal custo_unitario
        decimal custo_epi_mes
    }

    EPI_DISTRIBUICAO_FUNCAO {
        string epi_dist_id PK
        string epi_item_id FK
        string funcao
        string aplica_flag
    }

    FERRAMENTA_ITEM {
        string ferramenta_item_id PK
        string aba_id FK
        string descricao
        string unidade
        decimal quantidade
        decimal preco_total
    }

    MOBILIZACAO_ITEM {
        string mobilizacao_item_id PK
        string aba_id FK
        string descricao
        string tipo_mao_obra
    }

    MOBILIZACAO_QUANTIDADE_FUNCAO {
        string mobilizacao_qtd_id PK
        string mobilizacao_item_id FK
        string coluna_funcao
        decimal quantidade
    }
```

---

## 3) DER do banco (focado em operacao da aplicacao)

```mermaid
erDiagram
    CLIENTES ||--o{ PERMISSAO_OPERACIONAL : possui
    USUARIOS ||--o{ PERMISSAO_OPERACIONAL : recebe

    CLIENTES ||--o{ SERVICO_TCPO : escopo
    CATEGORIA_RECURSO ||--o{ SERVICO_TCPO : classifica
    USUARIOS ||--o{ SERVICO_TCPO : aprova
    SERVICO_TCPO ||--|| TCPO_EMBEDDINGS : embedding

    SERVICO_TCPO ||--o{ VERSAO_COMPOSICAO : versiona
    VERSAO_COMPOSICAO ||--o{ COMPOSICAO_TCPO : contem
    SERVICO_TCPO ||--o{ COMPOSICAO_TCPO : pai
    SERVICO_TCPO ||--o{ COMPOSICAO_TCPO : filho

    CLIENTES ||--o{ ASSOCIACAO_INTELIGENTE : contexto
    SERVICO_TCPO ||--o{ ASSOCIACAO_INTELIGENTE : referencia

    CLIENTES ||--o{ HISTORICO_BUSCA_CLIENTE : historico
    USUARIOS ||--o{ HISTORICO_BUSCA_CLIENTE : usuario
    CLIENTES ||--o{ AUDITORIA_LOG : auditoria
    USUARIOS ||--o{ AUDITORIA_LOG : usuario

    CLIENTES {
        uuid id PK
        string nome_fantasia
        string cnpj UK
        bool is_active
    }

    USUARIOS {
        uuid id PK
        string email UK
        bool is_active
        bool is_admin
    }

    PERMISSAO_OPERACIONAL {
        uuid usuario_id PK, FK
        uuid cliente_id PK, FK
        string perfil PK
    }

    CATEGORIA_RECURSO {
        int id PK
        string descricao
        string tipo_custo
    }

    SERVICO_TCPO {
        uuid id PK
        uuid cliente_id FK NULL
        string codigo_origem
        text descricao
        string unidade_medida
        decimal custo_unitario
        int categoria_id FK NULL
        string origem
        string status_homologacao
        string tipo_recurso
    }

    VERSAO_COMPOSICAO {
        uuid id PK
        uuid servico_id FK
        int numero_versao
        uuid cliente_id FK NULL
        bool is_ativa
    }

    COMPOSICAO_TCPO {
        uuid id PK
        uuid servico_pai_id FK
        uuid insumo_filho_id FK
        decimal quantidade_consumo
        uuid versao_id FK
    }

    TCPO_EMBEDDINGS {
        uuid id PK, FK
        vector vetor
    }

    ASSOCIACAO_INTELIGENTE {
        uuid id PK
        uuid cliente_id FK
        uuid servico_tcpo_id FK
        int frequencia_uso
        string status_validacao
    }

    HISTORICO_BUSCA_CLIENTE {
        uuid id PK
        uuid cliente_id FK NULL
        uuid usuario_id FK NULL
        text texto_busca
    }

    AUDITORIA_LOG {
        uuid id PK
        string tabela
        string operacao
        uuid usuario_id FK NULL
        uuid cliente_id FK NULL
    }
```

---

## 4) Como ler rapido

- Azul: estrutura da planilha (analitica e matricial).
- Verde: estrutura do banco (transacional e versionada).
- Linhas pontilhadas: caminhos de ETL possiveis.
- Caixa laranja: alerta de que nao existe mapeamento direto 1:1 hoje.

