import { useState } from 'react';
import { motion } from 'framer-motion';
import { Gem, AlertCircle, Star } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import api from '../lib/api';
import { usePositions } from '../hooks/usePlayers';
import { getScoreColor } from '../lib/utils';

interface OpportunityEntry {
  player: string;
  player_display: string | null;
  team?: string | null;
  market_opportunity_score: number;
  classification: string;
  is_high_opportunity: boolean;
  components: {
    performance: number;
    trajectory: number;
    value_gap: number;
    minutes_factor: number;
    league_factor: number;
    age_penalty: number;
  } | null;
}

interface OpportunitiesResult {
  position: string | null;
  total: number;
  opportunities: OpportunityEntry[];
}

const CLASS_LABELS: Record<string, { label: string; color: string }> = {
  'exceptional_opportunity': { label: 'Excepcional', color: '#22c55e' },
  'high_opportunity': { label: 'Alta', color: '#3b82f6' },
  'moderate_opportunity': { label: 'Moderada', color: '#eab308' },
  'low_opportunity': { label: 'Baixa', color: '#f97316' },
  'below_threshold': { label: 'Abaixo', color: '#ef4444' },
};

export default function OpportunitiesPage() {
  const [position, setPosition] = useState('Atacante');
  const [topN, setTopN] = useState(30);
  const [minMinutes, setMinMinutes] = useState(400);
  const { data: positions } = usePositions();

  const opportunities = useMutation({
    mutationFn: async () => {
      const res = await api.post('/market_opportunities', {
        position: position || null,
        top_n: topN,
        min_minutes: minMinutes,
      });
      return res.data as OpportunitiesResult;
    },
  });

  const results = opportunities.data?.opportunities ?? [];

  return (
    <div className="space-y-5">
      <div>
        <h1 className="page-title flex items-center gap-2.5">
          <Gem size={22} strokeWidth={2} style={{ color: 'var(--color-accent)' }} />
          Oportunidades de Mercado
        </h1>
        <p className="page-subtitle">
          Deteccao de talentos subvalorizados — inspirado em Brighton, Brentford, Midtjylland
        </p>
      </div>

      {opportunities.error && (
        <div className="flex items-center gap-2 px-4 py-3 rounded text-sm" style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444' }}>
          <AlertCircle size={16} /><span>Erro: {(opportunities.error as Error).message}</span>
        </div>
      )}

      <div className="card-glass rounded-lg p-5">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 items-end">
          <div>
            <label className="block text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>POSICAO</label>
            <select value={position} onChange={(e) => setPosition(e.target.value)} className="w-full px-3 py-2 rounded text-sm cursor-pointer outline-none" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-secondary)' }}>
              <option value="">Todas</option>
              {(positions || []).map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>MIN MINUTOS</label>
            <input type="number" value={minMinutes} onChange={(e) => setMinMinutes(Number(e.target.value))} className="w-full px-3 py-2 rounded text-sm outline-none" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)' }} />
          </div>
          <div>
            <label className="block text-[11px] font-[var(--font-display)] tracking-[0.12em] font-semibold uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>TOP N</label>
            <input type="number" value={topN} onChange={(e) => setTopN(Number(e.target.value))} className="w-full px-3 py-2 rounded text-sm outline-none" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)' }} />
          </div>
          <button
            onClick={() => opportunities.mutate()}
            disabled={opportunities.isPending}
            className="px-5 py-2 rounded text-sm font-[var(--font-display)] font-semibold tracking-wide uppercase transition-all cursor-pointer disabled:opacity-40"
            style={{ background: 'var(--color-accent)', color: '#fff', border: 'none' }}
          >
            {opportunities.isPending ? '...' : 'DETECTAR'}
          </button>
        </div>
      </div>

      {results.length > 0 && (
        <div className="card-glass rounded-lg overflow-hidden">
          <div className="px-5 py-3 flex items-center justify-between" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
            <span className="text-[11px] font-[var(--font-display)] tracking-[0.16em] font-semibold uppercase" style={{ color: 'var(--color-text-muted)' }}>
              {results.length} OPORTUNIDADES ENCONTRADAS
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                  <th className="px-4 py-2 text-left text-[10px] font-[var(--font-display)] tracking-wider uppercase" style={{ color: 'var(--color-text-muted)' }}>#</th>
                  <th className="px-4 py-2 text-left text-[10px] font-[var(--font-display)] tracking-wider uppercase" style={{ color: 'var(--color-text-muted)' }}>Jogador</th>
                  <th className="px-4 py-2 text-center text-[10px] font-[var(--font-display)] tracking-wider uppercase" style={{ color: 'var(--color-text-muted)' }}>Score</th>
                  <th className="px-4 py-2 text-center text-[10px] font-[var(--font-display)] tracking-wider uppercase" style={{ color: 'var(--color-text-muted)' }}>Classe</th>
                  <th className="px-4 py-2 text-center text-[10px] font-[var(--font-display)] tracking-wider uppercase hidden md:table-cell" style={{ color: 'var(--color-text-muted)' }}>Perf</th>
                  <th className="px-4 py-2 text-center text-[10px] font-[var(--font-display)] tracking-wider uppercase hidden md:table-cell" style={{ color: 'var(--color-text-muted)' }}>Traj</th>
                  <th className="px-4 py-2 text-center text-[10px] font-[var(--font-display)] tracking-wider uppercase hidden md:table-cell" style={{ color: 'var(--color-text-muted)' }}>Gap</th>
                </tr>
              </thead>
              <tbody>
                {results.map((opp, i) => {
                  const cl = CLASS_LABELS[opp.classification] || { label: opp.classification, color: '#6b7280' };
                  return (
                    <motion.tr
                      key={i}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.02 }}
                      style={{ borderBottom: '1px solid var(--color-border-subtle)' }}
                      className="hover:bg-white/[0.02]"
                    >
                      <td className="px-4 py-2.5 font-[var(--font-mono)] text-xs" style={{ color: 'var(--color-text-muted)' }}>{i + 1}</td>
                      <td className="px-4 py-2.5">
                        <div className="flex items-center gap-2">
                          {opp.is_high_opportunity && <Star size={12} style={{ color: '#eab308' }} />}
                          <div>
                            <div className="font-medium" style={{ color: 'var(--color-text-primary)' }}>{opp.player_display || opp.player}</div>
                            {opp.team && <div className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>{opp.team}</div>}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-2.5 text-center">
                        <span className="font-[var(--font-mono)] font-bold" style={{ color: getScoreColor(opp.market_opportunity_score) }}>
                          {opp.market_opportunity_score.toFixed(1)}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 text-center">
                        <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold" style={{ background: cl.color + '20', color: cl.color }}>
                          {cl.label}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 text-center hidden md:table-cell font-[var(--font-mono)] text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                        {opp.components?.performance?.toFixed(0) ?? '-'}
                      </td>
                      <td className="px-4 py-2.5 text-center hidden md:table-cell font-[var(--font-mono)] text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                        {opp.components?.trajectory?.toFixed(0) ?? '-'}
                      </td>
                      <td className="px-4 py-2.5 text-center hidden md:table-cell font-[var(--font-mono)] text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                        {opp.components?.value_gap?.toFixed(0) ?? '-'}
                      </td>
                    </motion.tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {results.length === 0 && !opportunities.isPending && (
        <div className="card-glass rounded-lg p-8 text-center" style={{ color: 'var(--color-text-muted)' }}>
          <Gem size={32} className="mx-auto mb-3 opacity-30" />
          <p className="text-sm">Selecione filtros e clique em DETECTAR</p>
          <p className="text-xs mt-1 opacity-60">score = performance x trajectory x value_gap - age_penalty</p>
        </div>
      )}
    </div>
  );
}
