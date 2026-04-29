import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, AlertCircle } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import api from '../lib/api';
import { usePlayers } from '../hooks/usePlayers';
import { getScoreColor } from '../lib/utils';

interface TrajectoryResult {
  player: string;
  display_name: string | null;
  position: string | null;
  predicted_rating_next_season: number | null;
  current_rating_estimate: number | null;
  trajectory_score: number | null;
  league_adjustment_factor: number | null;
  model_r2: number | null;
  top_features: Record<string, number> | null;
  method: string | null;
}

export default function TrajectoryPage() {
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedPlayer, setSelectedPlayer] = useState('');
  const [timer, setTimer] = useState<ReturnType<typeof setTimeout> | null>(null);

  const searchParams = useMemo(() => ({ search: debouncedSearch || undefined, limit: 10 }), [debouncedSearch]);
  const { data: searchData } = usePlayers(debouncedSearch.length >= 2 && !selectedPlayer ? searchParams : { limit: 0 });
  const players = searchData?.players ?? [];

  const handleSearchChange = (v: string) => {
    setSearch(v);
    setSelectedPlayer('');
    if (timer) clearTimeout(timer);
    setTimer(setTimeout(() => setDebouncedSearch(v), 200));
  };

  const trajectory = useMutation({
    mutationFn: async () => {
      const res = await api.post('/trajectory', { player_name: selectedPlayer });
      return res.data as TrajectoryResult;
    },
  });

  const result = trajectory.data;

  const trendLabel = (score: number | null) => {
    if (score === null) return { text: '-', color: '#6b7280' };
    if (score >= 3) return { text: 'IMPROVING', color: '#22c55e' };
    if (score <= -3) return { text: 'DECLINING', color: '#ef4444' };
    return { text: 'STABLE', color: '#eab308' };
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="page-title flex items-center gap-2.5">
          <TrendingUp size={22} strokeWidth={2} style={{ color: 'var(--color-accent)' }} />
          Trajetoria de Carreira
        </h1>
        <p className="page-subtitle">
          Previsao de evolucao com Gradient Boosting — Decroos et al. (2019), Pappalardo et al. (2019)
        </p>
      </div>

      {trajectory.error && (
        <div className="flex items-center gap-2 px-4 py-3 rounded text-sm" style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444' }}>
          <AlertCircle size={16} /><span>Erro: {(trajectory.error as Error).message}</span>
        </div>
      )}

      <div className="card-glass rounded-lg p-5 space-y-4" style={{ overflow: 'visible' }}>
        <div className="grid grid-cols-1 md:grid-cols-[1fr_auto] gap-3 items-end" style={{ overflow: 'visible' }}>
          <div>
            <label className="block text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>JOGADOR</label>
            <div className="relative">
              <input type="text" value={search} onChange={(e) => handleSearchChange(e.target.value)} placeholder="Digite o nome do jogador..." className="w-full px-3 py-2 rounded text-sm outline-none" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)' }} />
              {debouncedSearch.length >= 2 && !selectedPlayer && players.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 rounded overflow-hidden z-50 max-h-48 overflow-y-auto" style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-active)' }}>
                  {players.map((p, i) => (
                    <button key={i} onClick={() => { setSelectedPlayer(p.display_name || p.name); setSearch(p.display_name || p.name); setDebouncedSearch(''); }} className="w-full text-left px-3 py-2 text-sm hover:bg-white/5 cursor-pointer" style={{ borderBottom: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)' }}>
                      <div>{p.display_name || p.name}</div>
                      <div className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>{p.team} — {p.league}</div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
          <button
            onClick={() => trajectory.mutate()}
            disabled={!selectedPlayer || trajectory.isPending}
            className="px-5 py-2 rounded text-sm font-[var(--font-display)] font-semibold tracking-wide uppercase transition-all cursor-pointer disabled:opacity-40"
            style={{ background: 'var(--color-accent)', color: '#fff', border: 'none' }}
          >
            {trajectory.isPending ? '...' : 'ANALISAR'}
          </button>
        </div>
      </div>

      {result && (
        <>
          <div className="card-glass rounded-lg p-5" style={{ background: 'linear-gradient(135deg, rgba(30,41,59,0.8), rgba(15,23,42,0.8))' }}>
            <div className="font-bold text-xl">{result.player}</div>
            <div className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>
              {result.position} {result.method === 'heuristic_fallback' ? '| Metodo: heuristico' : `| R² = ${result.model_r2?.toFixed(3) ?? '-'}`}
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="card-glass rounded-lg p-4 text-center">
              <div className="text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase" style={{ color: 'var(--color-text-muted)' }}>RATING ATUAL</div>
              <div className="text-2xl font-[var(--font-mono)] font-bold mt-1" style={{ color: getScoreColor(result.current_rating_estimate ?? 50) }}>
                {result.current_rating_estimate?.toFixed(1) ?? '-'}
              </div>
              <div className="text-[9px]" style={{ color: 'var(--color-text-muted)' }}>Estimativa</div>
            </motion.div>

            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="card-glass rounded-lg p-4 text-center">
              <div className="text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase" style={{ color: 'var(--color-text-muted)' }}>RATING PROJETADO</div>
              <div className="text-2xl font-[var(--font-mono)] font-bold mt-1" style={{ color: getScoreColor(result.predicted_rating_next_season ?? 50) }}>
                {result.predicted_rating_next_season?.toFixed(1) ?? '-'}
              </div>
              <div className="text-[9px]" style={{ color: 'var(--color-text-muted)' }}>Proxima temporada</div>
            </motion.div>

            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="card-glass rounded-lg p-4 text-center">
              <div className="text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase" style={{ color: 'var(--color-text-muted)' }}>TENDENCIA</div>
              <div className="text-xl font-[var(--font-display)] font-bold mt-1 uppercase" style={{ color: trendLabel(result.trajectory_score).color }}>
                {trendLabel(result.trajectory_score).text}
              </div>
              <div className="text-[9px]" style={{ color: 'var(--color-text-muted)' }}>
                {result.trajectory_score !== null ? (result.trajectory_score > 0 ? '+' : '') + result.trajectory_score.toFixed(2) : '-'}
              </div>
            </motion.div>

            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="card-glass rounded-lg p-4 text-center">
              <div className="text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase" style={{ color: 'var(--color-text-muted)' }}>AJUSTE LIGA</div>
              <div className="text-2xl font-[var(--font-mono)] font-bold mt-1" style={{ color: 'var(--color-text-primary)' }}>
                {result.league_adjustment_factor?.toFixed(3) ?? '-'}
              </div>
              <div className="text-[9px]" style={{ color: 'var(--color-text-muted)' }}>Opta Power</div>
            </motion.div>
          </div>

          {result.top_features && Object.keys(result.top_features).length > 0 && (
            <div className="card-glass rounded-lg p-5">
              <div className="text-[11px] font-[var(--font-display)] tracking-[0.16em] font-semibold uppercase mb-4" style={{ color: 'var(--color-text-muted)' }}>FEATURES MAIS IMPORTANTES</div>
              <div className="space-y-2">
                {Object.entries(result.top_features).map(([feat, importance], i) => (
                  <div key={feat} className="flex items-center gap-3">
                    <span className="text-xs w-48 truncate" style={{ color: 'var(--color-text-secondary)' }}>{feat}</span>
                    <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: 'var(--color-surface-2)' }}>
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${(importance as number) * 100}%` }}
                        transition={{ delay: i * 0.05, duration: 0.5 }}
                        className="h-full rounded-full"
                        style={{ background: 'var(--color-accent)' }}
                      />
                    </div>
                    <span className="text-xs font-[var(--font-mono)] w-12 text-right" style={{ color: 'var(--color-text-muted)' }}>
                      {((importance as number) * 100).toFixed(1)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {!result && !trajectory.isPending && (
        <div className="card-glass rounded-lg p-8 text-center" style={{ color: 'var(--color-text-muted)' }}>
          <TrendingUp size={32} className="mx-auto mb-3 opacity-30" />
          <p className="text-sm">Selecione um jogador e clique em ANALISAR</p>
          <p className="text-xs mt-1 opacity-60">rating_t+1 = f(age, current_rating, minutes, progression_metrics)</p>
        </div>
      )}
    </div>
  );
}
