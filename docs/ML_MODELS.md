# Modelos de Machine Learning — Scouting BFSA

## Visao Geral

O sistema utiliza 7 modelos de ML no **Scouting Intelligence Engine** mais um motor preditivo original (**predictive_engine v3.0**). Todos os modelos sao calibrados com base em literatura academica (172 artigos revisados) e pesquisas brasileiras (PIBITI/TCC).

---

## Scouting Intelligence Engine (7 Modelos)

### Modelo 1: Player Trajectory Model

**Objetivo:** Prever a evolucao de carreira de um jogador nas proximas temporadas.

**Algoritmo:** Gradient Boosting Regressor

**Pipeline:**
```
Dados brutos
  → Normalizacao z-score
  → Feature Selection (Mutual Information)
  → Gradient Boosting Regressor
  → Cross-Validation (k-fold)
  → predicted_rating_next_season
```

**Saidas:**
- `predicted_rating_next_season` — Rating previsto para proxima temporada
- `trajectory_score` — Score de trajetoria (0-100)
- `trajectory_class` — Classificacao: `improving`, `stable`, `declining`

**Base Cientifica:**
| Referencia | Contribuicao |
|---|---|
| Decroos et al. (KDD 2019) — VAEP | Valoracao de acoes: VAEP(acao) = ΔP(gol) − ΔP(sofrer gol) |
| Bransen & Van Haaren (2020) | Contribuicao de passes on-the-ball |
| SciSkill Forecasting (MDPI 2025) | 86 features, RF para ETV, XGBoost para SciSkill |
| Can We Predict Success? (ICSPORTS 2025) | N=8.770, SHAP: trajetorias > atributos estaticos, F1=0.86 |
| Age Curves 2.0 (TransferLab) | Curvas de decaimento por habilidade |

**Endpoint:** `POST /api/trajectory`

---

### Modelo 2: Market Value Prediction

**Objetivo:** Estimar valor de transferencia de um jogador em EUR.

**Algoritmo:** XGBoost Regressor

**Segmentacao:** 9 modelos especializados por posicao x faixa etaria:
```
                    Jovem (≤23)    Prime (24-29)    Veterano (30+)
Goleiro/Defensor    modelo_1       modelo_2         modelo_3
Meio-campista       modelo_4       modelo_5         modelo_6
Atacante            modelo_7       modelo_8         modelo_9
```

**Saidas:**
- `estimated_market_value` — Valor estimado em EUR
- `market_value_gap` — Diferenca entre valor real e estimado

**Base Cientifica:**
| Referencia | Contribuicao |
|---|---|
| Khalife et al. (MDPI 2025) | 9 modelos posicao x idade, R² > 0.91 atacantes jovens |
| Poli, Besson, Ravenel (CIES 2021) | MLR R² > 85% |
| Gyarmati & Stanojevic (2016) | Data-driven player assessment |

**Endpoint:** `POST /api/market_value`

---

### Modelo 3: Market Opportunity Detector

**Objetivo:** Identificar jogadores com alto potencial e valor de mercado abaixo do esperado.

**Formula:**
```
opportunity_score = performance_score × trajectory_weight × value_gap_factor − age_penalty
```

**Classificacao:**
| Faixa | Classificacao |
|---|---|
| > 80 | Exceptional Opportunity |
| 60-80 | High Opportunity |
| 40-60 | Moderate Opportunity |
| < 40 | Low Opportunity |

**Inspiracao:** Modelos de recrutamento do Brighton (Caicedo £4.5M → £115M), Brentford e FC Midtjylland.

**Base Cientifica:**
| Referencia | Contribuicao |
|---|---|
| Brighton Analytics (Starlizard) | Caso Caicedo e Mitoma |
| GDA (TransferLab/Analytics FC) | Goal Difference Added via Cadeias de Markov |
| SciSkill Forecasting (MDPI 2025) | Combinacao de performance + trajetoria |

**Endpoint:** `POST /api/market_opportunities`

---

### Modelo 4: Player Replacement Engine

**Objetivo:** Encontrar substitutos ideais para um jogador de referencia.

**Metodos de Similaridade (3 combinados):**

