import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Database,
  ChevronDown,
  Target,
  Users,
  BarChart3,
  Crosshair,
  ArrowRight,
  Loader2,
  Info,
  Trophy,
  Shield,
  TrendingUp,
  TrendingDown,
  Activity,
  Zap,
  AlertTriangle,
} from 'lucide-react';
import {
  useStatsBombCompetitions,
  useStatsBombMatches,
  useStatsBombMatchSummary,
  useStatsBombLineups,
  useStatsBombShots,
  useStatsBombSeasonInsights,
} from '../hooks/useStatsBomb';
import type {
  StatsBombCompetition,
  StatsBombTeamStats,
  StatsBombShot,
  StatsBombSeasonInsights,
  StatsBombSeasonTeam,
  StatsBombTopScorer,
  StatsBombTopXg,
  StatsBombXgAnalysis,
  StatsBombTacticalEntry,
} from '../types/api';

// ── Stat comparison bar ──

function StatBar({ label, home, away, unit }: { label: string; home: number; away: number; unit?: string }) {
  const max = Math.max(home, away, 1);
  const homePct = (home / max) * 100;
  const awayPct = (away / max) * 100;

  return (
    <div className="py-2">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-sm font-mono font-bold" style={{ color: 'var(--color-text-primary)' }}>
          {typeof home === 'number' && home % 1 !== 0 ? home.toFixed(2) : home}{unit ?? ''}
        </span>
        <span
          className="text-[10px] uppercase tracking-widest font-semibold"
          style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-display)' }}
        >
          {label}
        </span>
        <span className="text-sm font-mono font-bold" style={{ color: 'var(--color-text-primary)' }}>
          {typeof away === 'number' && away % 1 !== 0 ? away.toFixed(2) : away}{unit ?? ''}
        </span>
      </div>
      <div className="flex gap-1 h-1.5">
        <div className="flex-1 rounded-full overflow-hidden" style={{ background: 'var(--color-surface-elevated)' }}>
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{ width: `${homePct}%`, background: 'var(--color-accent)', marginLeft: 'auto' }}
          />
        </div>
        <div className="flex-1 rounded-full overflow-hidden" style={{ background: 'var(--color-surface-elevated)' }}>
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{ width: `${awayPct}%`, background: '#3b82f6' }}
          />
        </div>
      </div>
    </div>
  );
}

// ── Shot map (simplified pitch view) ──

function ShotMap({ shots }: { shots: StatsBombShot[] }) {
  if (!shots.length) return null;

  // StatsBomb pitch is 120x80
  const W = 400;
  const H = 260;
  const scaleX = (x: number) => (x / 120) * W;
  const scaleY = (y: number) => (y / 80) * H;

  const teams = [...new Set(shots.map(s => s.team))];
  const teamColors: Record<string, string> = {};
  teams.forEach((t, i) => { teamColors[t] = i === 0 ? 'var(--color-accent)' : '#3b82f6'; });

  return (
    <div className="glass-panel p-5">
      <div className="flex items-center gap-2 mb-4">
        <Crosshair size={16} style={{ color: 'var(--color-accent)' }} />
        <h3
          className="text-xs uppercase tracking-widest font-semibold"
          style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-display)' }}
        >
          Mapa de Finalizacoes (xG)
        </h3>
      </div>
      {/* Legend */}
      <div className="flex gap-4 mb-3">
        {teams.map(t => (
          <div key={t} className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full" style={{ background: teamColors[t] }} />
            <span className="text-[11px]" style={{ color: 'var(--color-text-secondary)' }}>{t}</span>
          </div>
        ))}
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ maxHeight: 300 }}>
        {/* Pitch outline */}
        <rect x={0} y={0} width={W} height={H} rx={4} fill="none" stroke="var(--color-border-subtle)" strokeWidth={1} />
        {/* Center line */}
        <line x1={W / 2} y1={0} x2={W / 2} y2={H} stroke="var(--color-border-subtle)" strokeWidth={0.5} />
        {/* Center circle */}
        <circle cx={W / 2} cy={H / 2} r={30} fill="none" stroke="var(--color-border-subtle)" strokeWidth={0.5} />
        {/* Penalty areas */}
        <rect x={0} y={scaleY(18)} width={scaleX(18)} height={scaleY(44)} fill="none" stroke="var(--color-border-subtle)" strokeWidth={0.5} />
        <rect x={scaleX(102)} y={scaleY(18)} width={scaleX(18)} height={scaleY(44)} fill="none" stroke="var(--color-border-subtle)" strokeWidth={0.5} />
        {/* Goals */}
        <rect x={-2} y={scaleY(30)} width={3} height={scaleY(20)} fill="var(--color-text-muted)" rx={1} />
        <rect x={W - 1} y={scaleY(30)} width={3} height={scaleY(20)} fill="var(--color-text-muted)" rx={1} />

        {/* Shots */}
        {shots.map((s, i) => {
          if (s.location_x == null || s.location_y == null) return null;
          const r = Math.max(3, Math.min(12, s.xg * 25));
          const isGoal = s.outcome === 'Goal';
          const color = teamColors[s.team] ?? '#888';
          return (
            <circle
              key={i}
              cx={scaleX(s.location_x)}
              cy={scaleY(s.location_y)}
              r={r}
              fill={isGoal ? color : 'transparent'}
              stroke={color}
              strokeWidth={1.5}
              opacity={0.85}
            >
              <title>{`${s.player} ${s.minute}' — xG: ${s.xg} (${s.outcome})`}</title>
            </circle>
          );
        })}
      </svg>
      <div className="flex items-center gap-4 mt-3">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full border-2" style={{ borderColor: 'var(--color-text-muted)' }} />
          <span className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>Fora</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full" style={{ background: 'var(--color-text-muted)' }} />
          <span className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>Gol</span>
        </div>
        <span className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>
          Tamanho = xG
        </span>
      </div>
    </div>
  );
}

