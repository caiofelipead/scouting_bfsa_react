import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { getFlagUrl } from '../lib/countryFlags';
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
  Search,
  X,
  FileText,
  ExternalLink,
  Video,
  DollarSign,
  Activity,
} from 'lucide-react';
import RadarChart from './RadarChart';
import PositionPitch from './PositionPitch';
import SkeletonProfile from './SkeletonProfile';
import { usePlayerProfile, useRadarData, useSkillCornerSearch } from '../hooks/usePlayers';
import { cn, getScoreClass, getScoreColor, getPerformanceLabel, formatNumber } from '../lib/utils';
import { proxyImageUrl, isProxyFallback } from '../lib/api';

function PlayerPhoto({ url, alt, size = 'sm' }: { url: string | null; alt: string; size?: 'sm' | 'lg' }) {
  const [failed, setFailed] = useState(false);
  const [prevUrl, setPrevUrl] = useState(url);
  if (url !== prevUrl) { setPrevUrl(url); setFailed(false); }
  if (!url || failed) {
    return (
      <div className={size === 'lg' ? 'player-photo-placeholder-lg' : 'player-photo-placeholder'}>
        <User size={size === 'lg' ? 24 : 16} strokeWidth={1.5} />
      </div>
    );
  }
  return (
    <img
      src={proxyImageUrl(url)!}
      alt={alt}
      className={size === 'lg' ? 'player-photo-hex-lg' : 'player-photo-hex'}
      loading="lazy"
      decoding="async"
      referrerPolicy="no-referrer"
      onLoad={(e) => { if (isProxyFallback(e.currentTarget)) setFailed(true); }}
      onError={() => setFailed(true)}
    />
  );
}

function ClubLogo({ url, alt, className = 'w-5 h-5 object-contain', fallback }: { url: string | null; alt: string; className?: string; fallback?: React.ReactNode }) {
  const [failed, setFailed] = useState(false);
  const [prevUrl, setPrevUrl] = useState(url);
  if (url !== prevUrl) { setPrevUrl(url); setFailed(false); }
  if (!url || failed) return <>{fallback ?? null}</>;
  return (
    <img
      src={proxyImageUrl(url)!}
      alt={alt}
      className={className}
      loading="lazy"
      decoding="async"
      referrerPolicy="no-referrer"
      onLoad={(e) => { if (isProxyFallback(e.currentTarget)) setFailed(true); }}
      onError={() => setFailed(true)}
    />
  );
}

interface PlayerProfileProps {
  playerDisplayName: string | null;
  onClose?: () => void;
}

const stagger = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.03, delayChildren: 0.05 },
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

function getAnalysisScoreColor(score: number): string {
  if (score >= 4) return '#22c55e';
  if (score >= 3) return '#3b82f6';
  if (score >= 2) return '#eab308';
  return '#ef4444';
}

const SCORE_LABELS: Record<string, string> = {
  'Técnica': 'Técnica',
  'Físico': 'Físico',
  'Tática': 'Tática',
  'Mental': 'Mental',
  'Nota_Desempenho': 'Nota Desempenho',
  'Potencial': 'Potencial',
};

const LINK_ICONS: Record<string, { label: string; icon: string }> = {
  'ogol': { label: 'ogol', icon: 'link' },
  'TM': { label: 'Transfermarkt', icon: 'link' },
  'Vídeo': { label: 'Vídeo', icon: 'video' },
  'Relatório': { label: 'Relatório', icon: 'file' },
};

function getRecommendationBadge(score: number | null): { label: string; cls: string } | null {
  if (score == null) return null;
  if (score >= 72) return { label: 'Top Target', cls: 'badge-top-target' };
  if (score >= 62) return { label: 'Alta Prioridade', cls: 'badge-high-priority' };
  if (score >= 50) return { label: 'Monitorar', cls: 'badge-monitor' };
  if (score >= 38) return { label: 'Avaliar', cls: 'badge-evaluate' };
  return { label: 'Descartar', cls: 'badge-discard' };
}

