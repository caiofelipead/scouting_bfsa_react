import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Trophy, ArrowUpDown, AlertCircle, Target, User } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useRankings, usePositions, useLeagues } from '../hooks/usePlayers';
import { getScoreColor, formatNumber } from '../lib/utils';
import api, { proxyImageUrl } from '../lib/api';
import type { RankingsQueryParams } from '../types/api';

interface PredictionRankingEntry {
  rank: number;
  name: string;
  display_name: string;
  team: string | null;
  age: number;
  league: string;
  minutes: number;
  ssp: number;
  p_success: number;
  risk_level: string;
  league_gap: number;
  tier_origin: number;
  tier_target: number;
  photo_url: string | null;
  club_logo: string | null;
  league_logo: string | null;
}

const LIGAS_TARGET = [
  'Serie A Brasil', 'Serie B Brasil', 'Serie C Brasil',
  'Premier League', 'La Liga', 'Bundesliga', 'Serie A Italia', 'Ligue 1',
  'Liga Portugal', 'Eredivisie', 'MLS', 'Liga MX',
  'Liga Argentina', 'J1 League', 'Saudi Pro League',
];

const RISK_COLORS: Record<string, string> = {
  baixo: '#22c55e',
  medio: '#eab308',
  alto: '#ef4444',
  'muito alto': '#991b1b',
};

