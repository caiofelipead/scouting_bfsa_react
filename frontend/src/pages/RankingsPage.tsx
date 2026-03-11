import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Trophy, ArrowUpDown, AlertCircle } from 'lucide-react';
import { useRankings, usePositions, useLeagues } from '../hooks/usePlayers';
import { getScoreColor, formatNumber } from '../lib/utils';
import type { RankingsQueryParams } from '../types/api';

export default function RankingsPage() {
  const [position, setPosition] = useState('Atacante');
  const [minMinutes, setMinMinutes] = useState(500);
  const [league, setLeague] = useState('');
  const [topN, setTopN] = useState(50);

  const { data: positions = [], error: posErr } = usePositions();
  const { data: leagues = [], error: leagueErr } = useLeagues();

  const queryParams = useMemo<RankingsQueryParams>(() => ({
    position,
    min_minutes: minMinutes,
    league: league || undefined,
    top_n: topN,
  }), [position, minMinutes, league, topN]);

  const { data: rankings, isLoading, error: rankErr } = useRankings(queryParams);
  const anyError = rankErr || posErr || leagueErr;

  // Extract unique index names from first player for column headers
  const indexColumns = useMemo(() => {
    if (!rankings?.players?.length) return [];
    const first = rankings.players[0];
    return Object.keys(first.indices || {});
  }, [rankings]);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-[var(--font-display)] text-lg font-bold tracking-tight flex items-center gap-2">
          <Trophy size={18} style={{ color: 'var(--color-accent)' }} />
          Rankings
        </h1>
        <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
          SSP = 0.25×WP + 0.25×Efficiency + 0.15×Cluster + 0.35×Percentil (POSITION_WEIGHTS)
        </p>
      </div>

      {/* Error display */}
      {anyError && (
        <div
          className="flex items-center gap-2 px-4 py-3 rounded text-sm"
          style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444' }}
        >
          <AlertCircle size={16} />
          <span>Erro ao carregar dados: {(anyError as Error).message || 'Erro desconhecido'}</span>
        </div>
      )}

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
            {positions.length > 0 ? (
              positions.map((p) => <option key={p} value={p}>{p}</option>)
            ) : (
              <>
                <option value="Atacante">Atacante</option>
                <option value="Extremo">Extremo</option>
                <option value="Meia">Meia</option>
                <option value="Volante">Volante</option>
                <option value="Lateral">Lateral</option>
                <option value="Zagueiro">Zagueiro</option>
                <option value="Goleiro">Goleiro</option>
              </>
            )}
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
        <div>
          <label className="block text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>
            TOP N
          </label>
          <input
            type="number"
            value={topN}
            onChange={(e) => setTopN(Number(e.target.value))}
            className="w-20 px-3 py-2 rounded text-sm outline-none"
            style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)' }}
          />
        </div>
      </div>

      {/* Info bar */}
      {rankings && (
        <div
          className="px-4 py-2 rounded text-xs"
          style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-muted)' }}
        >
          {rankings.total} jogadores classificados para {rankings.position} | Min. {minMinutes} minutos
        </div>
      )}

      {/* Table */}
      <div className="card-glass rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                <th className="px-3 py-2.5 text-left text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-text-muted)' }}>#</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-text-muted)' }}>Jogador</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-text-muted)' }}>Equipa</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-text-muted)' }}>Liga</th>
                <th className="px-3 py-2.5 text-right text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-text-muted)' }}>Idade</th>
                <th className="px-3 py-2.5 text-right text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-text-muted)' }}>Min</th>
                {indexColumns.map((col) => (
                  <th key={col} className="px-3 py-2.5 text-right text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-text-muted)' }}>
                    {col.replace(/ index$/i, '').slice(0, 12)}
                  </th>
                ))}
                <th className="px-3 py-2.5 text-right text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-accent)' }}>
                  <span className="flex items-center justify-end gap-1">SSP <ArrowUpDown size={10} /></span>
                </th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                Array.from({ length: 10 }).map((_, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                    {Array.from({ length: 7 + indexColumns.length }).map((_, j) => (
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
                    <td className="px-3 py-2.5 text-xs" style={{ color: 'var(--color-text-muted)' }}>{entry.league || '—'}</td>
                    <td className="px-3 py-2.5 text-right font-[var(--font-mono)] text-xs" style={{ color: 'var(--color-text-muted)' }}>{entry.age != null ? formatNumber(entry.age) : '—'}</td>
                    <td className="px-3 py-2.5 text-right font-[var(--font-mono)] text-xs" style={{ color: 'var(--color-text-muted)' }}>{entry.minutes != null ? formatNumber(entry.minutes) : '—'}</td>
                    {indexColumns.map((col) => {
                      const val = entry.indices?.[col];
                      return (
                        <td key={col} className="px-3 py-2.5 text-right font-[var(--font-mono)] text-xs" style={{ color: val != null ? getScoreColor(val) : 'var(--color-text-muted)' }}>
                          {val != null ? val.toFixed(1) : '—'}
                        </td>
                      );
                    })}
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
                  <td colSpan={7 + indexColumns.length} className="px-3 py-8 text-center text-xs" style={{ color: 'var(--color-text-muted)' }}>
                    {anyError ? 'Erro ao carregar ranking — verifique a conexao com o servidor' : 'Nenhum resultado'}
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
