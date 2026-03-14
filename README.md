# Scouting Dashboard | Botafogo-SP

Dashboard de scouting profissional com motor preditivo de ML e visualizações estilo Wyscout.

---

## Arquitetura

```
Google Sheets
     ↓
PostgreSQL
     ↓
FastAPI Backend
     ├── predictive_engine.py    (Scout Score Preditivo, clustering, similaridade)
     ├── scouting_intelligence.py (7 modelos de ML — Scouting Intelligence Engine)
     ├── league_power_model.py   (Opta Power Ranking, ajuste por liga)
     ├── calibration.py          (coeficientes calibrados por literatura acadêmica)
     └── similarity.py           (índices compostos, percentis, ranking)
     ↓
API REST (JSON)
     ↓
React Frontend (Dashboard)
```

---

## Motor Analítico — Scouting Intelligence Engine

### Modelo 1: Player Trajectory Model
Previsão de evolução de carreira usando **Gradient Boosting Regressor**.

- **Pipeline:** normalização z-score → feature selection (mutual information) → gradient boosting → cross-validation
- **Saída:** `predicted_rating_next_season`, `trajectory_score`
- **Endpoint:** `POST /api/trajectory`

### Modelo 2: Market Value Prediction
Estimativa de valor de mercado com **XGBoost Regressor**.

- **Segmentação:** posição × faixa etária (Khalife et al., 2025)
- **Saída:** `estimated_market_value`, `market_value_gap`
- **Endpoint:** `POST /api/market_value`

### Modelo 3: Market Opportunity Detector
Score composto para identificação de oportunidades de mercado.

- **Fórmula:** `performance × trajectory × value_gap − age_penalty`
- **Inspiração:** Brighton, Brentford, FC Midtjylland
- **Saída:** `market_opportunity_score` (0-100)
- **Endpoint:** `POST /api/market_opportunities`

### Modelo 4: Player Replacement Engine
Motor de busca de substitutos com similaridade multi-método.

- **Métodos:** Cosine Similarity (45%) + Mahalanobis Distance (35%) + Cluster Proximity (20%)
- **Saída:** Top-N substitutos com scores de similaridade, trajetória e valor
- **Endpoint:** `POST /api/replacements`

### Modelo 5: Temporal Performance Trend
Análise temporal de tendência de performance.

- **Cálculo:** `trend = rolling_mean(current) − rolling_mean(previous)`
- **Classificação:** `improving`, `stable`, `declining`

### Modelo 6: League Strength Adjustment
Ajuste de métricas por nível de liga via Opta Power Ranking.

- **Fórmula:** `adjusted_metric = metric × league_strength_factor × opta_league_power`
- **Endpoint:** `GET /api/league_powers`

### Modelo 7: Contract Impact Analyzer
Análise de impacto de contratação no elenco do Botafogo-SP.

- **Componentes:** necessidade posicional (20%), ganho de qualidade (25%), complementaridade tática (15%), perfil etário (10%), eficiência financeira (15%), avaliação de risco (15%)
- **Referências:** Pappalardo et al. (2019) PlayeRank, Kuper & Szymanski (2009) Soccernomics, Poli et al. (CIES 2021), Age Curves 2.0, Frost & Groom (2025)
- **Saída:** `impact_score` (0-100), classificação, recomendação, detalhamento por componente
- **Endpoint:** `POST /api/contract_impact`

---

## Motor Preditivo Original (predictive_engine v3.0)

- **Scout Score Preditivo (SSP):** ensemble de WP-weights + xG-residual + cluster-fit + percentil
- **Win-Probability Model:** Logistic Regression com coeficientes calibrados
- **Clusterização Tática:** K-Means + Gaussian Mixture + RF interpreter
- **Similaridade Avançada:** Mahalanobis + Random Forest proximity
- **Predição de Contratação:** `ContractSuccessPredictor` com ajuste por liga

---

## Base Científica — Mapa Referência × Modelo

| Referência | Modelo(s) |
|-----------|-----------|
| Decroos et al. (KDD 2019) — VAEP | M1 Trajectory, M3 Opportunity |
| Bransen & Van Haaren (2020) | M1 Trajectory |
| SciSkill Forecasting (MDPI 2025) | M1 Trajectory + M3 Opportunity |
| Can We Predict Success? (ICSPORTS 2025) | M1 Trajectory |
| Age Curves 2.0 — TransferLab | M1 Trajectory + M5 Trend |
| Khalife et al. (MDPI 2025) | M2 Market Value |
| Poli / Bryson et al. (CIES / MDPI 2021) | M2 Market Value |
| Gyarmati & Stanojevic (2016) | M2 Market Value |
| GDA — TransferLab / Analytics FC | M1 Trajectory + M3 Opportunity |
| Brighton Analytics (Starlizard) | M3 Opportunity |
| KickClone — Bhatt et al. (AIMV 2025) | M4 Replacement Engine |
| Spatial Similarity Index (PMC 2025) | M4 Replacement Engine |
| FPSRec (IEEE BigData 2024) | M4 Replacement Engine |
| Opta Power Rankings (Stats Perform 2025) | M6 League Adjustment |
| MDPI 2025 Systematic Review (172 artigos) | Visão geral |
| LJMU + KU Leuven (2025) | Visão geral / agenda |
| Frost & Groom (2025) | Processo de integração |

