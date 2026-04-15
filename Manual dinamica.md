DINAMICA BUDGET
Sistema de Orçamentação para Construção Civil


Manual de Instalação e Deploy
Ambiente de Produção — Intranet


Servidor: Windows Server 2022 Standard


1. Visão Geral
Este manual descreve o procedimento completo de instalação do sistema Dinamica Budget em um servidor Windows Server 2022 Standard na rede intranet corporativa. O documento cobre desde a preparação do servidor até a validação final do sistema em operação.

1.1 Arquitetura da Solução
O Dinamica Budget é composto por três camadas principais:
•	Backend (API): FastAPI (Python 3.12) — motor de busca, RBAC, composições, homologação
•	Banco de Dados: PostgreSQL 16 com extensões pgvector (busca semântica) e pg_trgm (busca fuzzy)
•	Frontend (SPA): React 19 + TypeScript — build estático servido por IIS
•	Motor ML: Sentence Transformers (all-MiniLM-L6-v2) — execução local, sem internet

1.2 Requisitos do Servidor
Componente	Especificação Mínima	Servidor Alvo
Sistema Operacional	Windows Server 2019+	Windows Server 2022 Standard
Processador	4 cores x86_64	Intel E3-1225 v6 @ 3.30GHz (4C/4T)
Memória RAM	8 GB	16 GB
Disco	100 GB livres	900 GB SATA 7.200 RPM
Rede	1 Gbps Ethernet	Placa integrada

1.3 Softwares a Instalar
Software	Versão	Finalidade
Python	3.12.x	Runtime do backend FastAPI
PostgreSQL	16.x	Banco de dados principal
pgvector	0.7.x	Extensão de busca vetorial
Node.js	20 LTS ou 22 LTS	Build do frontend React
IIS	10.0 (nativo)	Servir frontend + reverse proxy
NSSM	2.24+	Gerenciar FastAPI como serviço Windows
URL Rewrite	2.1	Módulo IIS para reverse proxy
ARR	3.0	Application Request Routing para IIS

IMPORTANTE — Modelo de ML
O modelo all-MiniLM-L6-v2 (~90 MB) precisa ser baixado na primeira execução. Se o servidor não tiver acesso à internet, faça o download em outra máquina e copie a pasta ml_models/ para o servidor antes de iniciar a aplicação. Instruções na Seção 6.
 
2. Preparação do Servidor Windows
2.1 Configurar IP Fixo
O servidor precisa de um endereço IP fixo na rede intranet para que os usuários acessem a aplicação sempre pelo mesmo endereço.
1.	Abrir o Painel de Controle > Rede e Internet > Central de Rede e Compartilhamento.
2.	Clicar em "Alterar as configurações do adaptador" no menu lateral esquerdo.
3.	Clicar com botão direito no adaptador de rede ativo > Propriedades.
4.	Selecionar "Protocolo IP Versão 4 (TCP/IPv4)" > Propriedades.
5.	Marcar "Usar o seguinte endereço IP" e preencher:

Campo	Exemplo	O que preencher
Endereço IP	192.168.1.100	IP fixo atribuído pela equipe de rede
Máscara de sub-rede	255.255.255.0	Máscara da sua rede local
Gateway padrão	192.168.1.1	IP do roteador/gateway da rede
DNS preferencial	192.168.1.1	IP do servidor DNS interno
DNS alternativo	8.8.8.8	DNS externo (se houver acesso internet)

6.	Clicar OK em todas as janelas para aplicar.
7.	Abrir o Prompt de Comando (cmd) e verificar:
ipconfig
ping 192.168.1.1

2.2 Configurar Nome do Servidor (Hostname)
Definir um nome amigável facilita o acesso pelos usuários.
8.	Abrir Configurações > Sistema > Sobre > Renomear este computador.
9.	Definir um nome como: SRVBUDGET (sem espaços, sem caracteres especiais).
10.	Reiniciar o servidor quando solicitado.

2.3 Registrar DNS na Rede (Solicitar ao Administrador de Rede)
Para que os usuários acessem o sistema por um nome amigável (ex: budget.empresa.local), solicite à equipe de infraestrutura/rede:

Solicitação para equipe de rede/infraestrutura
Criar registro DNS tipo A no servidor DNS interno:    Nome: budget.empresa.local    Tipo: A    Valor: 192.168.1.100 (IP fixo do servidor)  Se não houver servidor DNS interno, os usuários acessarão pelo IP diretamente: http://192.168.1.100

