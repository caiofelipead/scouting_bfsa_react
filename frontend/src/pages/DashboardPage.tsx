import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Search, Filter, ChevronRight } from 'lucide-react';
import PlayerProfile from '../components/PlayerProfile';
import { usePlayers } from '../hooks/usePlayers';
import api from '../lib/api';
import { cn, getScoreColor, formatNumber } from '../lib/utils';

export default function DashboardPage() {
  const { players, total, loading, fetchPlayers } = usePlayers();
  const [selectedPlayer, setSelectedPlayer] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [position, setPosition] = useState('');
  const [league, setLeague] = useState('');
  const [positions, setPositions] = useState<string[]>([]);
  const [leagues, setLeagues] = useState<string[]>([]);
  const isFirstMount = useRef(true);

  useEffect(() => {
    api.get('/config/positions').then((res) => setPositions(res.data.positions)).catch(() => {});
    api.get('/config/leagues').then((res) => setLeagues(res.data.leagues)).catch(() => {});
  }, []);

  // Fetch immediately on mount (no debounce), debounce only on filter changes
  useEffect(() => {
    const params = { search, position: position || undefined, league: league || undefined, min_minutes: 0, limit: 60 };

    if (isFirstMount.current) {
      isFirstMount.current = false;
      fetchPlayers(params);
      return;
    }

    const timeout = setTimeout(() => fetchPlayers(params), 300);
    return () => clearTimeout(timeout);
  }, [search, position, league, fetchPlayers]);

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
            onChange={(e) => setSearch(e.target.value)}
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
            <span className="text-[10px] font-[var(--font-mono)]" style={{ color: 'var(--color-text-muted)' }}>
              {total}
            </span>
          </div>

          <div className="max-h-[65vh] overflow-y-auto">
            {loading || (players.length === 0 && total === 0 && isFirstMount.current) ? (
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
                const isSelected = selectedPlayer === player.display_name;
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
