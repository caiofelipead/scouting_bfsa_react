import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { ScatterChart as ScatterIcon, SlidersHorizontal } from 'lucide-react';
// @ts-expect-error — .jsx component (intentionally untyped per request)
import ScatterPlot from '../components/ScatterPlot';
import { useRankings, usePositions, useLeagues } from '../hooks/usePlayers';
import PlayerProfile from '../components/PlayerProfile';
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

export default function ScatterPlotPage() {
  const [position, setPosition] = useState<string>('Atacante');
  const [league, setLeague] = useState<string>('');
  const [minMinutes, setMinMinutes] = useState<number>(500);
  const [topN] = useState<number>(150);
  const [xAxis, setXAxis] = useState<string>('');
  const [yAxis, setYAxis] = useState<string>('');
  const [selectedPlayer, setSelectedPlayer] = useState<string | null>(null);
  const [minSigma, setMinSigma] = useState<number>(1);

  const { data: positions = [] } = usePositions();
  const { data: leagues = [] } = useLeagues();

  const queryParams = useMemo<RankingsQueryParams>(() => ({
    position,
    min_minutes: minMinutes,
    league: league || undefined,
    top_n: topN,
  }), [position, minMinutes, league, topN]);

  const { data, isLoading, isFetching } = useRankings(queryParams);
  const players = data?.players ?? [];

  // Available indices from the first player (they all share the same keys per position)
  const availableIndices = useMemo(() => {
    const set = new Set<string>();
    for (const p of players) {
      for (const k of Object.keys(p.indices || {})) set.add(k);
    }
    return Array.from(set);
  }, [players]);

  // Seed axis choices when available
  const effectiveX = xAxis || availableIndices[0] || '';
  const effectiveY = yAxis || availableIndices[1] || availableIndices[0] || '';

  // Top-3 SSP are rendered in accent red + always labeled.
  const highlightLabels = useMemo(
    () => new Set(
      [...players]
        .sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
        .slice(0, 3)
        .map((p) => p.display_name || p.name),
    ),
    [players],
  );

  const scatterPoints = useMemo<ScatterPoint[]>(() => {
    if (!effectiveX || !effectiveY) return [];
    return players
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
  }, [players, effectiveX, effectiveY, highlightLabels]);

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
            Plote quaisquer dois indices com destaque automatico de outliers (media ± {minSigma}·SD).
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
          <span>{players.length} jogadores</span>
        </div>
      </div>

      {/* Filter bar */}
      <div className="card-glass p-4">
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
              onChange={(e) => setMinMinutes(Number(e.target.value) || 0)}
              className="input-thin w-24"
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
      </div>

      {/* Chart */}
      <div className="card-glass p-4">
        {isLoading ? (
          <div className="skeleton h-[520px] w-full rounded-lg" />
        ) : scatterPoints.length === 0 ? (
          <div className="py-20 text-center text-sm" style={{ color: 'var(--color-text-muted)' }}>
            Nenhum dado disponivel para os filtros selecionados.
          </div>
        ) : (
          <ScatterPlot
            points={scatterPoints}
            xLabel={effectiveX}
            yLabel={effectiveY}
            title={`${effectiveY} vs ${effectiveX}`}
            subtitle={`${position} · ${league || 'Todas as ligas'} · minutos ≥ ${minMinutes}`}
            footnote={`*Amostra de ${players.length} jogadores · outliers destacados > μ + ${minSigma}σ`}
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