2.4 Configurar Firewall do Windows
O firewall precisa liberar as portas usadas pela aplicação. Abra o Windows Defender Firewall com Segurança Avançada.

Regra 1 — Porta 80 (HTTP — acesso dos usuários)
11.	No menu esquerdo, clicar em "Regras de Entrada".
12.	No menu direito, clicar em "Nova Regra...".
13.	Selecionar "Porta" > Avançar.
14.	Selecionar "TCP" e digitar: 80
15.	Selecionar "Permitir a conexão" > Avançar.
16.	Marcar os três perfis: Domínio, Particular, Público > Avançar.
17.	Nome: "Dinamica Budget HTTP" > Concluir.

Regra 2 — Porta 443 (HTTPS — se usar certificado SSL futuro)
Repetir o procedimento acima, mas para a porta 443. Nome: "Dinamica Budget HTTPS".

NOTA — Portas internas
As portas 8000 (FastAPI) e 5432 (PostgreSQL) NÃO devem ser abertas no firewall. O acesso a elas será feito internamente pelo IIS (reverse proxy). Isso protege o backend de acesso direto.
 
3. Instalação do PostgreSQL 16
3.1 Download e Instalação
18.	Acessar: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
19.	Baixar o instalador Windows x86-64 para PostgreSQL 16.x.
20.	Executar o instalador como Administrador.
21.	Na tela de componentes, marcar todos: PostgreSQL Server, pgAdmin 4, Stack Builder, Command Line Tools.
22.	Diretório de dados: manter o padrão (C:\Program Files\PostgreSQL\16\data) ou alterar para disco com mais espaço.
23.	Definir a senha do superusuário postgres. ANOTAR ESTA SENHA — ela será usada na configuração do .env.
24.	Porta: manter 5432 (padrão).
25.	Locale: Portuguese, Brazil (ou manter default).
26.	Concluir a instalação.

ANOTE ESTAS INFORMAÇÕES
Usuário: postgres Senha: (a que você definiu acima) Porta: 5432 Estas informações serão usadas na Seção 5 para configurar o arquivo .env.

3.2 Instalar Extensão pgvector
O pgvector habilita busca por similaridade semântica (vetorial) no banco de dados.
27.	Acessar: https://github.com/pgvector/pgvector/releases
28.	Baixar o arquivo .zip correspondente ao PostgreSQL 16 Windows.
29.	Extrair o conteúdo e copiar os arquivos para as pastas do PostgreSQL:
•	vector.dll → C:\Program Files\PostgreSQL\16\lib\
•	vector.control e vector--*.sql → C:\Program Files\PostgreSQL\16\share\extension\
30.	Reiniciar o serviço PostgreSQL:
net stop postgresql-x64-16
net start postgresql-x64-16

3.3 Criar o Banco de Dados
31.	Abrir o pgAdmin 4 (instalado junto com o PostgreSQL).
32.	Conectar ao servidor local (localhost:5432) com o usuário postgres.
33.	Clicar com botão direito em "Databases" > Create > Database.
34.	Nome do banco: dinamica_budget
35.	Owner: postgres
36.	Clicar em Save.

37.	Abrir o Query Tool (botão SQL no pgAdmin) e executar:
-- Habilitar extensões necessárias
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
 
-- Verificar se foram instaladas:
SELECT extname, extversion FROM pg_extension;

O resultado deve listar vector e pg_trgm na lista de extensões.
 
4. Instalação do Python 3.12
4.1 Download e Instalação
38.	Acessar: https://www.python.org/downloads/
39.	Baixar Python 3.12.x (Windows installer 64-bit).

CRÍTICO — Marcar estas opções durante a instalação
Na PRIMEIRA tela do instalador:    [x] Add python.exe to PATH   ← OBRIGATÓRIO    [x] Use admin privileges when installing py  Clicar em "Customize installation" e marcar:    [x] pip    [x] py launcher    [x] for all users

40.	Avançar e concluir a instalação.
41.	Abrir novo Prompt de Comando (cmd) e verificar:
python --version
# Esperado: Python 3.12.x
 
pip --version
# Esperado: pip 24.x from ...
 
