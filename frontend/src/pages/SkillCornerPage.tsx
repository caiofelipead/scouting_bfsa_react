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
      className="flex items-start gap-3 px-4 py-3 rounded-lg"
      style={{
        background: 'rgba(234, 179, 8, 0.08)',
        border: '1px solid rgba(234, 179, 8, 0.25)',
      }}
    >
      <AlertTriangle size={16} className="mt-0.5 shrink-0" style={{ color: '#eab308' }} />
      <div>
        <div className="text-sm font-medium" style={{ color: '#eab308' }}>
          Fora da cobertura SkillCorner
        </div>
        <div className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
          {league ? `Liga: ${league}. ` : ''}
          Os dados SkillCorner estao disponiveis apenas para ligas sul-americanas e Liga Portugal.
          Use "Vincular atleta" para buscar manualmente na base SkillCorner.
        </div>
      </div>
    </motion.div>
  );
}

// ── Metric card ──

function MetricCard({ name, value, percentile, delay }: { name: string; value: number; percentile?: number; delay: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className="p-3 rounded"
      style={{
        background: 'var(--color-surface-2)',
        border: '1px solid var(--color-border-subtle)',
      }}
    >
      <div className="text-[10px] mb-1 leading-tight" style={{ color: 'var(--color-text-muted)' }}>
        {name.replace(/_/g, ' ').replace(/ index$/i, '').replace(/per 90/i, '/90')}
      </div>
      <div className="text-lg font-[var(--font-mono)] font-bold" style={{ color: 'var(--color-text-primary)' }}>
        {value.toFixed(2)}
      </div>
      {percentile != null && (
        <div className="mt-2">
          <div className="flex items-center justify-between mb-0.5">
            <span className="text-[9px]" style={{ color: 'var(--color-text-muted)' }}>Percentil</span>
            <span className="text-[9px] font-[var(--font-mono)] font-semibold" style={{ color: getScoreColor(percentile) }}>
              P{percentile.toFixed(0)}
            </span>
          </div>
          <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--color-surface-1)' }}>
            <motion.div
              className="h-full rounded-full"
              style={{ background: getScoreColor(percentile) }}
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(percentile, 100)}%` }}
              transition={{ duration: 0.6, delay: delay + 0.2 }}
            />
          </div>
        </div>
      )}
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
          className="flex items-center gap-1 px-2.5 py-1.5 rounded text-xs transition-colors cursor-pointer"
          style={{
            background: open ? 'var(--color-accent-glow)' : 'var(--color-surface-2)',
            color: open ? 'var(--color-accent)' : 'var(--color-text-muted)',
            border: `1px solid ${open ? 'rgba(220,38,38,0.3)' : 'var(--color-border-subtle)'}`,
          }}
        >
          <Search size={11} />
          Vincular atleta
        </button>
        {scOverride && (
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] px-2 py-0.5 rounded" style={{ background: 'rgba(34,197,94,0.1)', color: '#22c55e', border: '1px solid rgba(34,197,94,0.2)' }}>
              {scOverride}
            </span>
            <button
              onClick={() => { onOverride(null); setQuery(''); setOpen(false); }}
              className="p-0.5 rounded cursor-pointer hover:bg-white/5"
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
            className="mt-2"
          >
            <input
              type="text"
              placeholder="Buscar jogador na base SkillCorner..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full px-3 py-2 rounded text-xs outline-none"
              style={{
                background: 'var(--color-surface-1)',
                border: '1px solid var(--color-border-subtle)',
                color: 'var(--color-text-primary)',
              }}
              autoFocus
            />
            {results && results.length > 0 && (
              <div
                className="mt-1 rounded overflow-hidden max-h-48 overflow-y-auto"
                style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-subtle)' }}
              >
                {results.map((r) => (
                  <button
                    key={`${r.player_name}-${r.team_name}`}
                    onClick={() => {
                      onOverride(r.player_name);
                      setOpen(false);
                      setQuery('');
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
            {query.length >= 2 && results && results.length === 0 && (
              <div className="text-[10px] py-2" style={{ color: 'var(--color-text-muted)' }}>
                Nenhum jogador encontrado
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
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
    <div className="space-y-5">
      {/* Header */}
      <div>
        <h1 className="font-[var(--font-display)] text-lg font-bold tracking-tight flex items-center gap-2">
          <Activity size={18} style={{ color: 'var(--color-accent)' }} />
          SkillCorner
        </h1>
        <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
          Metricas fisicas e indices de performance da base SkillCorner
        </p>
      </div>

      {/* Coverage info */}
      <div
        className="flex items-start gap-2 px-4 py-3 rounded-lg"
        style={{
          background: 'rgba(59, 130, 246, 0.06)',
          border: '1px solid rgba(59, 130, 246, 0.2)',
        }}
      >
        <Info size={14} className="mt-0.5 shrink-0" style={{ color: '#3b82f6' }} />
        <div className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
          <span className="font-medium" style={{ color: '#3b82f6' }}>Cobertura:</span>{' '}
          Ligas sul-americanas (Brasil, Argentina, Colombia, Chile, Libertadores, Sul-Americana) e Liga Portugal.
          {coverage && (
            <span className="text-[10px] ml-1" style={{ color: 'var(--color-text-muted)' }}>
              ({coverage.covered_leagues.length} ligas)
            </span>
          )}
        </div>
      </div>

      {/* Search */}
      <div className="card-glass rounded-lg p-5">
        <div>
          <label
            className="block text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-1"
            style={{ color: 'var(--color-text-muted)' }}
          >
            JOGADOR
          </label>
          <div className="relative">
            <input
              type="text"
              value={search}
              onChange={(e) => handleSearchChange(e.target.value)}
              placeholder="Digite o nome do jogador..."
              className="w-full px-3 py-2 rounded text-sm outline-none"
              style={{
                background: 'var(--color-surface-2)',
                border: '1px solid var(--color-border-subtle)',
                color: 'var(--color-text-primary)',
              }}
            />
            {debouncedSearch.length >= 2 && !selectedPlayer && players.length > 0 && (
              <div
                className="absolute top-full left-0 right-0 mt-1 rounded overflow-hidden z-50 max-h-48 overflow-y-auto"
                style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-active)' }}
              >
                {players.map((p, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      setSelectedPlayer(p.display_name || p.name);
                      setSearch(p.display_name || p.name);
                      setDebouncedSearch('');
                    }}
                    className="w-full text-left px-3 py-2 text-sm transition-colors hover:bg-white/5 cursor-pointer"
                    style={{
                      borderBottom: '1px solid var(--color-border-subtle)',
                      color: 'var(--color-text-primary)',
                    }}
                  >
                    <div>{p.display_name || p.name}</div>
                    <div className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>
                      {p.team} — {p.position} {p.league ? `· ${p.league}` : ''}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="card-glass rounded-lg p-8 text-center">
          <div className="skeleton h-48 rounded" />
        </div>
      )}

      {/* Results */}
      {scProfile && selectedPlayer && (
        <>
          {/* Coverage warning */}
          <CoverageBanner covered={scProfile.covered} league={scProfile.league} />

          {/* Match info + Identity resolver */}
          <div className="card-glass rounded-lg p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <MapPin size={14} style={{ color: 'var(--color-accent)' }} />
                <span
                  className="text-[10px] font-[var(--font-display)] tracking-[0.2em] uppercase"
                  style={{ color: 'var(--color-text-muted)' }}
                >
                  RESOLUCAO DE IDENTIDADE
                </span>
              </div>
              {scProfile.found && (
                <span
                  className="text-[10px] px-2 py-0.5 rounded"
                  style={{ background: 'rgba(34,197,94,0.1)', color: '#22c55e', border: '1px solid rgba(34,197,94,0.2)' }}
                >
                  MATCH ENCONTRADO
                </span>
              )}
              {!scProfile.found && (
                <span
                  className="text-[10px] px-2 py-0.5 rounded"
                  style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.2)' }}
                >
                  SEM MATCH
                </span>
              )}
            </div>

            {scProfile.found && (
              <div className="flex flex-wrap gap-4 mb-3 text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                <span>SC: <strong style={{ color: 'var(--color-text-primary)' }}>{scProfile.matched_name}</strong></span>
                {scProfile.matched_team && <span>Time: {scProfile.matched_team}</span>}
                {scProfile.matched_position && <span>Pos: {scProfile.matched_position}</span>}
                {scProfile.position && (
                  <span
                    className="px-1.5 py-0.5 rounded text-[10px]"
                    style={{ background: 'var(--color-accent-glow)', color: 'var(--color-accent)' }}
                  >
                    {scProfile.position}
                  </span>
                )}
              </div>
            )}

            <IdentityResolver scOverride={scOverride} onOverride={setScOverride} />
          </div>

          {/* Data sections */}
          {scProfile.found && (
            <>
              {/* Physical data */}
              {physicalEntries.length > 0 && (
                <div className="card-glass rounded-lg overflow-hidden">
                  <button
                    onClick={() => setExpandedSection(expandedSection === 'physical' ? null : 'physical')}
                    className="w-full flex items-center justify-between px-5 py-3 cursor-pointer hover:bg-white/[0.02] transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      {expandedSection === 'physical' ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                      <span className="text-[10px] font-[var(--font-display)] tracking-[0.2em] uppercase" style={{ color: 'var(--color-text-muted)' }}>
                        DADOS FISICOS
                      </span>
                    </div>
                    <span className="text-xs font-[var(--font-mono)]" style={{ color: 'var(--color-text-muted)' }}>
                      {physicalEntries.length} metricas
                    </span>
                  </button>
                  <AnimatePresence>
                    {expandedSection === 'physical' && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="px-5 pb-5"
                      >
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                          {physicalEntries.map(([name, value], i) => (
                            <MetricCard key={name} name={name} value={value} percentile={physicalPercentiles[name]} delay={0.2 + i * 0.05} />
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )}

              {/* All other metrics */}
              {otherMetrics.length > 0 && (
                <div className="card-glass rounded-lg overflow-hidden">
                  <button
                    onClick={() => setExpandedSection(expandedSection === 'all' ? null : 'all')}
                    className="w-full flex items-center justify-between px-5 py-3 cursor-pointer hover:bg-white/[0.02] transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      {expandedSection === 'all' ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                      <span className="text-[10px] font-[var(--font-display)] tracking-[0.2em] uppercase" style={{ color: 'var(--color-text-muted)' }}>
                        TODAS AS METRICAS
                      </span>
                    </div>
                    <span className="text-xs font-[var(--font-mono)]" style={{ color: 'var(--color-text-muted)' }}>
                      {otherMetrics.length} metricas
                    </span>
                  </button>
                  <AnimatePresence>
                    {expandedSection === 'all' && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="px-5 pb-5"
                      >
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                          {otherMetrics.map(([name, value], i) => (
                            <MetricCard key={name} name={name} value={value} delay={0.1 + i * 0.03} />
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )}
            </>
          )}

          {/* No data found */}
          {!scProfile.found && !isLoading && (
            <div className="card-glass rounded-lg p-6 text-center" style={{ color: 'var(--color-text-muted)' }}>
              <Activity size={28} className="mx-auto mb-2 opacity-30" />
              <p className="text-sm mb-1">Nenhum dado SkillCorner encontrado para este jogador</p>
              <p className="text-[10px]">Use "Vincular atleta" acima para selecionar manualmente na base SkillCorner</p>
            </div>
          )}
        </>
      )}

      {/* Empty state */}
      {!selectedPlayer && !isLoading && (
        <div className="card-glass rounded-lg p-8 text-center" style={{ color: 'var(--color-text-muted)' }}>
          <Activity size={32} className="mx-auto mb-3 opacity-30" />
          <p className="text-sm">Selecione um jogador para ver os dados SkillCorner</p>
        </div>
      )}
    </div>
  );
}
