# Guia de Instalacao e Configuracao — Scouting BFSA

## Pre-requisitos

- **Node.js** 18+ (recomendado: 20 LTS)
- **Python** 3.10+
- **PostgreSQL** 14+ (ou SQLite para desenvolvimento local)
- **Git**

---

## 1. Clonar o Repositorio

```bash
git clone https://github.com/caiofelipead/scouting_bfsa_react.git
cd scouting_bfsa_react
```

---

## 2. Configurar o Backend

### 2.1. Criar ambiente virtual Python

```bash
cd backend
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 2.2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2.3. Configurar variaveis de ambiente

```bash
cp .env.example .env
```

Editar o arquivo `.env` com seus valores:

```env
# === OBRIGATORIAS ===

# Connection string PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/scouting_db

# Chave secreta para assinatura JWT (gerar uma string aleatoria de 64 caracteres)
JWT_SECRET_KEY=sua-chave-secreta-aleatoria-aqui

# Admin inicial (criado automaticamente no primeiro startup)
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=SenhaForte123!

# === OPCIONAIS ===

# Nome do admin
ADMIN_NAME=Administrador

# Tempo de expiracao do token em minutos (padrao: 480 = 8 horas)
TOKEN_EXPIRE_MINUTES=480

# Origens CORS permitidas (separadas por virgula)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Chave da API-Football (obter em api-football.com)
API_FOOTBALL_KEY=sua-chave-api-football

# Google Sheets (para sincronizacao de dados)
GOOGLE_SHEET_ID=id-da-sua-planilha
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"..."}
```

### 2.4. Criar banco de dados PostgreSQL

```bash
# Conectar ao PostgreSQL
psql -U postgres

# Criar banco
CREATE DATABASE scouting_db;
CREATE USER scouting_user WITH PASSWORD 'senha_segura';
GRANT ALL PRIVILEGES ON DATABASE scouting_db TO scouting_user;
\q
```

Atualizar `DATABASE_URL` no `.env`:
```
DATABASE_URL=postgresql://scouting_user:senha_segura@localhost:5432/scouting_db
```

> **Nota:** Para desenvolvimento rapido sem PostgreSQL, o sistema pode usar SQLite como fallback para autenticacao. Basta deixar `DATABASE_URL` vazio.

### 2.5. Iniciar o backend

```bash
uvicorn main:app --reload --port 8000
```

O servidor estara disponivel em:
- **API:** http://localhost:8000
- **Swagger (docs):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 3. Configurar o Frontend

### 3.1. Instalar dependencias

```bash
cd frontend
npm install
```

### 3.2. Iniciar servidor de desenvolvimento

```bash
npm run dev
```

O frontend estara disponivel em **http://localhost:5173**.

O Vite esta configurado com proxy reverso automatico:
- `/api/*` → `http://localhost:8000` (backend local)

> **Nota:** Nao e necessario configurar variaveis de ambiente no frontend para desenvolvimento local.

---

## 4. Acessar o Sistema

1. Abrir http://localhost:5173 no navegador
2. Fazer login com as credenciais do admin configuradas no `.env`:
   - Email: `admin@example.com`
   - Senha: `SenhaForte123!`

---

## 5. Deploy em Producao

### 5.1. Frontend (Vercel)

1. Conectar o repositorio no [Vercel](https://vercel.com)
2. Configurar:
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
3. O arquivo `vercel.json` ja esta configurado para proxy da API

### 5.2. Backend (Render)

1. Criar um **Web Service** no [Render](https://render.com)
2. Configurar:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Adicionar variaveis de ambiente no painel do Render
4. Criar um banco PostgreSQL no Render e copiar a connection string

### 5.3. Variaveis de Ambiente (Producao)

| Variavel | Obrigatoria | Onde |
|---|---|---|
| `DATABASE_URL` | Sim | Render |
| `JWT_SECRET_KEY` | Sim | Render |
| `ADMIN_EMAIL` | Sim | Render |
| `ADMIN_PASSWORD` | Sim | Render |
| `CORS_ORIGINS` | Sim | Render |
| `API_FOOTBALL_KEY` | Nao | Render |
| `GOOGLE_SHEET_ID` | Nao | Render |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Nao | Render |

---

## 6. Integracoes Opcionais

### 6.1. Google Sheets (Dados Wyscout)

Para acessar planilhas privadas:

1. Criar projeto no [Google Cloud Console](https://console.cloud.google.com)
2. Ativar a API Google Sheets
3. Criar uma Service Account
4. Baixar o JSON de credenciais
5. Compartilhar a planilha com o email da Service Account
6. Definir `GOOGLE_SERVICE_ACCOUNT_JSON` com o conteudo do JSON
7. Definir `GOOGLE_SHEET_ID` com o ID da planilha

> **Fallback:** Sem Service Account, o sistema usa export CSV publico (planilha deve estar publicada na web).

### 6.2. API-Football

1. Criar conta em [api-football.com](https://www.api-football.com)
2. Obter chave de API (tier gratuito: 100 chamadas/dia)
3. Definir `API_FOOTBALL_KEY` no `.env`

### 6.3. SkillCorner

Os dados do SkillCorner sao integrados via matching fuzzy de nomes com a base interna. Nao requer configuracao adicional alem dos dados ja presentes no sistema.

---

## 7. Executar Testes

### Frontend
```bash
cd frontend

# Executar todos os testes
npm run test

# Testes em modo watch
npm run test:watch

# Lint
npm run lint
```

### Backend
```bash
cd backend

# Executar testes
pytest

# Com cobertura
pytest --cov=.

# Teste especifico
pytest tests/test_auth.py -v
```

---

## 8. Resolucao de Problemas

### Backend nao inicia
- Verificar se PostgreSQL esta rodando: `pg_isready`
- Verificar `DATABASE_URL` no `.env`
- Verificar se `JWT_SECRET_KEY` esta definido

### Frontend nao conecta ao backend
- Verificar se backend esta rodando na porta 8000
- Verificar proxy em `vite.config.ts`
- Abrir DevTools → Network para ver erros de requisicao

### Erros 502/503/504 em producao
- Normal durante cold start do Render (free tier)
- O frontend tem retry automatico com backoff exponencial (ate 6 tentativas)
- Primeira requisicao pode levar ate 30-60s

### Token JWT expirado
- Frontend faz redirect automatico para login
- Aumentar `TOKEN_EXPIRE_MINUTES` se necessario

### Rate limit atingido
- Limite padrao: 300 req/min por IP
- Aguardar 1 minuto ou verificar se ha loop de requisicoes no frontend
