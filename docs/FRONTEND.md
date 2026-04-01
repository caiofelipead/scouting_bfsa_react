# Documentacao do Frontend — Scouting BFSA

## Visao Geral

Single Page Application (SPA) construida com React 19 + TypeScript, usando Vite como build tool e Tailwind CSS v4 para estilizacao. O frontend e implantado na Vercel com proxy reverso para a API no Render.

---

## Estrutura de Diretorios

```
frontend/
├── src/
│   ├── App.tsx                    # Componente raiz — router com lazy loading
│   ├── main.tsx                   # Entry point — React Query + Theme providers
│   ├── index.css                  # Design system (Tailwind + CSS variables)
│   │
│   ├── components/                # Componentes reutilizaveis
│   │   ├── Layout.tsx             # Layout principal com sidebar de navegacao
│   │   ├── LoginPage.tsx          # Pagina de autenticacao
│   │   ├── PlayerProfile.tsx      # Card de perfil do jogador
│   │   ├── RadarChart.tsx         # Grafico radar (Recharts)
│   │   ├── SkeletonProfile.tsx    # Skeleton loading para perfis
│   │   ├── ErrorBoundary.tsx      # Captura de erros em runtime
│   │   └── report/               # Componentes do relatorio PDF
│   │       ├── ReportHeader.tsx   # Cabecalho com foto e dados
│   │       ├── ReportRadar.tsx    # Radar para relatorio
│   │       ├── WedgeRadar.tsx     # Radar em formato wedge
│   │       ├── DeltaChart.tsx     # Grafico de diferenca (delta)
│   │       ├── StatBox.tsx        # Caixa de metrica individual
│   │       └── SectionDivider.tsx # Separador visual de secoes
│   │
│   ├── pages/                     # Paginas (lazy-loaded)
│   │   ├── DashboardPage.tsx      # Lista de jogadores com filtros
│   │   ├── IndicesPage.tsx        # Indices compostos por jogador
│   │   ├── ReportPage.tsx         # Relatorio detalhado
│   │   ├── ComparisonPage.tsx     # Comparacao lado a lado
│   │   ├── SkillCornerPage.tsx    # Metricas fisicas (SkillCorner)
│   │   ├── DataBrowserPage.tsx    # Navegador de dados brutos
│   │   ├── RankingsPage.tsx       # Rankings por posicao
│   │   ├── PredictionPage.tsx     # Predicao de sucesso
│   │   ├── SimilarityPage.tsx     # Busca de jogadores similares
│   │   ├── ClustersPage.tsx       # Clusterizacao tatica
│   │   ├── AnalysesPage.tsx       # Navegador de analises
│   │   ├── TrajectoryPage.tsx     # Evolucao de carreira (M1)
│   │   ├── OpportunitiesPage.tsx  # Oportunidades de mercado (M3)
│   │   ├── ReplacementsPage.tsx   # Busca de substitutos (M4)
│   │   ├── ContractImpactPage.tsx # Impacto de contratacao (M7)
│   │   ├── ScoutingReportPage.tsx # Relatorio completo com export PDF
│   │   ├── ApiFootballPage.tsx    # Dados API-Football ao vivo
│   │   ├── VAEPPage.tsx           # VAEP ratings + PlayeRank (radar, scatter, tables)
│   │   ├── OfferedPage.tsx        # Jogadores oferecidos
│   │   └── scoutingReportStyles.ts # Estilos do relatorio
│   │
│   ├── hooks/                     # Custom hooks
│   │   ├── useAuth.ts             # Autenticacao (login/logout/token)
│   │   ├── usePlayers.ts          # Queries de jogadores e rankings
│   │   ├── useVaep.ts             # Queries VAEP + PlayeRank (5 hooks)
│   │   ├── useScoutingReport.ts   # Agregacao de queries do relatorio
│   │   └── useApiFootball.ts      # Queries da API-Football
│   │
│   ├── contexts/                  # Contextos React
│   │   └── ThemeContext.tsx        # Tema claro/escuro (localStorage)
│   │
│   ├── lib/                       # Utilitarios
│   │   ├── api.ts                 # Cliente Axios configurado
│   │   ├── utils.ts               # Funcoes utilitarias
│   │   └── countryFlags.ts        # Mapeamento pais → emoji bandeira
│   │
│   ├── types/                     # Tipos TypeScript
│   │   ├── api.ts                 # Interfaces da API
│   │   └── vaep.ts                # Interfaces VAEP + PlayeRank
│   │
│   ├── test/                      # Testes
│   │   └── setup.ts               # Configuracao do Vitest
│   │
│   └── assets/                    # Imagens estaticas
│       ├── botafogo-sp-shield.png # Escudo do Botafogo SP
│       └── ...                    # Outros assets
│
├── package.json                   # Dependencias e scripts
├── vite.config.ts                 # Configuracao Vite + proxy
├── tsconfig.json                  # Configuracao TypeScript
├── vercel.json                    # Rewrites para deploy Vercel
└── eslint.config.js               # Configuracao ESLint
```

