import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Database,
  Activity,
  Users,
  Trophy,
  BarChart3,
  Search,
  ChevronDown,
  ChevronRight,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Target,
  TrendingUp,
  Calendar,
  Shield,
  Zap,
} from 'lucide-react';
import {
  useSoccerDataHealth,
  useSoccerDataExplore,
  useSeasonXg,
  usePlayerPredictions,
  useSeasonSimulation,
  useSquads,
  useRankings,
} from '../hooks/useSoccerData';

// ── Known IDs (Opta-style) ─────────────────────────────────────────
// tmcl = tournament calendar ID (used as query param or path segment)

const TOURNAMENTS = [
  { tmcl: 'tmcl9n3sycmiqlbc6uvwkqmz9', label: 'Serie A Brasil 2025' },
  { tmcl: 'u2o8k2phxqftls4yvzm3j8u5c', label: 'Serie B Brasil 2025' },
  { tmcl: '4eot5d7lhrv9s97lp6j9nfmys', label: 'Premier League 2024/25' },
  { tmcl: '34pl8szyvrbwcmfkuocjm3r6t', label: 'La Liga 2024/25' },
  { tmcl: '1r097lpxe0xn03ihb7wi98kao', label: 'Serie A Italia 2024/25' },
  { tmcl: '6by3h89i2eykc341oz7lv1ddd', label: 'Bundesliga 2024/25' },
  { tmcl: '4s076msj76570wzkzck9xrjr5', label: 'Ligue 1 2024/25' },
];

// contestant_id = team/club ID (from screenshot: Botafogo-SP = 1t97ffnd5cp7611ay7ucgk9qak)
const KNOWN_TEAMS = [
  { id: '1t97ffnd5cp7611ay7ucgk9qak', label: 'Botafogo-SP' },
  { id: 'bekmuil8m1ynqfk5kgibnf0y9', label: 'Botafogo RJ' },
  { id: '85fk31okjdvs0ydsbtd1nl0k5', label: 'Palmeiras' },
  { id: '4ap2kcrxbjoa39t05j34tlmxy', label: 'Flamengo' },
  { id: '1tnk5ksq27fh7a3d7d6b85rit', label: 'Corinthians' },
  { id: 'eiv6s9ydxh4ihc8p2lnmug7v5', label: 'Sao Paulo' },
];

const BOTAFOGO_SP = KNOWN_TEAMS[0];

// ── Tab definitions ─────────────────────────────────────────────────

type TabId = 'overview' | 'xg' | 'predictions' | 'simulation' | 'squads' | 'rankings' | 'explorer';

const TABS: { id: TabId; label: string; icon: React.ReactNode }[] = [
  { id: 'overview', label: 'Visao Geral', icon: <Activity size={14} /> },
  { id: 'xg', label: 'Expected Goals', icon: <Target size={14} /> },
  { id: 'predictions', label: 'Predicoes', icon: <TrendingUp size={14} /> },
  { id: 'simulation', label: 'Simulacao', icon: <BarChart3 size={14} /> },
  { id: 'squads', label: 'Elencos', icon: <Users size={14} /> },
  { id: 'rankings', label: 'Classificacao', icon: <Trophy size={14} /> },
  { id: 'explorer', label: 'Explorer', icon: <Search size={14} /> },
];

// ── JSON Viewer Component ───────────────────────────────────────────

