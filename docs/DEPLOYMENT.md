# Guia de Deploy — Scouting BFSA

## Arquitetura de Deploy

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Vercel     │  /api/* │   Render     │         │ PostgreSQL  │
│  (Frontend)  │────────→│  (Backend)   │────────→│  (Database)  │
│  React SPA   │         │  FastAPI     │         │             │
└─────────────┘         └─────────────┘         └─────────────┘
       │                        │
       │                        ├── Google Sheets API
       │                        ├── API-Football v3
       │                        └── SkillCorner (dados)
       │
       ├── Vercel Analytics
       └── Vercel Speed Insights
```

---

## Frontend — Vercel

### Configuracao

**Framework:** Vite (React + TypeScript)
**Root Directory:** `frontend`
**Build Command:** `npm run build`
**Output Directory:** `dist`

### Proxy Reverso (vercel.json)

```json
{
  "rewrites": [
    { "source": "/api/team-logo/:path*",   "destination": "https://scouting-bfsa-react.onrender.com/api/team-logo/:path*" },
    { "source": "/api/image-proxy/:path*", "destination": "https://scouting-bfsa-react.onrender.com/api/image-proxy/:path*" },
    { "source": "/api/player-face/:path*", "destination": "https://scouting-bfsa-react.onrender.com/api/player-face/:path*" },
    { "source": "/api/config/:path*",      "destination": "https://scouting-bfsa-react.onrender.com/api/config/:path*" }
  ]
}
```

Apenas 4 prefixos de **assets** (logos, faces, image-proxy e config)
passam pelo proxy do Vercel — eles batem no edge cache (`s-maxage`) e
quase nunca chegam ao Render.

Todos os demais endpoints analiticos (rankings, players, similarity,
trajectory, contract_impact, vaep, playerank, etc.) sao chamados
**direto no Render** pelo helper `frontend/src/config/api.ts::apiUrl()`.
Isso evita que payloads JSON pesados consumam o **Origin Transfer**
do plano Hobby do Vercel (10 GB/mes).

> Atenção: a variável `CORS_ORIGINS` no Render PRECISA incluir o domínio
> Vercel servido aos usuários (ex: `https://scouting-bfsa-react.vercel.app`),
> caso contrário os preflights vindos do browser falham.

### Deploy Automatico

- Push na branch `main` dispara build e deploy automatico
- Preview deployments em branches de feature
- Rollback instantaneo via painel Vercel

### Monitoramento

- **Vercel Analytics:** Metricas de uso e page views
- **Speed Insights:** Core Web Vitals (LCP, FID, CLS)

---

## Backend — Render

### Configuracao do Web Service

| Campo | Valor |
|---|---|
| **Environment** | Python 3 |
| **Root Directory** | `backend` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Plan** | **Standard (2 GB RAM) recomendado** — Starter (512 MB) entrava em OOM com a carga atual mesmo após otimizações de RAM (ver `PERFORMANCE.md`). |

### Variaveis de Ambiente

Configurar no painel Environment do Render:

```env
DATABASE_URL=postgresql://user:password@host:5432/scouting_db
JWT_SECRET_KEY=chave-secreta-64-caracteres
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=SenhaForte123!
ADMIN_NAME=Administrador
TOKEN_EXPIRE_MINUTES=480
CORS_ORIGINS=https://seu-dominio.vercel.app,https://scouting-bfsa-react.onrender.com
API_FOOTBALL_KEY=sua-chave
GOOGLE_SHEET_ID=id-planilha
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
```

### PostgreSQL (Render)

1. Criar um servico **PostgreSQL** no Render
2. Copiar a **Internal Database URL**
3. Usar como `DATABASE_URL` no Web Service

### Cold Start

O tier gratuito do Render suspende o servico apos 15 minutos de inatividade.

**Mitigacoes implementadas:**
- Frontend: Retry automatico com backoff exponencial (ate 6 tentativas, ~105s total)
- Backend: GZip para respostas menores e mais rapidas
- Cache: TTL de 5 min para endpoints pesados

---

## Banco de Dados

### PostgreSQL

**Tabelas principais:**
- `users` — Usuarios do sistema (auth)
- Dados de jogadores sincronizados do Google Sheets

**Conexao:**
- Connection pooling automatico via psycopg2
- Fallback para SQLite em desenvolvimento (apenas auth)

### Sincronizacao Google Sheets

```
Google Sheets (dados Wyscout)
  → sync_sheets.py (background job)
  → data_loader.py (parse)
  → PostgreSQL
```

---

## CORS

Origens permitidas (configurar via `CORS_ORIGINS`):
```
https://botafogo-sp.vercel.app          # Producao
https://scouting-bfsa-react.onrender.com # Backend direto
http://localhost:5173                     # Dev frontend
http://localhost:8000                     # Dev backend
```

---

## Seguranca em Producao

### Checklist

- [ ] `JWT_SECRET_KEY` com pelo menos 64 caracteres aleatorios
- [ ] `ADMIN_PASSWORD` forte (8+ caracteres, maiusculas, numeros)
- [ ] HTTPS habilitado (automatico em Vercel e Render)
- [ ] `CORS_ORIGINS` restrito aos dominios necessarios
- [ ] Rate limiting ativo (300 req/min por IP)
- [ ] Logs de erro monitorados

### Nao incluir no deploy
- Arquivos `.env` (usar variaveis de ambiente do provedor)
- Credenciais de Service Account em repositorio publico
- Chaves de API no codigo fonte

---

## Monitoramento

### Frontend (Vercel)
- Page views e visitantes unicos
- Core Web Vitals (LCP, FID, CLS)
- Erros de runtime (Error Boundary)

### Backend (Render)
- Logs de servidor em tempo real
- Metricas de uso de CPU e memoria
- Alertas de erro (500+)

### Aplicacao
- Console warnings para retry de cold start
- Log de cache hits/misses
- Metricas de latencia por endpoint

---

## Workflow de CI/CD

```
Developer
  → git push origin main
  → Vercel: build + deploy automatico (frontend)
  → Render: build + deploy automatico (backend)
  → Testes manuais (staging)
  → Producao ativa
```

### Branches
- `main` — Branch de producao (auto-deploy)
- `claude/*` — Branches de feature (preview deploys no Vercel)
- PRs para `main` disparam preview deployments