### Referências Detalhadas

**Trajectory & Performance Prediction:**
- Decroos, Bransen, Van Haaren, Davis (KDD 2019). *Actions Speak Louder than Goals: Valuing Player Actions in Soccer (VAEP).* VAEP(ação) = ΔP(gol) − ΔP(sofrer gol). Implementação: socceraction (ML-KULeuven).
- Bransen & Van Haaren (2020). *Measuring Players' On-the-Ball Contributions from Passes.*
- MDPI Applied Sciences (2025). *Forecasting Future Development in Quality and Value of Football Players.* 86 features, RF melhor para ETV, XGBoost para SciSkill.
- ICSPORTS (2025). *Can We Really Predict Which Football Players Will Succeed?* N=8.770. SHAP: trajetórias > atributos estáticos. Janela 22-26: F1=0.86.
- Age Curves 2.0 (TransferLab / Analytics FC). Curvas de decaimento por habilidade: drible decai cedo, passe estável.

**Market Value & Opportunity:**
- Khalife et al. (MDPI 2025). *Dynamic Financial Valuation of Football Players.* XGBoost, 9 modelos (posição × faixa etária). R² > 0.91 atacantes jovens.
- Poli, Besson, Ravenel (CIES / MDPI 2021). *Econometric Approach to Assessing Transfer Fees.* MLR R² > 85%.
- Gyarmati & Stanojevic (2016). *Towards Data-Driven Football Player Assessment.*
- GDA (TransferLab / Analytics FC). Goal Difference Added per 90min via Cadeias de Markov.
- Brighton & Hove Albion (Starlizard). Caicedo £4.5m → £115m. Mitoma £3m → ~£50m+.

**Similaridade & Substituição:**
- Bhatt, Pandya, Raje, Shah (AIMV 2025). *KickClone.* Normalização → PCA → Cosine Similarity → Top-K. +200K jogadores.
- *Spatial Similarity Index for Scouting in Football.* PMC/NCBI 2025. Estatística de Lee.
- *FPSRec: Football Players Scouting Recommendation System.* IEEE BigData 2024. IA generativa para relatórios.

**Revisões Sistemáticas:**
- MDPI 2025. *Machine Learning Applied to Professional Football.* 172 artigos (2019-2024). RF, XGBoost, GBM = mais utilizados.
- LJMU + KU Leuven (2025). *Perspectives on Data Analytics for Gaining a Competitive Advantage in Football.* Science & Medicine in Football.
- Frost & Groom (2025). *The Use of Performance Analysis and Data-Driven Approaches within Football Recruitment.*
- Opta Power Rankings (Stats Perform 2025). Elo modificado, +13.500 clubes, escala 0-100.

### Calibração do Motor Original (predictive_engine.py)
- PIBITI João Vitor Oliveira (Insper, 2025): Coeficientes β de rating por posição.
- Victor Valvano Schimidt (UNESP, 2021): Coeficientes de win-probability.
- Eduardo Baptista dos Santos (MBA USP/ICMC, 2024): Classificação de jogadores por posição.
- Frederico Ferra (NOVA IMS, 2025): PCA + K-Means + RF para clustering tático.
- Tiago Pinto (ISEP Porto, 2024): Gradient Boosting para predição de performance.
- Felipe Nunes (UFMG, 2025): Fuzzy + Random Forest para recrutamento.
- Gabriel Buso (UFSC, 2025): Modelos xG e xGOT.

---

## Endpoints API

### Scouting Intelligence (novos)
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/trajectory` | Previsão de evolução de carreira |
| POST | `/api/market_value` | Estimativa de valor de mercado |
| POST | `/api/market_opportunities` | Detecção de oportunidades |
| POST | `/api/replacements` | Busca de substitutos |
| POST | `/api/contract_impact` | Análise de impacto de contratação |
| GET | `/api/league_powers` | Coeficientes Opta Power por liga |

### Core (existentes)
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/players` | Lista de jogadores |
| GET | `/api/players/{name}/profile` | Perfil completo |
| POST | `/api/rankings` | Ranking por posição |
| POST | `/api/similarity` | Jogadores similares |
| POST | `/api/prediction` | Predição de sucesso de contratação |
| POST | `/api/clusters` | Clusterização tática |
| POST | `/api/comparison` | Comparação entre jogadores |

---

## Rodar Localmente

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

---

## Funcionalidades

- **Perfil Individual:** Radar de atributos + percentis estilo Wyscout
- **Comparativo:** Scatter plot + comparação entre jogadores
- **Dados Físicos:** Métricas SkillCorner com radar de rankings
- **Rankings Preditivos:** Scout Score Preditivo com calibração acadêmica
- **Previsão de Evolução:** Trajetória de carreira com Gradient Boosting
- **Valuation:** Estimativa de valor de mercado com XGBoost
- **Oportunidades:** Detecção de talentos subvalorizados
- **Substituição:** Motor de busca de substitutos multi-método
- **Impacto de Contratação:** Análise de impacto no elenco com 6 dimensões
- **Análise Temporal:** Tendências de performance

---

**Desenvolvido para Botafogo SA Ribeirão Preto**
