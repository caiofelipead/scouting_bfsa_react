import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Search, Filter, ChevronRight, SlidersHorizontal } from 'lucide-react';
import PlayerProfile from '../components/PlayerProfile';
import { usePlayers, usePositions, useLeagues } from '../hooks/usePlayers';
import { cn, getScoreColor, formatNumber } from '../lib/utils';
import type { PlayersQueryParams } from '../types/api';

export default function DashboardPage() {
  const [selectedPlayer, setSelectedPlayer] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [position, setPosition] = useState('');
  const [league, setLeague] = useState('');
  const [minAge, setMinAge] = useState('');
  const [maxAge, setMaxAge] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [debouncedSearch, setDebouncedSearch] = useState('');

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
    limit: 60,
  }), [debouncedSearch, position, league, minAge, maxAge]);

  const { data, isLoading, isFetching } = usePlayers(queryParams);
  const players = data?.players ?? [];
  const total = data?.total ?? 0;

  return (
    <div className="space-y-5">
      {/* Page header */}
      <div>
        <h1 className="font-[var(--font-display)] text-lg font-bold tracking-tight">Jogadores</h1>
        <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
          {total} jogadores no banco de dados WyScout
        </p>
      </div>

      {/* Filters */}
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px] max-w-sm">
            <Search
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2"
              style={{ color: 'var(--color-text-muted)' }}
            />
            <input
              type="text"
              value={search}
              onChange={(e) => handleSearchChange(e.target.value)}
              placeholder="Buscar jogador..."
              className="w-full pl-9 pr-3 py-2 rounded text-sm outline-none transition-colors"
              style={{
                background: 'var(--color-surface-1)',
                border: '1px solid var(--color-border-subtle)',
                color: 'var(--color-text-primary)',
                fontFamily: 'var(--font-body)',
              }}
            />
          </div>

          <select
            value={position}
            onChange={(e) => setPosition(e.target.value)}
            className="px-3 py-2 rounded text-sm cursor-pointer outline-none"
            style={{
              background: 'var(--color-surface-1)',
              border: '1px solid var(--color-border-subtle)',
              color: 'var(--color-text-secondary)',
              fontFamily: 'var(--font-body)',
            }}
          >
            <option value="">Todas posicoes</option>
            {positions.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>

          <select
            value={league}
            onChange={(e) => setLeague(e.target.value)}
            className="px-3 py-2 rounded text-sm cursor-pointer outline-none"
            style={{
              background: 'var(--color-surface-1)',
              border: '1px solid var(--color-border-subtle)',
              color: 'var(--color-text-secondary)',
              fontFamily: 'var(--font-body)',
            }}
          >
            <option value="">Todas ligas</option>
            {leagues.map((l) => (
              <option key={l} value={l}>{l}</option>
            ))}
          </select>

          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-1.5 px-3 py-2 rounded text-sm transition-colors cursor-pointer"
            style={{
              background: showAdvanced ? 'var(--color-accent-glow)' : 'var(--color-surface-1)',
              border: `1px solid ${showAdvanced ? 'var(--color-accent)' : 'var(--color-border-subtle)'}`,
              color: showAdvanced ? 'var(--color-accent)' : 'var(--color-text-secondary)',
              fontFamily: 'var(--font-body)',
            }}
          >
            <SlidersHorizontal size={13} />
            Filtros
          </button>
        </div>

        {/* Advanced filters row */}
        {showAdvanced && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="flex flex-wrap items-end gap-3 overflow-hidden"
          >
            <div>
              <label className="block text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>
                IDADE MIN
              </label>
              <input
                type="number"
                value={minAge}
                onChange={(e) => setMinAge(e.target.value)}
                placeholder="16"
                className="w-20 px-3 py-2 rounded text-sm outline-none"
                style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)' }}
              />
            </div>
            <div>
              <label className="block text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>
                IDADE MAX
              </label>
              <input
                type="number"
                value={maxAge}
                onChange={(e) => setMaxAge(e.target.value)}
                placeholder="40"
                className="w-20 px-3 py-2 rounded text-sm outline-none"
                style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)' }}
              />
            </div>
          </motion.div>
        )}
      </div>

      {/* Content: list + profile */}
      <div className="grid grid-cols-1 xl:grid-cols-[1fr_1.1fr] gap-5">
        {/* Player list */}
        <div className="card-glass rounded-lg overflow-hidden">
          <div
            className="px-4 py-2.5 flex items-center justify-between"
            style={{ borderBottom: '1px solid var(--color-border-subtle)' }}
          >
            <span
              className="text-[10px] font-[var(--font-display)] tracking-[0.15em] uppercase"
              style={{ color: 'var(--color-text-muted)' }}
            >
              RESULTADOS
            </span>
            <div className="flex items-center gap-2">
              {isFetching && !isLoading && (
                <div className="w-3 h-3 border border-current border-t-transparent rounded-full animate-spin" style={{ color: 'var(--color-accent)' }} />
              )}
              <span className="text-[10px] font-[var(--font-mono)]" style={{ color: 'var(--color-text-muted)' }}>
                {total}
              </span>
            </div>
          </div>

          <div className="max-h-[65vh] overflow-y-auto">
            {isLoading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="skeleton-table-row px-4">
                  <div /><div /><div /><div /><div />
                </div>
              ))
            ) : players.length === 0 ? (
              <div className="p-8 text-center text-xs" style={{ color: 'var(--color-text-muted)' }}>
                Nenhum jogador encontrado
              </div>
            ) : (
              players.map((player, i) => {
                const isSelected = selectedPlayer === (player.display_name || player.name);
                return (
                  <motion.button
                    key={player.id + '-' + i}
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.02 }}
                    onClick={() => setSelectedPlayer(player.display_name || player.name)}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors cursor-pointer"
                    style={{
                      background: isSelected ? 'var(--color-accent-glow)' : 'transparent',
                      borderBottom: '1px solid var(--color-border-subtle)',
                      borderLeft: isSelected ? '2px solid var(--color-accent)' : '2px solid transparent',
                    }}
                  >
                    {/* Rank */}
                    <span
                      className="text-[10px] font-[var(--font-mono)] w-6 text-right"
                      style={{ color: 'var(--color-text-muted)' }}
                    >
                      {i + 1}
                    </span>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium truncate" style={{ color: 'var(--color-text-primary)' }}>
                        {player.name}
                      </div>
                      <div className="flex items-center gap-2 mt-0.5">
                        {player.team && (
                          <span className="text-[10px] truncate" style={{ color: 'var(--color-text-muted)' }}>
                            {player.team}
                          </span>
                        )}
                        {player.position && (
                          <span
                            className="text-[9px] px-1 py-0.5 rounded"
                            style={{
                              background: 'rgba(255,255,255,0.04)',
                              color: 'var(--color-text-muted)',
                              border: '1px solid var(--color-border-subtle)',
                            }}
                          >
                            {player.position}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Score badge */}
                    {player.score != null && (
                      <span
                        className="text-[10px] font-[var(--font-mono)] font-bold px-1.5 py-0.5 rounded"
                        style={{ color: getScoreColor(player.score), background: `${getScoreColor(player.score)}15` }}
                      >
                        {player.score.toFixed(1)}
                      </span>
                    )}

                    {/* Minutes */}
                    {player.minutes_played && (
                      <span
                        className="text-[10px] font-[var(--font-mono)]"
                        style={{ color: 'var(--color-text-muted)' }}
                      >
                        {formatNumber(player.minutes_played)}'
                      </span>
                    )}

                    {/* Age */}
                    {player.age && (
                      <span
                        className="text-[10px] font-[var(--font-mono)] w-6 text-right"
                        style={{ color: 'var(--color-text-muted)' }}
                      >
                        {player.age}
                      </span>
                    )}

                    <ChevronRight
                      size={12}
                      style={{ color: isSelected ? 'var(--color-accent)' : 'var(--color-text-muted)', opacity: 0.5 }}
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
              className="card-glass rounded-lg p-12 text-center"
              style={{ color: 'var(--color-text-muted)' }}
            >
              <Filter size={32} className="mx-auto mb-3 opacity-30" />
              <p className="text-sm">Selecione um jogador para ver o perfil completo</p>
              <p className="text-xs mt-1 opacity-60">Com radar de percentis, indices compostos e dados SkillCorner</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