---

## Navegacao e Rotas

O sistema utiliza navegacao por abas (tabs) em vez de rotas URL tradicionais. A sidebar agrupa as paginas em 4 secoes:

### ANALISE
| Tab ID | Pagina | Descricao |
|---|---|---|
| `dashboard` | DashboardPage | Lista de jogadores com filtros (posicao, liga, idade) e scout scores |
| `indices` | IndicesPage | Breakdown de indices compostos por jogador |
| `report` | ReportPage | Relatorio detalhado com radar e estatisticas |
| `comparison` | ComparisonPage | Comparacao side-by-side entre dois jogadores |

### MERCADO
| Tab ID | Pagina | Descricao |
|---|---|---|
| `rankings` | RankingsPage | Rankings por posicao com Scout Score Preditivo |
| `prediction` | PredictionPage | Predicao de sucesso de contratacao |
| `trajectory` | TrajectoryPage | Previsao de evolucao de carreira (Modelo 1) |
| `opportunities` | OpportunitiesPage | Deteccao de talentos subvalorizados (Modelo 3) |
| `contract_impact` | ContractImpactPage | Analise de impacto no elenco (Modelo 7) |

### MONITORAMENTO
| Tab ID | Pagina | Descricao |
|---|---|---|
| `skillcorner` | SkillCornerPage | Metricas fisicas do SkillCorner |
| `similarity` | SimilarityPage | Busca de jogadores similares |
| `replacements` | ReplacementsPage | Motor de busca de substitutos (Modelo 4) |
| `clusters` | ClustersPage | Clusterizacao tatica (K-Means + GMM) |

### RELATORIOS
| Tab ID | Pagina | Descricao |
|---|---|---|
| `scouting_report` | ScoutingReportPage | Relatorio completo com exportacao PDF |
| `apifootball` | ApiFootballPage | Dados em tempo real da API-Football |
| `data` | DataBrowserPage | Navegador de dados brutos |
| `analyses` | AnalysesPage | Navegador de analises |

---

## Gerenciamento de Estado

### TanStack React Query
O estado do servidor e gerenciado via React Query com estrategia de cache agressiva para evitar refetches desnecessarios.

**Configuracao padrao:**
- `staleTime`: 5-10 minutos
- `gcTime`: 15-30 minutos
- `retry`: 1 tentativa em caso de falha
- `refetchOnWindowFocus`: desabilitado

**Query Key Factories (usePlayers.ts):**
```typescript
// Exemplo de factory pattern para chaves de query
const playerKeys = {
  all: ['players'] as const,
  lists: () => [...playerKeys.all, 'list'] as const,
  list: (params: PlayerParams) => [...playerKeys.lists(), params] as const,
  detail: (name: string) => [...playerKeys.all, 'detail', name] as const,
};
```

### Autenticacao (useAuth)
- Token JWT armazenado em `localStorage`
- Hook `useAuth()` fornece: `user`, `isAuthenticated`, `login()`, `logout()`
- Interceptor Axios adiciona `Authorization: Bearer <token>` automaticamente
- Auto-redirect para login quando token expira (resposta 401)

### Tema (ThemeContext)
- Suporte a tema claro e escuro
- Preferencia salva em `localStorage`
- Alternancia via toggle na sidebar

---

## Componentes Principais

### Layout.tsx
Componente de layout com sidebar colapsavel contendo:
- Logo do Botafogo SP
- Menu de navegacao com 4 secoes
- Toggle de tema (claro/escuro)
- Informacoes do usuario e botao de logout