5. Instalação do Node.js
O Node.js é necessário apenas para compilar o frontend. Após o build, ele não é mais usado.
42.	Acessar: https://nodejs.org/
43.	Baixar a versão LTS (20 ou 22) — Windows Installer (.msi) 64-bit.
44.	Executar o instalador com todas as opções padrão.
45.	Verificar a instalação:
node --version
# Esperado: v20.x.x ou v22.x.x
 
npm --version
# Esperado: 10.x.x
 
6. Deploy do Backend (FastAPI)
6.1 Copiar os Arquivos do Projeto
46.	Criar a pasta do projeto:
mkdir C:\DinamicaBudget
47.	Copiar TODOS os arquivos do repositório do projeto para C:\DinamicaBudget\
A estrutura deve ficar assim:
C:\DinamicaBudget\
  app\
  alembic\
  frontend\
  requirements.txt
  .env.example
  alembic.ini
  ...

6.2 Criar Ambiente Virtual Python
48.	Abrir o Prompt de Comando como Administrador.
49.	Navegar até a pasta do projeto e criar o ambiente virtual:
cd C:\DinamicaBudget
python -m venv venv
50.	Ativar o ambiente virtual:
venv\Scripts\activate
O prompt deve mudar para: (venv) C:\DinamicaBudget>

6.3 Instalar Dependências Python
51.	Com o ambiente virtual ativado, instalar as dependências:
pip install -r requirements.txt

NOTA — PyTorch CPU
O PyTorch será instalado na versão CPU-only (~800 MB de download). Isso é intencional — o servidor não precisa de GPU. A instalação pode levar 5-10 minutos dependendo da velocidade da internet.

6.4 Configurar o Arquivo .env
52.	Copiar o arquivo de exemplo:
copy .env.example .env
53.	Abrir o arquivo .env com o Bloco de Notas (ou outro editor de texto):
notepad .env
54.	Editar as seguintes variáveis (as demais podem ficar com os valores padrão):

Variável	O que colocar	Exemplo
DATABASE_URL	Dados de conexão ao PostgreSQL (trocar password pela senha do passo 3.1)	postgresql+asyncpg://postgres:SuaSenhaAqui@localhost:5432/dinamica_budget
SECRET_KEY	Chave secreta de 64 caracteres (ver passo seguinte)	(gerada automaticamente)
ALLOWED_ORIGINS	URLs do frontend que terão acesso	["http://budget.empresa.local","http://192.168.1.100"]
SENTENCE_TRANSFORMERS_HOME	Pasta local para cache do modelo ML	./ml_models
DEBUG	Manter false em produção	false
LOG_LEVEL	Nível de log	INFO

55.	Gerar a SECRET_KEY (executar no prompt com venv ativado):
python -c "import secrets; print(secrets.token_hex(32))"
 
# Exemplo de saída: a1b2c3d4e5f6...64 caracteres hexadecimais
# Copiar o resultado e colar no campo SECRET_KEY do .env

SEGURANÇA — SECRET_KEY
A SECRET_KEY protege todos os tokens JWT do sistema. NUNCA use o valor padrão em produção. NUNCA compartilhe esta chave. Se ela for comprometida, todos os tokens de autenticação ficam vulneráveis.

6.5 Preparar o Modelo de ML (Offline)
Se o servidor NÃO tem acesso à internet, siga este procedimento em uma máquina COM internet:
56.	Na máquina com internet, instalar as mesmas dependências Python.
57.	Executar o seguinte script para baixar o modelo:
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2',
    cache_folder='./ml_models')
print('Modelo baixado com sucesso')"
58.	Copiar toda a pasta ml_models/ para C:\DinamicaBudget\ml_models\ no servidor.

Se o servidor TEM acesso à internet, o modelo será baixado automaticamente na primeira execução.

6.6 Executar as Migrações do Banco de Dados
59.	Com o venv ativado, executar:
cd C:\DinamicaBudget
alembic upgrade head
Este comando cria todas as tabelas, índices e extensões necessárias no banco de dados.
60.	Verificar o resultado — deve exibir algo como:
INFO  [alembic.runtime.migration] Running upgrade  -> 001, create base tables
INFO  [alembic.runtime.migration] Running upgrade 001 -> 002, pgvector extension
...
INFO  [alembic.runtime.migration] Running upgrade 006 -> 007, fix defaults

6.7 Testar a API Manualmente
61.	Iniciar a API em modo de teste:
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
62.	Abrir o navegador no servidor e acessar: http://127.0.0.1:8000/health
Resposta esperada:
{ "status": "ok", "embedder_ready": true }
63.	Acessar a documentação interativa: http://127.0.0.1:8000/docs
64.	Se tudo funciona, parar a API com Ctrl+C.

