import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Trophy, ArrowUpDown } from 'lucide-react';
import { useRankings } from '../hooks/usePlayers';
import api from '../lib/api';
import { getScoreColor, formatNumber } from '../lib/utils';

export default function RankingsPage() {
  const { rankings, loading, fetchRankings } = useRankings();
  const [position, setPosition] = useState('Atacante');
  const [minMinutes, setMinMinutes] = useState(500);
  const [league, setLeague] = useState('');
  const [positions, setPositions] = useState<string[]>([]);
  const [leagues, setLeagues] = useState<string[]>([]);
  const hasFetched = useRef(false);

  useEffect(() => {
    api.get('/config/positions').then((r) => setPositions(r.data.positions)).catch(() => {});
    api.get('/config/leagues').then((r) => setLeagues(r.data.leagues)).catch(() => {});
  }, []);

  useEffect(() => {
    fetchRankings(position, minMinutes, league || undefined, 50).then(() => { hasFetched.current = true; });
  }, [position, minMinutes, league, fetchRankings]);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-[var(--font-display)] text-lg font-bold tracking-tight flex items-center gap-2">
          <Trophy size={18} style={{ color: 'var(--color-accent)' }} />
          Rankings
        </h1>
        <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
          Classificacao ponderada por indices compostos e Scout Score
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label className="block text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>
            POSICAO
          </label>
          <select
            value={position}
            onChange={(e) => setPosition(e.target.value)}
            className="px-3 py-2 rounded text-sm cursor-pointer outline-none"
            style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-secondary)', fontFamily: 'var(--font-body)' }}
          >
            {positions.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>
            MIN. MINUTOS
          </label>
          <input
            type="number"
            value={minMinutes}
            onChange={(e) => setMinMinutes(Number(e.target.value))}
            className="w-24 px-3 py-2 rounded text-sm outline-none"
            style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)' }}
          />
        </div>
        <div>
          <label className="block text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>
            LIGA
          </label>
          <select
            value={league}
            onChange={(e) => setLeague(e.target.value)}
            className="px-3 py-2 rounded text-sm cursor-pointer outline-none"
            style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-secondary)', fontFamily: 'var(--font-body)' }}
          >
            <option value="">Todas</option>
            {leagues.map((l) => <option key={l} value={l}>{l}</option>)}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="card-glass rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                <th className="px-3 py-2.5 text-left text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-text-muted)' }}>#</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-text-muted)' }}>Jogador</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-text-muted)' }}>Equipa</th>
                <th className="px-3 py-2.5 text-right text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-text-muted)' }}>Idade</th>
                <th className="px-3 py-2.5 text-right text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-text-muted)' }}>Min</th>
                <th className="px-3 py-2.5 text-right text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-accent)' }}>
                  <span className="flex items-center justify-end gap-1">Score <ArrowUpDown size={10} /></span>
                </th>
              </tr>
            </thead>
            <tbody>
              {loading || (!rankings && !hasFetched.current) ? (
                Array.from({ length: 10 }).map((_, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                    {Array.from({ length: 6 }).map((_, j) => (
                      <td key={j} className="px-3 py-2.5"><div className="skeleton h-4 rounded" /></td>
                    ))}
                  </tr>
                ))
              ) : rankings && rankings.players.length > 0 ? (
                rankings.players.map((entry, i) => (
                  <motion.tr
                    key={entry.rank}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.02 }}
                    style={{ borderBottom: '1px solid var(--color-border-subtle)' }}
                    className="transition-colors hover:bg-white/[0.02]"
                  >
                    <td className="px-3 py-2.5 font-[var(--font-mono)] text-xs" style={{ color: i < 3 ? 'var(--color-accent)' : 'var(--color-text-muted)' }}>
                      {entry.rank}
                    </td>
                    <td className="px-3 py-2.5 font-medium">{entry.name}</td>
                    <td className="px-3 py-2.5 text-xs" style={{ color: 'var(--color-text-secondary)' }}>{entry.team || '—'}</td>
                    <td className="px-3 py-2.5 text-right font-[var(--font-mono)] text-xs" style={{ color: 'var(--color-text-muted)' }}>{formatNumber(entry.age)}</td>
                    <td className="px-3 py-2.5 text-right font-[var(--font-mono)] text-xs" style={{ color: 'var(--color-text-muted)' }}>{formatNumber(entry.minutes)}</td>
                    <td className="px-3 py-2.5 text-right">
                      <span
                        className="inline-block px-2 py-0.5 rounded text-xs font-[var(--font-mono)] font-bold"
                        style={{ color: getScoreColor(entry.score), background: `${getScoreColor(entry.score)}15` }}
                      >
                        {entry.score.toFixed(1)}
                      </span>
                    </td>
                  </motion.tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="px-3 py-8 text-center text-xs" style={{ color: 'var(--color-text-muted)' }}>
                    Nenhum resultado
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
