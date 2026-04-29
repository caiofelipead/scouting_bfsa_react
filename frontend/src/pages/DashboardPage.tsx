import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Filter, ChevronRight, SlidersHorizontal, User } from 'lucide-react';
import PlayerProfile from '../components/PlayerProfile';
import { usePlayers, usePositions, useLeagues } from '../hooks/usePlayers';
import { cn, getScoreColor, formatNumber } from '../lib/utils';
import { proxyImageUrl, isProxyFallback } from '../lib/api';
import type { PlayersQueryParams } from '../types/api';
import PlayerFiltersBar, {
  applyPlayerFilters,
  EMPTY_PLAYER_FILTERS,
  type PlayerFilterState,
} from '../components/PlayerFiltersBar';

function PlayerPhoto({ url, alt, size = 'sm' }: { url: string | null; alt: string; size?: 'sm' | 'lg' }) {
  const [failed, setFailed] = useState(false);
  const [src, setSrc] = useState(url);

  // Reset on url change
  if (url !== src && !failed) setSrc(url);
  if (url !== src && failed) { setSrc(url); setFailed(false); }

  if (!src || failed) {
    return (
      <div className={size === 'lg' ? 'player-photo-placeholder-lg' : 'player-photo-placeholder'}>
        <User size={size === 'lg' ? 24 : 16} strokeWidth={1.5} />
      </div>
    );
  }
  return (
    <img
      src={proxyImageUrl(src)!}
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

function ClubLogo({ url, alt, className = 'w-3.5 h-3.5 object-contain' }: { url: string | null; alt: string; className?: string }) {
  const [failed, setFailed] = useState(false);
  if (!url || failed) return null;
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

function getRecommendationBadge(score: number | null): { label: string; cls: string } | null {
  if (score == null) return null;
  if (score >= 72) return { label: 'Top Target', cls: 'badge-top-target' };
  if (score >= 62) return { label: 'Alta Prioridade', cls: 'badge-high-priority' };
  if (score >= 50) return { label: 'Monitorar', cls: 'badge-monitor' };
  if (score >= 38) return { label: 'Avaliar', cls: 'badge-evaluate' };
  return { label: 'Descartar', cls: 'badge-discard' };
}

export default function DashboardPage() {
  const [selectedPlayer, setSelectedPlayer] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [position, setPosition] = useState('');
  const [league, setLeague] = useState('');
  const [minAge, setMinAge] = useState('');
  const [maxAge, setMaxAge] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [clientFilters, setClientFilters] = useState<PlayerFilterState>(EMPTY_PLAYER_FILTERS);

  const { data: positions = [] } = usePositions();
  const { data: leagues = [] } = useLeagues();

  // Debounce search input
  const [debounceTimer, setDebounceTimer] = useState<ReturnType<typeof setTimeout> | null>(null);
  const handleSearchChange = (value: string) => {
    setSearch(value);
    if (debounceTimer) clearTimeout(debounceTimer);
    setDebounceTimer(setTimeout(() => setDebouncedSearch(value), 300));
  };

  const queryParams = useMemo<PlayersQueryParams>(() => ({
    search: debouncedSearch || undefined,
    position: position || undefined,
    league: league || undefined,
    min_age: minAge ? Number(minAge) : undefined,
    max_age: maxAge ? Number(maxAge) : undefined,
    min_minutes: 0,
    limit: 120,
  }), [debouncedSearch, position, league, minAge, maxAge]);

  const { data, isLoading, isFetching } = usePlayers(queryParams);
  // Sort players by SSP (scout_score) descending, then apply client-side refinements.
  const sortedPlayers = useMemo(() => {
    const list = data?.players ?? [];
    return [...list].sort((a, b) => (b.score ?? 0) - (a.score ?? 0));
  }, [data]);
  const players = useMemo(
    () => applyPlayerFilters(sortedPlayers, clientFilters),
    [sortedPlayers, clientFilters],
  );
  const availableNationalities = useMemo(() => {
    const set = new Set<string>();
    for (const p of sortedPlayers) if (p.nationality) set.add(p.nationality);
    return Array.from(set).sort((a, b) => a.localeCompare(b));
  }, [sortedPlayers]);
  const total = data?.total ?? 0;

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="page-title">Jogadores</h1>
        <p className="page-subtitle">
          <span className="stat-num font-semibold" style={{ color: 'var(--color-text-secondary)' }}>{total.toLocaleString('pt-BR')}</span>{' '}
          jogadores no banco de dados WyScout
        </p>
      </div>

      {/* Filters — compact horizontal bar */}
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="relative flex-1 min-w-[220px] max-w-sm">
            <Search
              size={15}
              strokeWidth={1.75}
              className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none"
              style={{ color: 'var(--color-text-muted)' }}
            />
            <input
              type="text"
              value={search}
              onChange={(e) => handleSearchChange(e.target.value)}
              placeholder="Buscar jogador..."
              className="w-full pl-10 pr-3 py-2.5 text-sm"
              style={{ fontFamily: 'var(--font-body)' }}
            />
          </div>

          <select
            value={position}
            onChange={(e) => setPosition(e.target.value)}
            className="px-3 py-2.5 text-sm cursor-pointer"
            style={{ fontFamily: 'var(--font-body)' }}
          >
            <option value="">Todas posições</option>
            {positions.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>

          <select
            value={league}
            onChange={(e) => setLeague(e.target.value)}
            className="px-3 py-2.5 text-sm cursor-pointer"
            style={{ fontFamily: 'var(--font-body)' }}
          >
            <option value="">Todas ligas</option>
            {leagues.map((l) => (
              <option key={l} value={l}>{l}</option>
            ))}
          </select>

          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-1.5 px-3 py-2.5 rounded-lg text-sm transition-all cursor-pointer font-medium"
            style={{
              background: showAdvanced ? 'var(--color-accent-glow)' : 'var(--color-surface-1)',
              border: `1px solid ${showAdvanced ? 'var(--color-accent-dim)' : 'var(--color-border-subtle)'}`,
              color: showAdvanced ? 'var(--color-accent)' : 'var(--color-text-secondary)',
              fontFamily: 'var(--font-body)',
            }}
          >
            <SlidersHorizontal size={14} strokeWidth={1.75} />
            Filtros
          </button>

          {/* Micro-animation: loading indicator when filters are being applied */}
          <AnimatePresence>
            {isFetching && !isLoading && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="filter-loading-spinner"
              />
            )}
          </AnimatePresence>
        </div>

        {/* Advanced filters row */}
        <AnimatePresence>
          {showAdvanced && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="flex flex-wrap items-end gap-3 overflow-hidden"
            >
              <div>
                <label className="block eyebrow mb-1.5">IDADE MIN</label>
                <input
                  type="number"
                  value={minAge}
                  onChange={(e) => setMinAge(e.target.value)}
                  placeholder="16"
                  className="w-20 px-3 py-2.5 text-sm stat-num"
                />
              </div>
              <div>
                <label className="block eyebrow mb-1.5">IDADE MAX</label>
                <input
                  type="number"
                  value={maxAge}
                  onChange={(e) => setMaxAge(e.target.value)}
                  placeholder="40"
                  className="w-20 px-3 py-2.5 text-sm stat-num"
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Client-side refinements (operate on the loaded window) */}
        <div className="pt-2">
          <PlayerFiltersBar
            value={clientFilters}
            onChange={setClientFilters}
            nationalities={availableNationalities}
            hiddenFields={['nameQuery', 'ageMin', 'ageMax']}
          />
        </div>
      </div>

      {/* Content: list + profile */}
      <div className="grid grid-cols-1 xl:grid-cols-[1fr_1.1fr] gap-5">
        {/* Player list */}
        <div className="card-glass overflow-hidden">
          <div
            className="px-5 py-3 flex items-center justify-between"
            style={{ borderBottom: '1px solid var(--color-border-active)' }}
          >
            <span className="eyebrow-strong">
              Resultados
            </span>
            <div className="flex items-center gap-2">
              {isFetching && !isLoading && (
                <div className="filter-loading-spinner" />
              )}
              <span className="text-[11px] stat-num font-semibold" style={{ color: 'var(--color-text-secondary)' }}>
                {total.toLocaleString('pt-BR')}
              </span>
            </div>
          </div>

          <div className="max-h-[65vh] overflow-y-auto">
            {isLoading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="flex items-center gap-3 px-5 py-3" style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                  <div className="skeleton w-10 h-10 rounded-full" />
                  <div className="flex-1 space-y-2">
                    <div className="skeleton h-4 w-40 rounded" />
                    <div className="skeleton h-3 w-24 rounded" />
                  </div>
                  <div className="skeleton h-5 w-12 rounded" />
                </div>
              ))
            ) : players.length === 0 ? (
              <div className="p-8 text-center text-xs" style={{ color: 'var(--color-text-muted)' }}>
                Nenhum jogador encontrado
              </div>
            ) : (
              players.map((player, i) => {
                const isSelected = selectedPlayer === (player.display_name || player.name);
                const badge = getRecommendationBadge(player.score);
                return (
                  <motion.button
                    key={player.id + '-' + i}
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: Math.min(i * 0.015, 0.3) }}
                    onClick={() => setSelectedPlayer(player.display_name || player.name)}
                    className="w-full flex items-center gap-3 px-5 py-3 text-left transition-all duration-200 cursor-pointer focus-ring-inset"
                    style={{
                      background: isSelected ? 'var(--color-accent-glow)' : i % 2 === 0 ? 'transparent' : 'var(--color-surface-0)',
                      borderBottom: '1px solid var(--color-border-subtle)',
                      borderLeft: isSelected ? '3px solid var(--color-accent)' : '3px solid transparent',
                    }}
                  >
                    {/* Player photo */}
                    <PlayerPhoto
                      url={player.photo_url}
                      alt={player.name}
                      size="sm"
                    />

                    {/* Rank */}
                    <span
                      className="text-[11px] stat-num font-semibold w-6 text-right"
                      style={{ color: i < 3 ? 'var(--color-accent)' : 'var(--color-text-faint)' }}
                    >
                      {i + 1}
                    </span>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-[14px] font-semibold truncate tracking-tight" style={{ color: 'var(--color-text-primary)' }}>
                          {player.name}
                        </span>
                        {player.team && (
                          <span className="text-[11px] shrink-0 flex items-center gap-1 truncate" style={{ color: 'var(--color-text-muted)' }}>
                            <ClubLogo url={player.club_logo} alt="" className="w-3.5 h-3.5 object-contain inline-block" />
                            {player.team}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        {player.position && (
                          <span
                            className="text-[10px] px-1.5 py-0.5 rounded font-semibold tracking-wide uppercase"
                            style={{
                              background: 'var(--color-surface-2)',
                              color: 'var(--color-text-secondary)',
                              border: '1px solid var(--color-border-subtle)',
                            }}
                          >
                            {player.position}
                          </span>
                        )}
                        {player.age && (
                          <span className="text-[11px] stat-num" style={{ color: 'var(--color-text-muted)' }}>
                            {player.age}a
                          </span>
                        )}
                        {player.minutes_played != null && (
                          <span className="text-[11px] stat-num" style={{ color: 'var(--color-text-faint)' }}>
                            {formatNumber(player.minutes_played)}′
                          </span>
                        )}
                      </div>
                    </div>

                    {/* SSP badge + recommendation */}
                    <div className="flex flex-col items-end gap-1 shrink-0">
                      {player.score != null && (
                        <span
                          className="text-[12px] stat-num font-bold px-2 py-0.5 rounded"
                          style={{
                            color: getScoreColor(player.score),
                            background: `${getScoreColor(player.score)}1F`,
                            border: `1px solid ${getScoreColor(player.score)}33`,
                          }}
                        >
                          {player.score.toFixed(1)}
                        </span>
                      )}
                      {badge && (
                        <span className={cn('text-[9px] px-1.5 py-0.5 rounded-full font-[var(--font-display)] tracking-wider uppercase', badge.cls)}>
                          {badge.label}
                        </span>
                      )}
                    </div>

                    <ChevronRight
                      size={14}
                      strokeWidth={1.75}
                      style={{ color: isSelected ? 'var(--color-accent)' : 'var(--color-text-faint)', opacity: 0.7 }}
                    />
                  </motion.button>
                );
              })
            )}
          </div>
        </div>

        {/* Player profile panel */}
        <div>
          {selectedPlayer ? (
            <PlayerProfile
              playerDisplayName={selectedPlayer}
              onClose={() => setSelectedPlayer(null)}
            />
          ) : (
            <div
              className="card-glass p-12 text-center"
              style={{ color: 'var(--color-text-muted)' }}
            >
              <Filter size={36} className="mx-auto mb-4 opacity-40" style={{ color: 'var(--color-text-faint)' }} />
              <p className="text-[15px] font-medium" style={{ color: 'var(--color-text-secondary)' }}>Selecione um jogador para ver o perfil completo</p>
              <p className="text-[12px] mt-1.5" style={{ color: 'var(--color-text-faint)' }}>Com radar de percentis, índices compostos e dados SkillCorner</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
