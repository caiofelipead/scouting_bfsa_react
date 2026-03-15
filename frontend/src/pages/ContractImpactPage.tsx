import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  UserPlus,
  AlertCircle,
  Shield,
  TrendingUp,
  Crosshair,
  Clock,
  DollarSign,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Users,
} from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import api from '../lib/api';
import { usePlayers } from '../hooks/usePlayers';

interface ComponentDetail {
  score: number;
  [key: string]: unknown;
}

interface ImpactResult {
  candidate: {
    name: string;
    position: string;
    age: number;
    league: string | null;
    estimated_value: number | null;
  };
  impact_score: number;
  classification: string;
  recommendation: string;
  component_scores: Record<string, number>;
  component_weights: Record<string, number>;
  positional_need: ComponentDetail & {
    current_depth: number;
    ideal_depth: number;
    avg_age_at_position: number;
    need_level: string;
  };
  quality_uplift: ComponentDetail & {
    avg_percentile: number;
    uplift_ratio: number | null;
    metrics_compared: number;
    top_metrics: Record<string, { candidate: number; squad_avg: number; ratio: number }>;
  };
  tactical_complementarity: ComponentDetail & {
    avg_similarity_to_sector: number | null;
    sector: string;
    sector_player_count: number;
    profile_type: string;
  };
  age_profile_fit: ComponentDetail & {
    candidate_category: string;
    squad_distribution: { young_pct: number; prime_pct: number; experienced_pct: number };
    remaining_career_years: number;
    avg_squad_age: number;
  };
  financial_efficiency: ComponentDetail & {
    estimated_value_eur_m: number | null;
    value_gap: number | null;
    trajectory_score: number | null;
    is_undervalued: boolean;
  };
  risk_assessment: ComponentDetail & {
    risk_level: string;
    risks: string[];
    league_gap: number;
  };
  squad_context: {
    current_players_at_position: { name: string; age: number }[];
    squad_size: number;
    position_depth: number;
    ideal_depth: number;
  };
}

const CLASSIFICATION_CONFIG: Record<string, { label: string; color: string; icon: typeof CheckCircle }> = {
  high_impact: { label: 'Alto Impacto', color: '#22c55e', icon: CheckCircle },
  positive_impact: { label: 'Impacto Positivo', color: '#3b82f6', icon: TrendingUp },
  moderate_impact: { label: 'Impacto Moderado', color: '#eab308', icon: AlertTriangle },
  low_impact: { label: 'Impacto Baixo', color: '#f97316', icon: AlertTriangle },
  negative_impact: { label: 'Impacto Negativo', color: '#ef4444', icon: XCircle },
};

const COMPONENT_LABELS: Record<string, { label: string; icon: typeof Shield }> = {
  positional_need: { label: 'Necessidade Posicional', icon: Users },
  quality_uplift: { label: 'Ganho de Qualidade', icon: TrendingUp },
  tactical_complementarity: { label: 'Complementaridade Tática', icon: Crosshair },
  age_profile_fit: { label: 'Perfil Etário', icon: Clock },
  financial_efficiency: { label: 'Eficiência Financeira', icon: DollarSign },
  risk_assessment: { label: 'Avaliação de Risco', icon: Shield },
};

function getScoreColor(score: number): string {
  if (score >= 75) return '#22c55e';
  if (score >= 60) return '#3b82f6';
  if (score >= 45) return '#eab308';
  if (score >= 30) return '#f97316';
  return '#ef4444';
}

function formatEUR(millions: number): string {
  if (millions >= 1.0) return `€${millions.toFixed(1)}M`;
  return `€${(millions * 1000).toFixed(0)}K`;
}

