# Documentacao da API — Scouting BFSA

## Visao Geral

API REST construida com FastAPI, servida via Uvicorn com compressao GZip e rate limiting (300 req/min por IP).

**Base URL:**
- Producao: `https://scouting-bfsa-react.onrender.com/api`
- Desenvolvimento: `http://localhost:8000/api`

**Autenticacao:** Bearer Token (JWT) em todas as rotas exceto `/auth/login`.

---

## Autenticacao

### `POST /auth/login`
Autentica um usuario e retorna token JWT.

**Request:**
```json
{
  "email": "admin@example.com",
  "password": "senha123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "email": "admin@example.com",
    "name": "Administrador"
  }
}
```

### `POST /auth/me`
Retorna dados do usuario autenticado.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "email": "admin@example.com",
  "name": "Administrador"
}
```

### `POST /auth/logout`
Invalida a sessao atual.

---

## Jogadores (Core)

### `GET /players`
Lista jogadores com filtros opcionais.

**Query Parameters:**
| Parametro | Tipo | Descricao |
|---|---|---|
| `position` | string | Filtrar por posicao (ex: "Atacante") |
| `league` | string | Filtrar por liga |
| `min_age` | int | Idade minima |
| `max_age` | int | Idade maxima |
| `search` | string | Busca por nome |
| `page` | int | Pagina (default: 1) |
| `per_page` | int | Itens por pagina (default: 50) |

**Response (200):**
```json
{
  "players": [
    {
      "name": "Jogador Exemplo",
      "team": "Botafogo SP",
      "position": "Atacante",
      "league": "Serie B",
      "nationality": "Brazil",
      "age": 24,
      "minutes_played": 2340,
      "scout_score": 72.5
    }
  ],
  "total": 1500,
  "page": 1,
  "per_page": 50
}
```

### `GET /players/{name}/profile`
Retorna perfil completo de um jogador.

**Response (200):**
```json
{
  "name": "Jogador Exemplo",
  "team": "Botafogo SP",
  "position": "Atacante",
  "league": "Serie B",
  "nationality": "Brazil",
  "age": 24,
  "minutes_played": 2340,
  "scout_score": 72.5,
  "performance_class": "Above Average",
  "photo_url": "https://...",
  "team_logo_url": "https://...",
  "percentile": 78,
  "metrics": { ... }
}
```

### `GET /players/{name}/radar`
Retorna dados do radar de atributos (estilo Wyscout).

**Response (200):**
```json
{
  "labels": ["Finalizacao", "Passe", "Drible", "Defesa", "Fisico", "Criacao"],
  "values": [85, 72, 68, 45, 78, 71],
  "percentiles": [92, 78, 65, 40, 82, 73]
}
```

### `GET /players/{name}/indices`
Retorna indices compostos do jogador por posicao, incluindo o indice "Passes Quebrando Linhas" (proxy de line-breaking passes do StatsBomb 360).

**Response (200):**
```json
{
  "player": "Jogador Exemplo",
  "position": "Atacante",
  "indices": [
    {
      "name": "Finalizacao",
      "value": 85.2,
      "percentile": 92,
      "metrics": [
        { "name": "Goals per 90", "value": 0.45, "percentile": 88 },
        { "name": "xG per 90", "value": 0.38, "percentile": 85 }
      ]
    },
    {
      "name": "Passes Quebrando Linhas",
      "value": 72.5,
      "percentile": 78,
      "metrics": [
        { "name": "Passes inteligentes/90", "value": 2.1, "percentile": 82 },
        { "name": "Passes em profundidade/90", "value": 0.8, "percentile": 75 },
        { "name": "Passes progressivos/90", "value": 5.3, "percentile": 71 }
      ]
    }
  ]
}
```

---

## Rankings

### `POST /rankings`
Retorna ranking de jogadores por posicao com Scout Score.

**Request:**
```json
{
  "position": "Atacante",
  "league": "Serie B",
  "top_n": 20,
  "min_minutes": 900
}
```

**Response (200):**
```json
{
  "rankings": [
    {
      "rank": 1,
      "name": "Jogador Exemplo",
      "team": "Botafogo SP",
      "scout_score": 85.3,
      "performance_class": "Elite",
      "age": 24,
      "minutes_played": 2340
    }
  ]
}
```

---

## Analise Comparativa

### `POST /comparison`
Compara dois jogadores lado a lado.

**Request:**
```json
{
  "player_a": "Jogador A",
  "player_b": "Jogador B"
}
```

### `POST /similarity`
Encontra jogadores similares a um jogador de referencia.

**Request:**
```json
{
  "player_name": "Jogador Exemplo",
  "top_n": 10,
  "position": "Atacante"
}
```

---

## Scouting Intelligence Engine (7 Modelos)

### Modelo 1: `POST /trajectory`
Previsao de evolucao de carreira usando Gradient Boosting.

**Request:**
```json
{
  "player_name": "Jogador Exemplo"
}
```

**Response (200):**
```json
{
  "player": "Jogador Exemplo",
  "predicted_rating_next_season": 78.5,
  "trajectory_score": 82.3,
  "trajectory_class": "improving",
  "confidence": 0.85
}
```

### Modelo 2: `POST /market_value`
Estimativa de valor de mercado com XGBoost.

**Request:**
```json
{
  "player_name": "Jogador Exemplo"
}
```

**Response (200):**
```json
{
  "player": "Jogador Exemplo",
  "estimated_market_value": 2500000,
  "market_value_gap": -500000,
  "valuation_model": "xgboost_striker_young"
}
```

### Modelo 3: `POST /market_opportunities`
Deteccao de oportunidades de mercado — talentos subvalorizados.

**Request:**
```json
{
  "position": "Atacante",
  "top_n": 15,
  "min_minutes": 900
}
```

**Response (200):**
```json
{
  "opportunities": [
    {
      "name": "Jogador Exemplo",
      "market_opportunity_score": 87.3,
      "classification": "Exceptional",
      "components": {
        "performance": 85,
        "trajectory": 90,
        "value_gap": 80,
        "age_penalty": -5
      }
    }
  ]
}
```

### Modelo 4: `POST /replacements`
Motor de busca de substitutos com similaridade multi-metodo.

**Request:**
```json
{
  "player_name": "Jogador Referencia",
  "top_n": 10
}
```

**Response (200):**
```json
{
  "reference_player": "Jogador Referencia",
  "replacements": [
    {
      "name": "Substituto 1",
      "similarity_score": 0.92,
      "cosine_similarity": 0.95,
      "mahalanobis_distance": 0.88,
      "cluster_proximity": 0.93,
      "trajectory_score": 78,
      "estimated_value": 1500000
    }
  ]
}
```

### Modelo 6: `GET /league_powers`
Coeficientes Opta Power Rankings por liga.

**Response (200):**
```json
{
  "leagues": [
    { "league": "Premier League", "power_ranking": 95.2 },
    { "league": "Serie A BR", "power_ranking": 62.8 }
  ]
}
```

### Modelo 7: `POST /contract_impact`
Analise de impacto de contratacao no elenco.

**Request:**
```json
{
  "candidate_player": "Jogador Candidato",
  "position": "Atacante"
}
```

**Response (200):**
```json
{
  "candidate": "Jogador Candidato",
  "impact_score": 78.5,
  "classification": "Alto Impacto",
  "recommendation": "Recomendado",
  "components": {
    "positional_need": 85,
    "quality_uplift": 80,
    "tactical_complementarity": 72,
    "age_profile": 90,
    "financial_efficiency": 65,
    "risk_assessment": 78
  }
}
```

---

## VAEP & PlayeRank

### `POST /vaep/run-pipeline`
Executa o pipeline VAEP completo. Calcula valores de acao e ratings por jogador.

**Request:**
```json
{
  "season": "2024/25",
  "competition_id": null
}
```

**Response (200):**
```json
{
  "season": "2024/25",
  "method": "heuristic_vaep",
  "total_players": 450,
  "total_actions": 0,
  "total_games": 0,
  "top_players": [
    {
      "player_name": "Jogador Exemplo",
      "team": "Botafogo SP",
      "league": "Serie B",
      "position": "Atacante",
      "minutes_played": 2340,
      "total_vaep": 12.45,
      "vaep_per90": 0.478,
      "offensive_vaep": 0.385,
      "defensive_vaep": 0.093,
      "actions_count": 0,
      "season": "2024/25"
    }
  ]
}
```

### `GET /vaep/ratings`
Retorna ratings VAEP pre-calculados com filtros opcionais.

**Query Parameters:**
| Parametro | Tipo | Descricao |
|---|---|---|
| `position` | string | Filtrar por posicao |
| `min_minutes` | int | Minutos minimos (default: 0) |
| `season` | string | Temporada |
| `league` | string | Liga |

**Response (200):**
```json
{
  "total": 450,
  "season": "2024/25",
  "ratings": [
    {
      "player_name": "Jogador Exemplo",
      "team": "Botafogo SP",
      "vaep_per90": 0.478,
      "offensive_vaep": 0.385,
      "defensive_vaep": 0.093
    }
  ]
}
```

### `GET /vaep/player/{player_name}`
Retorna VAEP detalhado de um jogador com top acoes valoradas.

**Response (200):**
```json
{
  "player_name": "Jogador Exemplo",
  "vaep_per90": 0.478,
  "offensive_vaep": 0.385,
  "defensive_vaep": 0.093,
  "top_actions": [
    {
      "action_type": "pass",
      "vaep_value": 0.045,
      "offensive_value": 0.038,
      "defensive_value": 0.007,
      "x_start": 45.2,
      "y_start": 30.1,
      "x_end": 78.5,
      "y_end": 42.3,
      "minute": 67,
      "second": 23
    }
  ]
}
```

### `GET /vaep/compare`
Comparacao VAEP entre jogadores selecionados.

**Query Parameters:**
| Parametro | Tipo | Descricao |
|---|---|---|
| `player_names` | string[] | Nomes dos jogadores (2-10) |
| `season` | string | Temporada (opcional) |

**Response (200):**
```json
{
  "players": [
    { "player_name": "Jogador A", "vaep_per90": 0.478, "offensive_vaep": 0.385, "defensive_vaep": 0.093 },
    { "player_name": "Jogador B", "vaep_per90": 0.352, "offensive_vaep": 0.210, "defensive_vaep": 0.142 }
  ]
}
```

### `GET /playerank/rankings`
Rankings PlayeRank multi-dimensional filtrados por cluster e dimensao.

**Query Parameters:**
| Parametro | Tipo | Descricao |
|---|---|---|
| `role_cluster` | string | Filtrar por role tatico (ex: "Goal Scorer", "Playmaker") |
| `dimension` | string | Ordenar por dimensao (scoring_dim, playmaking_dim, etc.) |
| `league` | string | Filtrar por liga |
| `season` | string | Temporada |

**Response (200):**
```json
{
  "total": 120,
  "role_cluster": "Goal Scorer",
  "season": "2024/25",
  "rankings": [
    {
      "player_name": "Jogador Exemplo",
      "team": "Botafogo SP",
      "role_cluster": "Goal Scorer",
      "composite_score": 78.5,
      "dimensions": {
        "scoring": 92,
        "playmaking": 45,
        "defending": 20,
        "physical": 68,
        "possession": 55
      },
      "percentile_in_cluster": 95.2,
      "cluster_size": 42
    }
  ]
}
```

---

## Clustering Tatico

### `POST /clusters`
Classificacao tatica por agrupamento de perfis similares.

**Request:**
```json
{
  "position": "Atacante",
  "n_clusters": 5
}
```

---

## Predicao de Contratacao

### `POST /prediction`
Probabilidade de sucesso de contratacao.

**Request:**
```json
{
  "player_name": "Jogador Exemplo"
}
```

---

## SkillCorner (Dados Fisicos)

### `GET /skillcorner/search`
Busca jogadores no banco SkillCorner.

**Query Parameters:**
| Parametro | Tipo | Descricao |
|---|---|---|
| `query` | string | Nome do jogador |

### `GET /skillcorner/player/{name}`
Metricas fisicas de um jogador.

**Response (200):**
```json
{
  "name": "Jogador Exemplo",
  "metrics": {
    "sprints_per_90": 28.5,
    "max_speed_kmh": 34.2,
    "accelerations_per_90": 42.1,
    "distance_per_90_km": 10.8,
    "high_intensity_runs": 85,
    "pressing_intensity": 7.2
  }
}
```

### `POST /skillcorner/comparison`
Compara metricas fisicas entre dois jogadores.

### `GET /skillcorner/coverage`
Lista ligas cobertas pelo SkillCorner.

---

## API-Football (Dados ao Vivo)

### `GET /apifootball/leagues`
Lista ligas disponiveis.

### `GET /apifootball/teams`
Lista times por liga.

**Query Parameters:** `league_id` (int)

### `GET /apifootball/standings`
Classificacao de uma liga.

**Query Parameters:** `league_id` (int), `season` (int)

### `GET /apifootball/fixtures`
Partidas de um time ou liga.

**Query Parameters:** `team_id` (int), `league_id` (int), `season` (int)

### `GET /apifootball/squad`
Elenco de um time.

**Query Parameters:** `team_id` (int)

### `GET /apifootball/player-stats`
Estatisticas de um jogador por temporada.

---

## Configuracao

### `GET /config/positions`
Lista posicoes disponiveis no sistema.

### `GET /config/leagues`
Lista ligas disponiveis no sistema.

---

## Utilitarios

### `GET /api/image-proxy`
Proxy CORS para imagens externas.

**Query Parameters:** `url` (string) — URL da imagem

### `GET /api/team-logo/{team}`
Logo do time com cache local.

---

## Codigos de Erro

| Codigo | Descricao |
|---|---|
| 400 | Requisicao invalida (parametros faltando ou incorretos) |
| 401 | Token invalido ou expirado |
| 403 | Acesso negado |
| 404 | Recurso nao encontrado |
| 429 | Rate limit excedido (max 300 req/min) |
| 500 | Erro interno do servidor |
| 502/503/504 | Backend indisponivel (cold start — cliente deve fazer retry) |

---

## Rate Limiting

- **Limite:** 300 requisicoes por minuto por IP
- **Implementacao:** slowapi (baseado em limits)
- **Header de resposta:** `X-RateLimit-Remaining`, `X-RateLimit-Limit`

## Autenticacao JWT

- **Algoritmo:** HS256
- **Expiracao:** 480 minutos (8 horas), configuravel via `TOKEN_EXPIRE_MINUTES`
- **Header:** `Authorization: Bearer <token>`
- **Token refresh:** Via `POST /auth/me` (retorna novo token se valido)
