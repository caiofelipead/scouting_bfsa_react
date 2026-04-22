import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { ScatterChart as ScatterIcon, SlidersHorizontal } from 'lucide-react';
// @ts-expect-error — .jsx component (intentionally untyped per request)
import ScatterPlot from '../components/ScatterPlot';
import { useRankings, usePositions, useLeagues } from '../hooks/usePlayers';
import PlayerProfile from '../components/PlayerProfile';
import PlayerFiltersBar, {
  applyPlayerFilters,
  EMPTY_PLAYER_FILTERS,
  type PlayerFilterState,
} from '../components/PlayerFiltersBar';
import type { RankingsQueryParams, RankingEntry } from '../types/api';

interface ScatterPoint {
  x: number;
  y: number;
  label: string;
  category: string | null;
  team: string | null;
  age: number | null;
  minutes: number | null;
  meta: RankingEntry;
}

const DEFAULT_TOP_N = 300;

export default function ScatterPlotPage() {
  // ── Server-side (affect /api/rankings query) ──
  const [position, setPosition] = useState<string>('Atacante');
  const [league, setLeague] = useState<string>('');
  const [minMinutes, setMinMinutes] = useState<number>(500);
  const [topN, setTopN] = useState<number>(DEFAULT_TOP_N);

  // ── Client-side refinements ──
  const [filters, setFilters] = useState<PlayerFilterState>(EMPTY_PLAYER_FILTERS);

  // ── Chart config ──
  const [xAxis, setXAxis] = useState<string>('');
  const [yAxis, setYAxis] = useState<string>('');
  const [minSigma, setMinSigma] = useState<number>(1);

  const [selectedPlayer, setSelectedPlayer] = useState<string | null>(null);

  const { data: positions = [] } = usePositions();
  const { data: leagues = [] } = useLeagues();

  const queryParams = useMemo<RankingsQueryParams>(() => ({
    position,
    min_minutes: minMinutes,
    league: league || undefined,
    top_n: topN,
  }), [position, minMinutes, league, topN]);

  const { data, isLoading, isFetching } = useRankings(queryParams);
  const rawPlayers = data?.players ?? [];

  // Derived lists for dropdowns (from the currently-loaded dataset)
  const availableIndices = useMemo(() => {
    const set = new Set<string>();
    for (const p of rawPlayers) {
      for (const k of Object.keys(p.indices || {})) set.add(k);
    }
    return Array.from(set);
  }, [rawPlayers]);

  const availableNationalities = useMemo(() => {
    const set = new Set<string>();
    for (const p of rawPlayers) {
      if (p.nationality) set.add(p.nationality);
    }
    return Array.from(set).sort((a, b) => a.localeCompare(b));
  }, [rawPlayers]);

  // Apply client-side filters
  const filteredPlayers = useMemo(
    () => applyPlayerFilters(rawPlayers, filters),
    [rawPlayers, filters],
  );

  const effectiveX = xAxis || availableIndices[0] || '';
  const effectiveY = yAxis || availableIndices[1] || availableIndices[0] || '';

  // Top-3 SSP among the filtered players are highlighted.
  const highlightLabels = useMemo(
    () => new Set(
      [...filteredPlayers]
        .sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
        .slice(0, 3)
        .map((p) => p.display_name || p.name),
    ),
    [filteredPlayers],
  );

  const scatterPoints = useMemo<ScatterPoint[]>(() => {
    if (!effectiveX || !effectiveY) return [];
    return filteredPlayers
      .map<ScatterPoint | null>((p) => {
        const x = p.indices?.[effectiveX];
        const y = p.indices?.[effectiveY];
        if (typeof x !== 'number' || typeof y !== 'number') return null;
        const label = p.display_name || p.name;
        return {
          x,
          y,
          label,
          category: highlightLabels.has(label) ? 'TOP SSP' : null,
          team: p.team,
          age: p.age,
          minutes: p.minutes,
          meta: p,
        };
      })
      .filter((v): v is ScatterPoint => v !== null);
  }, [filteredPlayers, effectiveX, effectiveY, highlightLabels]);

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="font-[var(--font-display)] text-xl font-bold tracking-tight flex items-center gap-2">
            <ScatterIcon size={20} strokeWidth={1.5} style={{ color: 'var(--color-accent)' }} />
            Scatter Plot
          </h1>
          <p className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>
            Filtre por posição, liga, idade, nacionalidade, time e score; escolha dois índices para plotar.
          </p>
        </div>
        <div className="flex items-center gap-2 text-[10px] font-[var(--font-mono)]" style={{ color: 'var(--color-text-muted)' }}>
          {isFetching && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="filter-loading-spinner"
              style={{ width: 12, height: 12 }}
            />
          )}
          <span>{filteredPlayers.length} / {rawPlayers.length} jogadores</span>
        </div>
      </div>

      {/* Filter bar */}
      <div className="card-glass p-4 space-y-3">
        {/* Row 1 — core query (drives backend request) */}
        <div className="flex flex-wrap items-end gap-3">
          <FilterGroup label="POSICAO">
            <select
              value={position}
              onChange={(e) => { setPosition(e.target.value); setXAxis(''); setYAxis(''); }}
              className="input-thin cursor-pointer"
            >
              {positions.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </FilterGroup>

          <FilterGroup label="LIGA">
            <select
              value={league}
              onChange={(e) => setLeague(e.target.value)}
              className="input-thin cursor-pointer"
            >
              <option value="">Todas ligas</option>
              {leagues.map((l) => (
                <option key={l} value={l}>{l}</option>
              ))}
            </select>
          </FilterGroup>

          <FilterGroup label="MIN MIN">
            <input
              type="number"
              value={minMinutes}
              min={0}
              onChange={(e) => setMinMinutes(Number(e.target.value) || 0)}
              className="input-thin w-20"
              style={{ fontFamily: 'var(--font-mono)' }}
            />
          </FilterGroup>

          <FilterGroup label="TOP N">
            <input
              type="number"
              value={topN}
              min={20}
              max={500}
              step={50}
              onChange={(e) => setTopN(Math.min(500, Math.max(20, Number(e.target.value) || DEFAULT_TOP_N)))}
              className="input-thin w-20"
              style={{ fontFamily: 'var(--font-mono)' }}
            />
          </FilterGroup>

          <div style={{ width: 1, height: 32, background: 'var(--color-border-subtle)' }} />

          <FilterGroup label="EIXO X">
            <select
              value={effectiveX}
              onChange={(e) => setXAxis(e.target.value)}
              className="input-thin cursor-pointer"
              disabled={availableIndices.length === 0}
            >
              {availableIndices.map((idx) => (
                <option key={idx} value={idx}>{idx}</option>
              ))}
            </select>
          </FilterGroup>

          <FilterGroup label="EIXO Y">
            <select
              value={effectiveY}
              onChange={(e) => setYAxis(e.target.value)}
              className="input-thin cursor-pointer"
              disabled={availableIndices.length === 0}
            >
              {availableIndices.map((idx) => (
                <option key={idx} value={idx}>{idx}</option>
              ))}
            </select>
          </FilterGroup>

          <FilterGroup label="OUTLIER (σ)">
            <div className="flex items-center gap-2">
              <SlidersHorizontal size={14} strokeWidth={1.5} style={{ color: 'var(--color-text-muted)' }} />
              <input
                type="range"
                min={0.5}
                max={2.5}
                step={0.25}
                value={minSigma}
                onChange={(e) => setMinSigma(Number(e.target.value))}
                style={{ width: 80 }}
              />
              <span className="text-xs font-[var(--font-mono)]" style={{ color: 'var(--color-text-secondary)' }}>
                {minSigma.toFixed(2)}
              </span>
            </div>
          </FilterGroup>
        </div>

        {/* Row 2 — client-side refinements */}
        <div className="pt-3" style={{ borderTop: '1px solid var(--color-border-subtle)' }}>
          <PlayerFiltersBar
            value={filters}
            onChange={setFilters}
            nationalities={availableNationalities}
          />
        </div>
      </div>

      {/* Chart */}
      <div className="card-glass p-4">
        {isLoading ? (
          <div className="skeleton h-[520px] w-full rounded-lg" />
        ) : scatterPoints.length === 0 ? (
          <div className="py-20 text-center text-sm" style={{ color: 'var(--color-text-muted)' }}>
            Nenhum jogador corresponde aos filtros atuais.
          </div>
        ) : (
          <ScatterPlot
            points={scatterPoints}
            xLabel={effectiveX}
            yLabel={effectiveY}
            title={`${effectiveY} vs ${effectiveX}`}
            subtitle={buildSubtitle({ position, league, minMinutes, filters })}
            footnote={`*Amostra de ${scatterPoints.length} jogadores · outliers destacados > μ + ${minSigma}σ`}
            minOutlierSigma={minSigma}
            highlightCategories={['TOP SSP']}
            maxLabels={12}
            onPointClick={(pt: ScatterPoint) => setSelectedPlayer(pt.label)}
          />
        )}
      </div>

      {/* Profile panel when a point is clicked */}
      {selectedPlayer && (
        <div>
          <PlayerProfile
            playerDisplayName={selectedPlayer}
            onClose={() => setSelectedPlayer(null)}
          />
        </div>
      )}

      <style>{`
        .input-thin {
          background: var(--color-surface-1);
          border-bottom: 1px solid var(--color-surface-3);
          color: var(--color-text-primary);
          padding: 8px 10px;
          border-radius: 8px;
          font-size: 12px;
          outline: none;
          font-family: var(--font-body);
        }
        .input-thin:focus {
          border-bottom-color: var(--color-accent);
        }
      `}</style>
    </div>
  );
}

function buildSubtitle(f: {
  position: string;
  league: string;
  minMinutes: number;
  filters: PlayerFilterState;
}): string {
  const { filters: ff } = f;
  const parts: string[] = [f.position, f.league || 'Todas as ligas', `minutos ≥ ${f.minMinutes}`];
  if (ff.ageMin || ff.ageMax) parts.push(`idade ${ff.ageMin || '—'}–${ff.ageMax || '—'}`);
  if (ff.nationality) parts.push(ff.nationality);
  if (ff.teamQuery) parts.push(`time: "${ff.teamQuery}"`);
  if (ff.nameQuery) parts.push(`nome: "${ff.nameQuery}"`);
  if (ff.minScore) parts.push(`SSP ≥ ${ff.minScore}`);
  if (ff.maxMinutes) parts.push(`minutos ≤ ${ff.maxMinutes}`);
  return parts.join(' · ');
}

function FilterGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <label
        className="text-[9px] font-[var(--font-display)] tracking-[0.18em] uppercase font-semibold"
        style={{ color: 'var(--color-text-muted)' }}
      >
        {label}
      </label>
      {children}
    </div>
  );
}
