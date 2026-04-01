import { useState, useMemo, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BarChart3,
  TrendingUp,
  Shield,
  Target,
  Zap,
  Users,
  User,
  Search,
  ChevronDown,
  ExternalLink,
  X,
  Camera,
} from 'lucide-react';
import {
  RadarChart as RechartsRadar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ScatterChart,
  Scatter,
  Cell,
  Legend,
} from 'recharts';
import {
  useVaepRatings,
  useRunVaepPipeline,
  usePlayerankRankings,
  useEnrichmentStatus,
  useSyncPhotos,
} from '../hooks/useVaep';
import type { VAEPRating, PlayeRankScore } from '../types/vaep';
import { getScoreColor } from '../lib/utils';
import PlayerProfile from '../components/PlayerProfile';

// ── VAEPRadar Component ──────────────────────────────────────────────

function VAEPRadar({ player, leagueAvg }: { player: VAEPRating; leagueAvg: { offensive: number; defensive: number } }) {
  const data = [
    { metric: 'VAEP/90', player: player.vaep_per90 * 100, league: (leagueAvg.offensive + leagueAvg.defensive) * 100 },
    { metric: 'Ofensivo', player: player.offensive_vaep * 100, league: leagueAvg.offensive * 100 },
    { metric: 'Defensivo', player: player.defensive_vaep * 100, league: leagueAvg.defensive * 100 },
    { metric: 'Total', player: Math.min(player.total_vaep, 50), league: 20 },
    { metric: 'Minutos', player: Math.min(player.minutes_played / 30, 100), league: 50 },
  ];

  return (
    <div className="card p-4">
      <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
        <Target size={16} className="text-blue-400" />
        VAEP Radar — {player.player_name}
      </h3>
      <ResponsiveContainer width="100%" height={260}>
        <RechartsRadar data={data}>
          <PolarGrid stroke="#334155" />
          <PolarAngleAxis dataKey="metric" tick={{ fill: '#94a3b8', fontSize: 11 }} />
          <PolarRadiusAxis tick={false} axisLine={false} />
          <Radar name="Jogador" dataKey="player" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
          <Radar name="Media Liga" dataKey="league" stroke="#64748b" fill="#64748b" fillOpacity={0.1} />
          <Legend wrapperStyle={{ fontSize: 11 }} />
        </RechartsRadar>
      </ResponsiveContainer>
    </div>
  );
}

// ── PlayeRankCard Component ──────────────────────────────────────────

