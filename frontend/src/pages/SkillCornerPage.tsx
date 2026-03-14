import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Activity,
  AlertTriangle,
  Search,
  X,
  MapPin,
  ChevronDown,
  ChevronRight,
  Info,
  Zap,
  TrendingUp,
  Star,
} from 'lucide-react';
import {
  usePlayers,
  usePositions,
  useSkillCornerSearch,
  useSkillCornerPlayer,
  useSkillCornerCoverage,
} from '../hooks/usePlayers';
import { getScoreColor } from '../lib/utils';

// ── Coverage banner ──

function CoverageBanner({ covered, league }: { covered: boolean; league: string | null }) {
  if (covered) return null;
  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-start gap-3 px-5 py-4 rounded-2xl"
      style={{
        background: 'linear-gradient(135deg, rgba(234, 179, 8, 0.06) 0%, rgba(234, 179, 8, 0.02) 100%)',
        border: '1px solid rgba(234, 179, 8, 0.15)',
        backdropFilter: 'blur(12px)',
      }}
    >
      <AlertTriangle size={16} className="mt-0.5 shrink-0" style={{ color: '#eab308' }} />
      <div>
        <div className="text-sm font-semibold tracking-wide" style={{ color: '#eab308', fontFamily: 'var(--font-display)' }}>
          Fora da cobertura SkillCorner
        </div>
        <div className="text-xs mt-1 leading-relaxed" style={{ color: 'var(--color-text-muted)' }}>
          {league ? `Liga: ${league}. ` : ''}
          Os dados SkillCorner estao disponiveis apenas para ligas sul-americanas e Liga Portugal.
          Use "Vincular atleta" para buscar manualmente na base SkillCorner.
        </div>
      </div>
    </motion.div>
  );
}

// ── Metric card with glassmorphism ──

