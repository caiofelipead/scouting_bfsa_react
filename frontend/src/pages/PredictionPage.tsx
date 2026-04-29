import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Target, AlertCircle } from 'lucide-react';
import { useMutation, useQuery } from '@tanstack/react-query';
import api from '../lib/api';
import { usePlayers, usePositions } from '../hooks/usePlayers';
import { getScoreColor } from '../lib/utils';
import type { PredictionResponse } from '../types/api';

const LIGAS = [
  'Serie A Brasil', 'Serie B Brasil', 'Serie C Brasil', 'Serie D Brasil',
  'Paulista A1', 'Paulista A2', 'Paulista A3',
  'Carioca A1', 'Gaucho A1', 'Mineiro A1', 'Paranaense A1',
  'Copa do Brasil', 'Copa do Nordeste',
  'Premier League', 'La Liga', 'Bundesliga', 'Serie A Italia', 'Ligue 1',
  'Championship', 'La Liga 2', 'Serie B Italia', '2. Bundesliga', 'Ligue 2',
  'Liga Portugal', 'Eredivisie', 'Belgian Pro League', 'Super Lig',
  'Liga Argentina', 'MLS', 'Liga MX', 'Liga Colombia', 'Liga Chile',
  'Copa Libertadores', 'Copa Sudamericana',
  'J1 League', 'K-League 1', 'Saudi Pro League',
  'A-League',
];

