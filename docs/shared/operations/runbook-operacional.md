# Runbook Operacional — Dinamica Budget

Este documento descreve os procedimentos de instalação, manutenção e resolução de problemas para o ambiente **On-Premise** do Dinamica Budget.

---

## 🚀 Instalação e Configuração

### 1. Pré-requisitos
- **SO:** Windows Server 2019+ ou Windows 10/11
- **DB:** PostgreSQL 15 ou 16 com extensão `pgvector`
- **Runtime:** Python 3.12+ e Node.js 20+
- **Processador:** Mínimo 4 cores (recomendado para embeddings locais)

### 2. Passos Iniciais
1. Clone o repositório ou descompacte o pacote de entrega.
2. Crie um ambiente virtual: `python -m venv .venv`
3. Ative e instale dependências: `.\.venv\Scripts\activate; pip install -r requirements.txt`
4. Configure o arquivo `.env` baseado no `.env.example`.
5. Execute as migrações: `alembic upgrade head`
6. Instale dependências do frontend: `cd frontend; npm install; npm run build`

### 3. Deploy via IIS (Windows)
- Utilize o **HttpPlatformHandler** ou **NSSM** para manter o `uvicorn` rodando como serviço.
- Aponte o site do IIS para a pasta `app/frontend/dist` para servir o conteúdo estático.

---

## 🛠️ Operações Diárias

### 1. Monitoramento de Saúde
Execute o script de diagnóstico periodicamente:
```powershell
powershell -File scripts/health-check.ps1
```

### 2. Backup do Banco de Dados
Recomendado executar via **Task Scheduler** diariamente:
```powershell
pg_dump -h localhost -U postgres -Fc dinamica_budget > C:\Backups\dinamica_budget_$(get-date -f yyyyMMdd).dump
```

### 3. Verificação de Logs
Os logs da aplicação ficam localizados na pasta raiz do projeto:
- `logs/app.log`: Erros de negócio e traços de execução.
- `logs/access.log`: Requisições HTTP (se configurado no uvicorn).

---

## 🔌 Troubleshooting (Resolução de Problemas)

| Problema | Causa Provável | Solução |
|:---|:---|:---|
| **Erro 500 no Login** | Banco de dados inacessível ou SECRET_KEY inválida. | Verifique se o serviço PostgreSQL está rodando e valide a string de conexão no `.env`. |
| **Busca Inteligente Lenta** | Falta de memória RAM para carregar o modelo de ML. | Garanta que o servidor tem pelo menos 4GB livres. Reinicie a aplicação para limpar o cache. |
| **Falha no Upload de Planilha** | Pasta temporária sem permissão de escrita. | Verifique as permissões de pasta do usuário que executa o uvicorn. |
| **Erro de CORS no Navegador** | `ALLOWED_ORIGINS` no .env não inclui o endereço de acesso. | Atualize o `.env` com o domínio correto (ex: `["http://orcamento.empresa.com"]`). |
| **Banco "Unhealthy"** | Pool de conexões esgotado. | Aumentar `DATABASE_POOL_SIZE` no `.env` ou verificar conexões presas no Postgres via `pg_stat_activity`. |

---

## 🔄 Procedimento de Restore (Recuperação)

Em caso de falha catastrófica ou migração de servidor:
1. Reinstale os pré-requisitos.
2. Crie um banco vazio: `CREATE DATABASE dinamica_budget;`
3. Restaure o dump: `pg_restore -h localhost -U postgres -d dinamica_budget caminho_do_backup.dump`
4. Re-aponte o `.env` e inicie os serviços.