Se embedder_ready estiver false
O modelo ML não foi carregado. Verifique se a pasta ml_models/ existe e contém os arquivos do modelo. Verifique os logs no terminal — erros de carregamento serão exibidos.
 
7. Configurar FastAPI como Serviço Windows
Para que a API inicie automaticamente quando o servidor ligar (e reinicie em caso de falha), vamos registrá-la como um serviço Windows usando o NSSM.

7.1 Instalar o NSSM
65.	Acessar: https://nssm.cc/download
66.	Baixar a versão mais recente (nssm-2.24.zip ou superior).
67.	Extrair o arquivo .zip.
68.	Copiar o nssm.exe (pasta win64) para C:\Windows\System32\ (facilita o uso no prompt).

7.2 Registrar o Serviço
69.	Abrir o Prompt de Comando como Administrador.
70.	Executar:
nssm install DinamicaBudgetAPI
71.	Na janela que abrir, preencher:

Campo	Valor
Path	C:\DinamicaBudget\venv\Scripts\python.exe
Startup directory	C:\DinamicaBudget
Arguments	-m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2

72.	Na aba "Details":
•	Display name: Dinamica Budget API
•	Description: FastAPI backend - sistema de orçamentação Dinamica Budget
•	Startup type: Automatic

73.	Na aba "I/O" (para logs):
•	Output (stdout): C:\DinamicaBudget\logs\stdout.log
•	Error (stderr): C:\DinamicaBudget\logs\stderr.log

74.	Criar a pasta de logs:
mkdir C:\DinamicaBudget\logs
75.	Clicar em "Install service".

7.3 Configurar Variáveis de Ambiente para o Serviço
76.	Executar no prompt:
nssm set DinamicaBudgetAPI AppEnvironmentExtra SENTENCE_TRANSFORMERS_HOME=C:\DinamicaBudget\ml_models

7.4 Iniciar e Verificar o Serviço
77.	Iniciar o serviço:
nssm start DinamicaBudgetAPI
78.	Verificar que está rodando:
nssm status DinamicaBudgetAPI
Esperado: SERVICE_RUNNING
79.	Testar: abrir http://127.0.0.1:8000/health no navegador.
 
8. Build do Frontend
8.1 Configurar URL da API
80.	Criar o arquivo de ambiente do frontend:
cd C:\DinamicaBudget\frontend
copy .env.example .env.production
81.	Editar o arquivo .env.production:
notepad .env.production
82.	Definir a URL da API (vazia, pois o IIS fará reverse proxy na mesma origem):
VITE_API_URL=

8.2 Instalar Dependências e Compilar
83.	No prompt, executar:
cd C:\DinamicaBudget\frontend
npm install
npm run build
O build gera uma pasta dist/ com os arquivos estáticos do frontend (HTML, CSS, JS).
84.	Verificar que a pasta foi criada:
dir C:\DinamicaBudget\frontend\dist
Deve conter: index.html, assets/ (com .js e .css).

8.3 Copiar Build para Pasta do IIS
85.	Criar a pasta do site no IIS:
mkdir C:\inetpub\DinamicaBudget
86.	Copiar os arquivos do build:
xcopy C:\DinamicaBudget\frontend\dist\* C:\inetpub\DinamicaBudget\ /E /Y
 
9. Configurar o IIS (Servidor Web)
9.1 Habilitar o IIS no Windows Server
87.	Abrir o Server Manager (Gerenciador do Servidor).
88.	Clicar em "Manage" > "Add Roles and Features" (Adicionar Funções e Recursos).
89.	Avançar até "Server Roles" e marcar: Web Server (IIS).
90.	Em "Role Services", garantir que estão marcados:
•	Common HTTP Features > Default Document, Static Content
•	Health and Diagnostics > HTTP Logging
•	Performance > Static Content Compression
•	Security > Request Filtering
91.	Concluir a instalação.