```
                            Peso
Cosine Similarity           45%     Angulo entre vetores de metricas
Mahalanobis Distance        35%     Distancia ponderada por correlacao
Cluster Proximity           20%     Proximidade no espaco de clusters
─────────────────────────────────
Total                      100%     Score final de similaridade
```

**Pipeline:**
```
Jogador referencia
  → Extrair vetor de metricas
  → Filtrar candidatos (mesma posicao, ligas alvo)
  → Calcular 3 distancias
  → Ponderar: 0.45×Cosine + 0.35×Mahalanobis + 0.20×ClusterProx
  → Ranquear por similaridade descendente
  → Enriquecer com trajetoria e valor de mercado
```

**Base Cientifica:**
| Referencia | Contribuicao |
|---|---|
| KickClone — Bhatt et al. (AIMV 2025) | Normalizacao → PCA → Cosine → Top-K, +200K jogadores |
| Spatial Similarity Index (PMC 2025) | Estatistica de Lee para similaridade espacial |
| FPSRec (IEEE BigData 2024) | IA generativa para relatorios de scouting |

**Endpoint:** `POST /api/replacements`

---

### Modelo 5: Temporal Performance Trend

**Objetivo:** Analisar tendencia temporal de performance.

**Calculo:**
```
trend = rolling_mean(current_window) − rolling_mean(previous_window)
```

**Classificacao:**
| Tendencia | Criterio |
|---|---|
| `improving` | trend > +threshold |
| `stable` | -threshold ≤ trend ≤ +threshold |
| `declining` | trend < -threshold |

**Referencia:** Age Curves 2.0 (TransferLab/Analytics FC) — curvas de decaimento por habilidade (drible decai cedo, passe se mantem estavel).

---

### Modelo 6: League Strength Adjustment

**Objetivo:** Ajustar metricas de jogadores pelo nivel competitivo da liga.

**Formula:**
```
adjusted_metric = raw_metric × league_strength_factor × opta_league_power
```

**Fonte:** Opta Power Rankings (Stats Perform 2025)
- 13.500+ clubes avaliados
- Escala 0-100
- Baseado em Elo modificado

**Endpoint:** `GET /api/league_powers`

---

### Modelo 7: Contract Impact Analyzer

**Objetivo:** Analisar o impacto potencial de uma contratacao no elenco do Botafogo-SP.

**6 Componentes do Score:**
```
                              Peso    Descricao
Necessidade Posicional        20%     Carencia na posicao do elenco atual
Ganho de Qualidade            25%     Melhoria vs titulares atuais
Complementaridade Tatica      15%     Encaixe no esquema tatico
Perfil Etario                 10%     Alinhamento com janela de idade ideal
Eficiencia Financeira         15%     Custo-beneficio da operacao
Avaliacao de Risco            15%     Fatores de risco (lesoes, adaptacao)
───────────────────────────────────
Impact Score                 100%     Score final (0-100)
```

**Classificacao de Impacto:**
| Score | Classificacao |
|---|---|
| > 80 | Impacto Excepcional |
| 60-80 | Alto Impacto |
| 40-60 | Impacto Moderado |
| < 40 | Baixo Impacto |

**Base Cientifica:**
| Referencia | Contribuicao |
|---|---|
| Pappalardo et al. (2019) PlayeRank | Framework de avaliacao multi-dimensional |
| Kuper & Szymanski (2009) Soccernomics | Economia do futebol |
| Poli et al. (CIES 2021) | Modelo econometrico de transferencias |
| Age Curves 2.0 | Perfil etario ideal por posicao |
| Frost & Groom (2025) | Processo de integracao e recrutamento |

**Endpoint:** `POST /api/contract_impact`

---

## VAEP Engine — Valuing Actions by Estimating Probabilities

### Objetivo
Calcular o valor individual de cada acao de um jogador em campo, baseado na variacao de probabilidade de marcar e sofrer golos.

### Formula
```
VAEP(acao) = ΔP(scoring) − ΔP(conceding)
```
Onde `ΔP(scoring)` e a variacao na probabilidade de gol apos a acao, e `ΔP(conceding)` e a variacao na probabilidade de sofrer gol.

### Pipeline

