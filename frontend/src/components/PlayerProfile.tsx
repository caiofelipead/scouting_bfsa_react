import { motion, AnimatePresence } from 'framer-motion';
import {
  User,
  MapPin,
  Clock,
  Trophy,
  ChevronRight,
  BarChart3,
  Target,
  Shield,
  TrendingUp,
} from 'lucide-react';
import RadarChart from './RadarChart';
import SkeletonProfile from './SkeletonProfile';
import { usePlayerProfile, useRadarData } from '../hooks/usePlayers';
import { cn, getScoreClass, getScoreColor, getPerformanceLabel, formatNumber } from '../lib/utils';

interface PlayerProfileProps {
  playerDisplayName: string | null;
  onClose?: () => void;
}

const stagger = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.06, delayChildren: 0.1 },
  },
};

const fadeUp = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.22, 1, 0.36, 1] } },
};

function getPdiColor(pdi: number): string {
  if (pdi >= 75) return '#22c55e';
  if (pdi >= 60) return '#3b82f6';
  if (pdi >= 40) return '#eab308';
  return '#ef4444';
}

function getPdiLabel(pdi: number): string {
  if (pdi >= 75) return 'ALTO POTENCIAL';
  if (pdi >= 60) return 'PROMISSOR';
  if (pdi >= 40) return 'MODERADO';
  return 'BAIXO';
}