9.2 Instalar Módulos de Reverse Proxy
Dois módulos são necessários para que o IIS encaminhe requisições /api/* para o FastAPI:

URL Rewrite
92.	Acessar: https://www.iis.net/downloads/microsoft/url-rewrite
93.	Baixar e instalar o URL Rewrite 2.1.

Application Request Routing (ARR)
94.	Acessar: https://www.iis.net/downloads/microsoft/application-request-routing
95.	Baixar e instalar o ARR 3.0.
96.	Após instalar ambos, reiniciar o IIS:
iisreset

9.3 Habilitar Proxy no ARR
97.	Abrir o IIS Manager (Gerenciador do IIS).
98.	Clicar no nome do servidor (nó raiz) na árvore à esquerda.
99.	Na área central, dar duplo clique em "Application Request Routing Cache".
100.	No painel direito, clicar em "Server Proxy Settings...".
101.	Marcar: [x] Enable proxy.
102.	Clicar em Apply.

9.4 Criar o Site no IIS
103.	No IIS Manager, expandir o servidor > clicar com botão direito em "Sites" > Add Website.
104.	Preencher:

Campo	Valor
Site name	DinamicaBudget
Physical path	C:\inetpub\DinamicaBudget
Binding > Type	http
Binding > IP address	All Unassigned
Binding > Port	80
Binding > Host name	budget.empresa.local (ou deixar vazio se usar IP direto)

105.	Clicar OK.
106.	Se o "Default Web Site" estiver ocupando a porta 80, pare-o ou altere sua porta:
Clicar com botão direito em "Default Web Site" > Manage Website > Stop.

9.5 Configurar Reverse Proxy (URL Rewrite)
Agora vamos configurar o IIS para encaminhar todas as requisições /api/* e /health para o FastAPI (porta 8000).
107.	Selecionar o site "DinamicaBudget" no IIS Manager.
108.	Dar duplo clique em "URL Rewrite".
109.	No painel direito, clicar em "Add Rule(s)..." > Blank Rule > OK.

Regra 1 — API Reverse Proxy
Campo	Valor
Name	API Reverse Proxy
Match URL > Pattern	^(api/.*|health|docs|redoc|openapi.json)(.*)$
Action > Action type	Rewrite
Action > Rewrite URL	http://127.0.0.1:8000/{R:0}
[x] Stop processing	Marcado

110.	Clicar em Apply.

Regra 2 — SPA Fallback (para React Router)
Como o frontend é uma Single Page Application (SPA), todas as rotas desconhecidas devem retornar o index.html:
111.	Adicionar nova regra:
Campo	Valor
Name	SPA Fallback
Match URL > Pattern	(.*)
Conditions > Logical grouping	Match All
Condition 1	{REQUEST_FILENAME} Is Not A File
Condition 2	{REQUEST_FILENAME} Is Not A Directory
Action > Action type	Rewrite
Action > Rewrite URL	/index.html

112.	Clicar em Apply.

ORDEM DAS REGRAS
A regra "API Reverse Proxy" DEVE estar ANTES da regra "SPA Fallback". Use as setas de prioridade no IIS para reordenar se necessário.

9.6 Alternativa — web.config Manual
Se preferir, crie diretamente o arquivo web.config em C:\inetpub\DinamicaBudget\:
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <rewrite>
      <rules>
        <rule name="API Reverse Proxy" stopProcessing="true">
          <match url="^(api/.*|health|docs|redoc|openapi.json)(.*)$" />
          <action type="Rewrite" url="http://127.0.0.1:8000/{R:0}" />
        </rule>
        <rule name="SPA Fallback" stopProcessing="true">
          <match url="(.*)" />
          <conditions>
            <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
            <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
          </conditions>
          <action type="Rewrite" url="/index.html" />
        </rule>
      </rules>
    </rewrite>
  </system.webServer>
</configuration>
 
10. Validação da Instalação
10.1 Checklist de Verificação
Execute cada teste abaixo a partir de uma estação de trabalho na rede (não no próprio servidor):

#	Teste	Como verificar	Resultado esperado
1	Health check API	Acessar http://budget.empresa.local/health	{ "status": "ok", "embedder_ready": true }
2	Documentação API	Acessar http://budget.empresa.local/docs	Swagger UI com todos os endpoints
3	Frontend carrega	Acessar http://budget.empresa.local	Tela de login do Dinamica Budget
4	Login funciona	Fazer login com usuário admin criado	Redireciona para o Dashboard
5	Busca funciona	Pesquisar um serviço TCPO	Resultados com scores e fases
6	PostgreSQL ativo	No servidor: nssm status postgresql-x64-16	SERVICE_RUNNING
7	FastAPI ativo	No servidor: nssm status DinamicaBudgetAPI	SERVICE_RUNNING
 
11. Cutover — Configurações Pós-Instalação
Após a instalação e validação técnica, siga os passos abaixo para colocar o sistema em operação.

11.1 Criar o Usuário Administrador
113.	Abrir a documentação interativa: http://budget.empresa.local/docs
114.	Localizar o endpoint POST /api/v1/auth/login — usar para testar.
115.	Como o sistema é novo e não tem usuários, é necessário criar o primeiro admin diretamente no banco.
116.	Abrir o pgAdmin 4 e conectar ao banco dinamica_budget.
117.	Executar o seguinte SQL para criar o hash da senha:

No prompt do servidor (com venv ativado):
python -c "
from passlib.hash import bcrypt
senha = input('Digite a senha do admin: ')
print('Hash:', bcrypt.hash(senha))"
 
# Copiar o hash gerado (começa com $2b$12$...)

118.	No pgAdmin, executar:
INSERT INTO usuarios (id, nome, email, senha_hash, is_active, is_admin)
VALUES (
  gen_random_uuid(),
  'Administrador',
  'admin@empresa.local',
  '$2b$12$...COLE_O_HASH_AQUI...',
  true,
  true
);

119.	Testar o login: acessar http://budget.empresa.local e fazer login com o email e senha definidos.

11.2 Importar Dados TCPO
O catálogo de serviços TCPO precisa ser populado no banco de dados. Os dados podem vir de um arquivo SQL, CSV ou script específico da sua base TCPO.
120.	Preparar o arquivo SQL ou CSV com os serviços TCPO.
121.	Importar via pgAdmin (Query Tool) ou script Python.
122.	Após importar, gerar os embeddings para busca semântica:

No Swagger (http://budget.empresa.local/docs):
•	Autenticar com o botão "Authorize" usando email/senha do admin
•	Executar: POST /api/v1/admin/compute-embeddings
Este processo pode levar alguns minutos dependendo da quantidade de serviços importados.

11.3 Criar Clientes
Cada empresa/departamento que usa o sistema deve ser cadastrado como um "Cliente".
123.	No Swagger, executar POST /api/v1/clientes/ com:
{
  "nome_fantasia": "Nome da Empresa",
  "cnpj": "12345678000190"
}
124.	Repetir para cada cliente.

11.4 Criar Usuários e Atribuir Perfis
125.	Criar usuários via POST /api/v1/auth/usuarios:
{
  "nome": "João Silva",
  "email": "joao@empresa.local",
  "password": "SenhaSegura123",
  "is_admin": false
}
126.	Vincular o usuário a um cliente com perfil via PUT /api/v1/usuarios/{id}/perfis-cliente:
{
  "cliente_id": "uuid-do-cliente",
  "perfis": ["USUARIO"]
}

Perfil	Pode fazer
USUARIO	Buscar serviços, criar itens próprios (PENDENTE), visualizar composições
APROVADOR	Tudo do USUARIO + aprovar/reprovar itens, clonar composições, excluir associações
ADMIN (is_admin)	Acesso total: criar usuários, clientes, serviços TCPO, compute embeddings
 
12. Manutenção e Operação
12.1 Logs
Os logs da aplicação ficam em:
•	Stdout: C:\DinamicaBudget\logs\stdout.log
•	Stderr: C:\DinamicaBudget\logs\stderr.log
•	IIS: C:\inetpub\logs\LogFiles\

12.2 Reiniciar a API
nssm restart DinamicaBudgetAPI

12.3 Atualizar a Aplicação
127.	Parar o serviço:
nssm stop DinamicaBudgetAPI
128.	Copiar os novos arquivos do projeto para C:\DinamicaBudget\ (substituir).
129.	Ativar o venv e instalar novas dependências (se houver):
cd C:\DinamicaBudget
venv\Scripts\activate
pip install -r requirements.txt
130.	Executar migrações de banco (se houver novas):
alembic upgrade head
131.	Recompilar o frontend (se houver alterações):
cd frontend
npm install
npm run build
xcopy dist\* C:\inetpub\DinamicaBudget\ /E /Y
132.	Reiniciar o serviço:
nssm start DinamicaBudgetAPI

12.4 Backup do Banco de Dados
Agendar backup diário via Agendador de Tarefas do Windows:
133.	Criar o script de backup:
REM C:\DinamicaBudget\scripts\backup.bat
@echo off
set PGPASSWORD=SuaSenhaPostgres
set BACKUP_DIR=C:\DinamicaBudget\backups
set FILENAME=%BACKUP_DIR%\dinamica_%date:~6,4%%date:~3,2%%date:~0,2%.sql
 
"C:\Program Files\PostgreSQL\16\bin\pg_dump" -U postgres -h localhost dinamica_budget > %FILENAME%
 
echo Backup salvo em %FILENAME%
134.	Abrir o Agendador de Tarefas (taskschd.msc).
135.	Criar Tarefa Básica > Nome: "Backup Dinamica Budget" > Diário > 02:00.
136.	Ação: Iniciar Programa > C:\DinamicaBudget\scripts\backup.bat.

12.5 Monitoramento de Saúde
O endpoint /health pode ser usado por ferramentas de monitoramento:
curl http://127.0.0.1:8000/health
 
# Resposta normal:
{ "status": "ok", "embedder_ready": true }
 
# Se embedder_ready = false:
# O modelo ML não está carregado. Reinicie o servico.
 
13. Resolução de Problemas
Sintoma	Causa Provável	Solução
Tela de login não carrega (ERR_CONNECTION_REFUSED)	IIS não está rodando ou porta 80 não está liberada no firewall	1. Verificar IIS: iisreset 2. Verificar firewall: porta 80 liberada 3. Verificar se o site está Started no IIS Manager
Login retorna erro 502 Bad Gateway	Serviço FastAPI não está rodando	1. Executar: nssm status DinamicaBudgetAPI 2. Se parado: nssm start DinamicaBudgetAPI 3. Verificar logs: C:\DinamicaBudget\logs\stderr.log
Erro "SECRET_KEY insegura" nos logs	O arquivo .env não tem uma SECRET_KEY válida	Gerar nova chave: python -c "import secrets; print(secrets.token_hex(32))" Colar no .env e reiniciar o servico
Busca semântica não funciona (só fuzzy retorna)	embedder_ready = false	1. Verificar se ml_models/ existe e contém o modelo 2. Reiniciar o servico: nssm restart DinamicaBudgetAPI 3. Verificar logs de erro no startup
Erro de conexão ao banco (OperationalError)	PostgreSQL parado ou dados de conexão errados no .env	1. Verificar PostgreSQL: net start postgresql-x64-16 2. Verificar DATABASE_URL no .env 3. Testar conexão via pgAdmin
Frontend mostra página em branco	Build do frontend não foi copiado ou web.config incorreto	1. Verificar C:\inetpub\DinamicaBudget\index.html existe 2. Verificar web.config (regras de rewrite) 3. Verificar console do navegador (F12)
Rotas como /composicoes retornam 404	Regra SPA Fallback não está configurada no IIS	Adicionar regra SPA Fallback no URL Rewrite (ver Seção 9.5)
Timeout ao importar muitos serviços TCPO	Compute-embeddings demora em grandes volumes	O processo é batch com paginação. Aguardar — pode levar 10-30 min para 50.000+ itens. Não interromper.


14. Diagrama de Fluxo de Rede

                                                        
  ESTAÇÕES DE TRABALHO           SERVIDOR (SRVBUDGET)   
  ════════════════════           ═════════════════════   
                                                        
  ┌──────────────┐               ┌─────────────────┐   
  │  Navegador   │──── HTTP ────►│   IIS (porta 80) │   
  │  do Usuário  │   porta 80    │                  │   
  │              │               │  /api/*  ──────► │──►┌─────────────────┐
  └──────────────┘               │  /health ──────► │   │  FastAPI        │
                                 │                  │   │  (porta 8000)   │
                                 │  /* (frontend)   │   │                 │
                                 │  serve index.html│   │  ┌───────────┐  │
                                 └─────────────────┘   │  │ ML Model  │  │
                                                        │  └───────────┘  │
                                                        │        │        │
                                                        └────────┼────────┘
                                                                 │         
                                                                 ▼         
                                                        ┌─────────────────┐
                                                        │  PostgreSQL 16   │
                                                        │  (porta 5432)    │
                                                        │  + pgvector      │
                                                        │  + pg_trgm       │
                                                        └─────────────────┘
                                                                           
  PORTAS ABERTAS NO FIREWALL: 80 (HTTP)                                    
  PORTAS INTERNAS (sem firewall): 8000, 5432                               


— Fim do Manual de Instalação —