```
Eventos Wyscout (PostgreSQL)
  → Conversao para SPADL (socceraction)
  → Feature Engineering (action + game state features)
  → Label Generation (scoring/conceding em proximas 10 acoes)
  → Treino: XGBoost Classifier (scoring model + conceding model)
  → Predicao: P(scoring), P(conceding) por game state
  → VAEP value = ΔP(scoring) − ΔP(conceding) por acao
  → Agregacao: VAEP/90 por jogador
  → Persistencia: PostgreSQL (vaep_ratings + vaep_actions)
```

### Dual Mode
1. **Full mode** (socceraction instalado + event data): Pipeline completo com conversao SPADL, feature engineering e XGBoost
2. **Heuristic mode** (fallback): Estima VAEP a partir de estatisticas agregadas Wyscout usando pesos calibrados

### Heuristic VAEP — Pesos de Aproximacao
```
Ofensivo:
  Goals/90 × 0.30 + xG/90 × 0.15 + Assists/90 × 0.15 + xA/90 × 0.10
  + Key passes/90 × 0.08 + Progressive passes/90 × 0.06
  + Dribbles/90 × 0.04 + Shots/90 × 0.04 + Crosses/90 × 0.04 + Touches box/90 × 0.04

Defensivo:
  Defensive actions/90 × 0.25 + Interceptions/90 × 0.25
  + Tackles/90 × 0.20 + Aerial wins % × 0.15 + Clearances/90 × 0.15

Scaling: offensive × 0.35, defensive × 0.08
(Calibrado: top 10 jogadores ≈ 0.5-0.8 VAEP/90 — Decroos et al., 2019)
```

### Integracao com Modelos Existentes
- **M1 (Trajectory):** `vaep_per90` disponivel como feature para previsao
- **M3 (Opportunity):** Performance percentile enriquecido com VAEP (70% metric + 30% VAEP)
- **M4 (Replacement):** Resultados de similaridade enriquecidos com `vaep_per90` e `playerank_score`

### Saidas
- `vaep_per90` — VAEP total por 90 minutos
- `offensive_vaep` — Componente ofensivo
- `defensive_vaep` — Componente defensivo
- `total_vaep` — VAEP total acumulado na temporada
- `actions_count` — Numero de acoes avaliadas

### Tabelas PostgreSQL
```sql
vaep_ratings   — Ratings agregados por jogador/temporada
vaep_actions   — Valores VAEP por acao individual (com coordenadas x,y)
```

### Base Cientifica
| Referencia | Contribuicao |
|---|---|
| Decroos et al. (KDD 2019) — VAEP | Framework original: acoes como shifts de probabilidade |
| Bransen & Van Haaren (2020) | Contribuicao de passes on-the-ball |
| SciSports Labs — fot-valuing-actions | Implementacao de referencia (4 notebooks Jupyter) |
| socceraction (ML-KULeuven) | Biblioteca open-source para conversao SPADL e VAEP |

### Endpoints
- `POST /api/vaep/run-pipeline` — Executa pipeline completo
- `GET /api/vaep/ratings` — Ratings pre-calculados com filtros
- `GET /api/vaep/player/{name}` — VAEP detalhado + top acoes
- `GET /api/vaep/compare` — Comparacao entre jogadores

---

## PlayeRank Engine — Multi-dimensional Role-Aware Evaluation

### Objetivo
Avaliar jogadores em multiplas dimensoes de performance, considerando seu papel tatico real (nao apenas posicao nominal), e produzir rankings dentro de clusters posicionais.

### Pipeline
```
VAEP ratings + Metricas Wyscout
  → K-Means Clustering (6 roles taticos)
  → 5 Dimensoes de Score (percentile-based)
  → Composite Score (pesos role-specific)
  → Percentile dentro do Cluster
  → Persistencia: PostgreSQL (playerank_scores)
```

### Roles Taticos (6 clusters)
| Cluster | Role | Perfil |
|---|---|---|
| 0 | Goal Scorer | Finalizacao, xG, toques na area |
| 1 | Playmaker | Assistencias, passes decisivos, xA |
| 2 | Box-to-Box | Equilibrio ofensivo/defensivo |
| 3 | Defensive Anchor | Intercecoes, tackles, duelos aereos |
| 4 | Wide Player | Cruzamentos, corridas progressivas, dribles |
| 5 | Ball-Playing Defender | Passes progressivos, intercecoes, construcao |