function PlayeRankCard({ score, onSelect }: { score: PlayeRankScore; onSelect: (name: string) => void }) {
  const dims = score.dimensions;
  const bars = [
    { label: 'Scoring', value: dims.scoring ?? 0, color: '#ef4444' },
    { label: 'Playmaking', value: dims.playmaking ?? 0, color: '#3b82f6' },
    { label: 'Defending', value: dims.defending ?? 0, color: '#22c55e' },
    { label: 'Physical', value: dims.physical ?? 0, color: '#f59e0b' },
    { label: 'Possession', value: dims.possession ?? 0, color: '#8b5cf6' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="card p-4 cursor-pointer hover:ring-1 hover:ring-blue-500/30 transition-all"
      onClick={() => onSelect(score.player_name)}
    >
      <div className="flex items-center justify-between mb-3">
        <div>
          <h4 className="font-semibold text-sm hover:text-blue-400 transition-colors">{score.player_name}</h4>
          <p className="text-xs text-gray-400">
            {score.team} · {score.role_cluster}
          </p>
        </div>
        <div className="text-right">
          <div
            className="text-lg font-bold"
            style={{ color: getScoreColor(score.composite_score) }}
          >
            {score.composite_score.toFixed(1)}
          </div>
          <div className="text-[10px] text-gray-500">
            P{score.percentile_in_cluster.toFixed(0)} no cluster ({score.cluster_size})
          </div>
        </div>
      </div>

      <div className="space-y-2">
        {bars.map((b) => (
          <div key={b.label} className="flex items-center gap-2">
            <span className="text-[10px] w-20 text-gray-400">{b.label}</span>
            <div className="flex-1 h-2 rounded-full bg-gray-800 overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${Math.min(b.value, 100)}%` }}
                transition={{ duration: 0.6, ease: 'easeOut' }}
                className="h-full rounded-full"
                style={{ backgroundColor: b.color }}
              />
            </div>
            <span className="text-[10px] w-8 text-right font-mono text-gray-300">
              {b.value.toFixed(0)}
            </span>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

// ── VAEPComparison Scatter Component ─────────────────────────────────

function VAEPScatter({ ratings }: { ratings: VAEPRating[] }) {
  const data = ratings
    .filter((r) => r.minutes_played >= 200)
    .map((r) => ({
      name: r.player_name,
      vaep: r.vaep_per90,
      minutes: r.minutes_played,
      team: r.team ?? '',
      position: r.position ?? '',
    }));

  const COLORS = ['#3b82f6', '#22c55e', '#ef4444', '#f59e0b', '#8b5cf6'];

  return (
    <div className="card p-4">
      <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
        <BarChart3 size={16} className="text-purple-400" />
        VAEP/90 vs Minutos Jogados
      </h3>
      <ResponsiveContainer width="100%" height={320}>
        <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis
            dataKey="minutes"
            name="Minutos"
            type="number"
            tick={{ fill: '#94a3b8', fontSize: 10 }}
            label={{ value: 'Minutos', position: 'bottom', fill: '#64748b', fontSize: 11 }}
          />
          <YAxis
            dataKey="vaep"
            name="VAEP/90"
            type="number"
            tick={{ fill: '#94a3b8', fontSize: 10 }}
            label={{ value: 'VAEP/90', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 11 }}
          />
          <Tooltip
            content={({ payload }) => {
              if (!payload?.length) return null;
              const d = payload[0].payload;
              return (
                <div className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-xs">
                  <p className="font-semibold">{d.name}</p>
                  <p className="text-gray-400">{d.team} · {d.position}</p>
                  <p className="text-blue-400">VAEP/90: {d.vaep.toFixed(4)}</p>
                  <p className="text-gray-300">Minutos: {d.minutes}</p>
                </div>
              );
            }}
          />
          <Scatter data={data}>
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} fillOpacity={0.7} />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Clickable Player Name ────────────────────────────────────────────

function PlayerNameCell({
  name,
  onSelect,
}: {
  name: string;
  onSelect: (name: string) => void;
}) {
  const openInNewTab = (e: React.MouseEvent) => {
    e.stopPropagation();
    const url = `${window.location.origin}${window.location.pathname}?tab=vaep&player=${encodeURIComponent(name)}`;
    window.open(url, '_blank');
  };

  return (
    <td className="py-2 px-3 font-medium">
      <div className="flex items-center gap-1.5">
        <button
          onClick={() => onSelect(name)}
          className="hover:underline cursor-pointer text-left transition-colors hover:text-blue-400"
        >
          {name}
        </button>
        <button
          onClick={openInNewTab}
          className="opacity-0 group-hover:opacity-60 hover:!opacity-100 transition-opacity text-gray-400 hover:text-blue-400 shrink-0"
          title="Abrir perfil em nova aba"
        >
          <ExternalLink size={12} />
        </button>
      </div>
    </td>
  );
}

// ── Main VAEP Page ───────────────────────────────────────────────────

export default function VAEPPage() {
  const [position, setPosition] = useState('');
  const [minMinutes, setMinMinutes] = useState(0);
  const [activeTab, setActiveTab] = useState<'vaep' | 'playerank'>('vaep');
  const [selectedPlayer, setSelectedPlayer] = useState<string | null>(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get('player') || null;
  });
  const profileRef = useRef<HTMLDivElement>(null);

  // Clean URL params after reading player
  useEffect(() => {
    if (window.location.search.includes('player=')) {
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, []);

  // Scroll to profile when player is selected
  useEffect(() => {
    if (selectedPlayer && profileRef.current) {
      profileRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [selectedPlayer]);

  const ratingsQuery = useVaepRatings({
    position: position || undefined,
    min_minutes: minMinutes,
  });

  const playerankQuery = usePlayerankRankings({});
  const runPipeline = useRunVaepPipeline();
  const enrichmentStatus = useEnrichmentStatus();
  const syncPhotos = useSyncPhotos();

  const ratings = ratingsQuery.data?.ratings ?? [];
  const playerankScores = playerankQuery.data?.rankings ?? [];

  // Compute league averages for radar
  const leagueAvg = useMemo(() => {
    if (ratings.length === 0) return { offensive: 0.05, defensive: 0.02 };
    const avgOff = ratings.reduce((s, r) => s + r.offensive_vaep, 0) / ratings.length;
    const avgDef = ratings.reduce((s, r) => s + r.defensive_vaep, 0) / ratings.length;
    return { offensive: avgOff, defensive: avgDef };
  }, [ratings]);

  const topPlayer = ratings[0] ?? null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold flex items-center gap-2">
            <Zap size={22} className="text-yellow-400" />
            VAEP & PlayeRank
          </h1>
          <p className="text-xs text-gray-400 mt-1">
            Valorizacao de Acoes (Decroos et al., KDD 2019) + Ranking Multi-dimensional (Pappalardo et al., 2019)
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => syncPhotos.mutate()}
            disabled={syncPhotos.isPending}
            className="text-xs px-3 py-1.5 rounded flex items-center gap-1 border border-gray-700 text-gray-300 hover:text-white hover:border-gray-500 transition-colors"
          >
            {syncPhotos.isPending ? (
              <div className="animate-spin h-3 w-3 border border-white border-t-transparent rounded-full" />
            ) : (
              <Camera size={14} />
            )}
            Sincronizar Fotos
            {enrichmentStatus.data && (
              <span className="text-[10px] text-gray-500 ml-1">
                ({enrichmentStatus.data.coverage_pct}%)
              </span>
            )}
          </button>
          <button
            onClick={() => runPipeline.mutate()}
            disabled={runPipeline.isPending}
            className="btn-primary text-xs px-3 py-1.5 rounded flex items-center gap-1"
          >
            {runPipeline.isPending ? (
              <div className="animate-spin h-3 w-3 border border-white border-t-transparent rounded-full" />
            ) : (
              <TrendingUp size={14} />
            )}
            Calcular VAEP
          </button>
        </div>
      </div>

      {/* Pipeline result banner */}
      {runPipeline.data && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="card p-3 border-green-800 bg-green-900/20"
        >
          <p className="text-xs text-green-300">
            {ratings.length > 0
              ? `Pipeline concluido: ${ratings.length} jogadores com ratings VAEP`
              : `Pipeline iniciado para ${runPipeline.data.total_players} jogadores. Calculando em segundo plano...`}
          </p>
        </motion.div>
      )}

      {/* Photo sync result banner */}
      {syncPhotos.data && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="card p-3 border-blue-800 bg-blue-900/20"
        >
          <p className="text-xs text-blue-300">
            <Camera size={12} className="inline mr-1" />
            {syncPhotos.data.message}
          </p>
        </motion.div>
      )}

      {/* Tab switch */}
      <div className="flex gap-1 bg-gray-800/50 p-1 rounded-lg w-fit">
        <button
          onClick={() => setActiveTab('vaep')}
          className={`px-3 py-1.5 text-xs rounded transition-colors ${
            activeTab === 'vaep' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
          }`}
        >
          VAEP Ratings
        </button>
        <button
          onClick={() => setActiveTab('playerank')}
          className={`px-3 py-1.5 text-xs rounded transition-colors ${
            activeTab === 'playerank' ? 'bg-purple-600 text-white' : 'text-gray-400 hover:text-white'
          }`}
        >
          PlayeRank
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-400">Posicao</label>
          <select
            value={position}
            onChange={(e) => setPosition(e.target.value)}
            className="input-field text-xs w-32"
          >
            <option value="">Todas</option>
            <option value="Atacante">Atacante</option>
            <option value="Extremo">Extremo</option>
            <option value="Meia">Meia</option>
            <option value="Volante">Volante</option>
            <option value="Lateral">Lateral</option>
            <option value="Zagueiro">Zagueiro</option>
            <option value="Goleiro">Goleiro</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-400">Min. Minutos</label>
          <input
            type="number"
            value={minMinutes}
            onChange={(e) => setMinMinutes(Number(e.target.value))}
            className="input-field text-xs w-20"
            min={0}
            step={100}
          />
        </div>
      </div>

      {/* VAEP Tab */}
      {activeTab === 'vaep' && (
        <div className="space-y-6">
          {/* Top charts row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {topPlayer && <VAEPRadar player={topPlayer} leagueAvg={leagueAvg} />}
            {ratings.length > 0 && <VAEPScatter ratings={ratings} />}
          </div>

          {/* Top VAEP Bar Chart */}
          {ratings.length > 0 && (
            <div className="card p-4">
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <BarChart3 size={16} className="text-blue-400" />
                Top 20 — VAEP por 90 minutos
              </h3>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart
                  data={ratings.slice(0, 20).map((r) => ({
                    name: r.player_name.length > 18 ? r.player_name.slice(0, 16) + '...' : r.player_name,
                    fullName: r.player_name,
                    vaep: r.vaep_per90,
                    offensive: r.offensive_vaep,
                    defensive: r.defensive_vaep,
                    team: r.team,
                  }))}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                  <YAxis
                    dataKey="name"
                    type="category"
                    tick={{ fill: '#e2e8f0', fontSize: 10 }}
                    width={95}
                  />
                  <Tooltip
                    content={({ payload }) => {
                      if (!payload?.length) return null;
                      const d = payload[0].payload;
                      return (
                        <div className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-xs">
                          <p className="font-semibold">{d.fullName}</p>
                          <p className="text-gray-400">{d.team}</p>
                          <p className="text-blue-400">Ofensivo: {d.offensive.toFixed(4)}</p>
                          <p className="text-green-400">Defensivo: {d.defensive.toFixed(4)}</p>
                          <p className="text-yellow-400 font-semibold">Total: {d.vaep.toFixed(4)}</p>
                        </div>
                      );
                    }}
                  />
                  <Bar dataKey="offensive" stackId="vaep" fill="#3b82f6" name="Ofensivo" />
                  <Bar dataKey="defensive" stackId="vaep" fill="#22c55e" name="Defensivo" radius={[0, 4, 4, 0]} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Ratings Table */}
          <div className="card overflow-hidden">
            <div className="p-3 border-b border-gray-800">
              <h3 className="text-sm font-semibold flex items-center gap-2">
                <Shield size={16} className="text-green-400" />
                Tabela VAEP — {ratings.length} jogadores
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-gray-400 border-b border-gray-800">
                    <th className="text-left py-2 px-3">#</th>
                    <th className="text-left py-2 px-3">Jogador</th>
                    <th className="text-left py-2 px-3">Equipa</th>
                    <th className="text-left py-2 px-3">Pos</th>
                    <th className="text-right py-2 px-3">Min</th>
                    <th className="text-right py-2 px-3">VAEP/90</th>
                    <th className="text-right py-2 px-3">Ofensivo</th>
                    <th className="text-right py-2 px-3">Defensivo</th>
                    <th className="text-right py-2 px-3">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {ratings.map((r, i) => (
                    <tr
                      key={r.player_name}
                      className="group border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors cursor-pointer"
                      onClick={() => setSelectedPlayer(r.player_name)}
                    >
                      <td className="py-2 px-3 text-gray-500">{i + 1}</td>
                      <PlayerNameCell name={r.player_name} onSelect={setSelectedPlayer} />
                      <td className="py-2 px-3 text-gray-400">{r.team ?? '-'}</td>
                      <td className="py-2 px-3 text-gray-400">{r.position ?? '-'}</td>
                      <td className="py-2 px-3 text-right text-gray-300">{r.minutes_played}</td>
                      <td className="py-2 px-3 text-right font-mono font-semibold" style={{ color: getScoreColor(r.vaep_per90 * 200) }}>
                        {r.vaep_per90.toFixed(4)}
                      </td>
                      <td className="py-2 px-3 text-right text-blue-400 font-mono">{r.offensive_vaep.toFixed(4)}</td>
                      <td className="py-2 px-3 text-right text-green-400 font-mono">{r.defensive_vaep.toFixed(4)}</td>
                      <td className="py-2 px-3 text-right text-yellow-400 font-mono">{r.total_vaep.toFixed(2)}</td>
                    </tr>
                  ))}
                  {ratings.length === 0 && (
                    <tr>
                      <td colSpan={9} className="py-8 text-center text-gray-500">
                        {ratingsQuery.isLoading ? 'Carregando...' : 'Clique "Calcular VAEP" para gerar ratings'}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* PlayeRank Tab */}
      {activeTab === 'playerank' && (
        <div className="space-y-6">
          {/* PlayeRank Cards Grid */}
          {playerankScores.length > 0 ? (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {playerankScores.slice(0, 12).map((s) => (
                  <PlayeRankCard key={s.player_name} score={s} onSelect={setSelectedPlayer} />
                ))}
              </div>

              {/* Full PlayeRank Table */}
              <div className="card overflow-hidden">
                <div className="p-3 border-b border-gray-800">
                  <h3 className="text-sm font-semibold flex items-center gap-2">
                    <Users size={16} className="text-purple-400" />
                    PlayeRank Completo — {playerankScores.length} jogadores
                  </h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="text-gray-400 border-b border-gray-800">
                        <th className="text-left py-2 px-3">#</th>
                        <th className="text-left py-2 px-3">Jogador</th>
                        <th className="text-left py-2 px-3">Equipa</th>
                        <th className="text-left py-2 px-3">Cluster</th>
                        <th className="text-right py-2 px-3">Score</th>
                        <th className="text-right py-2 px-3">Scoring</th>
                        <th className="text-right py-2 px-3">Playmaking</th>
                        <th className="text-right py-2 px-3">Defending</th>
                        <th className="text-right py-2 px-3">Physical</th>
                        <th className="text-right py-2 px-3">Possession</th>
                        <th className="text-right py-2 px-3">Percentil</th>
                      </tr>
                    </thead>
                    <tbody>
                      {playerankScores.map((s, i) => (
                        <tr
                          key={s.player_name}
                          className="group border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors cursor-pointer"
                          onClick={() => setSelectedPlayer(s.player_name)}
                        >
                          <td className="py-2 px-3 text-gray-500">{i + 1}</td>
                          <PlayerNameCell name={s.player_name} onSelect={setSelectedPlayer} />
                          <td className="py-2 px-3 text-gray-400">{s.team ?? '-'}</td>
                          <td className="py-2 px-3">
                            <span className="px-1.5 py-0.5 rounded text-[10px] bg-gray-800 text-gray-300">
                              {s.role_cluster}
                            </span>
                          </td>
                          <td className="py-2 px-3 text-right font-semibold" style={{ color: getScoreColor(s.composite_score) }}>
                            {s.composite_score.toFixed(1)}
                          </td>
                          <td className="py-2 px-3 text-right text-red-400 font-mono">{(s.dimensions.scoring ?? 0).toFixed(0)}</td>
                          <td className="py-2 px-3 text-right text-blue-400 font-mono">{(s.dimensions.playmaking ?? 0).toFixed(0)}</td>
                          <td className="py-2 px-3 text-right text-green-400 font-mono">{(s.dimensions.defending ?? 0).toFixed(0)}</td>
                          <td className="py-2 px-3 text-right text-yellow-400 font-mono">{(s.dimensions.physical ?? 0).toFixed(0)}</td>
                          <td className="py-2 px-3 text-right text-purple-400 font-mono">{(s.dimensions.possession ?? 0).toFixed(0)}</td>
                          <td className="py-2 px-3 text-right text-gray-300">P{s.percentile_in_cluster.toFixed(0)}</td>
                        </tr>
                      ))}
                      {playerankScores.length === 0 && (
                        <tr>
                          <td colSpan={11} className="py-8 text-center text-gray-500">
                            {playerankQuery.isLoading ? 'Carregando...' : 'Execute o pipeline VAEP primeiro para gerar rankings'}
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : (
            <div className="card p-8 text-center text-gray-500">
              {playerankQuery.isLoading ? (
                <div className="animate-spin h-6 w-6 border-2 border-purple-500 border-t-transparent rounded-full mx-auto" />
              ) : (
                <p className="text-sm">Execute o pipeline VAEP primeiro para gerar rankings PlayeRank</p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Inline Player Profile */}
      <AnimatePresence>
        {selectedPlayer && (
          <motion.div
            ref={profileRef}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
            className="relative"
          >
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold flex items-center gap-2">
                <User size={16} className="text-blue-400" />
                Perfil do Jogador
              </h3>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    const url = `${window.location.origin}${window.location.pathname}?tab=vaep&player=${encodeURIComponent(selectedPlayer)}`;
                    window.open(url, '_blank');
                  }}
                  className="flex items-center gap-1 text-[10px] text-gray-400 hover:text-blue-400 transition-colors px-2 py-1 rounded hover:bg-gray-800"
                  title="Abrir perfil em nova aba"
                >
                  <ExternalLink size={12} />
                  Nova aba
                </button>
                <button
                  onClick={() => setSelectedPlayer(null)}
                  className="flex items-center gap-1 text-[10px] text-gray-400 hover:text-red-400 transition-colors px-2 py-1 rounded hover:bg-gray-800"
                >
                  <X size={12} />
                  Fechar
                </button>
              </div>
            </div>
            <PlayerProfile
              playerDisplayName={selectedPlayer}
              onClose={() => setSelectedPlayer(null)}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