export default function PlayerProfile({ playerDisplayName, onClose }: PlayerProfileProps) {
  const [scOverride, setScOverride] = useState<string | null>(null);
  const [scSearchOpen, setScSearchOpen] = useState(false);
  const [scSearchQuery, setScSearchQuery] = useState('');
  const { data: profile, isLoading: profileLoading } = usePlayerProfile(playerDisplayName, scOverride);
  const { data: radarData, isLoading: radarLoading } = useRadarData(playerDisplayName);
  const { data: scResults } = useSkillCornerSearch(scSearchOpen ? scSearchQuery : '');

  // Reset override when player changes
  useEffect(() => {
    setScOverride(null);
    setScSearchOpen(false);
    setScSearchQuery('');
  }, [playerDisplayName]);

  if (!playerDisplayName) return null;

  if (profileLoading || radarLoading) {
    return <SkeletonProfile />;
  }

  if (!profile) {
    return (
      <div className="card-glass p-8 text-center" style={{ color: 'var(--color-text-muted)' }}>
        Jogador nao encontrado
      </div>
    );
  }

  const { summary, percentiles, indices, scout_score, performance_class, skillcorner, skillcorner_physical, projection_score, ssp_lambdas, prediction, analises } = profile;
  const badge = getRecommendationBadge(scout_score);

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
        <motion.div variants={fadeUp} className="card-glass-accent overflow-hidden">
          <div className="p-6">
            {/* Top bar: position tag + badge + close */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span
                  className="px-2.5 py-1 rounded-full text-[11px] font-[var(--font-display)] tracking-[0.14em] font-semibold uppercase"
                  style={{
                    background: 'var(--color-accent-glow)',
                    color: 'var(--color-accent)',
                    border: '1px solid rgba(227, 6, 19, 0.3)',
                  }}
                >
                  {summary.position || '—'}
                </span>
                {summary.league && (
                  <span
                    className="px-2 py-1 rounded-full text-[10px] tracking-wide"
                    style={{
                      background: 'rgba(255,255,255,0.04)',
                      color: 'var(--color-text-muted)',
                      border: '1px solid var(--color-border-subtle)',
                    }}
                  >
                    {summary.league}
                  </span>
                )}
                {badge && (
                  <span className={cn('px-2 py-1 rounded-full text-[9px] font-[var(--font-display)] tracking-wider uppercase font-semibold', badge.cls)}>
                    {badge.label}
                  </span>
                )}
              </div>
              {onClose && (
                <button
                  onClick={onClose}
                  className="text-sm px-2 py-1 rounded-lg hover:bg-white/5 transition-colors cursor-pointer"
                  style={{ color: 'var(--color-text-muted)' }}
                >
                  Fechar
                </button>
              )}
            </div>

            {/* Player name, photo & team */}
            <div className="flex items-start gap-4">
              <PlayerPhoto url={summary.photo_url} alt={summary.name} size="lg" />
              <div className="flex-1 min-w-0">
                <h2 className="font-[var(--font-display)] text-2xl font-bold tracking-tight leading-tight mb-1">
                  {summary.name}
                </h2>
                {summary.team && (
                  <p className="flex items-center gap-1.5 text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                    <ClubLogo url={summary.club_logo} alt={summary.team} fallback={<Shield size={13} strokeWidth={1.5} />} />
                    {summary.team}
                  </p>
                )}

                {/* Meta row */}
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 mt-3">
                  {summary.age && (
                    <span className="flex items-center gap-1.5 text-[12px]" style={{ color: 'var(--color-text-secondary)' }}>
                      <User size={13} strokeWidth={1.75} style={{ color: 'var(--color-text-muted)' }} />
                      <span className="stat-num font-semibold">{summary.age}</span> anos
                    </span>
                  )}
                  {summary.nationality && (
                    <span className="flex items-center gap-1.5 text-[12px]" style={{ color: 'var(--color-text-secondary)' }}>
                      {getFlagUrl(summary.nationality) ? (
                        <img
                          src={getFlagUrl(summary.nationality, 20)!}
                          alt={summary.nationality}
                          style={{ width: 18, height: 13, objectFit: 'cover', borderRadius: 2 }}
                        />
                      ) : (
                        <MapPin size={13} strokeWidth={1.75} style={{ color: 'var(--color-text-muted)' }} />
                      )}
                      {summary.nationality}
                    </span>
                  )}
                  {summary.minutes_played && (
                    <span className="flex items-center gap-1.5 text-[12px]" style={{ color: 'var(--color-text-secondary)' }}>
                      <Clock size={13} strokeWidth={1.75} style={{ color: 'var(--color-text-muted)' }} />
                      <span className="stat-num font-semibold">{formatNumber(summary.minutes_played)}</span> min
                    </span>
                  )}
                </div>
              </div>
              <div className="shrink-0 self-start hidden sm:block">
                <PositionPitch position={summary.position} />
              </div>
            </div>
          </div>

          {/* Scout Score bar */}
          {scout_score !== null && (
            <div
              className="px-6 py-3.5 flex items-center justify-between"
              style={{ borderTop: '1px solid var(--color-border-active)' }}
            >
              <div className="flex items-center gap-2">
                <Target size={15} strokeWidth={1.75} style={{ color: 'var(--color-accent)' }} />
                <span className="eyebrow-strong" style={{ color: 'var(--color-text-secondary)' }}>
                  SSP — Scout Score Preditivo
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className={cn('px-3 py-1 rounded-md text-[14px] stat-num font-bold', getScoreClass(scout_score))}>
                  {scout_score.toFixed(1)}
                </span>
                {performance_class && (
                  <span
                    className="text-[11px] font-[var(--font-display)] tracking-[0.1em] font-semibold uppercase"
                    style={{ color: 'var(--color-text-secondary)' }}
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
              className="px-6 py-3.5 flex items-center justify-between"
              style={{ borderTop: '1px solid var(--color-border-subtle)' }}
            >
              <div className="flex items-center gap-2">
                <TrendingUp size={15} strokeWidth={1.75} style={{ color: getPdiColor(projection_score) }} />
                <span className="eyebrow-strong" style={{ color: 'var(--color-text-secondary)' }}>
                  Nota de Projeção (PDI)
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span
                  className="px-3 py-1 rounded-md text-[14px] stat-num font-bold"
                  style={{
                    color: getPdiColor(projection_score),
                    background: `${getPdiColor(projection_score)}1F`,
                    border: `1px solid ${getPdiColor(projection_score)}40`,
                  }}
                >
                  {projection_score.toFixed(1)}
                </span>
                <span
                  className="text-[11px] font-[var(--font-display)] tracking-[0.1em] font-semibold uppercase"
                  style={{ color: getPdiColor(projection_score) }}
                >
                  {getPdiLabel(projection_score)}
                </span>
              </div>
            </div>
          )}
        </motion.div>

        {/* ── Análises card ─────────────────────────────────────── */}
        {analises && (
          <motion.div variants={fadeUp} className="card-glass overflow-hidden">
            <div className="p-6">
              <div className="flex items-center gap-2 mb-4">
                <FileText size={15} strokeWidth={1.75} style={{ color: 'var(--color-accent)' }} />
                <span className="eyebrow-strong">
                  Análise do Scout
                </span>
                {analises.modelo && (
                  <span
                    className="ml-auto px-2 py-0.5 rounded-full text-[9px] font-[var(--font-display)] tracking-wider uppercase font-semibold"
                    style={{
                      background: analises.modelo === 'Descartado' ? 'rgba(239,68,68,0.1)' : analises.modelo === 'Livre' ? 'rgba(34,197,94,0.1)' : 'rgba(59,130,246,0.1)',
                      color: analises.modelo === 'Descartado' ? '#ef4444' : analises.modelo === 'Livre' ? '#22c55e' : '#3b82f6',
                      border: `1px solid ${analises.modelo === 'Descartado' ? 'rgba(239,68,68,0.2)' : analises.modelo === 'Livre' ? 'rgba(34,197,94,0.2)' : 'rgba(59,130,246,0.2)'}`,
                    }}
                  >
                    {analises.modelo}
                  </span>
                )}
              </div>

              {/* Score grades grid */}
              {Object.keys(analises.scores).length > 0 && (
                <div className="grid grid-cols-3 md:grid-cols-6 gap-3 mb-4">
                  {Object.entries(analises.scores).map(([key, value], i) => (
                    <motion.div
                      key={key}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.1 + i * 0.05 }}
                      className="text-center p-3 rounded-xl"
                      style={{
                        background: 'var(--color-surface-2)',
                        border: '1px solid var(--color-border-subtle)',
                      }}
                    >
                      <div className="text-[10px] mb-1.5 leading-tight uppercase tracking-wider font-semibold" style={{ color: 'var(--color-text-muted)' }}>
                        {SCORE_LABELS[key] || key}
                      </div>
                      <div
                        className="text-[22px] stat-num font-bold"
                        style={{ color: getAnalysisScoreColor(value) }}
                      >
                        {value.toFixed(1)}
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}

              {/* Analysis text */}
              {analises.analysis_text && (
                <div
                  className="text-[13px] leading-relaxed p-4 rounded-lg mb-4"
                  style={{
                    background: 'var(--color-surface-2)',
                    color: 'var(--color-text-secondary)',
                    border: '1px solid var(--color-border-subtle)',
                  }}
                >
                  <div className="eyebrow mb-2.5">
                    Parecer
                  </div>
                  {analises.analysis_text}
                </div>
              )}

              {/* Financial info row */}
              {(analises.faixa_salarial || analises.transfer_luvas) && (
                <div className="flex flex-wrap gap-3 mb-4">
                  {analises.faixa_salarial && (
                    <div className="flex items-center gap-2 px-3 py-2 rounded-lg text-[12px]" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)' }}>
                      <DollarSign size={13} strokeWidth={1.75} style={{ color: 'var(--color-text-muted)' }} />
                      <span className="eyebrow" style={{ fontSize: '10px' }}>Salário:</span>
                      <span className="font-semibold stat-num" style={{ color: 'var(--color-text-primary)' }}>{analises.faixa_salarial}</span>
                    </div>
                  )}
                  {analises.transfer_luvas && (
                    <div className="flex items-center gap-2 px-3 py-2 rounded-lg text-[12px]" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)' }}>
                      <DollarSign size={13} strokeWidth={1.75} style={{ color: 'var(--color-text-muted)' }} />
                      <span className="eyebrow" style={{ fontSize: '10px' }}>Transfer/Luvas:</span>
                      <span className="font-semibold stat-num" style={{ color: 'var(--color-text-primary)' }}>{analises.transfer_luvas}</span>
                    </div>
                  )}
                </div>
              )}

              {/* External links */}
              {Object.keys(analises.links).length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {Object.entries(analises.links).map(([key, url]) => {
                    const info = LINK_ICONS[key];
                    const label = info?.label || key;
                    const isVideo = key === 'Vídeo';
                    const isReport = key === 'Relatório';
                    return (
                      <a
                        key={key}
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-medium transition-colors hover:bg-white/10"
                        style={{
                          background: 'var(--color-surface-2)',
                          color: 'var(--color-text-secondary)',
                          border: '1px solid var(--color-border-subtle)',
                        }}
                      >
                        {isVideo ? (
                          <Video size={11} strokeWidth={1.5} />
                        ) : isReport ? (
                          <FileText size={11} strokeWidth={1.5} />
                        ) : (
                          <ExternalLink size={11} strokeWidth={1.5} />
                        )}
                        {label}
                      </a>
                    );
                  })}
                </div>
              )}
            </div>
          </motion.div>
        )}

        {/* ── Asymmetric grid: Radar + Indices ────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_0.65fr] gap-4">
          {/* Radar */}
          <motion.div variants={fadeUp} className="card-glass p-6">
            <div className="flex items-center gap-2 mb-4">
              <BarChart3 size={15} strokeWidth={1.75} style={{ color: 'var(--color-accent)' }} />
              <span className="eyebrow-strong">
                Percentis por Posição
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
              <div className="mt-5 grid grid-cols-2 gap-x-4 gap-y-1.5 pt-4" style={{ borderTop: '1px solid var(--color-border-subtle)' }}>
                {Object.entries(percentiles).map(([metric, value]) => (
                  <div key={metric} className="flex items-center justify-between">
                    <span className="text-[11px] truncate pr-2" style={{ color: 'var(--color-text-secondary)' }}>
                      {metric}
                    </span>
                    <span className="text-[11px] stat-num font-bold" style={{ color: getScoreColor(value) }}>
                      P{value.toFixed(0)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </motion.div>

          {/* Composite Indices */}
          <motion.div variants={fadeUp} className="card-glass p-6 flex flex-col">
            <div className="flex items-center gap-2 mb-4">
              <Trophy size={15} strokeWidth={1.75} style={{ color: 'var(--color-accent)' }} />
              <span className="eyebrow-strong">
                Índices Compostos
              </span>
            </div>
            <div className="flex-1 space-y-3.5">
              {Object.entries(indices).map(([name, value], i) => (
                <motion.div
                  key={name}
                  initial={{ opacity: 0, x: 8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.15 + i * 0.06 }}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[12.5px] font-medium" style={{ color: 'var(--color-text-secondary)' }}>
                      {name}
                    </span>
                    <span
                      className="text-[12.5px] stat-num font-bold"
                      style={{ color: getScoreColor(value) }}
                    >
                      {value.toFixed(1)}
                    </span>
                  </div>
                  <div
                    className="h-2 rounded-full overflow-hidden"
                    style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)' }}
                  >
                    <motion.div
                      className="h-full rounded-full"
                      style={{
                        background: `linear-gradient(90deg, var(--color-accent) 0%, ${getScoreColor(value)} 100%)`,
                      }}
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

        {/* ── SkillCorner section ─────────────────────────────────── */}
        <motion.div variants={fadeUp} className="card-glass p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Activity size={15} strokeWidth={1.75} style={{ color: 'var(--color-accent)' }} />
              <span className="eyebrow-strong">
                SkillCorner {scOverride ? <span style={{ color: 'var(--color-text-muted)', textTransform: 'none', letterSpacing: 0, marginLeft: 6 }}>· {scOverride}</span> : null}
              </span>
            </div>
            <button
              onClick={() => setScSearchOpen(!scSearchOpen)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] transition-colors cursor-pointer font-medium"
              style={{
                background: scSearchOpen ? 'var(--color-accent-glow)' : 'var(--color-surface-2)',
                color: scSearchOpen ? 'var(--color-accent)' : 'var(--color-text-secondary)',
                border: `1px solid ${scSearchOpen ? 'rgba(227,6,19,0.3)' : 'var(--color-border-subtle)'}`,
              }}
            >
              <Search size={11} strokeWidth={1.75} />
              Buscar atleta
            </button>
          </div>

          {/* SkillCorner player search */}
          {scSearchOpen && (
            <div className="mb-4 relative">
              <div className="flex items-center gap-2 mb-2">
                <input
                  type="text"
                  placeholder="Nome do jogador no SkillCorner..."
                  value={scSearchQuery}
                  onChange={(e) => setScSearchQuery(e.target.value)}
                  className="flex-1 px-3 py-2 rounded-lg text-xs outline-none"
                  style={{
                    background: 'var(--color-surface-1)',
                    borderBottom: '1px solid var(--color-surface-3)',
                    color: 'var(--color-text-primary)',
                    fontFamily: 'var(--font-body)',
                  }}
                  autoFocus
                />
                {scOverride && (
                  <button
                    onClick={() => { setScOverride(null); setScSearchQuery(''); setScSearchOpen(false); }}
                    className="px-2 py-1.5 rounded-lg text-[10px] cursor-pointer"
                    style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.2)' }}
                    title="Remover selecao manual"
                  >
                    <X size={10} />
                  </button>
                )}
              </div>
              {scResults && scResults.length > 0 && (
                <div
                  className="rounded-lg overflow-hidden max-h-48 overflow-y-auto"
                  style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-subtle)' }}
                >
                  {scResults.map((r) => (
                    <button
                      key={`${r.player_name}-${r.team_name}`}
                      onClick={() => {
                        setScOverride(r.player_name);
                        setScSearchOpen(false);
                        setScSearchQuery('');
                      }}
                      className="w-full text-left px-3 py-2 text-xs hover:bg-white/5 transition-colors cursor-pointer flex items-center justify-between"
                      style={{ borderBottom: '1px solid var(--color-border-subtle)' }}
                    >
                      <span style={{ color: 'var(--color-text-primary)' }}>{r.player_name}</span>
                      <span className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>
                        {r.team_name} {r.position_group ? `· ${r.position_group}` : ''}
                      </span>
                    </button>
                  ))}
                </div>
              )}
              {scSearchQuery.length >= 2 && scResults && scResults.length === 0 && (
                <div className="text-[10px] py-2" style={{ color: 'var(--color-text-muted)' }}>
                  Nenhum jogador encontrado
                </div>
              )}
            </div>
          )}

        {skillcorner && Object.keys(skillcorner).length > 0 && (
          <div className="mb-5">
            <div className="eyebrow mb-3">Índices</div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {Object.entries(skillcorner).map(([name, value], i) => (
                <motion.div
                  key={name}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 + i * 0.05 }}
                  className="p-4 rounded-xl"
                  style={{
                    background: 'var(--color-surface-2)',
                    border: '1px solid var(--color-border-subtle)',
                  }}
                >
                  <div
                    className="text-[11px] mb-1.5 leading-tight font-medium"
                    style={{ color: 'var(--color-text-muted)' }}
                  >
                    {name.replace(/ index$/i, '')}
                  </div>
                  <div
                    className="text-[20px] stat-num font-bold"
                    style={{ color: 'var(--color-text-primary)' }}
                  >
                    {typeof value === 'number' ? value.toFixed(2) : value}
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Physical data */}
        {skillcorner_physical && Object.keys(skillcorner_physical).length > 0 && (
          <div>
            <div className="eyebrow mb-3">Dados Físicos</div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
              {Object.entries(skillcorner_physical).map(([name, value], i) => (
                <motion.div
                  key={name}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 + i * 0.05 }}
                  className="p-4 rounded-xl"
                  style={{
                    background: 'var(--color-surface-2)',
                    border: '1px solid var(--color-border-subtle)',
                  }}
                >
                  <div
                    className="text-[11px] mb-1.5 leading-tight font-medium"
                    style={{ color: 'var(--color-text-muted)' }}
                  >
                    {name}
                  </div>
                  <div
                    className="text-[20px] stat-num font-bold"
                    style={{ color: 'var(--color-text-primary)' }}
                  >
                    {typeof value === 'number' ? value.toFixed(2) : value}
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* No data message */}
        {(!skillcorner || Object.keys(skillcorner).length === 0) && (!skillcorner_physical || Object.keys(skillcorner_physical).length === 0) && (
          <div className="text-[12px] py-3 text-center" style={{ color: 'var(--color-text-muted)' }}>
            Nenhum dado SkillCorner encontrado. Use "Buscar atleta" para selecionar manualmente.
          </div>
        )}

        </motion.div>
        {/* ── P(Sucesso) Prediction Card ──────────────────────────── */}
        {prediction && (
          <motion.div variants={fadeUp} className="card-glass p-6">
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp size={15} strokeWidth={1.75} style={{ color: prediction.success_probability >= 0.65 ? '#22c55e' : prediction.success_probability >= 0.40 ? '#eab308' : '#ef4444' }} />
              <span className="eyebrow-strong">
                Predição de Sucesso (Contratação)
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
              {/* P(Sucesso) main */}
              <div className="p-4 rounded-xl" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)' }}>
                <div className="text-[11px] mb-1.5 font-medium" style={{ color: 'var(--color-text-muted)' }}>P(Sucesso)</div>
                <div className="text-[26px] stat-num font-bold leading-none" style={{ color: prediction.success_probability >= 0.65 ? '#22c55e' : prediction.success_probability >= 0.40 ? '#eab308' : '#ef4444' }}>
                  {(prediction.success_probability * 100).toFixed(0)}%
                </div>
                <div className="text-[10px] font-[var(--font-display)] tracking-wider uppercase mt-1.5 font-semibold" style={{ color: 'var(--color-text-secondary)' }}>
                  Risco: {prediction.risk_level}
                </div>
              </div>

              {/* League Gap */}
              <div className="p-4 rounded-xl" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)' }}>
                <div className="text-[11px] mb-1.5 font-medium" style={{ color: 'var(--color-text-muted)' }}>Gap de Liga</div>
                <div className="text-[20px] stat-num font-bold leading-none" style={{ color: prediction.league_gap > 2 ? '#ef4444' : prediction.league_gap > 0 ? '#eab308' : '#22c55e' }}>
                  {prediction.league_gap > 0 ? '+' : ''}{prediction.league_gap.toFixed(1)}
                </div>
                <div className="text-[11px] mt-1.5 stat-num" style={{ color: 'var(--color-text-secondary)' }}>
                  Tier {prediction.tier_origin.toFixed(1)} → {prediction.tier_target.toFixed(1)}
                </div>
              </div>

              {/* Age Factor */}
              <div className="p-4 rounded-xl" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)' }}>
                <div className="text-[11px] mb-1.5 font-medium" style={{ color: 'var(--color-text-muted)' }}>Fator Idade</div>
                <div className="text-[20px] stat-num font-bold leading-none" style={{ color: getScoreColor(prediction.age_factor * 100) }}>
                  {(prediction.age_factor * 100).toFixed(0)}%
                </div>
                <div className="text-[11px] mt-1.5" style={{ color: 'var(--color-text-secondary)' }}>Pico aos 26 anos</div>
              </div>

              {/* Minutes Factor */}
              <div className="p-4 rounded-xl" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)' }}>
                <div className="text-[11px] mb-1.5 font-medium" style={{ color: 'var(--color-text-muted)' }}>Regularidade</div>
                <div className="text-[20px] stat-num font-bold leading-none" style={{ color: getScoreColor(prediction.minutes_factor * 100) }}>
                  {(prediction.minutes_factor * 100).toFixed(0)}%
                </div>
                <div className="text-[11px] mt-1.5" style={{ color: 'var(--color-text-secondary)' }}>Min jogados / 3000</div>
              </div>
            </div>

            {/* SSP Lambda weights */}
            {ssp_lambdas && (
              <div className="pt-4" style={{ borderTop: '1px solid var(--color-border-subtle)' }}>
                <div className="eyebrow mb-2.5">
                  SSP Lambdas (Composição do Score)
                </div>
                <div className="flex gap-2">
                  {Object.entries(ssp_lambdas).map(([key, weight]) => (
                    <div key={key} className="flex-1 text-center p-2.5 rounded-lg" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)' }}>
                      <div className="text-[10px] uppercase tracking-wider font-semibold" style={{ color: 'var(--color-text-muted)' }}>{key}</div>
                      <div className="text-[14px] stat-num font-bold mt-0.5" style={{ color: 'var(--color-text-primary)' }}>
                        {(weight * 100).toFixed(0)}%
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </motion.div>
    </AnimatePresence>
  );
}