### 5 Dimensoes de Score
```
                      Scoring    Playmaking    Defending    Physical    Possession
Goal Scorer           40%        15%           5%           15%         25%
Playmaker             10%        40%           5%           10%         35%
Box-to-Box            15%        20%           20%          25%         20%
Defensive Anchor      5%         10%           40%          25%         20%
Wide Player           15%        25%           10%          20%         30%
Ball-Playing Defender  5%        15%           35%          20%         25%
```

### Metricas por Dimensao
- **Scoring:** Goals/90, xG/90, Shots/90, Shot accuracy, Touches in box, Conversion rate
- **Playmaking:** Assists/90, xA/90, Key passes, Progressive passes, Final third passes, Smart passes
- **Defending:** Defensive actions/90, Interceptions, Tackles, Defensive duel win %, Aerial wins, Clearances
- **Physical:** Duels/90, Duel win %, Aerial duels, Accelerations, Progressive runs
- **Possession:** Pass accuracy, Passes/90, Forward passes, Dribbles, Dribble success %, Receptions

### VAEP Boost
Quando VAEP ratings estao disponiveis, o composite score recebe boost:
```
composite_final = composite_base × 0.85 + vaep_bonus × 0.15
vaep_bonus = min(vaep_per90 / 0.8 × 100, 100)
```

### Saidas
- `composite_score` — Score composto (0-100) ponderado por role
- `role_cluster` — Role tatico atribuido pelo clustering
- `dimensions` — Scores individuais por dimensao (0-100)
- `percentile_in_cluster` — Percentil dentro do cluster
- `cluster_size` — Tamanho do cluster

### Base Cientifica
| Referencia | Contribuicao |
|---|---|
| Pappalardo & Cintia (ACM TIST, 2019) — PlayeRank | Framework original: avaliacao role-aware multi-dimensional |
| Decroos et al. (KDD 2019) — VAEP | VAEP ratings como input para composite score |
| Frederico Ferra (NOVA IMS, 2025) | PCA + K-Means + RF para clustering tatico |

### Endpoint
- `GET /api/playerank/rankings` — Rankings filtrados por cluster, dimensao, liga

---

## Mapa de Referencias Cientificas (Atualizado)

```
                    M1        M2        M3        M4        M5        M6        M7        LBP       VAEP      PLR
Referencia          Traj.     Value     Opport.   Replace.  Trend     League    Impact    LineBrk   Engine    Engine
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
VAEP (KDD 2019)     ●                   ●                                                           ●
Bransen 2020        ●                                                                               ●
SciSkill (2025)     ●                   ●
ICSPORTS 2025       ●
Age Curves 2.0      ●                                       ●                   ●
Khalife (2025)                ●
CIES 2021                     ●                                                  ●
Gyarmati 2016                 ●
GDA TransferLab     ●                   ●
Brighton/Starlizard                     ●
KickClone 2025                                    ●
Spatial Sim. 2025                                 ●
FPSRec 2024                                      ●
Opta Power 2025                                                       ●
PlayeRank 2019                                                                   ●                             ●
Soccernomics 2009                                                                ●
Frost & Groom 2025                                                               ●
StatsBomb 360 2021                                                                         ●
PDI Griffis 2022                                                                           ●
PIM ScienceDirect25                                                                        ●
Analytics FC 2022                                                                          ●
xT vs VAEP 2020                                                                           ●
socceraction        ●                   ●                                                           ●
```

---

## Motor Preditivo Original (predictive_engine v3.0)

### Scout Score Preditivo (SSP)
Ensemble score combinando multiplas fontes:
```
SSP = w1×WP_score + w2×xG_residual + w3×cluster_fit + w4×percentil_score
```

### Win-Probability Model
Logistic Regression com coeficientes calibrados por posicao:
```
WP = σ(β0 + β1×metric1 + β2×metric2 + ... + βn×metricN)
```

