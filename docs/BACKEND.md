# Documentacao do Backend — Scouting BFSA

## Visao Geral

Backend construido com FastAPI (Python), servido via Uvicorn com compressao GZip, rate limiting e autenticacao JWT. O sistema integra dados de multiplas fontes (Google Sheets, API-Football, SkillCorner) e processa com 7 modelos de Machine Learning.

---

## Estrutura de Diretorios

```
backend/
├── main.py                        # App FastAPI principal (~200+ endpoints)
├── auth.py                        # Autenticacao JWT + PostgreSQL/SQLite
├── __init__.py
│
├── routes/                        # Rotas HTTP
│   ├── auth.py                    # Endpoints de login/logout
│   ├── apifootball.py             # Integracao API-Football v3
│   └── proxy.py                   # Proxy de imagens e logos
│
├── services/                      # Logica de negocio
│   ├── scouting_intelligence.py   # Motor de 7 modelos ML (~100KB)
│   ├── predictive_engine.py       # Scout Score Preditivo v3.0 (~47KB)
│   ├── similarity.py              # Similaridade multi-metodo (~22KB)
│   ├── calibration.py             # Coeficientes academicos (~22KB)
│   ├── league_power_model.py      # Opta Power Rankings
│   ├── enrichment.py              # Pipeline de enriquecimento (~29KB)
│   ├── database.py                # PostgreSQL + Google Sheets sync
│   ├── data_loader.py             # Carregamento CSV/Google Sheets
│   ├── sync_sheets.py             # Job de sincronizacao em background
│   ├── fuzzy_match.py             # Matching SkillCorner (RapidFuzz)
│   ├── player_assets.py           # Gestao de assets (fotos, logos)
│   └── api_football.py            # Servico API-Football
│
├── schemas/                       # Modelos de dados
│   └── models.py                  # Pydantic request/response (~40+ classes)
│
├── config/                        # Configuracao estatica
│   └── mappings.py                # Dicionarios (logos, flags, indices)
│
├── tests/                         # Testes
│   └── ...
│
├── requirements.txt               # Dependencias Python
├── pytest.ini                     # Configuracao de testes
└── .env.example                   # Template de variaveis de ambiente
```

---

## Modulos de Servico

### scouting_intelligence.py — Motor Principal (7 Modelos)

Arquivo central do sistema analitico com ~100KB de codigo. Implementa 7 modelos de ML:

#### Modelo 1: PlayerTrajectoryModel
**Objetivo:** Prever evolucao de carreira do jogador.
- **Algoritmo:** Gradient Boosting Regressor
- **Pipeline:** Normalizacao z-score → Feature Selection (Mutual Information) → Gradient Boosting → Cross-Validation
- **Saida:** `predicted_rating_next_season`, `trajectory_score`, `trajectory_class` (improving/stable/declining)
- **Referencia:** Decroos et al. (KDD 2019) VAEP, Bransen & Van Haaren (2020)

#### Modelo 2: MarketValuePredictor
**Objetivo:** Estimar valor de mercado do jogador.
- **Algoritmo:** XGBoost Regressor
- **Segmentacao:** 9 modelos separados por posicao x faixa etaria (Khalife et al., 2025)
- **Saida:** `estimated_market_value` (EUR), `market_value_gap`
- **Referencia:** Khalife et al. (MDPI 2025), R² > 0.91 para atacantes jovens

#### Modelo 3: MarketOpportunityDetector
**Objetivo:** Identificar talentos subvalorizados.
- **Formula:** `score = performance × trajectory × value_gap − age_penalty`
- **Classificacao:** Exceptional (>80), High (60-80), Moderate (40-60), Low (<40)
- **Inspiracao:** Modelos Brighton, Brentford, FC Midtjylland

#### Modelo 4: PlayerReplacementEngine
**Objetivo:** Encontrar substitutos para um jogador de referencia.
- **Metodos:** Cosine Similarity (peso 45%) + Mahalanobis Distance (35%) + Cluster Proximity (20%)
- **Saida:** Lista ranqueada com scores de similaridade, trajetoria e valor
- **Referencia:** KickClone (Bhatt et al., AIMV 2025), FPSRec (IEEE BigData 2024)