export default function ContractImpactPage() {
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedPlayer, setSelectedPlayer] = useState('');
  const [estimatedValue, setEstimatedValue] = useState('');
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

  const analysis = useMutation({
    mutationFn: async () => {
      const payload: Record<string, unknown> = { player_name: selectedPlayer };
      if (estimatedValue) payload.estimated_value = parseFloat(estimatedValue);
      const res = await api.post('/contract_impact', payload);
      return res.data as ImpactResult;
    },
  });

  const result = analysis.data;
  const classConfig = result ? CLASSIFICATION_CONFIG[result.classification] : null;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-[var(--font-display)] text-lg font-bold tracking-tight flex items-center gap-2">
          <UserPlus size={18} style={{ color: 'var(--color-accent)' }} />
          Impacto de Contratação
        </h1>
        <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
          Análise de impacto no elenco — PlayeRank, Soccernomics, Age Curves 2.0
        </p>
      </div>

      {analysis.error && (
        <div className="flex items-center gap-2 px-4 py-3 rounded text-sm" style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444' }}>
          <AlertCircle size={16} /><span>Erro: {(analysis.error as Error).message}</span>
        </div>
      )}

      {/* Input form */}
      <div className="card-glass rounded-lg p-5 space-y-4" style={{ overflow: 'visible', position: 'relative', zIndex: 10 }}>
        <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_auto] gap-3 items-end" style={{ overflow: 'visible' }}>
          <div>
            <label className="block text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>JOGADOR CANDIDATO</label>
            <div className="relative" style={{ zIndex: 100 }}>
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
          <div>
            <label className="block text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>VALOR €M (opcional)</label>
            <input type="number" value={estimatedValue} onChange={(e) => setEstimatedValue(e.target.value)} placeholder="Ex: 1.5" className="px-3 py-2 rounded text-sm outline-none w-40" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)' }} />
          </div>
          <button
            onClick={() => analysis.mutate()}
            disabled={!selectedPlayer || analysis.isPending}
            className="px-5 py-2 rounded text-sm font-[var(--font-display)] font-semibold tracking-wide uppercase transition-all cursor-pointer disabled:opacity-40"
            style={{ background: 'var(--color-accent)', color: '#fff', border: 'none' }}
          >
            {analysis.isPending ? '...' : 'ANALISAR'}
          </button>
        </div>
      </div>

      {/* Results */}
      {result && (
        <>
          {/* Header: player + main score */}
          <div className="card-glass rounded-lg p-5" style={{ background: 'linear-gradient(135deg, rgba(30,41,59,0.8), rgba(15,23,42,0.8))' }}>
            <div className="flex items-start justify-between flex-wrap gap-4">
              <div>
                <div className="font-bold text-xl">{result.candidate.name}</div>
                <div className="text-xs mt-1 flex items-center gap-2" style={{ color: 'var(--color-text-muted)' }}>
                  <span>{result.candidate.position}</span>
                  {result.candidate.league && <><span>·</span><span>{result.candidate.league}</span></>}
                  {result.candidate.age != null && <><span>·</span><span>{result.candidate.age.toFixed(0)} anos</span></>}
                  {result.candidate.estimated_value != null && <><span>·</span><span>{formatEUR(result.candidate.estimated_value)}</span></>}
                </div>
              </div>
              <div className="text-right">
                <div className="text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase" style={{ color: 'var(--color-text-muted)' }}>IMPACT SCORE</div>
                <div className="text-3xl font-[var(--font-mono)] font-bold" style={{ color: getScoreColor(result.impact_score) }}>
                  {result.impact_score.toFixed(1)}
                </div>
                {classConfig && (
                  <div className="flex items-center gap-1.5 justify-end mt-1">
                    <classConfig.icon size={14} style={{ color: classConfig.color }} />
                    <span className="text-xs font-[var(--font-display)] font-semibold uppercase" style={{ color: classConfig.color }}>
                      {classConfig.label}
                    </span>
                  </div>
                )}
              </div>
            </div>
            <div className="mt-3 text-sm" style={{ color: 'var(--color-text-secondary)' }}>
              {result.recommendation}
            </div>
          </div>

          {/* Component scores grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {Object.entries(COMPONENT_LABELS).map(([key, { label, icon: Icon }], idx) => {
              const score = result.component_scores[key] ?? 0;
              const weight = result.component_weights[key] ?? 0;
              return (
                <motion.div
                  key={key}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.08 }}
                  className="card-glass rounded-lg p-4"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <Icon size={14} style={{ color: getScoreColor(score) }} />
                    <span className="text-[10px] font-[var(--font-display)] tracking-[0.08em] uppercase" style={{ color: 'var(--color-text-muted)' }}>
                      {label}
                    </span>
                  </div>
                  <div className="text-2xl font-[var(--font-mono)] font-bold" style={{ color: getScoreColor(score) }}>
                    {score.toFixed(1)}
                  </div>
                  {/* Progress bar */}
                  <div className="mt-2 h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--color-surface-2)' }}>
                    <div className="h-full rounded-full transition-all" style={{ width: `${score}%`, background: getScoreColor(score) }} />
                  </div>
                  <div className="text-[9px] mt-1" style={{ color: 'var(--color-text-muted)' }}>Peso: {weight}%</div>
                </motion.div>
              );
            })}
          </div>

          {/* Detailed analysis sections */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Positional Need Detail */}
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }} className="card-glass rounded-lg p-4">
              <div className="text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-3 flex items-center gap-2" style={{ color: 'var(--color-text-muted)' }}>
                <Users size={14} /> CONTEXTO POSICIONAL
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span style={{ color: 'var(--color-text-secondary)' }}>Profundidade atual</span>
                  <span className="font-[var(--font-mono)]">{result.positional_need.current_depth} / {result.positional_need.ideal_depth}</span>
                </div>
                <div className="flex justify-between">
                  <span style={{ color: 'var(--color-text-secondary)' }}>Idade média na posição</span>
                  <span className="font-[var(--font-mono)]">{result.positional_need.avg_age_at_position} anos</span>
                </div>
                <div className="flex justify-between">
                  <span style={{ color: 'var(--color-text-secondary)' }}>Nível de necessidade</span>
                  <span className="font-[var(--font-display)] font-semibold uppercase text-xs" style={{ color: getScoreColor(result.component_scores.positional_need ?? 0) }}>
                    {result.positional_need.need_level}
                  </span>
                </div>
                {result.squad_context.current_players_at_position.length > 0 && (
                  <div className="mt-2 pt-2" style={{ borderTop: '1px solid var(--color-border-subtle)' }}>
                    <div className="text-[9px] uppercase tracking-wider mb-1" style={{ color: 'var(--color-text-muted)' }}>Jogadores na posição</div>
                    {result.squad_context.current_players_at_position.map((p, i) => (
                      <div key={i} className="flex justify-between text-xs py-0.5">
                        <span>{p.name}</span>
                        <span className="font-[var(--font-mono)]" style={{ color: 'var(--color-text-muted)' }}>{p.age} anos</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>

            {/* Quality Uplift Detail */}
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }} className="card-glass rounded-lg p-4">
              <div className="text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-3 flex items-center gap-2" style={{ color: 'var(--color-text-muted)' }}>
                <TrendingUp size={14} /> GANHO DE QUALIDADE
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span style={{ color: 'var(--color-text-secondary)' }}>Percentil médio</span>
                  <span className="font-[var(--font-mono)]">{result.quality_uplift.avg_percentile?.toFixed(1)}%</span>
                </div>
                {result.quality_uplift.uplift_ratio != null && (
                  <div className="flex justify-between">
                    <span style={{ color: 'var(--color-text-secondary)' }}>Ratio vs elenco</span>
                    <span className="font-[var(--font-mono)]" style={{ color: result.quality_uplift.uplift_ratio > 1 ? '#22c55e' : '#ef4444' }}>
                      {result.quality_uplift.uplift_ratio.toFixed(2)}x
                    </span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span style={{ color: 'var(--color-text-secondary)' }}>Métricas comparadas</span>
                  <span className="font-[var(--font-mono)]">{result.quality_uplift.metrics_compared}</span>
                </div>
                {Object.keys(result.quality_uplift.top_metrics || {}).length > 0 && (
                  <div className="mt-2 pt-2" style={{ borderTop: '1px solid var(--color-border-subtle)' }}>
                    <div className="text-[9px] uppercase tracking-wider mb-1" style={{ color: 'var(--color-text-muted)' }}>Top métricas</div>
                    {Object.entries(result.quality_uplift.top_metrics).slice(0, 4).map(([metric, data]) => (
                      <div key={metric} className="flex justify-between text-xs py-0.5">
                        <span className="truncate mr-2" style={{ color: 'var(--color-text-secondary)' }}>{metric.replace('/90', '').replace(', %', '%')}</span>
                        <span className="font-[var(--font-mono)] whitespace-nowrap" style={{ color: (data as { ratio: number }).ratio > 1 ? '#22c55e' : '#ef4444' }}>
                          {(data as { ratio: number }).ratio.toFixed(2)}x
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>

            {/* Tactical Complementarity */}
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7 }} className="card-glass rounded-lg p-4">
              <div className="text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-3 flex items-center gap-2" style={{ color: 'var(--color-text-muted)' }}>
                <Crosshair size={14} /> COMPLEMENTARIDADE TÁTICA
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span style={{ color: 'var(--color-text-secondary)' }}>Tipo de perfil</span>
                  <span className="font-[var(--font-display)] font-semibold uppercase text-xs" style={{
                    color: result.tactical_complementarity.profile_type === 'complementar' ? '#22c55e' :
                           result.tactical_complementarity.profile_type === 'similar' ? '#eab308' : '#ef4444'
                  }}>
                    {result.tactical_complementarity.profile_type}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span style={{ color: 'var(--color-text-secondary)' }}>Setor</span>
                  <span className="font-[var(--font-mono)] capitalize">{result.tactical_complementarity.sector}</span>
                </div>
                <div className="flex justify-between">
                  <span style={{ color: 'var(--color-text-secondary)' }}>Jogadores no setor</span>
                  <span className="font-[var(--font-mono)]">{result.tactical_complementarity.sector_player_count}</span>
                </div>
                {result.tactical_complementarity.avg_similarity_to_sector != null && (
                  <div className="flex justify-between">
                    <span style={{ color: 'var(--color-text-secondary)' }}>Similaridade média</span>
                    <span className="font-[var(--font-mono)]">{(result.tactical_complementarity.avg_similarity_to_sector * 100).toFixed(1)}%</span>
                  </div>
                )}
              </div>
            </motion.div>

            {/* Age Profile */}
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.8 }} className="card-glass rounded-lg p-4">
              <div className="text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-3 flex items-center gap-2" style={{ color: 'var(--color-text-muted)' }}>
                <Clock size={14} /> PERFIL ETÁRIO DO ELENCO
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span style={{ color: 'var(--color-text-secondary)' }}>Categoria do candidato</span>
                  <span className="font-[var(--font-display)] font-semibold uppercase text-xs">
                    {result.age_profile_fit.candidate_category === 'young' ? 'Jovem' :
                     result.age_profile_fit.candidate_category === 'prime' ? 'Prime' : 'Experiente'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span style={{ color: 'var(--color-text-secondary)' }}>Idade média do elenco</span>
                  <span className="font-[var(--font-mono)]">{result.age_profile_fit.avg_squad_age} anos</span>
                </div>
                <div className="flex justify-between">
                  <span style={{ color: 'var(--color-text-secondary)' }}>Anos restantes de carreira</span>
                  <span className="font-[var(--font-mono)]">{result.age_profile_fit.remaining_career_years} anos</span>
                </div>
                <div className="mt-2 pt-2" style={{ borderTop: '1px solid var(--color-border-subtle)' }}>
                  <div className="text-[9px] uppercase tracking-wider mb-2" style={{ color: 'var(--color-text-muted)' }}>Distribuição etária</div>
                  <div className="flex gap-1">
                    {[
                      { label: 'Jovens', pct: result.age_profile_fit.squad_distribution.young_pct, color: '#22c55e' },
                      { label: 'Prime', pct: result.age_profile_fit.squad_distribution.prime_pct, color: '#3b82f6' },
                      { label: 'Exp.', pct: result.age_profile_fit.squad_distribution.experienced_pct, color: '#f97316' },
                    ].map((seg) => (
                      <div key={seg.label} className="flex-1 text-center">
                        <div className="h-2 rounded-full mb-1" style={{ background: seg.color, opacity: 0.7 }}>
                          <div className="h-full rounded-full" style={{ width: `${seg.pct}%`, background: seg.color }} />
                        </div>
                        <div className="text-[9px]" style={{ color: 'var(--color-text-muted)' }}>{seg.label} {seg.pct.toFixed(0)}%</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Financial Efficiency */}
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.9 }} className="card-glass rounded-lg p-4">
              <div className="text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-3 flex items-center gap-2" style={{ color: 'var(--color-text-muted)' }}>
                <DollarSign size={14} /> EFICIÊNCIA FINANCEIRA
              </div>
              <div className="space-y-2 text-sm">
                {result.financial_efficiency.estimated_value_eur_m != null && (
                  <div className="flex justify-between">
                    <span style={{ color: 'var(--color-text-secondary)' }}>Valor estimado</span>
                    <span className="font-[var(--font-mono)] font-semibold">{formatEUR(result.financial_efficiency.estimated_value_eur_m)}</span>
                  </div>
                )}
                {result.financial_efficiency.value_gap != null && (
                  <div className="flex justify-between">
                    <span style={{ color: 'var(--color-text-secondary)' }}>Gap de valor</span>
                    <span className="font-[var(--font-mono)]" style={{ color: result.financial_efficiency.is_undervalued ? '#22c55e' : '#ef4444' }}>
                      {result.financial_efficiency.value_gap > 0 ? '+' : ''}{formatEUR(Math.abs(result.financial_efficiency.value_gap))}
                    </span>
                  </div>
                )}
                {result.financial_efficiency.trajectory_score != null && (
                  <div className="flex justify-between">
                    <span style={{ color: 'var(--color-text-secondary)' }}>Score de trajetória</span>
                    <span className="font-[var(--font-mono)]" style={{ color: result.financial_efficiency.trajectory_score > 0 ? '#22c55e' : '#ef4444' }}>
                      {result.financial_efficiency.trajectory_score > 0 ? '+' : ''}{result.financial_efficiency.trajectory_score.toFixed(1)}
                    </span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span style={{ color: 'var(--color-text-secondary)' }}>Subvalorizado?</span>
                  <span style={{ color: result.financial_efficiency.is_undervalued ? '#22c55e' : 'var(--color-text-muted)' }}>
                    {result.financial_efficiency.is_undervalued ? 'Sim' : 'Não'}
                  </span>
                </div>
              </div>
            </motion.div>

            {/* Risk Assessment */}
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.0 }} className="card-glass rounded-lg p-4">
              <div className="text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-3 flex items-center gap-2" style={{ color: 'var(--color-text-muted)' }}>
                <Shield size={14} /> AVALIAÇÃO DE RISCO
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span style={{ color: 'var(--color-text-secondary)' }}>Nível de risco</span>
                  <span className="font-[var(--font-display)] font-semibold uppercase text-xs" style={{
                    color: result.risk_assessment.risk_level === 'baixo' ? '#22c55e' :
                           result.risk_assessment.risk_level === 'moderado' ? '#eab308' :
                           result.risk_assessment.risk_level === 'alto' ? '#f97316' : '#ef4444'
                  }}>
                    {result.risk_assessment.risk_level}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span style={{ color: 'var(--color-text-secondary)' }}>Gap de liga (Opta)</span>
                  <span className="font-[var(--font-mono)]">{result.risk_assessment.league_gap.toFixed(1)} pts</span>
                </div>
                {result.risk_assessment.risks.length > 0 && (
                  <div className="mt-2 pt-2 space-y-1" style={{ borderTop: '1px solid var(--color-border-subtle)' }}>
                    <div className="text-[9px] uppercase tracking-wider mb-1" style={{ color: 'var(--color-text-muted)' }}>Fatores de risco</div>
                    {result.risk_assessment.risks.map((risk, i) => (
                      <div key={i} className="flex items-center gap-1.5 text-xs" style={{ color: '#f97316' }}>
                        <AlertTriangle size={10} />
                        <span>{risk}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          </div>
        </>
      )}

      {!result && !analysis.isPending && (
        <div className="card-glass rounded-lg p-8 text-center" style={{ color: 'var(--color-text-muted)' }}>
          <UserPlus size={32} className="mx-auto mb-3 opacity-30" />
          <p className="text-sm">Selecione um jogador e clique em ANALISAR</p>
          <p className="text-xs mt-1 opacity-60">Impacto no elenco do Botafogo-SP com 6 dimensões de análise</p>
        </div>
      )}
    </div>
  );
}