function MetricCard({ name, value, percentile, delay }: { name: string; value: number; percentile?: number; delay: number }) {
  const pctColor = percentile != null ? getScoreColor(percentile) : 'var(--color-text-muted)';

  return (
    <motion.div
      initial={{ opacity: 0, y: 12, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay, type: 'spring', stiffness: 300, damping: 30 }}
      className="relative group"
    >
      <div
        className="p-4 rounded-xl h-full transition-all duration-300"
        style={{
          background: 'linear-gradient(145deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%)',
          border: '1px solid rgba(255,255,255,0.06)',
          backdropFilter: 'blur(8px)',
        }}
      >
        {/* Metric name */}
        <div
          className="text-[10px] uppercase tracking-widest mb-3 leading-tight font-medium"
          style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-display)' }}
        >
          {name.replace(/_/g, ' ').replace(/ index$/i, '').replace(/per 90/i, '/90')}
        </div>

        {/* Value */}
        <div className="flex items-end justify-between">
          <span
            className="text-2xl font-bold tracking-tight"
            style={{ color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)' }}
          >
            {value.toFixed(2)}
          </span>
          {percentile != null && (
            <span
              className="text-xs font-bold mb-0.5"
              style={{ color: pctColor, fontFamily: 'var(--font-mono)' }}
            >
              P{percentile.toFixed(0)}
            </span>
          )}
        </div>

        {/* Percentile bar */}
        {percentile != null && (
          <div className="mt-3">
            <div
              className="h-1 rounded-full overflow-hidden"
              style={{ background: 'rgba(255,255,255,0.06)' }}
            >
              <motion.div
                className="h-full rounded-full"
                style={{
                  background: `linear-gradient(90deg, ${pctColor}88, ${pctColor})`,
                }}
                initial={{ width: 0 }}
                animate={{ width: `${Math.min(percentile, 100)}%` }}
                transition={{ duration: 0.8, delay: delay + 0.3, ease: 'easeOut' }}
              />
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
}

// ── Identity Resolution component ──

function IdentityResolver({
  scOverride,
  onOverride,
}: {
  scOverride: string | null;
  onOverride: (name: string | null) => void;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const { data: results } = useSkillCornerSearch(open ? query : '');

  return (
    <div>
      <div className="flex items-center gap-2">
        <button
          onClick={() => setOpen(!open)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 cursor-pointer"
          style={{
            background: open
              ? 'linear-gradient(135deg, rgba(227,6,19,0.15), rgba(227,6,19,0.05))'
              : 'rgba(255,255,255,0.04)',
            color: open ? 'var(--color-accent)' : 'var(--color-text-muted)',
            border: `1px solid ${open ? 'rgba(227,6,19,0.25)' : 'rgba(255,255,255,0.06)'}`,
            fontFamily: 'var(--font-display)',
          }}
        >
          <Search size={11} />
          Vincular atleta
        </button>
        {scOverride && (
          <div className="flex items-center gap-1.5">
            <span
              className="text-[10px] px-2.5 py-1 rounded-lg font-medium"
              style={{
                background: 'rgba(34,197,94,0.08)',
                color: '#22c55e',
                border: '1px solid rgba(34,197,94,0.15)',
                fontFamily: 'var(--font-display)',
              }}
            >
              {scOverride}
            </span>
            <button
              onClick={() => { onOverride(null); setQuery(''); setOpen(false); }}
              className="p-1 rounded-lg cursor-pointer hover:bg-white/5 transition-colors"
              style={{ color: 'var(--color-text-muted)' }}
              title="Remover vinculacao"
            >
              <X size={12} />
            </button>
          </div>
        )}
      </div>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-3"
          >
            <input
              type="text"
              placeholder="Buscar jogador na base SkillCorner..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl text-xs outline-none transition-colors"
              style={{
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid rgba(255,255,255,0.08)',
                color: 'var(--color-text-primary)',
                fontFamily: 'var(--font-body)',
              }}
              autoFocus
            />
            {results && results.length > 0 && (
              <div
                className="mt-1.5 rounded-xl overflow-hidden max-h-48 overflow-y-auto"
                style={{
                  background: 'rgba(14,14,14,0.95)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  backdropFilter: 'blur(20px)',
                }}
              >
                {results.map((r) => (
                  <button
                    key={`${r.player_name}-${r.team_name}`}
                    onClick={() => {
                      onOverride(r.player_name);
                      setOpen(false);
                      setQuery('');
                    }}
                    className="w-full text-left px-4 py-2.5 text-xs hover:bg-white/5 transition-colors cursor-pointer flex items-center justify-between"
                    style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}
                  >
                    <span style={{ color: 'var(--color-text-primary)', fontFamily: 'var(--font-display)', fontWeight: 500 }}>{r.player_name}</span>
                    <span className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>
                      {r.team_name} {r.position_group ? `· ${r.position_group}` : ''}
                    </span>
                  </button>
                ))}
              </div>
            )}
            {query.length >= 2 && results && results.length === 0 && (
              <div className="text-[10px] py-2 px-1" style={{ color: 'var(--color-text-muted)' }}>
                Nenhum jogador encontrado
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Section header button ──

function SectionHeader({
  icon: Icon,
  title,
  count,
  countLabel,
  expanded,
  onToggle,
}: {
  icon: typeof Activity;
  title: string;
  count: number;
  countLabel: string;
  expanded: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      onClick={onToggle}
      className="w-full flex items-center justify-between px-6 py-4 cursor-pointer hover:bg-white/[0.02] transition-all duration-200"
    >
      <div className="flex items-center gap-3">
        <div
          className="w-7 h-7 rounded-lg flex items-center justify-center"
          style={{ background: 'rgba(255,255,255,0.04)' }}
        >
          {expanded ? <ChevronDown size={13} style={{ color: 'var(--color-text-secondary)' }} /> : <ChevronRight size={13} style={{ color: 'var(--color-text-muted)' }} />}
        </div>
        <div className="flex items-center gap-2">
          <Icon size={14} style={{ color: 'var(--color-accent)' }} />
          <span
            className="text-[11px] font-semibold tracking-[0.15em] uppercase"
            style={{ color: expanded ? 'var(--color-text-secondary)' : 'var(--color-text-muted)', fontFamily: 'var(--font-display)' }}
          >
            {title}
          </span>
        </div>
      </div>
      <span
        className="text-[10px] font-medium px-2.5 py-1 rounded-lg"
        style={{
          color: 'var(--color-text-muted)',
          background: 'rgba(255,255,255,0.03)',
          fontFamily: 'var(--font-mono)',
        }}
      >
        {count} {countLabel}
      </span>
    </button>
  );
}

// ── Main page ──

export default function SkillCornerPage() {
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedPlayer, setSelectedPlayer] = useState('');
  const [scOverride, setScOverride] = useState<string | null>(null);
  const [expandedSection, setExpandedSection] = useState<string | null>('physical');
  const [debounceTimer, setDebounceTimer] = useState<ReturnType<typeof setTimeout> | null>(null);

  const { data: positions = [] } = usePositions();
  const { data: searchData } = usePlayers(
    debouncedSearch.length >= 2 && !selectedPlayer ? { search: debouncedSearch, limit: 10 } : { limit: 0 }
  );
  const players = searchData?.players ?? [];

  const { data: scProfile, isLoading } = useSkillCornerPlayer(
    selectedPlayer || null,
    scOverride
  );

  const { data: coverage } = useSkillCornerCoverage();

  // Reset override when player changes
  useEffect(() => {
    setScOverride(null);
  }, [selectedPlayer]);

  const handleSearchChange = (value: string) => {
    setSearch(value);
    setSelectedPlayer('');
    if (debounceTimer) clearTimeout(debounceTimer);
    setDebounceTimer(setTimeout(() => setDebouncedSearch(value), 200));
  };

  const indices = scProfile?.indices ?? {};
  const physical = scProfile?.physical ?? {};
  const physicalPercentiles = scProfile?.physical_percentiles ?? {};
  const allMetrics = scProfile?.all_metrics ?? {};
  const physicalEntries = Object.entries(physical);

  // Separate remaining metrics (not indices, not physical)
  const indexKeys = new Set(Object.keys(indices));
  const physicalOriginalKeys = new Set([
    'sprint_count_per_90', 'hi_count_per_90', 'distance_per_90',
    'high_speed_running_distance_per_90', 'accelerations_per_90', 'decelerations_per_90',
    'max_speed', 'avg_speed', 'pressing_index_per_90',
    'avg_psv99', 'avg_top_5_psv99',
  ]);
  const otherMetrics = Object.entries(allMetrics).filter(
    ([k]) => !indexKeys.has(k) && !physicalOriginalKeys.has(k) && !['age', 'count_match'].includes(k)
  );

  return (
    <div className="space-y-6">
      {/* ── Hero header ── */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-2xl px-7 py-6"
        style={{
          background: 'linear-gradient(135deg, rgba(18,18,18,0.95) 0%, rgba(10,10,10,0.9) 50%, rgba(20,20,20,0.85) 100%)',
          border: '1px solid rgba(255,255,255,0.06)',
          backdropFilter: 'blur(20px)',
        }}
      >
        {/* Subtle star accent */}
        <div
          className="absolute -top-8 -right-8 opacity-[0.03]"
          style={{ fontSize: '120px', lineHeight: 1, color: '#fff', fontFamily: 'serif' }}
        >
          ★
        </div>

        <div className="relative z-10 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2.5 mb-1">
              <div
                className="w-8 h-8 rounded-xl flex items-center justify-center"
                style={{
                  background: 'linear-gradient(135deg, rgba(227,6,19,0.2), rgba(227,6,19,0.05))',
                  border: '1px solid rgba(227,6,19,0.2)',
                }}
              >
                <Activity size={16} style={{ color: 'var(--color-accent)' }} />
              </div>
              <h1
                className="text-xl font-bold tracking-tight"
                style={{ fontFamily: 'var(--font-display)', color: 'var(--color-text-primary)' }}
              >
                SkillCorner
              </h1>
            </div>
            <p
              className="text-xs mt-1 ml-[42px] tracking-wide"
              style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-display)' }}
            >
              Metricas fisicas e indices de performance
            </p>
          </div>

          {/* Botafogo star watermark */}
          <div className="flex items-center gap-1 opacity-30">
            <Star size={10} fill="currentColor" style={{ color: 'var(--color-text-muted)' }} />
          </div>
        </div>
      </motion.div>

      {/* ── Coverage info ── */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="flex items-start gap-3 px-5 py-4 rounded-2xl"
        style={{
          background: 'linear-gradient(135deg, rgba(59,130,246,0.04) 0%, rgba(59,130,246,0.01) 100%)',
          border: '1px solid rgba(59,130,246,0.1)',
          backdropFilter: 'blur(12px)',
        }}
      >
        <Info size={14} className="mt-0.5 shrink-0" style={{ color: '#3b82f6' }} />
        <div className="text-xs leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
          <span className="font-semibold" style={{ color: '#3b82f6', fontFamily: 'var(--font-display)' }}>Cobertura:</span>{' '}
          Ligas sul-americanas (Brasil, Argentina, Colombia, Chile, Libertadores, Sul-Americana) e Liga Portugal.
          {coverage && (
            <span className="text-[10px] ml-1 font-medium" style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
              ({coverage.covered_leagues.length} ligas)
            </span>
          )}
        </div>
      </motion.div>

      {/* ── Search ── */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="rounded-2xl p-6"
        style={{
          background: 'linear-gradient(145deg, rgba(22,22,22,0.9) 0%, rgba(16,16,16,0.85) 100%)',
          border: '1px solid rgba(255,255,255,0.06)',
          backdropFilter: 'blur(20px)',
        }}
      >
        <div>
          <label
            className="block text-[10px] font-semibold tracking-[0.15em] uppercase mb-2"
            style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-display)' }}
          >
            JOGADOR
          </label>
          <div className="relative">
            <div className="absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none">
              <Search size={14} style={{ color: 'var(--color-text-muted)' }} />
            </div>
            <input
              type="text"
              value={search}
              onChange={(e) => handleSearchChange(e.target.value)}
              placeholder="Digite o nome do jogador..."
              className="w-full pl-10 pr-4 py-3 rounded-xl text-sm outline-none transition-all duration-200 focus:ring-1"
              style={{
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid rgba(255,255,255,0.06)',
                color: 'var(--color-text-primary)',
                fontFamily: 'var(--font-body)',
              }}
            />
            {debouncedSearch.length >= 2 && !selectedPlayer && players.length > 0 && (
              <div
                className="absolute top-full left-0 right-0 mt-2 rounded-xl overflow-hidden z-50 max-h-48 overflow-y-auto"
                style={{
                  background: 'rgba(14,14,14,0.97)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  backdropFilter: 'blur(24px)',
                  boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
                }}
              >
                {players.map((p, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      setSelectedPlayer(p.display_name || p.name);
                      setSearch(p.display_name || p.name);
                      setDebouncedSearch('');
                    }}
                    className="w-full text-left px-4 py-3 text-sm transition-colors hover:bg-white/5 cursor-pointer"
                    style={{
                      borderBottom: '1px solid rgba(255,255,255,0.04)',
                      color: 'var(--color-text-primary)',
                    }}
                  >
                    <div className="font-medium" style={{ fontFamily: 'var(--font-display)' }}>{p.display_name || p.name}</div>
                    <div className="text-[10px] mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
                      {p.team} — {p.position} {p.league ? `· ${p.league}` : ''}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </motion.div>

      {/* ── Loading ── */}
      {isLoading && (
        <div
          className="rounded-2xl p-8 text-center"
          style={{
            background: 'linear-gradient(145deg, rgba(22,22,22,0.9) 0%, rgba(16,16,16,0.85) 100%)',
            border: '1px solid rgba(255,255,255,0.06)',
          }}
        >
          <div className="skeleton h-48 rounded-xl" />
        </div>
      )}

      {/* ── Results ── */}
      {scProfile && selectedPlayer && (
        <>
          {/* Coverage warning */}
          <CoverageBanner covered={scProfile.covered} league={scProfile.league} />

          {/* Match info + Identity resolver */}
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="rounded-2xl p-6"
            style={{
              background: 'linear-gradient(145deg, rgba(22,22,22,0.9) 0%, rgba(16,16,16,0.85) 100%)',
              border: '1px solid rgba(255,255,255,0.06)',
              backdropFilter: 'blur(20px)',
            }}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2.5">
                <div
                  className="w-6 h-6 rounded-lg flex items-center justify-center"
                  style={{ background: 'rgba(255,255,255,0.04)' }}
                >
                  <MapPin size={12} style={{ color: 'var(--color-accent)' }} />
                </div>
                <span
                  className="text-[11px] font-semibold tracking-[0.15em] uppercase"
                  style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-display)' }}
                >
                  RESOLUCAO DE IDENTIDADE
                </span>
              </div>
              {scProfile.found && (
                <span
                  className="text-[10px] font-semibold px-3 py-1 rounded-lg"
                  style={{
                    background: 'rgba(34,197,94,0.08)',
                    color: '#22c55e',
                    border: '1px solid rgba(34,197,94,0.15)',
                    fontFamily: 'var(--font-display)',
                    letterSpacing: '0.05em',
                  }}
                >
                  MATCH ENCONTRADO
                </span>
              )}
              {!scProfile.found && (
                <span
                  className="text-[10px] font-semibold px-3 py-1 rounded-lg"
                  style={{
                    background: 'rgba(239,68,68,0.08)',
                    color: '#ef4444',
                    border: '1px solid rgba(239,68,68,0.15)',
                    fontFamily: 'var(--font-display)',
                    letterSpacing: '0.05em',
                  }}
                >
                  SEM MATCH
                </span>
              )}
            </div>

            {scProfile.found && (
              <div
                className="flex flex-wrap items-center gap-3 mb-4 px-4 py-3 rounded-xl"
                style={{
                  background: 'rgba(255,255,255,0.02)',
                  border: '1px solid rgba(255,255,255,0.04)',
                }}
              >
                <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>SC:</span>
                <span className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)', fontFamily: 'var(--font-display)' }}>
                  {scProfile.matched_name}
                </span>
                {scProfile.matched_team && (
                  <>
                    <span className="w-px h-3" style={{ background: 'rgba(255,255,255,0.1)' }} />
                    <span className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                      {scProfile.matched_team}
                    </span>
                  </>
                )}
                {scProfile.matched_position && (
                  <>
                    <span className="w-px h-3" style={{ background: 'rgba(255,255,255,0.1)' }} />
                    <span className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                      {scProfile.matched_position}
                    </span>
                  </>
                )}
                {scProfile.position && (
                  <span
                    className="px-2 py-0.5 rounded-md text-[10px] font-semibold"
                    style={{
                      background: 'linear-gradient(135deg, rgba(227,6,19,0.15), rgba(227,6,19,0.05))',
                      color: 'var(--color-accent)',
                      border: '1px solid rgba(227,6,19,0.2)',
                      fontFamily: 'var(--font-display)',
                    }}
                  >
                    {scProfile.position}
                  </span>
                )}
              </div>
            )}

            <IdentityResolver scOverride={scOverride} onOverride={setScOverride} />
          </motion.div>

          {/* ── Data sections ── */}
          {scProfile.found && (
            <>
              {/* Physical data */}
              {physicalEntries.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="rounded-2xl overflow-hidden"
                  style={{
                    background: 'linear-gradient(145deg, rgba(22,22,22,0.9) 0%, rgba(16,16,16,0.85) 100%)',
                    border: '1px solid rgba(255,255,255,0.06)',
                    backdropFilter: 'blur(20px)',
                  }}
                >
                  <SectionHeader
                    icon={Zap}
                    title="DADOS FISICOS"
                    count={physicalEntries.length}
                    countLabel="metricas"
                    expanded={expandedSection === 'physical'}
                    onToggle={() => setExpandedSection(expandedSection === 'physical' ? null : 'physical')}
                  />
                  <AnimatePresence>
                    {expandedSection === 'physical' && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.3, ease: 'easeInOut' }}
                        className="px-6 pb-6"
                      >
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                          {physicalEntries.map(([name, value], i) => (
                            <MetricCard key={name} name={name} value={value} percentile={physicalPercentiles[name]} delay={0.1 + i * 0.04} />
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              )}

              {/* All other metrics */}
              {otherMetrics.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="rounded-2xl overflow-hidden"
                  style={{
                    background: 'linear-gradient(145deg, rgba(22,22,22,0.9) 0%, rgba(16,16,16,0.85) 100%)',
                    border: '1px solid rgba(255,255,255,0.06)',
                    backdropFilter: 'blur(20px)',
                  }}
                >
                  <SectionHeader
                    icon={TrendingUp}
                    title="TODAS AS METRICAS"
                    count={otherMetrics.length}
                    countLabel="metricas"
                    expanded={expandedSection === 'all'}
                    onToggle={() => setExpandedSection(expandedSection === 'all' ? null : 'all')}
                  />
                  <AnimatePresence>
                    {expandedSection === 'all' && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.3, ease: 'easeInOut' }}
                        className="px-6 pb-6"
                      >
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                          {otherMetrics.map(([name, value], i) => (
                            <MetricCard key={name} name={name} value={value} delay={0.05 + i * 0.02} />
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              )}
            </>
          )}

          {/* No data found */}
          {!scProfile.found && !isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="rounded-2xl p-8 text-center"
              style={{
                background: 'linear-gradient(145deg, rgba(22,22,22,0.9) 0%, rgba(16,16,16,0.85) 100%)',
                border: '1px solid rgba(255,255,255,0.06)',
                color: 'var(--color-text-muted)',
              }}
            >
              <Activity size={28} className="mx-auto mb-3 opacity-20" />
              <p className="text-sm font-medium mb-1" style={{ fontFamily: 'var(--font-display)' }}>
                Nenhum dado SkillCorner encontrado
              </p>
              <p className="text-[10px]">Use "Vincular atleta" acima para selecionar manualmente na base SkillCorner</p>
            </motion.div>
          )}
        </>
      )}

      {/* Empty state */}
      {!selectedPlayer && !isLoading && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="rounded-2xl p-10 text-center"
          style={{
            background: 'linear-gradient(145deg, rgba(22,22,22,0.9) 0%, rgba(16,16,16,0.85) 100%)',
            border: '1px solid rgba(255,255,255,0.06)',
            color: 'var(--color-text-muted)',
          }}
        >
          <div
            className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4"
            style={{
              background: 'linear-gradient(135deg, rgba(227,6,19,0.1), rgba(227,6,19,0.02))',
              border: '1px solid rgba(227,6,19,0.1)',
            }}
          >
            <Activity size={24} style={{ color: 'var(--color-accent)', opacity: 0.5 }} />
          </div>
          <p className="text-sm font-medium" style={{ fontFamily: 'var(--font-display)' }}>
            Selecione um jogador para ver os dados SkillCorner
          </p>
          <p className="text-[10px] mt-1 opacity-60">
            Busque pelo nome acima
          </p>
        </motion.div>
      )}
    </div>
  );
}