#### Modelo 5: TemporalPerformanceTrend
**Objetivo:** Analisar tendencia temporal de performance.
- **Calculo:** `trend = rolling_mean(current) − rolling_mean(previous)`
- **Classificacao:** `improving`, `stable`, `declining`
- **Referencia:** Age Curves 2.0 (TransferLab/Analytics FC)

#### Modelo 6: LeagueStrengthAdjuster
**Objetivo:** Ajustar metricas pelo nivel da liga.
- **Formula:** `adjusted_metric = metric × league_strength_factor × opta_league_power`
- **Fonte:** Opta Power Rankings (Stats Perform 2025), 13.500+ clubes, escala 0-100

#### Modelo 7: ContractImpactAnalyzer
**Objetivo:** Analisar impacto de contratacao no elenco do Botafogo-SP.
- **6 Componentes:**
  - Necessidade posicional (peso 20%)
  - Ganho de qualidade (peso 25%)
  - Complementaridade tatica (peso 15%)
  - Perfil etario (peso 10%)
  - Eficiencia financeira (peso 15%)
  - Avaliacao de risco (peso 15%)
- **Saida:** `impact_score` (0-100), classificacao, recomendacao
- **Referencia:** Pappalardo et al. (2019) PlayeRank, Kuper & Szymanski (2009) Soccernomics

---

### predictive_engine.py — Motor Preditivo Original (v3.0)

Motor preditivo original com ~47KB. Inclui:

- **Scout Score Preditivo (SSP):** Ensemble de WP-weights + xG-residual + cluster-fit + percentil
- **Win-Probability Model:** Logistic Regression com coeficientes calibrados
- **Clusterizacao Tatica:** K-Means + Gaussian Mixture + Random Forest interpreter
- **Similaridade Avancada:** Mahalanobis + Random Forest proximity
- **ContractSuccessPredictor:** Predicao de sucesso com ajuste por liga

---

### similarity.py — Similaridade e Indices

Modulo de ~22KB responsavel por:
- Calculo de indices compostos por posicao (incluindo "Passes Quebrando Linhas")
- Percentis vs jogadores da mesma posicao
- Comparacao entre dois jogadores
- Busca de jogadores similares

**Indice "Passes Quebrando Linhas":** Proxy do metrica "line-breaking passes" do StatsBomb 360,
construido com metricas Wyscout disponiveis (smart passes, through balls, progressive passes,
passes to final third, passes to penalty area). Presente em todas as 7 posicoes de campo com
pesos ajustados por posicao. Baseado em: StatsBomb 360 (Odegaard, Dez 2023), Passing Danger
Index (Griffis, Cafe Tactiques 2022), PlayeRank (Pappalardo et al., 2019).

---

### calibration.py — Coeficientes Academicos

Modulo de ~22KB com coeficientes calibrados a partir de:
- PIBITI Joao Vitor Oliveira (Insper, 2025): Coeficientes β de rating por posicao
- Victor Valvano Schimidt (UNESP, 2021): Coeficientes de win-probability
- Eduardo Baptista dos Santos (MBA USP/ICMC, 2024): Classificacao por posicao
- Frederico Ferra (NOVA IMS, 2025): PCA + K-Means + RF clustering tatico
- Tiago Pinto (ISEP Porto, 2024): Gradient Boosting para predicao
- Felipe Nunes (UFMG, 2025): Fuzzy + Random Forest para recrutamento
- Gabriel Buso (UFSC, 2025): Modelos xG e xGOT

---

### enrichment.py — Pipeline de Enriquecimento

Pipeline de ~29KB que enriquece dados brutos com:
- Calculo de metricas derivadas (per 90 min)
- Normalizacao por posicao e liga
- Classificacao de performance
- Integracao com dados SkillCorner

---

### database.py — Acesso a Dados

Gerencia conexao com PostgreSQL e sincronizacao com Google Sheets:
- Connection pooling para PostgreSQL
- Fallback para Google Sheets publico (CSV export)
- Sync periodico em background

---

### fuzzy_match.py — Matching de Nomes

