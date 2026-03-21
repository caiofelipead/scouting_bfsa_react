import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  Globe,
  Trophy,
  ChevronDown,
  Loader2,
  Users,
  Calendar,
  Target,
  Award,
  Shield,
  AlertTriangle,
} from 'lucide-react';
import {
  useApiFootballCountries,
  useApiFootballLeagues,
  useApiFootballStandings,
  useApiFootballTopScorers,
  useApiFootballTopAssists,
  useApiFootballFixtures,
  useApiFootballSquads,
} from '../hooks/useApiFootball';
import { proxyImageUrl } from '../lib/api';
import type {
  ApiFootballStandingEntry,
  ApiFootballPlayerEntry,
  ApiFootballFixture,
  ApiFootballSquad,
} from '../types/api';

type SubTab = 'standings' | 'scorers' | 'fixtures' | 'squads';

// ── Helpers ──

function FormDots({ form }: { form: string | null }) {
  if (!form) return null;
  return (
    <div className="flex gap-0.5">
      {form.split('').map((c, i) => (
        <div
          key={i}
          className="w-[7px] h-[7px] rounded-full"
          style={{
            background:
              c === 'W' ? '#22c55e' : c === 'D' ? '#eab308' : c === 'L' ? '#ef4444' : 'var(--color-text-muted)',
          }}
          title={c === 'W' ? 'Vitória' : c === 'D' ? 'Empate' : 'Derrota'}
        />
      ))}
    </div>
  );
}

function SmallImg({ src, alt, size = 20 }: { src: string | null | undefined; alt: string; size?: number }) {
  const proxied = proxyImageUrl(src ?? null);
  if (!proxied) return <div className="rounded" style={{ width: size, height: size, background: 'var(--color-surface-elevated)' }} />;
  return <img src={proxied} alt={alt} width={size} height={size} className="object-contain" loading="lazy" />;
}

// ── Standings Table ──