export default function RankingsPage() {
  const [mode, setMode] = useState<'ssp' | 'prediction'>('ssp');
  const [position, setPosition] = useState('Atacante');
  const [minMinutes, setMinMinutes] = useState(500);
  const [league, setLeague] = useState('');
  const [topN, setTopN] = useState(50);
  const [leagueTarget, setLeagueTarget] = useState('Serie B Brasil');

  const { data: positions = [], error: posErr } = usePositions();
  const { data: leagues = [], error: leagueErr } = useLeagues();

  // SSP ranking (existing)
  const queryParams = useMemo<RankingsQueryParams>(() => ({
    position,
    min_minutes: minMinutes,
    league: league || undefined,
    top_n: topN,
  }), [position, minMinutes, league, topN]);

  const { data: rankings, isLoading: sspLoading, error: rankErr } = useRankings(mode === 'ssp' ? queryParams : { position: '_disabled_', min_minutes: 0 });

  // Prediction ranking
  const { data: predRanking, isLoading: predLoading, error: predErr } = useQuery({
    queryKey: ['prediction-ranking', position, minMinutes, league, topN, leagueTarget],
    queryFn: async () => {
      const res = await api.post('/rankings/prediction', {
        position, min_minutes: minMinutes, league: league || undefined, top_n: topN, league_target: leagueTarget,
      });
      return res.data as { position: string; league_target: string; total: number; players: PredictionRankingEntry[] };
    },
    enabled: mode === 'prediction',
    staleTime: 10 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const isLoading = mode === 'ssp' ? sspLoading : predLoading;
  const anyError = (mode === 'ssp' ? rankErr : predErr) || posErr || leagueErr;

  // Extract unique index names from first player for column headers
  const indexColumns = useMemo(() => {
    if (mode !== 'ssp' || !rankings?.players?.length) return [];
    const first = rankings.players[0];
    return Object.keys(first.indices || {});
  }, [rankings, mode]);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-[var(--font-display)] text-lg font-bold tracking-tight flex items-center gap-2">
          <Trophy size={18} style={{ color: 'var(--color-accent)' }} />
          Rankings
        </h1>
        <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
          {mode === 'ssp'
            ? 'SSP = 0.25×WP + 0.25×Efficiency + 0.15×Cluster + 0.35×Percentil'
            : 'P(Sucesso) = f(SSP, idade, liga_origem, liga_alvo, minutos)'}
        </p>
      </div>

      {/* Error display */}
      {anyError && (
        <div className="flex items-center gap-2 px-4 py-3 rounded text-sm" style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444' }}>
          <AlertCircle size={16} />
          <span>Erro ao carregar dados: {(anyError as Error).message || 'Erro desconhecido'}</span>
        </div>
      )}

      {/* Mode toggle */}
      <div className="flex gap-2">
        <button
          onClick={() => setMode('ssp')}
          className="px-4 py-2 rounded text-sm font-[var(--font-display)] tracking-wide cursor-pointer transition-all"
          style={{
            background: mode === 'ssp' ? 'var(--color-accent-glow)' : 'var(--color-surface-1)',
            color: mode === 'ssp' ? 'var(--color-accent)' : 'var(--color-text-secondary)',
            border: `1px solid ${mode === 'ssp' ? 'rgba(220,38,38,0.3)' : 'var(--color-border-subtle)'}`,
          }}
        >
          <Trophy size={14} className="inline mr-1.5" />
          SSP (Score Preditivo)
        </button>
        <button
          onClick={() => setMode('prediction')}
          className="px-4 py-2 rounded text-sm font-[var(--font-display)] tracking-wide cursor-pointer transition-all"
          style={{
            background: mode === 'prediction' ? 'var(--color-accent-glow)' : 'var(--color-surface-1)',
            color: mode === 'prediction' ? 'var(--color-accent)' : 'var(--color-text-secondary)',
            border: `1px solid ${mode === 'prediction' ? 'rgba(220,38,38,0.3)' : 'var(--color-border-subtle)'}`,
          }}
        >
          <Target size={14} className="inline mr-1.5" />
          P(Sucesso) Predicao
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label className="block text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>POSICAO</label>
          <select value={position} onChange={(e) => setPosition(e.target.value)} className="px-3 py-2 rounded text-sm cursor-pointer outline-none" style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-secondary)' }}>
            {positions.length > 0 ? positions.map((p) => <option key={p} value={p}>{p}</option>) : ['Atacante','Extremo','Meia','Volante','Lateral direito','Lateral esquerdo','Zagueiro','Goleiro'].map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>MIN. MINUTOS</label>
          <input type="number" value={minMinutes} onChange={(e) => setMinMinutes(Number(e.target.value))} className="w-24 px-3 py-2 rounded text-sm outline-none" style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)' }} />
        </div>
        <div>
          <label className="block text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>LIGA</label>
          <select value={league} onChange={(e) => setLeague(e.target.value)} className="px-3 py-2 rounded text-sm cursor-pointer outline-none" style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-secondary)' }}>
            <option value="">Todas</option>
            {leagues.map((l) => <option key={l} value={l}>{l}</option>)}
          </select>
        </div>
        {mode === 'prediction' && (
          <div>
            <label className="block text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>LIGA ALVO</label>
            <select value={leagueTarget} onChange={(e) => setLeagueTarget(e.target.value)} className="px-3 py-2 rounded text-sm cursor-pointer outline-none" style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-secondary)' }}>
              {LIGAS_TARGET.map(l => <option key={l} value={l}>{l}</option>)}
            </select>
          </div>
        )}
        <div>
          <label className="block text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>TOP N</label>
          <input type="number" value={topN} onChange={(e) => setTopN(Number(e.target.value))} className="w-20 px-3 py-2 rounded text-sm outline-none" style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)' }} />
        </div>
      </div>

      {/* Info bar */}
      {mode === 'ssp' && rankings && (
        <div className="px-4 py-2 rounded text-xs" style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-muted)' }}>
          {rankings.total} jogadores classificados para {rankings.position} | Min. {minMinutes} minutos
        </div>
      )}
      {mode === 'prediction' && predRanking && (
        <div className="px-4 py-2 rounded text-xs" style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-muted)' }}>
          {predRanking.total} jogadores | {predRanking.position} → {predRanking.league_target} | Min. {minMinutes} minutos
        </div>
      )}

      {/* Table */}
      <div className="card-glass rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          {mode === 'ssp' ? (
            /* SSP Ranking Table */
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
                    <motion.tr key={entry.rank} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.02 }} style={{ borderBottom: '1px solid var(--color-border-subtle)' }} className="transition-colors hover:bg-white/[0.02]">
                      <td className="px-3 py-2.5 font-[var(--font-mono)] text-xs" style={{ color: i < 3 ? 'var(--color-accent)' : 'var(--color-text-muted)' }}>{entry.rank}</td>
                      <td className="px-3 py-2.5">
                        <div className="flex items-center gap-2">
                          {entry.photo_url ? (
                            <img src={proxyImageUrl(entry.photo_url)!} alt="" className="w-7 h-7 rounded-full object-cover flex-shrink-0" style={{ background: 'var(--color-surface-2)' }} onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                          ) : (
                            <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: 'var(--color-surface-2)' }}><User size={14} style={{ color: 'var(--color-text-muted)' }} /></div>
                          )}
                          <span className="font-medium whitespace-nowrap">{entry.name}</span>
                        </div>
                      </td>
                      <td className="px-3 py-2.5">
                        <div className="flex items-center gap-1.5">
                          {entry.club_logo && <img src={proxyImageUrl(entry.club_logo)!} alt="" className="w-5 h-5 object-contain flex-shrink-0" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />}
                          <span className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>{entry.team || '—'}</span>
                        </div>
                      </td>
                      <td className="px-3 py-2.5">
                        <div className="flex items-center gap-1.5">
                          {entry.league_logo && <img src={proxyImageUrl(entry.league_logo)!} alt="" className="w-4 h-4 object-contain flex-shrink-0" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />}
                          <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>{entry.league || '—'}</span>
                        </div>
                      </td>
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
                        <span className="inline-block px-2 py-0.5 rounded text-xs font-[var(--font-mono)] font-bold" style={{ color: getScoreColor(entry.score), background: `${getScoreColor(entry.score)}15` }}>
                          {entry.score.toFixed(1)}
                        </span>
                      </td>
                    </motion.tr>
                  ))
                ) : (
                  <tr><td colSpan={7 + indexColumns.length} className="px-3 py-8 text-center text-xs" style={{ color: 'var(--color-text-muted)' }}>{anyError ? 'Erro ao carregar ranking' : 'Nenhum resultado'}</td></tr>
                )}
              </tbody>
            </table>
          ) : (
            /* Prediction Ranking Table */
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                  <th className="px-3 py-2.5 text-left text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-text-muted)' }}>#</th>
                  <th className="px-3 py-2.5 text-left text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-text-muted)' }}>Jogador</th>
                  <th className="px-3 py-2.5 text-left text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-text-muted)' }}>Equipa</th>
                  <th className="px-3 py-2.5 text-left text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-text-muted)' }}>Liga Origem</th>
                  <th className="px-3 py-2.5 text-right text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-text-muted)' }}>Idade</th>
                  <th className="px-3 py-2.5 text-right text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-text-muted)' }}>Min</th>
                  <th className="px-3 py-2.5 text-right text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-text-muted)' }}>SSP</th>
                  <th className="px-3 py-2.5 text-right text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-text-muted)' }}>Gap</th>
                  <th className="px-3 py-2.5 text-center text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-text-muted)' }}>Risco</th>
                  <th className="px-3 py-2.5 text-right text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-accent)' }}>
                    <span className="flex items-center justify-end gap-1">P(Sucesso) <ArrowUpDown size={10} /></span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  Array.from({ length: 10 }).map((_, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                      {Array.from({ length: 10 }).map((_, j) => (
                        <td key={j} className="px-3 py-2.5"><div className="skeleton h-4 rounded" /></td>
                      ))}
                    </tr>
                  ))
                ) : predRanking && predRanking.players.length > 0 ? (
                  predRanking.players.map((entry, i) => {
                    const prob = entry.p_success * 100;
                    const riskColor = RISK_COLORS[entry.risk_level] || '#6b7280';
                    return (
                      <motion.tr key={entry.rank} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.02 }} style={{ borderBottom: '1px solid var(--color-border-subtle)' }} className="transition-colors hover:bg-white/[0.02]">
                        <td className="px-3 py-2.5 font-[var(--font-mono)] text-xs" style={{ color: i < 3 ? 'var(--color-accent)' : 'var(--color-text-muted)' }}>{entry.rank}</td>
                        <td className="px-3 py-2.5">
                          <div className="flex items-center gap-2">
                            {entry.photo_url ? (
                              <img src={proxyImageUrl(entry.photo_url)!} alt="" className="w-7 h-7 rounded-full object-cover flex-shrink-0" style={{ background: 'var(--color-surface-2)' }} onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                            ) : (
                              <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: 'var(--color-surface-2)' }}><User size={14} style={{ color: 'var(--color-text-muted)' }} /></div>
                            )}
                            <span className="font-medium whitespace-nowrap">{entry.name}</span>
                          </div>
                        </td>
                        <td className="px-3 py-2.5">
                          <div className="flex items-center gap-1.5">
                            {entry.club_logo && <img src={proxyImageUrl(entry.club_logo)!} alt="" className="w-5 h-5 object-contain flex-shrink-0" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />}
                            <span className="text-xs whitespace-nowrap" style={{ color: 'var(--color-text-secondary)' }}>{entry.team || '—'}</span>
                          </div>
                        </td>
                        <td className="px-3 py-2.5">
                          <div className="flex items-center gap-1.5">
                            {entry.league_logo && <img src={proxyImageUrl(entry.league_logo)!} alt="" className="w-4 h-4 object-contain flex-shrink-0" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />}
                            <span className="text-xs whitespace-nowrap" style={{ color: 'var(--color-text-muted)' }}>{entry.league || '—'}</span>
                          </div>
                        </td>
                        <td className="px-3 py-2.5 text-right font-[var(--font-mono)] text-xs" style={{ color: 'var(--color-text-muted)' }}>{formatNumber(entry.age)}</td>
                        <td className="px-3 py-2.5 text-right font-[var(--font-mono)] text-xs" style={{ color: 'var(--color-text-muted)' }}>{formatNumber(entry.minutes)}</td>
                        <td className="px-3 py-2.5 text-right font-[var(--font-mono)] text-xs" style={{ color: getScoreColor(entry.ssp) }}>{entry.ssp.toFixed(1)}</td>
                        <td className="px-3 py-2.5 text-right font-[var(--font-mono)] text-xs" style={{ color: entry.league_gap > 2 ? '#ef4444' : entry.league_gap > 0 ? '#eab308' : '#22c55e' }}>
                          {entry.league_gap > 0 ? '+' : ''}{entry.league_gap.toFixed(0)}
                        </td>
                        <td className="px-3 py-2.5 text-center">
                          <span className="px-2 py-0.5 rounded text-[10px] font-[var(--font-display)] font-bold uppercase" style={{ color: riskColor, background: `${riskColor}15` }}>
                            {entry.risk_level}
                          </span>
                        </td>
                        <td className="px-3 py-2.5 text-right">
                          <span className="inline-block px-2.5 py-0.5 rounded text-xs font-[var(--font-mono)] font-bold" style={{ color: prob >= 65 ? '#22c55e' : prob >= 40 ? '#eab308' : '#ef4444', background: prob >= 65 ? 'rgba(34,197,94,0.1)' : prob >= 40 ? 'rgba(234,179,8,0.1)' : 'rgba(239,68,68,0.1)' }}>
                            {prob.toFixed(0)}%
                          </span>
                        </td>
                      </motion.tr>
                    );
                  })
                ) : (
                  <tr><td colSpan={10} className="px-3 py-8 text-center text-xs" style={{ color: 'var(--color-text-muted)' }}>{anyError ? 'Erro ao carregar ranking' : 'Nenhum resultado'}</td></tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