export default function PlayerProfile({ playerDisplayName, onClose }: PlayerProfileProps) {
  const { data: profile, isLoading: profileLoading } = usePlayerProfile(playerDisplayName);
  const { data: radarData, isLoading: radarLoading } = useRadarData(playerDisplayName);

  if (!playerDisplayName) return null;

  if (profileLoading || radarLoading) {
    return <SkeletonProfile />;
  }

  if (!profile) {
    return (
      <div className="card-glass rounded-lg p-8 text-center" style={{ color: 'var(--color-text-muted)' }}>
        Jogador nao encontrado
      </div>
    );
  }

  const { summary, percentiles, indices, scout_score, performance_class, skillcorner, projection_score } = profile;

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={playerDisplayName}
        variants={stagger}
        initial="hidden"
        animate="visible"
        exit={{ opacity: 0, scale: 0.95 }}
        className="space-y-4"
      >
        {/* ── Header card ─────────────────────────────────────────── */}
        <motion.div variants={fadeUp} className="card-glass-accent rounded-lg overflow-hidden">
          <div className="p-5">
            {/* Top bar: position tag + close */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span
                  className="px-2 py-0.5 rounded text-[10px] font-[var(--font-display)] tracking-[0.15em] uppercase"
                  style={{
                    background: 'var(--color-accent-glow)',
                    color: 'var(--color-accent)',
                    border: '1px solid rgba(220, 38, 38, 0.3)',
                  }}
                >
                  {summary.position || '—'}
                </span>
                {summary.league && (
                  <span
                    className="px-2 py-0.5 rounded text-[10px] tracking-wide"
                    style={{
                      background: 'rgba(255,255,255,0.04)',
                      color: 'var(--color-text-muted)',
                      border: '1px solid var(--color-border-subtle)',
                    }}
                  >
                    {summary.league}
                  </span>
                )}
              </div>
              {onClose && (
                <button
                  onClick={onClose}
                  className="text-sm px-2 py-1 rounded hover:bg-white/5 transition-colors"
                  style={{ color: 'var(--color-text-muted)' }}
                >
                  Fechar
                </button>
              )}
            </div>

            {/* Player name & team */}
            <h2 className="font-[var(--font-display)] text-2xl font-bold tracking-tight leading-tight mb-1">
              {summary.name}
            </h2>
            {summary.team && (
              <p className="flex items-center gap-1.5 text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                <Shield size={13} />
                {summary.team}
              </p>
            )}

            {/* Meta row */}
            <div className="flex flex-wrap items-center gap-4 mt-4">
              {summary.age && (
                <span className="flex items-center gap-1 text-xs" style={{ color: 'var(--color-text-muted)' }}>
                  <User size={12} />
                  {summary.age} anos
                </span>
              )}
              {summary.nationality && (
                <span className="flex items-center gap-1 text-xs" style={{ color: 'var(--color-text-muted)' }}>
                  <MapPin size={12} />
                  {summary.nationality}
                </span>
              )}
              {summary.minutes_played && (
                <span className="flex items-center gap-1 text-xs" style={{ color: 'var(--color-text-muted)' }}>
                  <Clock size={12} />
                  {formatNumber(summary.minutes_played)} min
                </span>
              )}
            </div>
          </div>

          {/* Scout Score bar */}
          {scout_score !== null && (
            <div
              className="px-5 py-3 flex items-center justify-between"
              style={{ borderTop: '1px solid var(--color-border-subtle)' }}
            >
              <div className="flex items-center gap-2">
                <Target size={14} style={{ color: 'var(--color-accent)' }} />
                <span
                  className="text-xs font-[var(--font-display)] tracking-[0.15em] uppercase"
                  style={{ color: 'var(--color-text-muted)' }}
                >
                  SCOUT SCORE
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className={cn('px-2.5 py-0.5 rounded text-xs font-[var(--font-mono)] font-bold', getScoreClass(scout_score))}>
                  {scout_score.toFixed(1)}
                </span>
                {performance_class && (
                  <span
                    className="text-[10px] font-[var(--font-display)] tracking-[0.1em]"
                    style={{ color: 'var(--color-text-muted)' }}
                  >
                    {getPerformanceLabel(performance_class)}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Projection Score (PDI) bar */}
          {projection_score !== null && projection_score !== undefined && (
            <div
              className="px-5 py-3 flex items-center justify-between"
              style={{ borderTop: '1px solid var(--color-border-subtle)' }}
            >
              <div className="flex items-center gap-2">
                <TrendingUp size={14} style={{ color: getPdiColor(projection_score) }} />
                <span
                  className="text-xs font-[var(--font-display)] tracking-[0.15em] uppercase"
                  style={{ color: 'var(--color-text-muted)' }}
                >
                  NOTA DE PROJECAO (PDI)
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span
                  className="px-2.5 py-0.5 rounded text-xs font-[var(--font-mono)] font-bold"
                  style={{ color: getPdiColor(projection_score), background: `${getPdiColor(projection_score)}15` }}
                >
                  {projection_score.toFixed(1)}
                </span>
                <span
                  className="text-[10px] font-[var(--font-display)] tracking-[0.1em]"
                  style={{ color: getPdiColor(projection_score) }}
                >
                  {getPdiLabel(projection_score)}
                </span>
              </div>
            </div>
          )}
        </motion.div>

        {/* ── Asymmetric grid: Radar + Indices ────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_0.65fr] gap-4">
          {/* Radar — uses real percentiles from calibration */}
          <motion.div variants={fadeUp} className="card-glass rounded-lg p-5">
            <div className="flex items-center gap-2 mb-4">
              <BarChart3 size={14} style={{ color: 'var(--color-accent)' }} />
              <span
                className="text-[10px] font-[var(--font-display)] tracking-[0.2em] uppercase"
                style={{ color: 'var(--color-text-muted)' }}
              >
                PERCENTIS POR POSICAO
              </span>
            </div>
            {radarData && radarData.labels.length > 0 ? (
              <RadarChart
                labels={radarData.labels}
                values={radarData.values}
                size={360}
                playerName={summary.name}
              />
            ) : (
              <div className="skeleton-radar max-w-[280px] mx-auto" />
            )}

            {/* Percentile detail grid */}
            {percentiles && Object.keys(percentiles).length > 0 && (
              <div className="mt-4 grid grid-cols-2 gap-x-4 gap-y-1">
                {Object.entries(percentiles).map(([metric, value]) => (
                  <div key={metric} className="flex items-center justify-between">
                    <span className="text-[10px] truncate pr-1" style={{ color: 'var(--color-text-muted)' }}>
                      {metric}
                    </span>
                    <span className="text-[10px] font-[var(--font-mono)] font-semibold" style={{ color: getScoreColor(value) }}>
                      P{value.toFixed(0)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </motion.div>

          {/* Composite Indices */}
          <motion.div variants={fadeUp} className="card-glass rounded-lg p-5 flex flex-col">
            <div className="flex items-center gap-2 mb-4">
              <Trophy size={14} style={{ color: 'var(--color-accent)' }} />
              <span
                className="text-[10px] font-[var(--font-display)] tracking-[0.2em] uppercase"
                style={{ color: 'var(--color-text-muted)' }}
              >
                INDICES COMPOSTOS
              </span>
            </div>
            <div className="flex-1 space-y-2.5">
              {Object.entries(indices).map(([name, value], i) => (
                <motion.div
                  key={name}
                  initial={{ opacity: 0, x: 8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.15 + i * 0.06 }}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                      {name}
                    </span>
                    <span
                      className="text-xs font-[var(--font-mono)] font-semibold"
                      style={{ color: getScoreColor(value) }}
                    >
                      {value.toFixed(1)}
                    </span>
                  </div>
                  <div
                    className="h-1.5 rounded-full overflow-hidden"
                    style={{ background: 'var(--color-surface-2)' }}
                  >
                    <motion.div
                      className="h-full rounded-full"
                      style={{ background: getScoreColor(value) }}
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.min(value, 100)}%` }}
                      transition={{ duration: 0.6, delay: 0.3 + i * 0.06, ease: [0.22, 1, 0.36, 1] }}
                    />
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* ── SkillCorner data ─────────────────────────────────────── */}
        {skillcorner && Object.keys(skillcorner).length > 0 && (
          <motion.div variants={fadeUp} className="card-glass rounded-lg p-5">
            <div className="flex items-center gap-2 mb-4">
              <ChevronRight size={14} style={{ color: 'var(--color-accent)' }} />
              <span
                className="text-[10px] font-[var(--font-display)] tracking-[0.2em] uppercase"
                style={{ color: 'var(--color-text-muted)' }}
              >
                SKILLCORNER INDICES
              </span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {Object.entries(skillcorner).map(([name, value], i) => (
                <motion.div
                  key={name}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 + i * 0.05 }}
                  className="p-3 rounded"
                  style={{
                    background: 'var(--color-surface-2)',
                    border: '1px solid var(--color-border-subtle)',
                  }}
                >
                  <div
                    className="text-[10px] mb-1 leading-tight"
                    style={{ color: 'var(--color-text-muted)' }}
                  >
                    {name.replace(/ index$/i, '')}
                  </div>
                  <div
                    className="text-lg font-[var(--font-mono)] font-bold"
                    style={{ color: 'var(--color-text-primary)' }}
                  >
                    {typeof value === 'number' ? value.toFixed(2) : value}
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </motion.div>
    </AnimatePresence>
  );
}