### Clusterizacao Tatica
Pipeline de 3 etapas:
```
Metricas por posicao
  → K-Means (k clusters iniciais)
  → Gaussian Mixture Model (refinamento)
  → Random Forest Interpreter (importancia de features)
  → Perfis taticos nomeados
```

### Similaridade Avancada
```
Mahalanobis Distance + Random Forest Proximity
  → Score de similaridade composto
```

### ContractSuccessPredictor
Predicao de probabilidade de sucesso com ajuste por forca de liga:
```
P(success) = base_prediction × league_adjustment_factor
```

---

## Indice Composto: Passes Quebrando Linhas

### Motivacao

A metrica "line-breaking passes" do StatsBomb 360 (ex: Odegaard com 17 passes quebrando linhas em um unico jogo, Dez 2023) e uma variavel critica para scouting analitico. Como o sistema utiliza dados Wyscout, foi construido um proxy composto que aproxima essa metrica.

### Fundamentacao Cientifica

| Referencia | Contribuicao |
|---|---|
| StatsBomb 360 — Line-Breaking Passes (2021) | Definicao original: passes que avancam ≥10% em direcao ao gol e cruzam um par de defensores |
| Griffis (Cafe Tactiques, 2022) — Passing Danger Index | Media harmonica de smart passes + deep completions + key passes + shot assists |
| Pappalardo et al. (ACM TIST, 2019) — PlayeRank | Framework role-aware com pesos aprendidos via SVM para avaliacao multi-dimensional |
| Decroos et al. (AAAI 2020) — xT vs VAEP | xT correlaciona mais com playmaking; VAEP favorece finalizacao |
| Springer (2025) — Decoding Defensive Performance | XGBoost + DNN para avaliar acoes defensivas com OBV, VAEP, xT |
| PIM — Player Impact Metric (ScienceDirect, 2025) | Pesos aprendidos por regressao logistica ordinal sobre xG + xT |
| Analytics FC (2022) — Breaking the First Line | Random Forest treinado em localizacao, angulo e comprimento de passe |
| Lin (Medium, 2025) — Decoding LBPs in EURO 2024 | Jenks Natural Breaks para detectar linhas defensivas com dados 360 |
| arXiv (2025) — Through the Gaps | Clustering para descobrir LBPs taticos em dados de tracking |

### Composicao por Posicao

As metricas Wyscout utilizadas como proxy, com enfase variavel por posicao:

| Metrica Wyscout | Proxy de | Peso Meia | Peso Extremo | Peso Volante | Peso Lateral | Peso Zagueiro |
|---|---|---|---|---|---|---|
| Passes inteligentes/90 | Smart passes (penetrativos, entre linhas) | Alto | Alto | Medio | Baixo | Baixo |
| Passes em profundidade/90 | Through balls (atras da ultima linha) | Alto | Alto | Medio | Medio | Baixo |
| Passes progressivos/90 | Avancos significativos (quebra da 1a linha) | Alto | Medio | Alto | Alto | Alto |
| Passes para terco final/90 | Quebra da linha de meio-campo | Alto | Medio | Alto | Alto | Alto |
| Passes para a area de penalti/90 | Quebra da ultima linha defensiva | Alto | Alto | Baixo | Medio | Baixo |
| Passes chave/90 | Ultimo passe antes de finalizacao | Medio | Medio | Baixo | Baixo | — |
| Acuracia das metricas acima (%) | Qualidade de execucao | Medio | Medio | Medio | Medio | Medio |

### Validacao

O indice foi projetado para capturar jogadores do perfil "construtor" (Odegaard, De Bruyne, Kroos) que se destacam em:
1. Volume de passes que ultrapassam linhas defensivas
2. Qualidade/precisao desses passes
3. Capacidade de jogar entre linhas com criatividade

---

## Calibracao de Pesos por Posicao (POSITION_WEIGHTS)

### Fontes de Referencia