function StandingsView({ standings }: { standings: ApiFootballStandingEntry[][] }) {
  if (!standings.length) {
    return <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>Nenhuma classificação encontrada.</p>;
  }

  return (
    <div className="space-y-6">
      {standings.map((group, gi) => (
        <div key={gi} className="glass-panel overflow-hidden">
          {standings.length > 1 && group[0]?.group && (
            <div
              className="px-4 py-2 text-[10px] uppercase tracking-widest font-semibold"
              style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-display)', borderBottom: '1px solid var(--color-border-subtle)' }}
            >
              {group[0].group}
            </div>
          )}
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
                  <th className="text-left px-3 py-2 font-semibold" style={{ color: 'var(--color-text-muted)', width: 30 }}>#</th>
                  <th className="text-left px-3 py-2 font-semibold" style={{ color: 'var(--color-text-muted)' }}>Time</th>
                  <th className="text-center px-2 py-2 font-semibold" style={{ color: 'var(--color-text-muted)' }}>J</th>
                  <th className="text-center px-2 py-2 font-semibold" style={{ color: 'var(--color-text-muted)' }}>V</th>
                  <th className="text-center px-2 py-2 font-semibold" style={{ color: 'var(--color-text-muted)' }}>E</th>
                  <th className="text-center px-2 py-2 font-semibold" style={{ color: 'var(--color-text-muted)' }}>D</th>
                  <th className="text-center px-2 py-2 font-semibold" style={{ color: 'var(--color-text-muted)' }}>GP</th>
                  <th className="text-center px-2 py-2 font-semibold" style={{ color: 'var(--color-text-muted)' }}>GC</th>
                  <th className="text-center px-2 py-2 font-semibold" style={{ color: 'var(--color-text-muted)' }}>SG</th>
                  <th className="text-center px-2 py-2 font-semibold" style={{ color: 'var(--color-text-muted)' }}>Pts</th>
                  <th className="text-center px-2 py-2 font-semibold hidden sm:table-cell" style={{ color: 'var(--color-text-muted)' }}>Forma</th>
                </tr>
              </thead>
              <tbody>
                {group.map((row) => (
                  <tr
                    key={row.team.id}
                    className="transition-colors hover:bg-white/5"
                    style={{ borderBottom: '1px solid var(--color-border-subtle)' }}
                  >
                    <td className="px-3 py-2 font-mono font-bold" style={{ color: 'var(--color-text-muted)' }}>
                      <div className="flex items-center gap-1">
                        {row.description && (
                          <div
                            className="w-[3px] h-4 rounded-full"
                            style={{
                              background: row.description.toLowerCase().includes('promotion') || row.description.toLowerCase().includes('champions')
                                ? '#22c55e'
                                : row.description.toLowerCase().includes('relegation')
                                ? '#ef4444'
                                : row.description.toLowerCase().includes('europa') || row.description.toLowerCase().includes('conference') || row.description.toLowerCase().includes('copa')
                                ? '#3b82f6'
                                : 'var(--color-text-muted)',
                            }}
                          />
                        )}
                        {row.rank}
                      </div>
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex items-center gap-2">
                        <SmallImg src={row.team.logo} alt={row.team.name} size={18} />
                        <span className="font-medium text-[13px]" style={{ color: 'var(--color-text-primary)' }}>
                          {row.team.name}
                        </span>
                      </div>
                    </td>
                    <td className="text-center px-2 py-2" style={{ color: 'var(--color-text-secondary)' }}>{row.all.played}</td>
                    <td className="text-center px-2 py-2" style={{ color: '#22c55e' }}>{row.all.win}</td>
                    <td className="text-center px-2 py-2" style={{ color: '#eab308' }}>{row.all.draw}</td>
                    <td className="text-center px-2 py-2" style={{ color: '#ef4444' }}>{row.all.lose}</td>
                    <td className="text-center px-2 py-2" style={{ color: 'var(--color-text-secondary)' }}>{row.all.goals.for}</td>
                    <td className="text-center px-2 py-2" style={{ color: 'var(--color-text-secondary)' }}>{row.all.goals.against}</td>
                    <td className="text-center px-2 py-2 font-mono font-bold" style={{ color: row.goalsDiff > 0 ? '#22c55e' : row.goalsDiff < 0 ? '#ef4444' : 'var(--color-text-secondary)' }}>
                      {row.goalsDiff > 0 ? `+${row.goalsDiff}` : row.goalsDiff}
                    </td>
                    <td className="text-center px-2 py-2 font-mono font-bold" style={{ color: 'var(--color-text-primary)' }}>{row.points}</td>
                    <td className="text-center px-2 py-2 hidden sm:table-cell">
                      <FormDots form={row.form} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Top Scorers / Assists Table ──

function PlayerRankingView({
  players,
  type,
}: {
  players: ApiFootballPlayerEntry[];
  type: 'goals' | 'assists';
}) {
  if (!players.length) {
    return <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>Nenhum dado encontrado.</p>;
  }

  return (
    <div className="glass-panel overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr style={{ borderBottom: '1px solid var(--color-border-subtle)' }}>
              <th className="text-left px-3 py-2 font-semibold" style={{ color: 'var(--color-text-muted)', width: 30 }}>#</th>
              <th className="text-left px-3 py-2 font-semibold" style={{ color: 'var(--color-text-muted)' }}>Jogador</th>
              <th className="text-left px-3 py-2 font-semibold hidden sm:table-cell" style={{ color: 'var(--color-text-muted)' }}>Time</th>
              <th className="text-center px-2 py-2 font-semibold" style={{ color: 'var(--color-text-muted)' }}>Jogos</th>
              <th className="text-center px-2 py-2 font-semibold" style={{ color: 'var(--color-text-muted)' }}>Min</th>
              <th className="text-center px-2 py-2 font-semibold" style={{ color: 'var(--color-accent)' }}>
                {type === 'goals' ? 'Gols' : 'Assist.'}
              </th>
              <th className="text-center px-2 py-2 font-semibold hidden md:table-cell" style={{ color: 'var(--color-text-muted)' }}>
                {type === 'goals' ? 'Assist.' : 'Gols'}
              </th>
              <th className="text-center px-2 py-2 font-semibold hidden md:table-cell" style={{ color: 'var(--color-text-muted)' }}>Nota</th>
            </tr>
          </thead>
          <tbody>
            {players.map((entry, i) => {
              const stat = entry.statistics[0];
              if (!stat) return null;
              const mainVal = type === 'goals' ? stat.goals.total : stat.goals.assists;
              const secVal = type === 'goals' ? stat.goals.assists : stat.goals.total;
              return (
                <tr
                  key={entry.player.id}
                  className="transition-colors hover:bg-white/5"
                  style={{ borderBottom: '1px solid var(--color-border-subtle)' }}
                >
                  <td className="px-3 py-2 font-mono font-bold" style={{ color: 'var(--color-text-muted)' }}>{i + 1}</td>
                  <td className="px-3 py-2">
                    <div className="flex items-center gap-2">
                      <SmallImg src={entry.player.photo} alt={entry.player.name} size={24} />
                      <div>
                        <div className="font-medium text-[13px]" style={{ color: 'var(--color-text-primary)' }}>
                          {entry.player.name}
                        </div>
                        <div className="text-[10px] sm:hidden" style={{ color: 'var(--color-text-muted)' }}>
                          {stat.team.name}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-3 py-2 hidden sm:table-cell">
                    <div className="flex items-center gap-1.5">
                      <SmallImg src={stat.team.logo} alt={stat.team.name} size={16} />
                      <span style={{ color: 'var(--color-text-secondary)' }}>{stat.team.name}</span>
                    </div>
                  </td>
                  <td className="text-center px-2 py-2" style={{ color: 'var(--color-text-secondary)' }}>{stat.games.appearences ?? '-'}</td>
                  <td className="text-center px-2 py-2" style={{ color: 'var(--color-text-secondary)' }}>{stat.games.minutes ?? '-'}</td>
                  <td className="text-center px-2 py-2 font-mono font-bold" style={{ color: 'var(--color-accent)' }}>{mainVal ?? 0}</td>
                  <td className="text-center px-2 py-2 font-mono hidden md:table-cell" style={{ color: 'var(--color-text-secondary)' }}>{secVal ?? 0}</td>
                  <td className="text-center px-2 py-2 font-mono hidden md:table-cell" style={{ color: 'var(--color-text-secondary)' }}>
                    {stat.games.rating ? parseFloat(stat.games.rating).toFixed(2) : '-'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Fixtures View ──

function FixturesView({ fixtures }: { fixtures: ApiFootballFixture[] }) {
  if (!fixtures.length) {
    return <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>Nenhum jogo encontrado.</p>;
  }

  const grouped = useMemo(() => {
    const map = new Map<string, ApiFootballFixture[]>();
    for (const f of fixtures) {
      const round = f.league.round;
      if (!map.has(round)) map.set(round, []);
      map.get(round)!.push(f);
    }
    return map;
  }, [fixtures]);

  return (
    <div className="space-y-4">
      {[...grouped.entries()].map(([round, matches]) => (
        <div key={round} className="glass-panel p-4">
          <div
            className="text-[10px] uppercase tracking-widest font-semibold mb-3"
            style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-display)' }}
          >
            {round}
          </div>
          <div className="space-y-2">
            {matches.map((m) => {
              const isFinished = m.fixture.status.short === 'FT' || m.fixture.status.short === 'AET' || m.fixture.status.short === 'PEN';
              const isLive = ['1H', '2H', 'HT', 'ET', 'P', 'BT', 'LIVE'].includes(m.fixture.status.short);
              const dateStr = new Date(m.fixture.date).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: '2-digit' });
              const timeStr = new Date(m.fixture.date).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });

              return (
                <div
                  key={m.fixture.id}
                  className="flex items-center gap-3 py-2 px-3 rounded-lg transition-colors hover:bg-white/5"
                  style={{ borderBottom: '1px solid var(--color-border-subtle)' }}
                >
                  {/* Date */}
                  <div className="text-[10px] font-mono w-16 shrink-0 text-center" style={{ color: 'var(--color-text-muted)' }}>
                    <div>{dateStr}</div>
                    <div>{timeStr}</div>
                  </div>

                  {/* Home */}
                  <div className="flex-1 flex items-center justify-end gap-2">
                    <span className="text-[13px] font-medium text-right" style={{ color: 'var(--color-text-primary)' }}>
                      {m.teams.home.name}
                    </span>
                    <SmallImg src={m.teams.home.logo} alt={m.teams.home.name} size={20} />
                  </div>

                  {/* Score */}
                  <div
                    className="w-16 text-center font-mono font-bold text-sm rounded px-2 py-1"
                    style={{
                      background: isLive ? 'rgba(239, 68, 68, 0.15)' : 'var(--color-surface-elevated)',
                      color: isLive ? '#ef4444' : isFinished ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
                    }}
                  >
                    {isFinished || isLive
                      ? `${m.goals.home ?? 0} - ${m.goals.away ?? 0}`
                      : 'vs'}
                  </div>

                  {/* Away */}
                  <div className="flex-1 flex items-center gap-2">
                    <SmallImg src={m.teams.away.logo} alt={m.teams.away.name} size={20} />
                    <span className="text-[13px] font-medium" style={{ color: 'var(--color-text-primary)' }}>
                      {m.teams.away.name}
                    </span>
                  </div>

                  {/* Status badge */}
                  {isLive && (
                    <span className="text-[9px] font-bold px-1.5 py-0.5 rounded" style={{ background: 'rgba(239, 68, 68, 0.2)', color: '#ef4444' }}>
                      {m.fixture.status.elapsed ? `${m.fixture.status.elapsed}'` : 'AO VIVO'}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Squads View ──

function SquadsView({ squads }: { squads: ApiFootballSquad[] }) {
  if (!squads.length) {
    return <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>Selecione um time para ver o elenco.</p>;
  }

  const squad = squads[0];
  const positionOrder = ['Goalkeeper', 'Defender', 'Midfielder', 'Attacker'];
  const positionLabels: Record<string, string> = {
    Goalkeeper: 'Goleiros',
    Defender: 'Defensores',
    Midfielder: 'Meio-campistas',
    Attacker: 'Atacantes',
  };

  const grouped = useMemo(() => {
    const map = new Map<string, typeof squad.players>();
    for (const pos of positionOrder) {
      map.set(pos, []);
    }
    for (const p of squad.players) {
      const list = map.get(p.position) ?? map.get('Attacker')!;
      list.push(p);
    }
    return map;
  }, [squad]);

  return (
    <div className="glass-panel p-5">
      <div className="flex items-center gap-2 mb-4">
        <SmallImg src={squad.team.logo} alt={squad.team.name} size={24} />
        <h3 className="font-semibold text-sm" style={{ color: 'var(--color-text-primary)' }}>{squad.team.name}</h3>
        <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ background: 'var(--color-surface-elevated)', color: 'var(--color-text-muted)' }}>
          {squad.players.length} jogadores
        </span>
      </div>
      <div className="space-y-4">
        {positionOrder.map((pos) => {
          const players = grouped.get(pos);
          if (!players?.length) return null;
          return (
            <div key={pos}>
              <div
                className="text-[10px] uppercase tracking-widest font-semibold mb-2"
                style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-display)' }}
              >
                {positionLabels[pos] ?? pos}
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                {players.map((p) => (
                  <div
                    key={p.id}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg"
                    style={{ background: 'var(--color-surface-elevated)' }}
                  >
                    <SmallImg src={p.photo} alt={p.name} size={28} />
                    <div className="min-w-0">
                      <div className="text-[12px] font-medium truncate" style={{ color: 'var(--color-text-primary)' }}>
                        {p.name}
                      </div>
                      <div className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>
                        {p.number ? `#${p.number}` : ''} {p.age ? `${p.age} anos` : ''}
                      </div>
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

// ── Dropdown component ──

function Dropdown({
  label,
  value,
  onChange,
  options,
  disabled,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
  disabled?: boolean;
}) {
  return (
    <div className="relative">
      <label
        className="block text-[9px] uppercase tracking-widest font-semibold mb-1"
        style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-display)' }}
      >
        {label}
      </label>
      <div className="relative">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          className="w-full appearance-none rounded-lg px-3 py-2 pr-8 text-sm font-medium cursor-pointer disabled:opacity-40"
          style={{
            background: 'var(--color-surface-elevated)',
            color: 'var(--color-text-primary)',
            border: '1px solid var(--color-border-subtle)',
          }}
        >
          {options.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <ChevronDown
          size={14}
          className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none"
          style={{ color: 'var(--color-text-muted)' }}
        />
      </div>
    </div>
  );
}

// ── Main Page ──

// Pre-defined leagues for quick access (Brazilian + top European)
const QUICK_LEAGUES = [
  { id: 71, name: 'Série A', country: 'Brazil', season: 2025 },
  { id: 72, name: 'Série B', country: 'Brazil', season: 2025 },
  { id: 73, name: 'Copa do Brasil', country: 'Brazil', season: 2025 },
  { id: 75, name: 'Série C', country: 'Brazil', season: 2025 },
  { id: 39, name: 'Premier League', country: 'England', season: 2024 },
  { id: 140, name: 'La Liga', country: 'Spain', season: 2024 },
  { id: 135, name: 'Serie A', country: 'Italy', season: 2024 },
  { id: 78, name: 'Bundesliga', country: 'Germany', season: 2024 },
  { id: 61, name: 'Ligue 1', country: 'France', season: 2024 },
  { id: 94, name: 'Primeira Liga', country: 'Portugal', season: 2024 },
  { id: 88, name: 'Eredivisie', country: 'Netherlands', season: 2024 },
  { id: 128, name: 'Liga Profesional', country: 'Argentina', season: 2025 },
];

export default function ApiFootballPage() {
  const [selectedLeagueId, setSelectedLeagueId] = useState(71); // Default: Série A Brazil
  const [selectedSeason, setSelectedSeason] = useState(2025);
  const [activeSubTab, setActiveSubTab] = useState<SubTab>('standings');
  const [selectedTeamId, setSelectedTeamId] = useState(0);
  const [scorerTab, setScorerTab] = useState<'goals' | 'assists'>('goals');

  // Update season when league changes
  const handleLeagueChange = (val: string) => {
    const leagueId = parseInt(val);
    setSelectedLeagueId(leagueId);
    const league = QUICK_LEAGUES.find((l) => l.id === leagueId);
    if (league) setSelectedSeason(league.season);
    setSelectedTeamId(0);
  };

  // Queries
  const standings = useApiFootballStandings(selectedLeagueId, selectedSeason);
  const topScorers = useApiFootballTopScorers(selectedLeagueId, selectedSeason);
  const topAssists = useApiFootballTopAssists(selectedLeagueId, selectedSeason);
  const fixtures = useApiFootballFixtures({ league: selectedLeagueId, season: selectedSeason });
  const squads = useApiFootballSquads(selectedTeamId);

  // Extract teams from standings for squad selector
  const teamsFromStandings = useMemo(() => {
    if (!standings.data?.length) return [];
    return standings.data.flat().map((s) => ({ id: s.team.id, name: s.team.name, logo: s.team.logo }));
  }, [standings.data]);

  const isLoading =
    (activeSubTab === 'standings' && standings.isLoading) ||
    (activeSubTab === 'scorers' && (topScorers.isLoading || topAssists.isLoading)) ||
    (activeSubTab === 'fixtures' && fixtures.isLoading) ||
    (activeSubTab === 'squads' && squads.isLoading && selectedTeamId > 0);

  const isError =
    (activeSubTab === 'standings' && standings.isError) ||
    (activeSubTab === 'scorers' && (topScorers.isError || topAssists.isError)) ||
    (activeSubTab === 'fixtures' && fixtures.isError);

  const subTabs: { id: SubTab; label: string; icon: React.ReactNode }[] = [
    { id: 'standings', label: 'Classificação', icon: <Trophy size={14} /> },
    { id: 'scorers', label: 'Artilheiros', icon: <Target size={14} /> },
    { id: 'fixtures', label: 'Jogos', icon: <Calendar size={14} /> },
    { id: 'squads', label: 'Elencos', icon: <Users size={14} /> },
  ];

  const selectedLeague = QUICK_LEAGUES.find((l) => l.id === selectedLeagueId);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Globe size={18} style={{ color: 'var(--color-accent)' }} />
          <h1
            className="text-lg font-bold tracking-tight"
            style={{ color: 'var(--color-text-primary)', fontFamily: 'var(--font-display)' }}
          >
            API-Football
          </h1>
        </div>
        <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
          Dados em tempo real de ligas, classificações, artilheiros, jogos e elencos.
        </p>
      </div>

      {/* Controls */}
      <div className="glass-panel p-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <Dropdown
            label="Liga"
            value={String(selectedLeagueId)}
            onChange={handleLeagueChange}
            options={QUICK_LEAGUES.map((l) => ({
              value: String(l.id),
              label: `${l.country} — ${l.name}`,
            }))}
          />
          <Dropdown
            label="Temporada"
            value={String(selectedSeason)}
            onChange={(v) => setSelectedSeason(parseInt(v))}
            options={[2025, 2024, 2023, 2022, 2021, 2020].map((y) => ({
              value: String(y),
              label: String(y),
            }))}
          />
          {activeSubTab === 'squads' && (
            <Dropdown
              label="Time"
              value={String(selectedTeamId)}
              onChange={(v) => setSelectedTeamId(parseInt(v))}
              options={[
                { value: '0', label: 'Selecione um time...' },
                ...teamsFromStandings.map((t) => ({ value: String(t.id), label: t.name })),
              ]}
              disabled={!teamsFromStandings.length}
            />
          )}
        </div>
      </div>

      {/* Sub-tabs */}
      <div className="flex gap-1 p-1 rounded-lg" style={{ background: 'var(--color-surface-elevated)' }}>
        {subTabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveSubTab(tab.id)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-md text-xs font-medium transition-all cursor-pointer flex-1 justify-center"
            style={{
              background: activeSubTab === tab.id ? 'var(--color-accent-glow)' : 'transparent',
              color: activeSubTab === tab.id ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
            }}
          >
            <span style={{ color: activeSubTab === tab.id ? 'var(--color-accent)' : 'var(--color-text-muted)' }}>
              {tab.icon}
            </span>
            <span className="hidden sm:inline">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Loading / Error states */}
      {isLoading && (
        <div className="flex items-center justify-center py-16 gap-3">
          <Loader2 size={20} className="animate-spin" style={{ color: 'var(--color-accent)' }} />
          <span className="text-sm" style={{ color: 'var(--color-text-muted)' }}>Carregando dados...</span>
        </div>
      )}

      {isError && (
        <div className="glass-panel p-6 flex items-center gap-3">
          <AlertTriangle size={18} style={{ color: '#ef4444' }} />
          <div>
            <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>Erro ao carregar dados</p>
            <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
              Verifique se a chave API_FOOTBALL_KEY está configurada no backend.
            </p>
          </div>
        </div>
      )}

      {/* Content */}
      {!isLoading && !isError && (
        <motion.div
          key={activeSubTab}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
        >
          {activeSubTab === 'standings' && standings.data && (
            <StandingsView standings={standings.data} />
          )}

          {activeSubTab === 'scorers' && (
            <div className="space-y-4">
              {/* Goal / Assist toggle */}
              <div className="flex gap-1 p-1 rounded-lg w-fit" style={{ background: 'var(--color-surface-elevated)' }}>
                <button
                  onClick={() => setScorerTab('goals')}
                  className="flex items-center gap-1.5 px-4 py-1.5 rounded-md text-xs font-medium transition-all cursor-pointer"
                  style={{
                    background: scorerTab === 'goals' ? 'var(--color-accent-glow)' : 'transparent',
                    color: scorerTab === 'goals' ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
                  }}
                >
                  <Target size={12} style={{ color: scorerTab === 'goals' ? 'var(--color-accent)' : 'var(--color-text-muted)' }} />
                  Artilheiros
                </button>
                <button
                  onClick={() => setScorerTab('assists')}
                  className="flex items-center gap-1.5 px-4 py-1.5 rounded-md text-xs font-medium transition-all cursor-pointer"
                  style={{
                    background: scorerTab === 'assists' ? 'var(--color-accent-glow)' : 'transparent',
                    color: scorerTab === 'assists' ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
                  }}
                >
                  <Award size={12} style={{ color: scorerTab === 'assists' ? 'var(--color-accent)' : 'var(--color-text-muted)' }} />
                  Garçons
                </button>
              </div>

              {scorerTab === 'goals' && topScorers.data && (
                <PlayerRankingView players={topScorers.data} type="goals" />
              )}
              {scorerTab === 'assists' && topAssists.data && (
                <PlayerRankingView players={topAssists.data} type="assists" />
              )}
            </div>
          )}

          {activeSubTab === 'fixtures' && fixtures.data && (
            <FixturesView fixtures={fixtures.data} />
          )}

          {activeSubTab === 'squads' && (
            selectedTeamId > 0 && squads.data ? (
              <SquadsView squads={squads.data} />
            ) : (
              <div className="glass-panel p-8 text-center">
                <Users size={32} className="mx-auto mb-3" style={{ color: 'var(--color-text-muted)' }} />
                <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
                  Selecione um time acima para visualizar o elenco completo.
                </p>
              </div>
            )
          )}
        </motion.div>
      )}
    </div>
  );
}
