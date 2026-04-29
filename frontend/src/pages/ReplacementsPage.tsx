import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Users, AlertCircle } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import api from '../lib/api';
import { usePlayers, usePositions } from '../hooks/usePlayers';
import { getScoreColor } from '../lib/utils';

interface ReplacementEntry {
  rank: number;
  player: string;
  display_name: string | null;
  team: string | null;
  position: string | null;
  age: number | null;
  minutes: number | null;
  similarity_score: number;
  cosine_similarity: number | null;
  mahalanobis_similarity: number | null;
  cluster_proximity: number | null;
  trajectory_score: number | null;
  predicted_rating: number | null;
  market_value_gap: number | null;
  estimated_value: number | null;
}

interface ReplacementResult {
  reference_player: string;
  position: string;
  total: number;
  replacements: ReplacementEntry[];
}

export default function ReplacementsPage() {
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedPlayer, setSelectedPlayer] = useState('');
  const [position, setPosition] = useState('');
  const [ageMin, setAgeMin] = useState('');
  const [ageMax, setAgeMax] = useState('');
  const [topN, setTopN] = useState(20);
  const [timer, setTimer] = useState<ReturnType<typeof setTimeout> | null>(null);
  const [expandedRow, setExpandedRow] = useState<number | null>(null);

  const { data: positions } = usePositions();
  const searchParams = useMemo(() => ({ search: debouncedSearch || undefined, limit: 10 }), [debouncedSearch]);
  const { data: searchData } = usePlayers(debouncedSearch.length >= 2 && !selectedPlayer ? searchParams : { limit: 0 });
  const players = searchData?.players ?? [];

  const handleSearchChange = (v: string) => {
    setSearch(v);
    setSelectedPlayer('');
    if (timer) clearTimeout(timer);
    setTimer(setTimeout(() => setDebouncedSearch(v), 200));
  };

  const replacements = useMutation({
    mutationFn: async () => {
      const payload: Record<string, unknown> = {
        player_name: selectedPlayer,
        top_n: topN,
        min_minutes: 400,
      };
      if (position) payload.position = position;
      if (ageMin) payload.age_min = parseFloat(ageMin);
      if (ageMax) payload.age_max = parseFloat(ageMax);
      const res = await api.post('/replacements', payload);
      return res.data as ReplacementResult;
    },
  });

  const results = replacements.data?.replacements ?? [];

  const simColor = (v: number) => {
    if (v >= 80) return '#22c55e';
    if (v >= 60) return '#eab308';
    return '#ef4444';
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="page-title flex items-center gap-2.5">
          <Users size={22} strokeWidth={2} style={{ color: 'var(--color-accent)' }} />
          Substitutos
        </h1>
        <p className="page-subtitle">
          Motor de substituicao multi-metodo — KickClone (2025), Cosine + Mahalanobis + Cluster
        </p>
      </div>

      {replacements.error && (
        <div className="flex items-center gap-2 px-4 py-3 rounded text-sm" style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444' }}>
          <AlertCircle size={16} /><span>Erro: {(replacements.error as Error).message}</span>
        </div>
      )}

      <div className="card-glass rounded-lg p-5 space-y-4" style={{ overflow: 'visible' }}>
        <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_auto_auto_auto_auto] gap-3 items-end" style={{ overflow: 'visible' }}>
          <div>
            <label className="block text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>JOGADOR ALVO</label>
            <div className="relative">
              <input type="text" value={search} onChange={(e) => handleSearchChange(e.target.value)} placeholder="Buscar jogador para substituir..." className="w-full px-3 py-2 rounded text-sm outline-none" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)' }} />
              {debouncedSearch.length >= 2 && !selectedPlayer && players.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 rounded overflow-hidden z-50 max-h-48 overflow-y-auto" style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-active)' }}>
                  {players.map((p, i) => (
                    <button key={i} onClick={() => { setSelectedPlayer(p.display_name || p.name); setSearch(p.display_name || p.name); setDebouncedSearch(''); if (p.position && !position) setPosition(p.position); }} className="w-full text-left px-3 py-2 text-sm hover:bg-white/5 cursor-pointer" style={{ borderBottom: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)' }}>
                      <div>{p.display_name || p.name}</div>
                      <div className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>{p.team} — {p.position} — {p.league}</div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
          <div>
            <label className="block text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>POSICAO</label>
            <select value={position} onChange={(e) => setPosition(e.target.value)} className="px-3 py-2 rounded text-sm cursor-pointer outline-none" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-secondary)' }}>
              <option value="">Auto</option>
              {(positions || []).map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>IDADE</label>
            <div className="flex gap-1">
              <input type="number" value={ageMin} onChange={(e) => setAgeMin(e.target.value)} placeholder="Min" className="w-16 px-2 py-2 rounded text-sm outline-none" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)' }} />
              <input type="number" value={ageMax} onChange={(e) => setAgeMax(e.target.value)} placeholder="Max" className="w-16 px-2 py-2 rounded text-sm outline-none" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)' }} />
            </div>
          </div>
          <div>
            <label className="block text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>TOP N</label>
            <input type="number" value={topN} onChange={(e) => setTopN(Number(e.target.value))} className="w-16 px-2 py-2 rounded text-sm outline-none" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)' }} />
          </div>
          <button
            onClick={() => replacements.mutate()}
            disabled={!selectedPlayer || replacements.isPending}
            className="px-5 py-2 rounded text-sm font-[var(--font-display)] font-semibold tracking-wide uppercase transition-all cursor-pointer disabled:opacity-40"
            style={{ background: 'var(--color-accent)', color: '#fff', border: 'none' }}
          >
            {replacements.isPending ? '...' : 'BUSCAR'}
          </button>
        </div>
      </div>

      {replacements.data && (
        <div className="card-glass rounded-lg p-4 mb-2" style={{ background: 'linear-gradient(135deg, rgba(30,41,59,0.8), rgba(15,23,42,0.8))' }}>
          <div className="font-bold text-lg">Substitutos para: {replacements.data.reference_player}</div>
          <div className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>
            {replacements.data.position} | {replacements.data.total} encontrados
          </div>
        </div>
      )}

      {results.length > 0 && (
        <div className="card-glass rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                  <th className="px-3 py-2 text-left text-[10px] font-[var(--font-display)] tracking-wider uppercase" style={{ color: 'var(--color-text-muted)' }}>#</th>
                  <th className="px-3 py-2 text-left text-[10px] font-[var(--font-display)] tracking-wider uppercase" style={{ color: 'var(--color-text-muted)' }}>Jogador</th>
                  <th className="px-3 py-2 text-center text-[10px] font-[var(--font-display)] tracking-wider uppercase" style={{ color: 'var(--color-text-muted)' }}>Sim.</th>
                  <th className="px-3 py-2 text-center text-[10px] font-[var(--font-display)] tracking-wider uppercase hidden md:table-cell" style={{ color: 'var(--color-text-muted)' }}>Idade</th>
                  <th className="px-3 py-2 text-center text-[10px] font-[var(--font-display)] tracking-wider uppercase hidden md:table-cell" style={{ color: 'var(--color-text-muted)' }}>Cosine</th>
                  <th className="px-3 py-2 text-center text-[10px] font-[var(--font-display)] tracking-wider uppercase hidden md:table-cell" style={{ color: 'var(--color-text-muted)' }}>Mahal.</th>
                  <th className="px-3 py-2 text-center text-[10px] font-[var(--font-display)] tracking-wider uppercase hidden lg:table-cell" style={{ color: 'var(--color-text-muted)' }}>Cluster</th>
                  <th className="px-3 py-2 text-center text-[10px] font-[var(--font-display)] tracking-wider uppercase hidden lg:table-cell" style={{ color: 'var(--color-text-muted)' }}>Traj.</th>
                </tr>
              </thead>
              <tbody>
                {results.map((rep, i) => (
                  <motion.tr
                    key={i}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.02 }}
                    style={{ borderBottom: '1px solid var(--color-border-subtle)', cursor: 'pointer' }}
                    className="hover:bg-white/[0.02]"
                    onClick={() => setExpandedRow(expandedRow === i ? null : i)}
                  >
                    <td className="px-3 py-2.5 font-[var(--font-mono)] text-xs" style={{ color: 'var(--color-text-muted)' }}>{rep.rank}</td>
                    <td className="px-3 py-2.5">
                      <div className="font-medium" style={{ color: 'var(--color-text-primary)' }}>{rep.display_name || rep.player}</div>
                      {rep.team && <div className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>{rep.team}</div>}
                    </td>
                    <td className="px-3 py-2.5 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <div className="w-16 h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--color-surface-2)' }}>
                          <div className="h-full rounded-full" style={{ width: `${rep.similarity_score}%`, background: simColor(rep.similarity_score) }} />
                        </div>
                        <span className="font-[var(--font-mono)] font-bold text-xs" style={{ color: simColor(rep.similarity_score) }}>
                          {rep.similarity_score.toFixed(1)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-3 py-2.5 text-center hidden md:table-cell font-[var(--font-mono)] text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                      {rep.age?.toFixed(0) ?? '-'}
                    </td>
                    <td className="px-3 py-2.5 text-center hidden md:table-cell font-[var(--font-mono)] text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                      {rep.cosine_similarity?.toFixed(1) ?? '-'}
                    </td>
                    <td className="px-3 py-2.5 text-center hidden md:table-cell font-[var(--font-mono)] text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                      {rep.mahalanobis_similarity?.toFixed(1) ?? '-'}
                    </td>
                    <td className="px-3 py-2.5 text-center hidden lg:table-cell font-[var(--font-mono)] text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                      {rep.cluster_proximity?.toFixed(1) ?? '-'}
                    </td>
                    <td className="px-3 py-2.5 text-center hidden lg:table-cell font-[var(--font-mono)] text-xs" style={{ color: rep.trajectory_score && rep.trajectory_score > 0 ? '#22c55e' : rep.trajectory_score && rep.trajectory_score < -3 ? '#ef4444' : 'var(--color-text-secondary)' }}>
                      {rep.trajectory_score ? (rep.trajectory_score > 0 ? '+' : '') + rep.trajectory_score.toFixed(1) : '-'}
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {results.length === 0 && !replacements.isPending && (
        <div className="card-glass rounded-lg p-8 text-center" style={{ color: 'var(--color-text-muted)' }}>
          <Users size={32} className="mx-auto mb-3 opacity-30" />
          <p className="text-sm">Selecione um jogador alvo e clique em BUSCAR</p>
          <p className="text-xs mt-1 opacity-60">Similaridade = 45% Cosine + 35% Mahalanobis + 20% Cluster</p>
        </div>
      )}
    </div>
  );
}
