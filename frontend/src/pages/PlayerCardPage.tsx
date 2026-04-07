import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  User,
  AlertCircle,
  Zap,
  Target,
  Crosshair,
  TrendingUp,
  Hand,
  Dribbble,
  Shield,
  Swords,
  Footprints,
  Building2,
  Clock,
  Flag,
  CalendarDays,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';
import { proxyImageUrl } from '../lib/api';
import { usePlayers, usePositions, usePlayerProfile } from '../hooks/usePlayers';
import { getScoreColor } from '../lib/utils';
import { getFlagUrl } from '../lib/countryFlags';
import type { IndicesResponse } from '../types/api';

// ── Percentile bar color (matches Streamlit reference) ──────────────

function getPercentileColor(p: number): string {
  if (p >= 90) return '#00e5a0';  // bright green/teal
  if (p >= 70) return '#2dd4a0';  // green
  if (p >= 50) return '#4ade80';  // lighter green
  if (p >= 30) return '#facc15';  // yellow
  if (p >= 10) return '#f97316';  // orange
  return '#ef4444';               // red
}

// ── Category icon mapping ───────────────────────────────────────────

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  'Finalização': <Crosshair size={16} strokeWidth={1.5} />,
  '1x1 Ofensivo': <Swords size={16} strokeWidth={1.5} />,
  'Jogo Aéreo': <TrendingUp size={16} strokeWidth={1.5} />,
  'Movimentação': <Footprints size={16} strokeWidth={1.5} />,
  'Link-up Play': <Hand size={16} strokeWidth={1.5} />,
  'Pressing': <Shield size={16} strokeWidth={1.5} />,
  'Passes Quebrando Linhas': <Zap size={16} strokeWidth={1.5} />,
  'Criação': <Zap size={16} strokeWidth={1.5} />,
  'Progressão': <TrendingUp size={16} strokeWidth={1.5} />,
  'Cruzamentos': <Target size={16} strokeWidth={1.5} />,
  'Trabalho Defensivo': <Shield size={16} strokeWidth={1.5} />,
  'Qualidade de Passe': <Target size={16} strokeWidth={1.5} />,
  'Duelos': <Swords size={16} strokeWidth={1.5} />,
  'Recuperação': <Shield size={16} strokeWidth={1.5} />,
  'Construção': <Building2 size={16} strokeWidth={1.5} />,
  'Cobertura': <Shield size={16} strokeWidth={1.5} />,
  'Disciplina': <AlertCircle size={16} strokeWidth={1.5} />,
};

function getCategoryIcon(name: string) {
  return CATEGORY_ICONS[name] || <Zap size={16} strokeWidth={1.5} />;
}

// ── Player photo component ──────────────────────────────────────────

function PlayerPhoto({ url, alt }: { url: string | null; alt: string }) {
  const [failed, setFailed] = useState(false);
  const [prevUrl, setPrevUrl] = useState(url);
  if (url !== prevUrl) { setPrevUrl(url); setFailed(false); }
  if (!url || failed) {
    return (
      <div className="w-24 h-24 rounded-full flex items-center justify-center" style={{ background: 'var(--color-surface-2)', border: '3px solid var(--color-border-active)' }}>
        <User size={32} strokeWidth={1.5} style={{ color: 'var(--color-text-muted)' }} />
      </div>
    );
  }
  return (
    <img
      src={proxyImageUrl(url)!}
      alt={alt}
      className="w-24 h-24 rounded-full object-cover flex-shrink-0"
      style={{ border: '3px solid var(--color-accent)' }}
      referrerPolicy="no-referrer"
      onError={() => setFailed(true)}
    />
  );
}

// ── Info pill component (nation, league, club, age, minutes) ────────

function InfoPill({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg" style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)' }}>
      <span style={{ color: 'var(--color-text-muted)' }}>{icon}</span>
      <div>
        <div className="text-[9px] uppercase tracking-wider" style={{ color: 'var(--color-text-muted)' }}>{label}</div>
        <div className="text-xs font-semibold" style={{ color: 'var(--color-text-primary)' }}>{value}</div>
      </div>
    </div>
  );
}

// ── Percentile metric row ───────────────────────────────────────────