// ── Key Insights from match data ──

function MatchInsights({ home, away }: { home: StatsBombTeamStats; away: StatsBombTeamStats }) {
  const insights: { text: string; icon: React.ReactNode; type: 'positive' | 'neutral' | 'negative' }[] = [];

  // xG vs Goals analysis
  const homeXgDiff = home.goals - home.xg_total;
  const awayXgDiff = away.goals - away.xg_total;

  if (Math.abs(homeXgDiff) > 0.5) {
    insights.push({
      text: `${home.team} ${homeXgDiff > 0 ? 'superou' : 'ficou abaixo do'} xG em ${Math.abs(homeXgDiff).toFixed(2)} (${home.goals} gols vs ${home.xg_total} xG)`,
      icon: <Target size={14} />,
      type: homeXgDiff > 0 ? 'positive' : 'negative',
    });
  }
  if (Math.abs(awayXgDiff) > 0.5) {
    insights.push({
      text: `${away.team} ${awayXgDiff > 0 ? 'superou' : 'ficou abaixo do'} xG em ${Math.abs(awayXgDiff).toFixed(2)} (${away.goals} gols vs ${away.xg_total} xG)`,
      icon: <Target size={14} />,
      type: awayXgDiff > 0 ? 'positive' : 'negative',
    });
  }

  // Possession dominance (approximated via passes)
  const totalPasses = home.passes + away.passes;
  if (totalPasses > 0) {
    const homePossPct = (home.passes / totalPasses * 100).toFixed(0);
    const awayPossPct = (away.passes / totalPasses * 100).toFixed(0);
    const dominant = home.passes > away.passes ? home : away;
    if (Math.abs(home.passes - away.passes) > totalPasses * 0.1) {
      insights.push({
        text: `${dominant.team} dominou posse (aprox. ${home.passes > away.passes ? homePossPct : awayPossPct}% dos passes)`,
        icon: <BarChart3 size={14} />,
        type: 'neutral',
      });
    }
  }

  // Shot efficiency
  if (home.shots > 0 && away.shots > 0) {
    const homeEff = home.shots_on_target / home.shots;
    const awayEff = away.shots_on_target / away.shots;
    const moreEfficient = homeEff > awayEff ? home : away;
    const effPct = (Math.max(homeEff, awayEff) * 100).toFixed(0);
    if (Math.abs(homeEff - awayEff) > 0.15) {
      insights.push({
        text: `${moreEfficient.team} teve melhor precisao de finalizacao (${effPct}% no alvo)`,
        icon: <Crosshair size={14} />,
        type: 'neutral',
      });
    }
  }

  // Pressing / defensive intensity
  const homeDef = home.tackles + home.interceptions;
  const awayDef = away.tackles + away.interceptions;
  if (Math.abs(homeDef - awayDef) > 5) {
    const moreIntense = homeDef > awayDef ? home : away;
    insights.push({
      text: `${moreIntense.team} mais agressivo defensivamente (${homeDef > awayDef ? homeDef : awayDef} desarmes+interceptacoes)`,
      icon: <Shield size={14} />,
      type: 'neutral',
    });
  }

  // Dribble dominance
  if (home.dribbles_completed + away.dribbles_completed > 0) {
    const homeDribPct = home.dribbles > 0 ? home.dribbles_completed / home.dribbles : 0;
    const awayDribPct = away.dribbles > 0 ? away.dribbles_completed / away.dribbles : 0;
    if (Math.abs(homeDribPct - awayDribPct) > 0.2) {
      const better = homeDribPct > awayDribPct ? home : away;
      insights.push({
        text: `${better.team} mais eficiente nos dribles (${(Math.max(homeDribPct, awayDribPct) * 100).toFixed(0)}% de sucesso)`,
        icon: <ArrowRight size={14} />,
        type: 'neutral',
      });
    }
  }

  if (insights.length === 0) return null;

  return (
    <div className="glass-panel p-5">
      <div className="flex items-center gap-2 mb-4">
        <Info size={16} style={{ color: 'var(--color-accent)' }} />
        <h3
          className="text-xs uppercase tracking-widest font-semibold"
          style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-display)' }}
        >
          Insights da Partida
        </h3>
      </div>
      <div className="space-y-2">
        {insights.map((ins, i) => {
          const bgColor = ins.type === 'positive'
            ? 'rgba(34, 197, 94, 0.06)'
            : ins.type === 'negative'
            ? 'rgba(239, 68, 68, 0.06)'
            : 'rgba(59, 130, 246, 0.06)';
          const borderColor = ins.type === 'positive'
            ? 'rgba(34, 197, 94, 0.15)'
            : ins.type === 'negative'
            ? 'rgba(239, 68, 68, 0.15)'
            : 'rgba(59, 130, 246, 0.15)';
          const iconColor = ins.type === 'positive' ? '#22c55e' : ins.type === 'negative' ? '#ef4444' : '#3b82f6';

          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.08 }}
              className="flex items-start gap-3 px-4 py-3 rounded-xl"
              style={{ background: bgColor, border: `1px solid ${borderColor}` }}
            >
              <span className="mt-0.5 shrink-0" style={{ color: iconColor }}>{ins.icon}</span>
              <span className="text-sm leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
                {ins.text}
              </span>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

// ── Top shots table ──

function TopShots({ shots }: { shots: StatsBombShot[] }) {
  const sorted = useMemo(() => [...shots].sort((a, b) => b.xg - a.xg).slice(0, 10), [shots]);
  if (!sorted.length) return null;

  return (
    <div className="glass-panel p-5">
      <div className="flex items-center gap-2 mb-4">
        <Trophy size={16} style={{ color: 'var(--color-accent)' }} />
        <h3
          className="text-xs uppercase tracking-widest font-semibold"
          style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-display)' }}
        >
          Top Finalizacoes por xG
        </h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
              {['Min', 'Jogador', 'Time', 'xG', 'Resultado', 'Tecnica', 'Parte'].map(h => (
                <th
                  key={h}
                  className="text-left py-2 px-2 text-[10px] uppercase tracking-widest font-semibold"
                  style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-display)' }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((s, i) => (
              <tr
                key={i}
                className="transition-colors"
                style={{ borderBottom: '1px solid var(--color-border-subtle)' }}
              >
                <td className="py-2 px-2 font-mono text-xs" style={{ color: 'var(--color-text-secondary)' }}>{s.minute}'</td>
                <td className="py-2 px-2 text-xs font-medium" style={{ color: 'var(--color-text-primary)' }}>{s.player}</td>
                <td className="py-2 px-2 text-xs" style={{ color: 'var(--color-text-secondary)' }}>{s.team}</td>
                <td className="py-2 px-2 font-mono text-xs font-bold" style={{ color: s.xg > 0.3 ? '#22c55e' : 'var(--color-text-secondary)' }}>
                  {s.xg.toFixed(3)}
                </td>
                <td className="py-2 px-2 text-xs">
                  <span
                    className="px-2 py-0.5 rounded-full text-[10px] font-semibold"
                    style={{
                      background: s.outcome === 'Goal' ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.08)',
                      color: s.outcome === 'Goal' ? '#22c55e' : 'var(--color-text-muted)',
                    }}
                  >
                    {s.outcome}
                  </span>
                </td>
                <td className="py-2 px-2 text-[11px]" style={{ color: 'var(--color-text-muted)' }}>{s.technique ?? '-'}</td>
                <td className="py-2 px-2 text-[11px]" style={{ color: 'var(--color-text-muted)' }}>{s.body_part ?? '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}


// ── Season Overview Cards ──

function SeasonOverview({ data }: { data: StatsBombSeasonInsights }) {
  const cards = [
    { label: 'Jogos', value: data.matches_processed, icon: <Activity size={16} /> },
    { label: 'Gols', value: data.total_goals, icon: <Target size={16} /> },
    { label: 'Media Gols/Jogo', value: data.avg_goals_per_match, icon: <BarChart3 size={16} /> },
    { label: 'Media xG/Jogo', value: data.avg_xg_per_match, icon: <Crosshair size={16} /> },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {cards.map((c, i) => (
        <motion.div
          key={c.label}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.06 }}
          className="glass-panel p-4 text-center"
        >
          <div className="flex items-center justify-center gap-2 mb-2">
            <span style={{ color: 'var(--color-accent)' }}>{c.icon}</span>
            <span
              className="text-[10px] uppercase tracking-widest font-semibold"
              style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-display)' }}
            >
              {c.label}
            </span>
          </div>
          <div className="text-2xl font-bold font-mono" style={{ color: 'var(--color-text-primary)' }}>
            {c.value}
          </div>
        </motion.div>
      ))}
    </div>
  );
}

// ── xG Analysis Panel ──

function XgAnalysisPanel({ analysis }: { analysis: StatsBombXgAnalysis[] }) {
  if (!analysis.length) return null;

  return (
    <div className="glass-panel p-5">
      <div className="flex items-center gap-2 mb-4">
        <Target size={16} style={{ color: 'var(--color-accent)' }} />
        <h3
          className="text-xs uppercase tracking-widest font-semibold"
          style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-display)' }}
        >
          Analise xG — Eficiencia Ofensiva
        </h3>
      </div>
      <div className="space-y-2">
        {analysis.slice(0, 10).map((t, i) => {
          const isOver = t.diff > 0;
          return (
            <motion.div
              key={t.team}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.04 }}
              className="flex items-center gap-3 px-4 py-2.5 rounded-xl"
              style={{
                background: isOver ? 'rgba(34, 197, 94, 0.05)' : 'rgba(239, 68, 68, 0.05)',
                border: `1px solid ${isOver ? 'rgba(34, 197, 94, 0.12)' : 'rgba(239, 68, 68, 0.12)'}`,
              }}
            >
              <span className="w-5 text-center shrink-0" style={{ color: isOver ? '#22c55e' : '#ef4444' }}>
                {isOver ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
              </span>
              <span className="flex-1 text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>
                {t.team}
              </span>
              <div className="flex items-center gap-4 text-xs font-mono">
                <span style={{ color: 'var(--color-text-secondary)' }}>
                  {t.goals} gols
                </span>
                <span style={{ color: 'var(--color-text-muted)' }}>
                  {t.xg} xG
                </span>
                <span
                  className="font-bold px-2 py-0.5 rounded-full text-[11px]"
                  style={{
                    color: isOver ? '#22c55e' : '#ef4444',
                    background: isOver ? 'rgba(34, 197, 94, 0.12)' : 'rgba(239, 68, 68, 0.12)',
                  }}
                >
                  {isOver ? '+' : ''}{t.diff}
                </span>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

// ── Top Performers Panel ──

function TopPerformersPanel({ scorers, xgLeaders }: { scorers: StatsBombTopScorer[]; xgLeaders: StatsBombTopXg[] }) {
  const [tab, setTab] = useState<'goals' | 'xg'>('goals');

  return (
    <div className="glass-panel p-5">
      <div className="flex items-center gap-2 mb-4">
        <Trophy size={16} style={{ color: 'var(--color-accent)' }} />
        <h3
          className="text-xs uppercase tracking-widest font-semibold"
          style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-display)' }}
        >
          Top Performers
        </h3>
      </div>
      {/* Sub-tabs */}
      <div className="flex gap-1 mb-4 p-0.5 rounded-lg" style={{ background: 'var(--color-surface-elevated)' }}>
        {(['goals', 'xg'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className="flex-1 py-1.5 px-3 rounded-md text-xs font-semibold transition-all"
            style={{
              background: tab === t ? 'var(--color-accent)' : 'transparent',
              color: tab === t ? '#fff' : 'var(--color-text-muted)',
              fontFamily: 'var(--font-display)',
            }}
          >
            {t === 'goals' ? 'Artilheiros' : 'Lideres xG'}
          </button>
        ))}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
              {['#', 'Jogador', 'Time', tab === 'goals' ? 'Gols' : 'xG', tab === 'goals' ? 'xG' : 'Gols', 'Diff'].map(h => (
                <th
                  key={h}
                  className="text-left py-2 px-2 text-[10px] uppercase tracking-widest font-semibold"
                  style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-display)' }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {(tab === 'goals' ? scorers : xgLeaders).slice(0, 10).map((p, i) => {
              const diff = 'xg_diff' in p ? p.xg_diff : 0;
              return (
                <motion.tr
                  key={p.player}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.03 }}
                  style={{ borderBottom: '1px solid var(--color-border-subtle)' }}
                >
                  <td className="py-2 px-2 font-mono text-xs font-bold" style={{ color: 'var(--color-accent)' }}>{i + 1}</td>
                  <td className="py-2 px-2 text-xs font-medium" style={{ color: 'var(--color-text-primary)' }}>{p.player}</td>
                  <td className="py-2 px-2 text-xs" style={{ color: 'var(--color-text-secondary)' }}>{p.team}</td>
                  <td className="py-2 px-2 font-mono text-xs font-bold" style={{ color: 'var(--color-text-primary)' }}>
                    {tab === 'goals' ? ('goals' in p ? p.goals : 0) : p.xg}
                  </td>
                  <td className="py-2 px-2 font-mono text-xs" style={{ color: 'var(--color-text-muted)' }}>
                    {tab === 'goals' ? p.xg : ('goals' in p ? p.goals : 0)}
                  </td>
                  <td className="py-2 px-2">
                    <span
                      className="font-mono text-[11px] font-bold px-1.5 py-0.5 rounded"
                      style={{
                        color: diff > 0 ? '#22c55e' : diff < 0 ? '#ef4444' : 'var(--color-text-muted)',
                        background: diff > 0 ? 'rgba(34,197,94,0.1)' : diff < 0 ? 'rgba(239,68,68,0.1)' : 'transparent',
                      }}
                    >
                      {diff > 0 ? '+' : ''}{diff}
                    </span>
                  </td>
                </motion.tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Tactical Patterns Panel ──

function TacticalPatternsPanel({ tactical }: { tactical: StatsBombSeasonInsights['tactical'] }) {
  const sections = [
    { key: 'most_possession' as const, label: 'Mais Posse (Passes)', icon: <BarChart3 size={14} />, unit: '' },
    { key: 'most_pressing' as const, label: 'Maior Pressao Defensiva', icon: <Shield size={14} />, unit: '/jogo' },
    { key: 'best_passing' as const, label: 'Melhor Precisao de Passe', icon: <ArrowRight size={14} />, unit: '%' },
    { key: 'most_shots' as const, label: 'Mais Finalizacoes', icon: <Crosshair size={14} />, unit: '' },
  ];

  return (
    <div className="glass-panel p-5">
      <div className="flex items-center gap-2 mb-4">
        <Zap size={16} style={{ color: 'var(--color-accent)' }} />
        <h3
          className="text-xs uppercase tracking-widest font-semibold"
          style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-display)' }}
        >
          Padroes Taticos
        </h3>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sections.map(sec => {
          const items = tactical[sec.key];
          if (!items?.length) return null;
          const maxVal = Math.max(...items.map(it => it.value), 1);
          return (
            <div
              key={sec.key}
              className="rounded-xl p-4"
              style={{ background: 'var(--color-surface-elevated)', border: '1px solid var(--color-border-subtle)' }}
            >
              <div className="flex items-center gap-2 mb-3">
                <span style={{ color: 'var(--color-accent)' }}>{sec.icon}</span>
                <span
                  className="text-[10px] uppercase tracking-widest font-semibold"
                  style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-display)' }}
                >
                  {sec.label}
                </span>
              </div>
              <div className="space-y-2">
                {items.map((it, i) => (
                  <div key={it.team} className="space-y-1">
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-medium" style={{ color: 'var(--color-text-primary)' }}>{it.team}</span>
                      <span className="text-xs font-mono font-bold" style={{ color: 'var(--color-text-secondary)' }}>
                        {it.value}{sec.unit}
                      </span>
                    </div>
                    <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--color-surface)' }}>
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${(it.value / maxVal) * 100}%` }}
                        transition={{ duration: 0.6, delay: i * 0.08 }}
                        className="h-full rounded-full"
                        style={{ background: i === 0 ? 'var(--color-accent)' : 'rgba(var(--color-accent-rgb, 99,102,241), 0.5)' }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Team Standings Table ──

function TeamStandingsPanel({ teams }: { teams: StatsBombSeasonTeam[] }) {
  if (!teams.length) return null;

  return (
    <div className="glass-panel p-5">
      <div className="flex items-center gap-2 mb-4">
        <Users size={16} style={{ color: 'var(--color-accent)' }} />
        <h3
          className="text-xs uppercase tracking-widest font-semibold"
          style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-display)' }}
        >
          Classificacao por Desempenho
        </h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
              {['#', 'Time', 'J', 'V', 'E', 'D', 'Pts', 'Gols', 'GC', 'SG', 'xG', 'xGA', 'Prec%'].map(h => (
                <th
                  key={h}
                  className="text-left py-2 px-1.5 text-[10px] uppercase tracking-widest font-semibold whitespace-nowrap"
                  style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-display)' }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {teams.map((t, i) => (
              <motion.tr
                key={t.team}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.02 }}
                style={{ borderBottom: '1px solid var(--color-border-subtle)' }}
              >
                <td className="py-2 px-1.5 font-mono text-xs font-bold" style={{ color: 'var(--color-accent)' }}>{i + 1}</td>
                <td className="py-2 px-1.5 text-xs font-medium whitespace-nowrap" style={{ color: 'var(--color-text-primary)' }}>{t.team}</td>
                <td className="py-2 px-1.5 font-mono text-xs" style={{ color: 'var(--color-text-secondary)' }}>{t.matches}</td>
                <td className="py-2 px-1.5 font-mono text-xs" style={{ color: '#22c55e' }}>{t.wins}</td>
                <td className="py-2 px-1.5 font-mono text-xs" style={{ color: 'var(--color-text-muted)' }}>{t.draws}</td>
                <td className="py-2 px-1.5 font-mono text-xs" style={{ color: '#ef4444' }}>{t.losses}</td>
                <td className="py-2 px-1.5 font-mono text-xs font-bold" style={{ color: 'var(--color-text-primary)' }}>{t.points}</td>
                <td className="py-2 px-1.5 font-mono text-xs" style={{ color: 'var(--color-text-secondary)' }}>{t.goals}</td>
                <td className="py-2 px-1.5 font-mono text-xs" style={{ color: 'var(--color-text-muted)' }}>{t.goals_against}</td>
                <td className="py-2 px-1.5 font-mono text-xs font-bold" style={{ color: t.goal_diff > 0 ? '#22c55e' : t.goal_diff < 0 ? '#ef4444' : 'var(--color-text-muted)' }}>
                  {t.goal_diff > 0 ? '+' : ''}{t.goal_diff}
                </td>
                <td className="py-2 px-1.5 font-mono text-xs" style={{ color: 'var(--color-text-secondary)' }}>{t.xg_total}</td>
                <td className="py-2 px-1.5 font-mono text-xs" style={{ color: 'var(--color-text-muted)' }}>{t.xg_against}</td>
                <td className="py-2 px-1.5 font-mono text-xs" style={{ color: 'var(--color-text-secondary)' }}>{t.pass_accuracy}%</td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Season Insights Tab Content ──

function SeasonInsightsContent({ data }: { data: StatsBombSeasonInsights }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="space-y-6"
    >
      <SeasonOverview data={data} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <XgAnalysisPanel analysis={data.xg_analysis} />
        <TopPerformersPanel scorers={data.top_scorers} xgLeaders={data.top_xg} />
      </div>
      <TacticalPatternsPanel tactical={data.tactical} />
      <TeamStandingsPanel teams={data.teams} />
    </motion.div>
  );
}

// ── Main page ──

type PageTab = 'match' | 'insights';

export default function StatsBombPage() {
  const [selectedComp, setSelectedComp] = useState<StatsBombCompetition | null>(null);
  const [selectedSeasonId, setSelectedSeasonId] = useState<number | null>(null);
  const [selectedMatchId, setSelectedMatchId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<PageTab>('match');

  const { data: compsData, isLoading: loadingComps } = useStatsBombCompetitions();
  const { data: matchesData, isLoading: loadingMatches } = useStatsBombMatches(
    selectedComp?.competition_id ?? null,
    selectedSeasonId,
  );
  const { data: summary, isLoading: loadingSummary } = useStatsBombMatchSummary(selectedMatchId);
  const { data: shotsData, isLoading: loadingShots } = useStatsBombShots(selectedMatchId);
  const {
    data: seasonInsights,
    isLoading: loadingInsights,
    error: insightsError,
  } = useStatsBombSeasonInsights(
    activeTab === 'insights' ? (selectedComp?.competition_id ?? null) : null,
    activeTab === 'insights' ? selectedSeasonId : null,
  );

  const competitions = compsData?.competitions ?? [];
  const matches = matchesData?.matches ?? [];
  const shots = shotsData?.shots ?? [];

  // Get selected match info
  const selectedMatch = useMemo(
    () => matches.find(m => m.match_id === selectedMatchId),
    [matches, selectedMatchId],
  );

  const home = summary?.teams?.[0];
  const away = summary?.teams?.[1];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-1">
          <Database size={20} style={{ color: 'var(--color-accent)' }} />
          <h1
            className="text-xl font-bold tracking-tight"
            style={{ color: 'var(--color-text-primary)', fontFamily: 'var(--font-display)' }}
          >
            StatsBomb Open Data
          </h1>
        </div>
        <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
          Jogos historicos com eventos detalhados, xG, finalizacoes e insights taticos — dados abertos e gratuitos.
        </p>
      </div>

      {/* Selectors */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Competition selector */}
        <div className="glass-panel p-4">
          <label
            className="block text-[10px] uppercase tracking-widest font-semibold mb-2"
            style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-display)' }}
          >
            Competicao
          </label>
          {loadingComps ? (
            <div className="flex items-center gap-2 py-2">
              <Loader2 size={14} className="animate-spin" style={{ color: 'var(--color-accent)' }} />
              <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Carregando...</span>
            </div>
          ) : (
            <div className="relative">
              <select
                className="w-full appearance-none text-sm py-2.5 px-3 pr-8 rounded-xl cursor-pointer"
                style={{
                  background: 'var(--color-surface-elevated)',
                  color: 'var(--color-text-primary)',
                  border: '1px solid var(--color-border-subtle)',
                }}
                value={selectedComp?.competition_id ?? ''}
                onChange={e => {
                  const comp = competitions.find(c => c.competition_id === Number(e.target.value));
                  setSelectedComp(comp ?? null);
                  setSelectedSeasonId(null);
                  setSelectedMatchId(null);
                }}
              >
                <option value="">Selecione...</option>
                {competitions.map(c => (
                  <option key={c.competition_id} value={c.competition_id}>
                    {c.country_name} — {c.competition_name}
                  </option>
                ))}
              </select>
              <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: 'var(--color-text-muted)' }} />
            </div>
          )}
        </div>

        {/* Season selector */}
        <div className="glass-panel p-4">
          <label
            className="block text-[10px] uppercase tracking-widest font-semibold mb-2"
            style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-display)' }}
          >
            Temporada
          </label>
          <div className="relative">
            <select
              className="w-full appearance-none text-sm py-2.5 px-3 pr-8 rounded-xl cursor-pointer"
              style={{
                background: 'var(--color-surface-elevated)',
                color: 'var(--color-text-primary)',
                border: '1px solid var(--color-border-subtle)',
                opacity: selectedComp ? 1 : 0.5,
              }}
              disabled={!selectedComp}
              value={selectedSeasonId ?? ''}
              onChange={e => {
                setSelectedSeasonId(Number(e.target.value) || null);
                setSelectedMatchId(null);
              }}
            >
              <option value="">Selecione...</option>
              {(selectedComp?.seasons ?? []).map(s => (
                <option key={s.season_id} value={s.season_id}>
                  {s.season_name}
                </option>
              ))}
            </select>
            <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: 'var(--color-text-muted)' }} />
          </div>
        </div>

        {/* Match selector */}
        <div className="glass-panel p-4">
          <label
            className="block text-[10px] uppercase tracking-widest font-semibold mb-2"
            style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-display)' }}
          >
            Partida
          </label>
          {loadingMatches ? (
            <div className="flex items-center gap-2 py-2">
              <Loader2 size={14} className="animate-spin" style={{ color: 'var(--color-accent)' }} />
              <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>Carregando jogos...</span>
            </div>
          ) : (
            <div className="relative">
              <select
                className="w-full appearance-none text-sm py-2.5 px-3 pr-8 rounded-xl cursor-pointer"
                style={{
                  background: 'var(--color-surface-elevated)',
                  color: 'var(--color-text-primary)',
                  border: '1px solid var(--color-border-subtle)',
                  opacity: matches.length ? 1 : 0.5,
                }}
                disabled={!matches.length}
                value={selectedMatchId ?? ''}
                onChange={e => setSelectedMatchId(Number(e.target.value) || null)}
              >
                <option value="">Selecione...</option>
                {matches.map(m => (
                  <option key={m.match_id} value={m.match_id}>
                    {m.match_date} — {m.home_team} {m.home_score ?? '?'} x {m.away_score ?? '?'} {m.away_team}
                  </option>
                ))}
              </select>
              <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: 'var(--color-text-muted)' }} />
            </div>
          )}
        </div>
      </div>

      {/* Tabs — only show when season is selected */}
      {selectedComp && selectedSeasonId && (
        <div className="flex gap-1 p-0.5 rounded-xl" style={{ background: 'var(--color-surface-elevated)' }}>
          {([
            { key: 'match' as PageTab, label: 'Partida', icon: <Target size={14} /> },
            { key: 'insights' as PageTab, label: 'Insights da Temporada', icon: <TrendingUp size={14} /> },
          ]).map(t => (
            <button
              key={t.key}
              onClick={() => setActiveTab(t.key)}
              className="flex items-center gap-2 flex-1 py-2.5 px-4 rounded-lg text-xs font-semibold transition-all"
              style={{
                background: activeTab === t.key ? 'var(--color-accent)' : 'transparent',
                color: activeTab === t.key ? '#fff' : 'var(--color-text-muted)',
                fontFamily: 'var(--font-display)',
              }}
            >
              {t.icon}
              {t.label}
            </button>
          ))}
        </div>
      )}

      {/* Tab content */}
      <AnimatePresence mode="wait">
        {activeTab === 'match' ? (
          <>
            {loadingSummary || loadingShots ? (
              <motion.div
                key="loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex items-center justify-center py-20 gap-3"
              >
                <Loader2 size={20} className="animate-spin" style={{ color: 'var(--color-accent)' }} />
                <span className="text-sm" style={{ color: 'var(--color-text-muted)' }}>Carregando dados da partida...</span>
              </motion.div>
            ) : selectedMatchId && home && away ? (
              <motion.div
                key="data"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="space-y-6"
              >
                {/* Score header */}
                <div className="glass-panel p-6 text-center">
                  <div className="flex items-center justify-center gap-6">
                    <div className="text-right flex-1">
                      <div className="text-lg font-bold" style={{ color: 'var(--color-text-primary)', fontFamily: 'var(--font-display)' }}>
                        {home.team}
                      </div>
                      <div className="text-[10px] uppercase tracking-widest mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
                        xG {home.xg_total}
                      </div>
                    </div>
                    <div
                      className="text-3xl font-bold font-mono px-6 py-2 rounded-2xl"
                      style={{
                        color: 'var(--color-text-primary)',
                        background: 'var(--color-surface-elevated)',
                      }}
                    >
                      {home.goals} — {away.goals}
                    </div>
                    <div className="text-left flex-1">
                      <div className="text-lg font-bold" style={{ color: 'var(--color-text-primary)', fontFamily: 'var(--font-display)' }}>
                        {away.team}
                      </div>
                      <div className="text-[10px] uppercase tracking-widest mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
                        xG {away.xg_total}
                      </div>
                    </div>
                  </div>
                  {selectedMatch && (
                    <div className="text-xs mt-3" style={{ color: 'var(--color-text-muted)' }}>
                      {selectedMatch.match_date}
                      {selectedMatch.stadium ? ` — ${selectedMatch.stadium}` : ''}
                      {selectedMatch.competition_stage ? ` — ${selectedMatch.competition_stage}` : ''}
                    </div>
                  )}
                </div>

                {/* Insights */}
                <MatchInsights home={home} away={away} />

                {/* Stats comparison */}
                <div className="glass-panel p-5">
                  <div className="flex items-center gap-2 mb-4">
                    <BarChart3 size={16} style={{ color: 'var(--color-accent)' }} />
                    <h3
                      className="text-xs uppercase tracking-widest font-semibold"
                      style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-display)' }}
                    >
                      Comparativo
                    </h3>
                  </div>
                  <div className="space-y-1">
                    <StatBar label="xG" home={home.xg_total} away={away.xg_total} />
                    <StatBar label="Finalizacoes" home={home.shots} away={away.shots} />
                    <StatBar label="No Alvo" home={home.shots_on_target} away={away.shots_on_target} />
                    <StatBar label="Passes" home={home.passes} away={away.passes} />
                    <StatBar label="Precisao Passes" home={home.pass_accuracy} away={away.pass_accuracy} unit="%" />
                    <StatBar label="Desarmes" home={home.tackles} away={away.tackles} />
                    <StatBar label="Interceptacoes" home={home.interceptions} away={away.interceptions} />
                    <StatBar label="Escanteios" home={home.corners} away={away.corners} />
                    <StatBar label="Dribles" home={home.dribbles_completed} away={away.dribbles_completed} />
                    <StatBar label="Faltas" home={home.fouls} away={away.fouls} />
                    <StatBar label="Amarelos" home={home.yellow_cards} away={away.yellow_cards} />
                  </div>
                </div>

                {/* Shot map + Top shots */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <ShotMap shots={shots} />
                  <TopShots shots={shots} />
                </div>
              </motion.div>
            ) : !selectedMatchId ? (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="glass-panel p-12 text-center"
              >
                <Database size={40} className="mx-auto mb-4" style={{ color: 'var(--color-text-muted)', opacity: 0.3 }} />
                <div className="text-sm font-medium" style={{ color: 'var(--color-text-muted)' }}>
                  Selecione uma competicao, temporada e partida para explorar os dados historicos.
                </div>
                <div className="text-xs mt-2" style={{ color: 'var(--color-text-muted)', opacity: 0.6 }}>
                  Dados abertos da StatsBomb — La Liga, Premier League, Champions League, Copa do Mundo e mais.
                </div>
              </motion.div>
            ) : null}
          </>
        ) : activeTab === 'insights' ? (
          <>
            {!selectedComp || !selectedSeasonId ? (
              <motion.div
                key="no-season"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="glass-panel p-12 text-center"
              >
                <TrendingUp size={40} className="mx-auto mb-4" style={{ color: 'var(--color-text-muted)', opacity: 0.3 }} />
                <div className="text-sm font-medium" style={{ color: 'var(--color-text-muted)' }}>
                  Selecione uma competicao e temporada para ver os insights agregados.
                </div>
              </motion.div>
            ) : loadingInsights ? (
              <motion.div
                key="loading-insights"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col items-center justify-center py-20 gap-3"
              >
                <Loader2 size={24} className="animate-spin" style={{ color: 'var(--color-accent)' }} />
                <span className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
                  Processando dados da temporada...
                </span>
                <span className="text-xs" style={{ color: 'var(--color-text-muted)', opacity: 0.6 }}>
                  Isso pode levar alguns segundos na primeira vez.
                </span>
              </motion.div>
            ) : insightsError ? (
              <motion.div
                key="error-insights"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="glass-panel p-8 text-center"
              >
                <AlertTriangle size={32} className="mx-auto mb-3" style={{ color: '#ef4444' }} />
                <div className="text-sm font-medium mb-1" style={{ color: 'var(--color-text-primary)' }}>
                  Erro ao carregar insights
                </div>
                <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                  Nao foi possivel processar os dados desta temporada. Tente novamente.
                </div>
              </motion.div>
            ) : seasonInsights ? (
              <SeasonInsightsContent key="insights-content" data={seasonInsights} />
            ) : null}
          </>
        ) : null}
      </AnimatePresence>
    </div>
  );
}