function JsonViewer({ data, depth = 0, maxDepth = 4 }: { data: unknown; depth?: number; maxDepth?: number }) {
  const [collapsed, setCollapsed] = useState(depth >= 2);

  if (data === null || data === undefined) {
    return <span className="text-gray-500 italic">null</span>;
  }
  if (typeof data === 'string') {
    return <span className="text-green-400">"{data}"</span>;
  }
  if (typeof data === 'number') {
    return <span className="text-blue-400">{data}</span>;
  }
  if (typeof data === 'boolean') {
    return <span className="text-yellow-400">{data ? 'true' : 'false'}</span>;
  }

  if (Array.isArray(data)) {
    if (data.length === 0) return <span className="text-gray-500">[]</span>;
    if (depth >= maxDepth) return <span className="text-gray-500">[...{data.length} items]</span>;
    return (
      <div className="ml-3">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="text-gray-400 hover:text-white text-xs flex items-center gap-1"
        >
          {collapsed ? <ChevronRight size={12} /> : <ChevronDown size={12} />}
          <span className="text-purple-400">Array</span>
          <span className="text-gray-500">({data.length})</span>
        </button>
        {!collapsed && (
          <div className="ml-2 border-l border-gray-800 pl-2">
            {data.slice(0, 30).map((item, i) => (
              <div key={i} className="py-0.5">
                <span className="text-gray-600 text-[10px] mr-1">{i}:</span>
                <JsonViewer data={item} depth={depth + 1} maxDepth={maxDepth} />
              </div>
            ))}
            {data.length > 30 && (
              <span className="text-gray-500 text-xs">...+{data.length - 30} items</span>
            )}
          </div>
        )}
      </div>
    );
  }

  if (typeof data === 'object') {
    const entries = Object.entries(data as Record<string, unknown>);
    if (entries.length === 0) return <span className="text-gray-500">{'{}'}</span>;
    if (depth >= maxDepth) return <span className="text-gray-500">{'{'} ...{entries.length} keys {'}'}</span>;
    return (
      <div className="ml-3">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="text-gray-400 hover:text-white text-xs flex items-center gap-1"
        >
          {collapsed ? <ChevronRight size={12} /> : <ChevronDown size={12} />}
          <span className="text-cyan-400">Object</span>
          <span className="text-gray-500">({entries.length} keys)</span>
        </button>
        {!collapsed && (
          <div className="ml-2 border-l border-gray-800 pl-2">
            {entries.map(([key, value]) => (
              <div key={key} className="py-0.5">
                <span className="text-orange-300 text-xs">{key}: </span>
                <JsonViewer data={value} depth={depth + 1} maxDepth={maxDepth} />
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  return <span className="text-gray-400">{String(data)}</span>;
}

// ── Data Panel (reusable) ───────────────────────────────────────────

function DataPanel({
  title,
  icon,
  data,
  isLoading,
  isError,
  error,
  emptyMessage,
}: {
  title: string;
  icon: React.ReactNode;
  data: unknown;
  isLoading: boolean;
  isError: boolean;
  error: unknown;
  emptyMessage?: string;
}) {
  return (
    <div className="card overflow-hidden">
      <div className="p-3 border-b border-gray-800 flex items-center gap-2">
        {icon}
        <h3 className="text-sm font-semibold">{title}</h3>
      </div>
      <div className="p-4 max-h-[600px] overflow-y-auto">
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 size={20} className="animate-spin text-blue-400" />
            <span className="ml-2 text-xs text-gray-400">Carregando...</span>
          </div>
        )}
        {isError && (
          <div className="flex items-center gap-2 text-red-400 text-xs py-4">
            <AlertCircle size={14} />
            <span>{(error as any)?.response?.data?.detail || (error as any)?.message || 'Erro ao carregar dados'}</span>
          </div>
        )}
        {!isLoading && !isError && !data && (
          <p className="text-xs text-gray-500 py-4">{emptyMessage || 'Nenhum dado disponivel'}</p>
        )}
        {!isLoading && !isError && data && (
          <div className="font-mono text-xs">
            <JsonViewer data={data} />
          </div>
        )}
      </div>
    </div>
  );
}

// ── Selector Components ─────────────────────────────────────────────

function TournamentSelector({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <div className="flex items-center gap-2">
      <label className="text-xs text-gray-400">Competicao (tmcl)</label>
      <select value={value} onChange={(e) => onChange(e.target.value)} className="input-field text-xs">
        {TOURNAMENTS.map((t) => (
          <option key={t.tmcl} value={t.tmcl}>{t.label}</option>
        ))}
      </select>
    </div>
  );
}

function TeamSelector({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <div className="flex items-center gap-2">
      <label className="text-xs text-gray-400">Equipe</label>
      <select value={value} onChange={(e) => onChange(e.target.value)} className="input-field text-xs">
        {KNOWN_TEAMS.map((t) => (
          <option key={t.id} value={t.id}>{t.label}</option>
        ))}
      </select>
    </div>
  );
}

// ── Overview Tab ────────────────────────────────────────────────────

function OverviewTab() {
  const health = useSoccerDataHealth();

  return (
    <div className="space-y-4">
      <div className="card p-4">
        <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
          <Database size={16} className="text-blue-400" />
          Status da Conexao
        </h3>
        {health.isLoading && (
          <div className="flex items-center gap-2 text-gray-400 text-xs">
            <Loader2 size={14} className="animate-spin" />
            Verificando conexao...
          </div>
        )}
        {health.data && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              {health.data.configured ? (
                <CheckCircle2 size={14} className="text-green-400" />
              ) : (
                <AlertCircle size={14} className="text-red-400" />
              )}
              <span className="text-xs">
                API Key: {health.data.configured ? 'Configurada' : 'Nao configurada'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              {health.data.status === 'ok' ? (
                <CheckCircle2 size={14} className="text-green-400" />
              ) : (
                <AlertCircle size={14} className="text-yellow-400" />
              )}
              <span className="text-xs">Status: {health.data.status} — {health.data.message}</span>
            </div>
          </div>
        )}
        {!health.data?.configured && !health.isLoading && (
          <div className="mt-3 p-3 rounded bg-yellow-900/20 border border-yellow-800/30">
            <p className="text-[11px] text-yellow-300">
              Configure a variavel de ambiente <code className="bg-gray-800 px-1 rounded">RAPIDAPI_SOCCER_DATA_KEY</code> no backend
              com sua chave do RapidAPI para ativar esta integracao.
            </p>
          </div>
        )}
      </div>

      <div className="card p-4">
        <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
          <Zap size={16} className="text-yellow-400" />
          Endpoints Disponiveis
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {[
            { icon: <Target size={14} className="text-red-400" />, name: 'Season xG', desc: 'Gols esperados por temporada' },
            { icon: <TrendingUp size={14} className="text-blue-400" />, name: 'Player Predictions', desc: 'Predicoes ML de desempenho' },
            { icon: <BarChart3 size={14} className="text-purple-400" />, name: 'Season Simulation', desc: 'Simulacao de temporada' },
            { icon: <Users size={14} className="text-green-400" />, name: 'Squads', desc: 'Elencos detalhados' },
            { icon: <Trophy size={14} className="text-yellow-400" />, name: 'Rankings', desc: 'Classificacao e standings' },
            { icon: <Calendar size={14} className="text-cyan-400" />, name: 'Fixtures', desc: 'Jogos e resultados' },
            { icon: <Shield size={14} className="text-orange-400" />, name: 'Team Stats', desc: 'Estatisticas de equipe' },
            { icon: <Activity size={14} className="text-pink-400" />, name: 'Match Facts', desc: 'Fatos e stats de partidas' },
            { icon: <BarChart3 size={14} className="text-indigo-400" />, name: 'Win Probability', desc: 'Probabilidade de vitoria' },
          ].map((ep) => (
            <div key={ep.name} className="flex items-start gap-2 p-2 rounded bg-gray-800/30">
              {ep.icon}
              <div>
                <p className="text-xs font-medium">{ep.name}</p>
                <p className="text-[10px] text-gray-500">{ep.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card p-4 border-blue-800/30 bg-blue-900/10">
        <p className="text-xs text-blue-300">
          <Database size={12} className="inline mr-1" />
          Esta pagina substitui o modulo VAEP & PlayeRank. A Soccer Data API fornece metricas
          reais como xG (Expected Goals), predicoes baseadas em ML, e simulacoes de temporada —
          dados mais confiaveis do que as aproximacoes heuristicas anteriores.
        </p>
      </div>
    </div>
  );
}

// ── Expected Goals Tab ──────────────────────────────────────────────

function XgTab() {
  const [tmcl, setTmcl] = useState(TOURNAMENTS[0].tmcl);
  const xgQuery = useSeasonXg(tmcl);

  return (
    <div className="space-y-4">
      <TournamentSelector value={tmcl} onChange={setTmcl} />
      <DataPanel
        title="Expected Goals (xG) da Temporada"
        icon={<Target size={16} className="text-red-400" />}
        data={xgQuery.data?.data}
        isLoading={xgQuery.isLoading}
        isError={xgQuery.isError}
        error={xgQuery.error}
      />
    </div>
  );
}

// ── Predictions Tab ─────────────────────────────────────────────────

function PredictionsTab() {
  const [teamId, setTeamId] = useState(BOTAFOGO_SP.id);
  const [tmcl, setTmcl] = useState(TOURNAMENTS[1].tmcl); // Serie B
  const predictionsQuery = usePlayerPredictions(teamId, tmcl);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <TeamSelector value={teamId} onChange={setTeamId} />
        <TournamentSelector value={tmcl} onChange={setTmcl} />
      </div>
      <DataPanel
        title="Predicoes de Desempenho (ML)"
        icon={<TrendingUp size={16} className="text-blue-400" />}
        data={predictionsQuery.data?.data}
        isLoading={predictionsQuery.isLoading}
        isError={predictionsQuery.isError}
        error={predictionsQuery.error}
      />
    </div>
  );
}

// ── Simulation Tab ──────────────────────────────────────────────────

function SimulationTab() {
  const [tmcl, setTmcl] = useState(TOURNAMENTS[0].tmcl);
  const simQuery = useSeasonSimulation(tmcl);

  return (
    <div className="space-y-4">
      <TournamentSelector value={tmcl} onChange={setTmcl} />
      <DataPanel
        title="Simulacao de Temporada"
        icon={<BarChart3 size={16} className="text-purple-400" />}
        data={simQuery.data?.data}
        isLoading={simQuery.isLoading}
        isError={simQuery.isError}
        error={simQuery.error}
      />
    </div>
  );
}

// ── Squads Tab ──────────────────────────────────────────────────────

function SquadsTab() {
  const [teamId, setTeamId] = useState(BOTAFOGO_SP.id);
  const [tmcl, setTmcl] = useState(TOURNAMENTS[1].tmcl); // Serie B
  const squadsQuery = useSquads(teamId, tmcl);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <TeamSelector value={teamId} onChange={setTeamId} />
        <TournamentSelector value={tmcl} onChange={setTmcl} />
      </div>
      <DataPanel
        title="Elenco"
        icon={<Users size={16} className="text-green-400" />}
        data={squadsQuery.data?.data}
        isLoading={squadsQuery.isLoading}
        isError={squadsQuery.isError}
        error={squadsQuery.error}
      />
    </div>
  );
}

// ── Rankings Tab ────────────────────────────────────────────────────

function RankingsTab() {
  const [tmcl, setTmcl] = useState(TOURNAMENTS[0].tmcl);
  const rankingsQuery = useRankings(tmcl);

  return (
    <div className="space-y-4">
      <TournamentSelector value={tmcl} onChange={setTmcl} />
      <DataPanel
        title="Classificacao"
        icon={<Trophy size={16} className="text-yellow-400" />}
        data={rankingsQuery.data?.data}
        isLoading={rankingsQuery.isLoading}
        isError={rankingsQuery.isError}
        error={rankingsQuery.error}
      />
    </div>
  );
}

// ── Explorer Tab ────────────────────────────────────────────────────

function ExplorerTab() {
  const [path, setPath] = useState('');
  const [submittedPath, setSubmittedPath] = useState('');
  const exploreQuery = useSoccerDataExplore(submittedPath, !!submittedPath);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittedPath(path.trim());
  };

  // Quick links using correct IDs from the API docs/screenshot
  const quickLinks = [
    {
      path: `squads/${BOTAFOGO_SP.id}?tmcl=${TOURNAMENTS[1].tmcl}&detailed=yes`,
      label: 'Elenco Botafogo-SP',
    },
    {
      path: `rankings/${TOURNAMENTS[0].tmcl}`,
      label: 'Classificacao Serie A',
    },
    {
      path: `season-expected-goals/${TOURNAMENTS[0].tmcl}`,
      label: 'xG Serie A',
    },
    {
      path: `season-simulation/${TOURNAMENTS[0].tmcl}`,
      label: 'Simulacao Serie A',
    },
    {
      path: `team-player-predictions/${BOTAFOGO_SP.id}?tmcl=${TOURNAMENTS[1].tmcl}`,
      label: 'Predicoes Botafogo-SP',
    },
    {
      path: `manager-preview/${BOTAFOGO_SP.id}`,
      label: 'Treinador Botafogo-SP',
    },
    {
      path: `season-playtime/${BOTAFOGO_SP.id}?tmcl=${TOURNAMENTS[1].tmcl}`,
      label: 'Minutos Botafogo-SP',
    },
    {
      path: `fixtures/${TOURNAMENTS[1].tmcl}`,
      label: 'Jogos Serie B',
    },
    {
      path: `team-stats/${BOTAFOGO_SP.id}?tmcl=${TOURNAMENTS[1].tmcl}`,
      label: 'Stats Botafogo-SP',
    },
  ];

  return (
    <div className="space-y-4">
      <div className="card p-4">
        <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
          <Search size={16} className="text-cyan-400" />
          API Explorer
        </h3>
        <p className="text-[10px] text-gray-500 mb-3">
          Teste qualquer endpoint. Insira o caminho apos /soccerdata/ — suporta parametros inline (ex: squads/abc?tmcl=xyz&detailed=yes).
        </p>
        <form onSubmit={handleSubmit} className="flex gap-2">
          <div className="flex-1 flex items-center gap-1">
            <span className="text-[10px] text-gray-500 whitespace-nowrap">/soccerdata/</span>
            <input
              type="text"
              value={path}
              onChange={(e) => setPath(e.target.value)}
              className="input-field text-xs flex-1"
              placeholder={`squads/${BOTAFOGO_SP.id}?tmcl=${TOURNAMENTS[1].tmcl}&detailed=yes`}
            />
          </div>
          <button
            type="submit"
            disabled={!path.trim()}
            className="btn-primary text-xs px-3 py-1.5 rounded flex items-center gap-1"
          >
            <Search size={12} />
            Buscar
          </button>
        </form>

        <div className="mt-3 flex flex-wrap gap-1.5">
          {quickLinks.map((link) => (
            <button
              key={link.path}
              onClick={() => { setPath(link.path); setSubmittedPath(link.path); }}
              className="text-[10px] px-2 py-1 rounded bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700 transition-colors"
            >
              {link.label}
            </button>
          ))}
        </div>
      </div>

      {submittedPath && (
        <DataPanel
          title={`/soccerdata/${submittedPath.split('?')[0]}`}
          icon={<Database size={16} className="text-cyan-400" />}
          data={exploreQuery.data?.data}
          isLoading={exploreQuery.isLoading}
          isError={exploreQuery.isError}
          error={exploreQuery.error}
        />
      )}
    </div>
  );
}

// ── Main Page ───────────────────────────────────────────────────────

export default function SoccerDataPage() {
  const [activeTab, setActiveTab] = useState<TabId>('overview');

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold flex items-center gap-2">
          <Database size={22} className="text-blue-400" />
          Soccer Data API
        </h1>
        <p className="text-xs text-gray-400 mt-1">
          Dados avancados de futebol: xG, predicoes, simulacoes, elencos e mais — via RapidAPI Soccer Data
        </p>
      </div>

      <div className="flex gap-1 bg-gray-800/50 p-1 rounded-lg overflow-x-auto">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-3 py-1.5 text-xs rounded transition-colors flex items-center gap-1.5 whitespace-nowrap ${
              activeTab === tab.id ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.15 }}
        >
          {activeTab === 'overview' && <OverviewTab />}
          {activeTab === 'xg' && <XgTab />}
          {activeTab === 'predictions' && <PredictionsTab />}
          {activeTab === 'simulation' && <SimulationTab />}
          {activeTab === 'squads' && <SquadsTab />}
          {activeTab === 'rankings' && <RankingsTab />}
          {activeTab === 'explorer' && <ExplorerTab />}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
