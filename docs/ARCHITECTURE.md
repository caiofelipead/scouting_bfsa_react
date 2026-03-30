# Arquitetura do Sistema — Scouting BFSA

## Visão Geral

O Scouting BFSA é uma plataforma profissional de análise e avaliação de jogadores de futebol, desenvolvida para o Botafogo SA Ribeirão Preto. O sistema combina modelos preditivos de Machine Learning com visualizações interativas estilo Wyscout.

---

## Diagrama de Arquitetura

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          FONTES DE DADOS                                │
│                                                                         │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐                │
│  │ Google Sheets │   │  API-Football │   │  SkillCorner  │               │
│  │  (Wyscout)    │   │    (v3)       │   │  (Físico)     │               │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘                │
│         │                   │                   │                        │
└─────────┼───────────────────┼───────────────────┼────────────────────────┘
          │                   │                   │
          ▼                   ▼                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        BACKEND (FastAPI)                                 │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    Camada de Dados                               │    │
│  │  ┌──────────┐   ┌───────────┐   ┌──────────────┐               │    │
│  │  │PostgreSQL │   │data_loader│   │  sync_sheets  │              │    │
│  │  │  (Dados)  │◄──│  (.py)    │◄──│    (.py)      │              │    │
│  │  └──────────┘   └───────────┘   └──────────────┘               │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                Motor Analítico (7 Modelos ML)                   │    │
│  │                                                                  │    │
│  │  ┌──────────────────┐  ┌──────────────────┐                     │    │
│  │  │ scouting_         │  │ predictive_       │                    │    │
│  │  │ intelligence.py   │  │ engine.py         │                    │    │
│  │  │ (M1-M7)           │  │ (SSP, WP, Cluster)│                   │    │
│  │  └──────────────────┘  └──────────────────┘                     │    │
│  │                                                                  │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐      │    │
│  │  │ similarity.py │  │calibration.py│  │league_power_     │      │    │
│  │  │(Cosine+Maha+  │  │(Acadêmico)   │  │model.py (Opta)   │      │    │
│  │  │ LineBrkPass)  │  │              │  │                  │      │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘      │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                  Serviços Auxiliares                             │    │
│  │  ┌────────────┐  ┌─────────────┐  ┌──────────────┐             │    │
│  │  │enrichment  │  │fuzzy_match  │  │player_assets │             │    │
│  │  │(.py)       │  │(.py)        │  │(.py)         │             │    │
│  │  └────────────┘  └─────────────┘  └──────────────┘             │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │          Autenticação & Segurança                               │    │
│  │  ┌──────────┐  ┌─────────┐  ┌──────────┐  ┌─────────────┐     │    │
│  │  │ JWT Auth │  │ bcrypt  │  │  CORS    │  │ Rate Limit  │     │    │
│  │  │ (auth.py)│  │ (hash)  │  │ (CORS)  │  │ (slowapi)   │     │    │
│  │  └──────────┘  └─────────┘  └──────────┘  └─────────────┘     │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Servidor: Uvicorn | GZip | Deploy: Render                             │
└──────────────────────────┬───────────────────────────────────────────────┘
                           │
                      API REST (JSON)
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                     FRONTEND (React 19 + TypeScript)                    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    Camada de Estado                              │    │
│  │  ┌─────────────────┐  ┌──────────┐  ┌────────────────┐         │    │
│  │  │ TanStack React  │  │ useAuth  │  │ ThemeContext    │         │    │
│  │  │ Query (cache)   │  │ (JWT)    │  │ (light/dark)   │         │    │
│  │  └─────────────────┘  └──────────┘  └────────────────┘         │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    17 Páginas (Lazy-loaded)                      │    │
│  │  Dashboard │ Índices │ Relatório │ Comparativo │ Rankings       │    │
│  │  Predição │ Trajetória │ Oportunidades │ Substituições          │    │
│  │  Impacto │ SkillCorner │ Similaridade │ Clusters               │    │
│  │  Scouting Report │ API-Football │ Dados │ Análises             │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                   Componentes Visuais                           │    │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐                │    │
│  │  │ RadarChart │  │PlayerProf. │  │ Report/*   │                │    │
│  │  │ (Recharts) │  │ (Perfil)   │  │ (PDF)      │                │    │
│  │  └────────────┘  └────────────┘  └────────────┘                │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Build: Vite 7 | CSS: Tailwind v4 | Deploy: Vercel                     │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Fluxo de Dados

### 1. Ingestão de Dados
```
Google Sheets (dados Wyscout) → sync_sheets.py → data_loader.py → PostgreSQL
```

### 2. Processamento Analítico
```
PostgreSQL → enrichment.py → calibration.py → scouting_intelligence.py (7 modelos)
                                             → predictive_engine.py (SSP, WP, clustering)
                                             → similarity.py (Cosine + Mahalanobis)
```

### 3. Entrega ao Frontend
```
FastAPI endpoints (JSON) → Axios (com JWT) → React Query (cache) → Componentes React
```

### 4. Exportação
```
Componentes React → html-to-image (PNG) → jsPDF → Download PDF
```

---

## Stack Tecnológica

### Frontend
| Tecnologia | Versão | Função |
|---|---|---|
| React | 19.2 | Framework de UI |
| TypeScript | 5.9 | Tipagem estática |
| Vite | 7.3 | Build tool e dev server |
| Tailwind CSS | 4.2 | Framework CSS utilitário |
| TanStack React Query | 5.90 | Gerenciamento de estado servidor |
| Axios | 1.13 | Cliente HTTP |
| Recharts | 3.8 | Gráficos e visualizações |
| Framer Motion | 12.35 | Animações |
| Lucide React | 0.577 | Ícones |
| html-to-image | 1.11 | Exportação de imagens |
| jsPDF | 4.2 | Geração de PDF |

### Backend
| Tecnologia | Versão | Função |
|---|---|---|
| FastAPI | 0.104+ | Framework web assíncrono |
| Uvicorn | 0.24+ | Servidor ASGI |
| PostgreSQL | - | Banco de dados principal |
| Pandas | 2.1+ | Análise de dados |
| NumPy | 1.24+ | Computação numérica |
| scikit-learn | 1.3+ | Machine Learning |
| python-jose | 3.3+ | Tokens JWT |
| bcrypt | 4.0+ | Hash de senhas |
| RapidFuzz | 3.5+ | Matching fuzzy de strings |
| slowapi | 0.1.9+ | Rate limiting |
| aiohttp | 3.9+ | HTTP assíncrono |
| cachetools | 5.3+ | Cache com TTL |
| Google API Client | 2.100+ | Integração Google Sheets |

---

## Infraestrutura de Deploy

### Frontend (Vercel)
- Build automático via push no repositório
- Proxy reverso: `/api/*` → backend no Render
- Analytics e Speed Insights do Vercel integrados

### Backend (Render)
- Servidor Uvicorn com compressão GZip
- PostgreSQL como banco de dados
- Rate limiting: 300 requisições/minuto por IP
- Variáveis de ambiente configuradas no painel do Render

### Comunicação
- Frontend chama `/api/*` → Vercel redireciona para `https://scouting-bfsa-react.onrender.com/api/*`
- Em desenvolvimento local: Vite proxy redireciona `/api` para `http://localhost:8000`

---

## Padrões de Projeto

### Frontend
- **Lazy Loading:** Todas as 17 páginas são carregadas sob demanda via `React.lazy()`
- **Code Splitting:** Cada página gera um chunk separado no build
- **Query Caching:** Stale time de 5-10min evita refetches desnecessários
- **Error Boundary:** Componente wrapper para captura de erros em runtime
- **Interceptors:** Token JWT adicionado automaticamente a todas as requisições

### Backend
- **Service Layer:** Lógica de negócio isolada em `/services/`
- **Route Layer:** Endpoints organizados em `/routes/`
- **Schema Validation:** Pydantic para validação de request/response
- **TTL Cache:** Endpoints pesados com cache de 5 minutos
- **Retry com Backoff:** Retentativas exponenciais para erros 502/503/504