### PlayerProfile.tsx
Card de perfil do jogador exibindo:
- Foto do jogador (com fallback)
- Nome, time, posicao, liga, nacionalidade
- Scout Score com badge de classificacao (Elite/Above/Average/Below)
- Badge de performance com codigo de cores

### RadarChart.tsx
Grafico radar usando Recharts com:
- 6+ atributos por posicao
- Valores percentuais (0-100)
- Estilo Wyscout com labels customizados
- Suporte a overlay de comparacao

### Componentes de Relatorio (report/)
Suite de componentes para geracao de relatorios PDF:
- **ReportHeader:** Cabecalho com foto, escudo e dados basicos
- **ReportRadar:** Radar full-page para o relatorio
- **WedgeRadar:** Radar em formato de cunha para comparacoes
- **DeltaChart:** Grafico de barras mostrando diferenca vs titular
- **StatBox:** Caixa individual de metrica com valor e percentil
- **SectionDivider:** Separador visual entre secoes do relatorio

---

## Sistema de Design (CSS)

### Fontes
- **Display:** Space Grotesk (branding)
- **Body:** Geist (interface)
- **Mono:** JetBrains Mono (dados numericos)

### Paleta de Cores (Tema Escuro — padrao)
| Token | Cor | Uso |
|---|---|---|
| `--color-void` | `#0A0A0A` | Background da pagina |
| `--color-surface-0` | `#0E0E0E` | Superficie nivel 0 |
| `--color-surface-1` | `#141414` | Superficie nivel 1 |
| `--color-surface-2` | `#1A1A1A` | Superficie nivel 2 |
| `--color-surface-3` | `#262626` | Superficie nivel 3 |
| `--color-accent` | `#E30613` | Vermelho Botafogo (destaque) |
| `--color-text-primary` | `#FFFFFF` | Texto principal |
| `--color-text-secondary` | `#A1A1AA` | Texto secundario |
| `--color-text-muted` | `#71717A` | Texto esmaecido |

### Badges de Score
| Classificacao | Cor | Faixa |
|---|---|---|
| Elite | `#22c55e` (verde) | Score >= 75 |
| Above Average | `#eab308` (amarelo) | Score >= 60 |
| Average | `#f97316` (laranja) | Score >= 40 |
| Below Average | `#ef4444` (vermelho) | Score < 40 |

### Classes CSS Customizadas
```css
.player-photo-hex    /* Foto hexagonal do jogador */
.score-elite         /* Badge Elite */
.score-above         /* Badge Above Average */
.badge-top-target    /* Badge de recomendacao */
.noise-overlay       /* Efeito de textura */
```

---

## Cliente HTTP (api.ts)

O cliente Axios e configurado com:

1. **Base URL:** `/api` (proxy para backend)
2. **Timeout:** 60 segundos (cold start do backend)
3. **Interceptor de Request:** Adiciona token JWT automaticamente
4. **Interceptor de Response:**
   - Retry automatico para 502/503/504 (ate 6 tentativas)
   - Backoff exponencial: 3s, 6s, 12s, 24s, 30s, 30s
   - Limpeza de sessao em caso de 401

---

## Exportacao PDF (ScoutingReportPage)

Fluxo de geracao do relatorio PDF:

1. Usuario seleciona jogador candidato e titular atual
2. Frontend agrega 9 queries paralelas via `useScoutingReport()`
3. Dados renderizados em template HTML (1440x1812px)
4. `html-to-image` converte cada secao em PNG
5. `jsPDF` monta o PDF com todas as paginas
6. Download automatico do arquivo

---

## Scripts Disponiveis

```bash
npm run dev       # Inicia servidor de desenvolvimento (porta 5173)
npm run build     # Build de producao otimizado
npm run preview   # Preview do build de producao
npm run lint      # Executa ESLint
npm run test      # Executa testes (Vitest)
npm run test:watch # Testes em modo watch
```

---

## Otimizacoes de Performance

1. **Lazy Loading:** Todas as 17 paginas carregadas sob demanda
2. **Code Splitting:** Chunks separados por pagina (~40-80KB cada)
3. **Query Caching:** Cache de 5-10 min evita refetches
4. **Skeleton Loading:** Placeholders visuais durante carregamento
5. **Debounced Search:** Debounce de 300ms na busca de jogadores
6. **Image Proxy:** Cache local de logos e fotos via CORS proxy
7. **Dynamic Imports:** html-to-image e jsPDF so carregam no clique de export