export default function PredictionPage() {
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedPlayer, setSelectedPlayer] = useState('');
  const [leagueOrigin, setLeagueOrigin] = useState('Serie A Brasil');
  const [leagueTarget, setLeagueTarget] = useState('Serie B Brasil');
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

  const prediction = useMutation({
    mutationFn: async () => {
      const res = await api.post('/prediction', {
        player_name: selectedPlayer,
        league_origin: leagueOrigin,
        league_target: leagueTarget,
      });
      return res.data as PredictionResponse;
    },
  });

  const result = prediction.data;
  const pred = result?.prediction;

  const riskColors: Record<string, string> = { 'baixo': '#22c55e', 'medio': '#eab308', 'alto': '#ef4444', 'muito alto': '#991b1b' };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="page-title flex items-center gap-2.5">
          <Target size={22} strokeWidth={2} style={{ color: 'var(--color-accent)' }} />
          Predicao de Sucesso
        </h1>
        <p className="page-subtitle">
          Modelo baseado em SSP + idade + nivel da liga + minutagem
        </p>
      </div>

      {prediction.error && (
        <div className="flex items-center gap-2 px-4 py-3 rounded text-sm" style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444' }}>
          <AlertCircle size={16} /><span>Erro: {(prediction.error as Error).message}</span>
        </div>
      )}

      <div className="card-glass rounded-lg p-5 space-y-4" style={{ overflow: 'visible' }}>
        <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_auto_auto] gap-3 items-end" style={{ overflow: 'visible' }}>
          <div>
            <label className="block text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>JOGADOR</label>
            <div className="relative">
              <input type="text" value={search} onChange={(e) => handleSearchChange(e.target.value)} placeholder="Digite o nome..." className="w-full px-3 py-2 rounded text-sm outline-none" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)' }} />
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
          <div>
            <label className="block text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>LIGA ORIGEM</label>
            <select value={leagueOrigin} onChange={(e) => setLeagueOrigin(e.target.value)} className="px-3 py-2 rounded text-sm cursor-pointer outline-none" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-secondary)' }}>
              {LIGAS.map(l => <option key={l} value={l}>{l}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>LIGA ALVO</label>
            <select value={leagueTarget} onChange={(e) => setLeagueTarget(e.target.value)} className="px-3 py-2 rounded text-sm cursor-pointer outline-none" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-secondary)' }}>
              {LIGAS.map(l => <option key={l} value={l}>{l}</option>)}
            </select>
          </div>
          <button
            onClick={() => prediction.mutate()}
            disabled={!selectedPlayer || prediction.isPending}
            className="px-5 py-2 rounded text-sm font-[var(--font-display)] font-semibold tracking-wide uppercase transition-all cursor-pointer disabled:opacity-40"
            style={{ background: 'var(--color-accent)', color: '#fff', border: 'none' }}
          >
            {prediction.isPending ? '...' : 'CALCULAR'}
          </button>
        </div>
      </div>

      {result && pred && (
        <>
          {/* Player header */}
          <div className="card-glass rounded-lg p-5" style={{ background: 'linear-gradient(135deg, rgba(30,41,59,0.8), rgba(15,23,42,0.8))' }}>
            <div className="font-bold text-xl">{result.player.name}</div>
            <div className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>
              {result.player.team} | {result.player.position} | {result.player.age} anos | {result.player.minutes} min
            </div>
          </div>

          {/* Main metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="card-glass rounded-lg p-4 text-center">
              <div className="text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase" style={{ color: 'var(--color-text-muted)' }}>SSP</div>
              <div className="text-2xl font-[var(--font-mono)] font-bold mt-1" style={{ color: getScoreColor(result.ssp_score) }}>{result.ssp_score.toFixed(1)}</div>
              <div className="text-[9px]" style={{ color: 'var(--color-text-muted)' }}>/100</div>
            </motion.div>
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="card-glass rounded-lg p-4 text-center">
              <div className="text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase" style={{ color: 'var(--color-text-muted)' }}>P(SUCESSO)</div>
              <div className="text-2xl font-[var(--font-mono)] font-bold mt-1" style={{ color: pred.success_probability >= 0.65 ? '#22c55e' : pred.success_probability >= 0.40 ? '#eab308' : '#ef4444' }}>
                {(pred.success_probability * 100).toFixed(0)}%
              </div>
              <div className="text-[9px]" style={{ color: 'var(--color-text-muted)' }}>Probabilidade</div>
            </motion.div>
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="card-glass rounded-lg p-4 text-center">
              <div className="text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase" style={{ color: 'var(--color-text-muted)' }}>RISCO</div>
              <div className="text-xl font-[var(--font-display)] font-bold mt-1 uppercase" style={{ color: riskColors[pred.risk_level] || '#6b7280' }}>
                {pred.risk_level}
              </div>
            </motion.div>
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="card-glass rounded-lg p-4 text-center">
              <div className="text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase" style={{ color: 'var(--color-text-muted)' }}>GAP DE LIGA</div>
              <div className="text-2xl font-[var(--font-mono)] font-bold mt-1" style={{ color: pred.league_gap > 2 ? '#ef4444' : pred.league_gap > 0 ? '#eab308' : '#22c55e' }}>
                {pred.league_gap > 0 ? '+' : ''}{pred.league_gap.toFixed(1)}
              </div>
              <div className="text-[9px]" style={{ color: 'var(--color-text-muted)' }}>Tier {pred.tier_origin.toFixed(1)} → {pred.tier_target.toFixed(1)}</div>
            </motion.div>
          </div>

          {/* Factor decomposition */}
          <div className="card-glass rounded-lg p-5">
            <div className="text-[11px] font-[var(--font-display)] tracking-[0.16em] font-semibold uppercase mb-4" style={{ color: 'var(--color-text-muted)' }}>DECOMPOSICAO DOS FATORES</div>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {[
                { label: 'SSP Ajustado', value: pred.ssp_contribution, fmt: (v: number) => v.toFixed(3), help: 'SSP descontado pela liga de origem' },
                { label: 'Fator Idade', value: pred.age_factor, fmt: (v: number) => v.toFixed(3), help: 'Peak=26, decay quadratico' },
                { label: 'Fator Liga', value: pred.league_factor, fmt: (v: number) => v.toFixed(3), help: `Tiers: ${pred.tier_origin.toFixed(1)} → ${pred.tier_target.toFixed(1)}` },
                { label: 'Fator Minutos', value: pred.minutes_factor, fmt: (v: number) => v.toFixed(3) },
                { label: 'Desconto Liga', value: pred.league_discount, fmt: (v: number) => `${(v * 100).toFixed(0)}%` },
              ].map((f, i) => (
                <div key={f.label} className="p-3 rounded text-center" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)' }}>
                  <div className="text-[9px] uppercase" style={{ color: 'var(--color-text-muted)' }}>{f.label}</div>
                  <div className="text-lg font-[var(--font-mono)] font-bold mt-1" style={{ color: getScoreColor(f.value * 100) }}>{f.fmt(f.value)}</div>
                  {f.help && <div className="text-[8px] mt-0.5" style={{ color: 'var(--color-text-muted)' }}>{f.help}</div>}
                </div>
              ))}
            </div>
          </div>

          {pred.league_gap >= 4 && (
            <div className="flex items-center gap-2 px-4 py-3 rounded text-sm" style={{ background: 'rgba(234,179,8,0.1)', border: '1px solid rgba(234,179,8,0.3)', color: '#eab308' }}>
              <AlertCircle size={16} />
              <span>Gap de {pred.league_gap.toFixed(0)} tiers ({leagueOrigin} → {leagueTarget}). Probabilidade limitada pelo ceiling.</span>
            </div>
          )}
        </>
      )}

      {!result && !prediction.isPending && (
        <div className="card-glass rounded-lg p-8 text-center" style={{ color: 'var(--color-text-muted)' }}>
          <Target size={32} className="mx-auto mb-3 opacity-30" />
          <p className="text-sm">Selecione um jogador e clique em CALCULAR</p>
          <p className="text-xs mt-1 opacity-60">P(Sucesso) = f(SSP, idade, liga_origem, liga_alvo, minutos)</p>
        </div>
      )}
    </div>
  );
}