**Academicas:**
| Referencia | Contribuicao para Pesos |
|---|---|
| Pappalardo et al. (ACM TIST, 2019) — PlayeRank | Pesos role-aware aprendidos por SVM em 31M eventos Wyscout |
| Sanchez-Lopez et al. (Apunts, 2023) — TOPSTATS | 12 variaveis Wyscout por posicao, validadas vs SofaScore (r=0.3-0.88) |
| PIM (ScienceDirect, 2025) | Pesos via regressao logistica ordinal sobre resultados de partida |
| Karakus & Arkadas (arXiv, 2025) | Volantes e laterais sao os maiores produtores de LBPs |
| Ichinose et al. (arXiv, 2025) | Correlacao moderada entre probabilidade de LBP e finalizacoes sofridas |
| Decoding Defensive Performance (Springer, 2025) | XGBoost + DNN com OBV, VAEP, xT para avaliacao defensiva |

**Praticas (Analistas/Plataformas):**
| Referencia | Contribuicao para Pesos |
|---|---|
| StatsBomb Radars (2023 Update) | PAdj Tackles/Interceptions, Deep Progressions, Defensive Action OBV |
| Wyscout Index (dataglossary.wyscout.com) | Pesos oficiais por posicao (nao publicados, mas metricas listadas) |
| Henshaw Analysis (Medium) | Ratings Wyscout com sub-categorias por arquetipo de jogador |
| Cafe Tactiques — PDI (Griffis, 2022) | Media harmonica de smart passes + deep completions + key passes |
| Cafe Tactiques — Defensive Metrics (2023) | Posicionamento > volume; metricas ajust. a posse sao superiores |
| DataMB Radars (datamb.football) | Templates por posicao: progressive passes, carries, duels |
| Soccermatics (soccermatics.readthedocs.io) | Radares Wyscout para scouting estatistico por posicao |
| Breaking The Lines — GK Analytics (2024) | PSxG +/-, sweeper actions, distribution como pilares de avaliacao |
| Analytics FC — GK Ability vs Team (2023) | Volatilidade sazonal de metricas de goleiro; PSxG-GA mais confiavel |
| Soccerment — Advanced Metrics | xGoT, xG per shot, touches in box para atacantes |

### Resumo dos Ajustes Aplicados

**Atacante:** xG reduzido (2.5, delta gols-xG importa mais), recepcao em profundidade aumentada (1.5)

**Extremo:** Corridas progressivas (2.0), passes inteligentes (2.0) — ball-carrying e criatividade sao as armas primarias

**Meia (perfil Odegaard):** Passes inteligentes (2.5), through balls (2.0), passes para area (2.0), acoes defensivas (1.5), passes para frente (1.0) — o meia moderno precisa pressionar e progredir

**Volante:** Intercecoes ajust. posse (2.5), cortes de carrinho ajust. (1.5), passes progressivos (2.0), passes inteligentes (1.5) — Rodri/Fernandinho perfil; DMs sao top line-breakers

**Laterais:** Cruzamentos brutos reduzidos (1.5, correlacao negativa com vitoria per Schimidt), precisao de cruzamentos aumentada (2.0), corridas progressivas (2.5), passes inteligentes (1.0), through balls (1.5), passes para area (1.5)

**Zagueiro:** Passes progressivos (1.5), precisao passes para frente (1.5), intercecoes ajust. posse (2.0), passes inteligentes (1.0) — perfil ball-playing CB moderno

**Goleiro:** Golos prevenidos (3.0, metrica #1 por PSxG research), defesas % reduzida (2.5, inflada por remates faceis), saidas (2.0), passes longos certos (2.0) — sweeper-keeper moderno

---

## Calibracao Academica Brasileira

| Pesquisador | Instituicao | Ano | Contribuicao |
|---|---|---|---|
| Joao Vitor Oliveira | Insper (PIBITI) | 2025 | Coeficientes β de rating por posicao |
| Victor Valvano Schimidt | UNESP | 2021 | Coeficientes de win-probability |
| Eduardo Baptista dos Santos | MBA USP/ICMC | 2024 | Classificacao de jogadores por posicao |
| Frederico Ferra | NOVA IMS | 2025 | PCA + K-Means + RF para clustering |
| Tiago Pinto | ISEP Porto | 2024 | Gradient Boosting para predicao |
| Felipe Nunes | UFMG | 2025 | Fuzzy + Random Forest para recrutamento |
| Gabriel Buso | UFSC | 2025 | Modelos xG e xGOT |