Usa RapidFuzz para matching fuzzy de nomes de jogadores entre:
- Base de dados interna (Wyscout)
- SkillCorner (dados fisicos)
- API-Football (dados ao vivo)

---

### league_power_model.py — Opta Power Rankings

Implementa o modelo de forca de liga baseado nos Power Rankings da Opta/Stats Perform:
- Escala 0-100 para todas as ligas
- Fator de ajuste aplicado a metricas de jogadores

---

## Autenticacao (auth.py)

Sistema de autenticacao JWT com:
- **Armazenamento:** PostgreSQL (tabela `users`) ou SQLite (fallback)
- **Hash de senhas:** bcrypt
- **Token:** JWT HS256 com expiracao configuravel (padrao: 480 min)
- **Admin seed:** Cria usuario admin no startup a partir de `ADMIN_EMAIL` / `ADMIN_PASSWORD`
- **Middleware:** Verifica token em todas as rotas protegidas

---

## Rotas (routes/)

### auth.py
- `POST /auth/login` — Autenticacao
- `POST /auth/me` — Dados do usuario
- `POST /auth/logout` — Logout

### apifootball.py
- `GET /apifootball/leagues` — Ligas
- `GET /apifootball/teams` — Times
- `GET /apifootball/standings` — Classificacao
- `GET /apifootball/fixtures` — Partidas
- `GET /apifootball/squad` — Elenco
- `GET /apifootball/player-stats` — Estatisticas

### proxy.py
- `GET /api/image-proxy` — Proxy CORS para imagens
- `GET /api/team-logo/{team}` — Logo com cache local

---

## Variaveis de Ambiente

| Variavel | Obrigatoria | Descricao |
|---|---|---|
| `DATABASE_URL` | Sim | Connection string PostgreSQL |
| `JWT_SECRET_KEY` | Sim | Chave de assinatura JWT |
| `ADMIN_EMAIL` | Sim | Email do admin inicial |
| `ADMIN_PASSWORD` | Sim | Senha do admin inicial |
| `ADMIN_NAME` | Nao | Nome do admin (default: "Administrador") |
| `TOKEN_EXPIRE_MINUTES` | Nao | Expiracao do token (default: 480) |
| `CORS_ORIGINS` | Nao | Origens CORS permitidas |
| `API_FOOTBALL_KEY` | Nao | Chave da API-Football.com |
| `GOOGLE_SHEET_ID` | Nao | ID da planilha Google Sheets |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Nao | Credenciais de Service Account |

---

## Middlewares

1. **CORS:** Whitelist de origens configuravel
2. **GZip:** Compressao de todas as respostas
3. **Rate Limiting:** 300 requisicoes/minuto por IP (slowapi)
4. **Error Handling:** Tratamento global de excecoes com logging

---

## Cache

- **TTL Cache (cachetools):** 5 minutos para endpoints pesados (rankings, similarity)
- **Resultado:** Reduz latencia de ~2s para ~50ms em requests repetidos
- **Invalidacao:** Automatica por TTL, sem invalidacao manual

---

## Integrações Externas

### Google Sheets
- **Uso:** Fonte primaria de dados Wyscout
- **Acesso:** Via Service Account (privado) ou CSV export (publico)
- **Sync:** Background job periodico via `sync_sheets.py`

### API-Football (v3)
- **Uso:** Dados ao vivo (classificacoes, partidas, elencos)
- **Limite:** 100 chamadas/dia (tier gratuito)
- **Client:** aiohttp (async)

### SkillCorner
- **Uso:** Metricas fisicas (sprints, velocidade max, distancia)
- **Matching:** RapidFuzz para associar nomes entre bases
- **Metricas:** 8 metricas fisicas por jogador

---

## Execucao Local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variaveis de ambiente
cp .env.example .env
# Editar .env com seus valores

# Iniciar servidor
uvicorn main:app --reload --port 8000

# O servidor estara disponivel em http://localhost:8000
# Documentacao Swagger: http://localhost:8000/docs
# Documentacao ReDoc: http://localhost:8000/redoc
```

---

## Testes

```bash
# Executar testes
pytest

# Com cobertura
pytest --cov=.

# Testes especificos
pytest tests/test_auth.py
```

Configuracao em `pytest.ini`.