function MetricRow({ name, value, percentile, index }: { name: string; value: number | null; percentile: number; index: number }) {
  const color = getPercentileColor(percentile);
  const displayName = name
    .replace('/90', '')
    .replace(', %', '%')
    .replace('Duelos aérios', 'Duelos aéreos');

  return (
    <motion.div
      className="flex items-center gap-3 py-1.5"
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.03, duration: 0.3 }}
    >
      <div className="flex-1 min-w-0">
        <span className="text-[11px] font-[var(--font-mono)] uppercase tracking-wide truncate block" style={{ color: 'var(--color-text-secondary)' }}>
          {displayName}
        </span>
      </div>
      <div className="w-14 text-right">
        <span className="text-[11px] font-[var(--font-mono)] font-medium" style={{ color: 'var(--color-text-secondary)' }}>
          {value != null ? value.toFixed(2) : '—'}
        </span>
      </div>
      <div className="w-28 h-2 rounded-full overflow-hidden flex-shrink-0" style={{ background: 'var(--color-surface-2)' }}>
        <motion.div
          className="h-full rounded-full"
          style={{ background: color }}
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(Math.max(percentile, 1), 100)}%` }}
          transition={{ duration: 0.5, delay: 0.1 + index * 0.03 }}
        />
      </div>
      <div className="w-8 text-right">
        <span className="text-[11px] font-[var(--font-mono)] font-bold" style={{ color }}>
          {Math.round(percentile)}
        </span>
      </div>
    </motion.div>
  );
}

// ── Category section ────────────────────────────────────────────────

function CategorySection({ name, score, metrics, startIndex }: {
  name: string;
  score: number;
  metrics: { metric: string; value: number | null; percentile: number }[];
  startIndex: number;
}) {
  const scoreColor = getPercentileColor(score);

  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2 mb-2">
        <span style={{ color: scoreColor }}>{getCategoryIcon(name)}</span>
        <span className="text-xs font-[var(--font-display)] font-bold tracking-wide uppercase" style={{ color: scoreColor }}>
          {name}
        </span>
        <span
          className="text-[11px] font-[var(--font-mono)] font-bold px-2 py-0.5 rounded-full"
          style={{ background: `${scoreColor}20`, color: scoreColor }}
        >
          {Math.round(score)}
        </span>
      </div>
      {metrics.map((m, i) => (
        <MetricRow
          key={m.metric}
          name={m.metric}
          value={m.value}
          percentile={m.percentile}
          index={startIndex + i}
        />
      ))}
    </div>
  );
}

// ── Main page component ─────────────────────────────────────────────

export default function PlayerCardPage() {
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedPlayer, setSelectedPlayer] = useState('');
  const [position, setPosition] = useState('Atacante');
  const [debounceTimer, setDebounceTimer] = useState<ReturnType<typeof setTimeout> | null>(null);

  const { data: positions = [] } = usePositions();

  const searchParams = useMemo(() => ({ search: debouncedSearch || undefined, limit: 10 }), [debouncedSearch]);
  const { data: searchData } = usePlayers(debouncedSearch.length >= 2 && !selectedPlayer ? searchParams : { limit: 0 });
  const players = searchData?.players ?? [];

  const handleSearchChange = (value: string) => {
    setSearch(value);
    setSelectedPlayer('');
    if (debounceTimer) clearTimeout(debounceTimer);
    setDebounceTimer(setTimeout(() => setDebouncedSearch(value), 200));
  };

  // Fetch indices data
  const { data: indicesData, isLoading, error } = useQuery({
    queryKey: ['indices', selectedPlayer, position],
    queryFn: async () => {
      const res = await api.get(`/players/${encodeURIComponent(selectedPlayer)}/indices`, { params: { position } });
      return res.data as IndicesResponse;
    },
    enabled: !!selectedPlayer,
    staleTime: 10 * 60 * 1000,
  });

  // Fetch player profile for photo, nationality, league info
  const { data: profileData } = usePlayerProfile(selectedPlayer || null);

  const summary = indicesData?.summary;
  const nationality = profileData?.summary?.nationality;
  const league = profileData?.summary?.league;
  const leagueLogo = profileData?.summary?.league_logo;
  const photoUrl = profileData?.summary?.photo_url;
  const clubLogo = profileData?.summary?.club_logo;

  // Split categories into two columns for layout
  const categories = indicesData?.breakdown
    ? Object.entries(indicesData.breakdown).map(([name, metrics]) => ({
        name,
        score: indicesData.indices[name] ?? 0,
        metrics,
      }))
    : [];

  const midpoint = Math.ceil(categories.length / 2);
  const leftCategories = categories.slice(0, midpoint);
  const rightCategories = categories.slice(midpoint);

  return (
    <div className="space-y-5">
      {/* Page title */}
      <div>
        <h1 className="font-[var(--font-display)] text-lg font-bold tracking-tight flex items-center gap-2">
          <Target size={18} style={{ color: 'var(--color-accent)' }} />
          Player Card
        </h1>
        <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
          Perfil completo com ranking percentil por categoria
        </p>
      </div>

      {error && (
        <div className="flex items-center gap-2 px-4 py-3 rounded text-sm" style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444' }}>
          <AlertCircle size={16} />
          <span>Erro: {(error as Error).message}</span>
        </div>
      )}

      {/* Search controls */}
      <div className="card-glass rounded-lg p-5 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-[1fr_auto] gap-3 items-end">
          <div>
            <label className="block text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>
              JOGADOR
            </label>
            <div className="relative">
              <input
                type="text"
                value={search}
                onChange={(e) => handleSearchChange(e.target.value)}
                placeholder="Digite o nome do jogador..."
                className="w-full px-3 py-2 rounded text-sm outline-none input-focus"
                style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)' }}
              />
              {debouncedSearch.length >= 2 && !selectedPlayer && players.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 rounded overflow-hidden z-50 max-h-48 overflow-y-auto" style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-border-active)' }}>
                  {players.map((p, i) => (
                    <button
                      key={i}
                      onClick={() => {
                        setSelectedPlayer(p.display_name || p.name);
                        setSearch(p.display_name || p.name);
                        setDebouncedSearch('');
                      }}
                      className="w-full text-left px-3 py-2 text-sm transition-colors hover:bg-white/5 cursor-pointer"
                      style={{ borderBottom: '1px solid var(--color-border-subtle)', color: 'var(--color-text-primary)' }}
                    >
                      <div>{p.display_name || p.name}</div>
                      <div className="text-[10px]" style={{ color: 'var(--color-text-muted)' }}>
                        {p.team} — {p.position}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
          <div>
            <label className="block text-[10px] font-[var(--font-display)] tracking-[0.1em] uppercase mb-1" style={{ color: 'var(--color-text-muted)' }}>
              POSIÇÃO
            </label>
            <select
              value={position}
              onChange={(e) => setPosition(e.target.value)}
              className="px-3 py-2 rounded text-sm cursor-pointer outline-none"
              style={{ background: 'var(--color-surface-2)', border: '1px solid var(--color-border-subtle)', color: 'var(--color-text-secondary)' }}
            >
              {(positions.length > 0 ? positions : ['Atacante', 'Extremo', 'Meia', 'Volante', 'Lateral direito', 'Lateral esquerdo', 'Zagueiro', 'Goleiro']).map(p =>
                <option key={p} value={p}>{p}</option>
              )}
            </select>
          </div>
        </div>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="card-glass rounded-lg p-8 text-center">
          <div className="skeleton h-48 rounded" />
        </div>
      )}

      {/* Player card content */}
      {indicesData && summary && (
        <>
          {/* ── Player Header ─────────────────────────────────────── */}
          <div className="card-glass rounded-lg p-6">
            <div className="flex flex-col md:flex-row items-center md:items-start gap-5">
              {/* Photo */}
              <PlayerPhoto url={photoUrl ?? null} alt={summary.name} />

              {/* Info */}
              <div className="flex-1 text-center md:text-left">
                {/* Position & evaluated-as badges */}
                <div className="flex items-center justify-center md:justify-start gap-2 mb-1">
                  <span className="text-[10px] font-[var(--font-mono)] font-bold px-2 py-0.5 rounded" style={{ background: 'var(--color-accent)', color: '#fff' }}>
                    {summary.position_raw || position}
                  </span>
                  <span className="text-[10px] font-[var(--font-mono)] font-bold px-2 py-0.5 rounded" style={{ background: 'var(--color-surface-3)', color: 'var(--color-text-secondary)' }}>
                    AVALIANDO: {indicesData.position}
                  </span>
                </div>

                {/* Player name */}
                <h2 className="font-[var(--font-display)] text-2xl md:text-3xl font-bold tracking-tight uppercase" style={{ color: 'var(--color-text-primary)' }}>
                  {summary.name}
                </h2>

                {/* Info pills */}
                <div className="flex flex-wrap items-center justify-center md:justify-start gap-2 mt-3">
                  {nationality && (
                    <InfoPill
                      icon={
                        getFlagUrl(nationality) ? (
                          <img src={getFlagUrl(nationality, 20)!} alt={nationality} className="w-4 h-3 object-cover rounded-sm" />
                        ) : (
                          <Flag size={14} strokeWidth={1.5} />
                        )
                      }
                      label="NAÇÃO"
                      value={nationality}
                    />
                  )}
                  {league && (
                    <InfoPill
                      icon={
                        leagueLogo ? (
                          <img src={proxyImageUrl(leagueLogo)!} alt={league} className="w-4 h-4 object-contain" referrerPolicy="no-referrer" onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none' }} />
                        ) : (
                          <Building2 size={14} strokeWidth={1.5} />
                        )
                      }
                      label="LIGA"
                      value={league}
                    />
                  )}
                  {summary.team && (
                    <InfoPill
                      icon={
                        clubLogo ? (
                          <img src={proxyImageUrl(clubLogo)!} alt={summary.team} className="w-4 h-4 object-contain" referrerPolicy="no-referrer" onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none' }} />
                        ) : (
                          <Shield size={14} strokeWidth={1.5} />
                        )
                      }
                      label="CLUBE"
                      value={summary.team}
                    />
                  )}
                  {summary.age != null && (
                    <InfoPill
                      icon={<CalendarDays size={14} strokeWidth={1.5} />}
                      label="IDADE"
                      value={`${Math.round(summary.age)} anos`}
                    />
                  )}
                  {summary.minutes != null && (
                    <InfoPill
                      icon={<Clock size={14} strokeWidth={1.5} />}
                      label="MINUTOS"
                      value={Math.round(summary.minutes).toLocaleString()}
                    />
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* ── Percentile description ────────────────────────────── */}
          <div className="text-center">
            <span className="text-[10px] font-[var(--font-mono)] tracking-[0.15em] uppercase" style={{ color: 'var(--color-text-muted)' }}>
              PERCENTIL VS {indicesData.position.toUpperCase()} · SÉRIE B BRASIL · PER 90 MINUTES
            </span>
          </div>

          {/* ── Two-column metrics layout ─────────────────────────── */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {/* Left column */}
            <div className="space-y-5">
              {leftCategories.map((cat, ci) => {
                const prevMetrics = leftCategories.slice(0, ci).reduce((a, c) => a + c.metrics.length, 0);
                return (
                  <div key={cat.name} className="card-glass rounded-lg p-5">
                    <CategorySection
                      name={cat.name}
                      score={cat.score}
                      metrics={cat.metrics}
                      startIndex={prevMetrics}
                    />
                  </div>
                );
              })}
            </div>

            {/* Right column */}
            <div className="space-y-5">
              {rightCategories.map((cat, ci) => {
                const prevMetrics = rightCategories.slice(0, ci).reduce((a, c) => a + c.metrics.length, 0);
                return (
                  <div key={cat.name} className="card-glass rounded-lg p-5">
                    <CategorySection
                      name={cat.name}
                      score={cat.score}
                      metrics={cat.metrics}
                      startIndex={prevMetrics}
                    />
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}

      {/* Empty state */}
      {!selectedPlayer && !isLoading && (
        <div className="card-glass rounded-lg p-8 text-center" style={{ color: 'var(--color-text-muted)' }}>
          <Target size={32} className="mx-auto mb-3 opacity-30" />
          <p className="text-sm">Selecione um jogador para ver o Player Card completo</p>
        </div>
      )}
    </div>
  );
}
