import { RotateCcw, Search } from 'lucide-react';

export interface PlayerFilterState {
  nameQuery: string;
  teamQuery: string;
  nationality: string;
  ageMin: string;
  ageMax: string;
  minScore: string;
  maxMinutes: string;
}

export const EMPTY_PLAYER_FILTERS: PlayerFilterState = {
  nameQuery: '',
  teamQuery: '',
  nationality: '',
  ageMin: '',
  ageMax: '',
  minScore: '',
  maxMinutes: '',
};

interface PlayerRowLike {
  display_name?: string | null;
  name?: string | null;
  team?: string | null;
  nationality?: string | null;
  age?: number | null;
  minutes?: number | null;
  score?: number | null;
}

export function applyPlayerFilters<T extends PlayerRowLike>(
  rows: T[],
  filters: PlayerFilterState,
): T[] {
  const ageMinN = filters.ageMin !== '' ? Number(filters.ageMin) : null;
  const ageMaxN = filters.ageMax !== '' ? Number(filters.ageMax) : null;
  const maxMinutesN = filters.maxMinutes !== '' ? Number(filters.maxMinutes) : null;
  const minScoreN = filters.minScore !== '' ? Number(filters.minScore) : null;
  const teamLc = filters.teamQuery.trim().toLowerCase();
  const nameLc = filters.nameQuery.trim().toLowerCase();

  return rows.filter((p) => {
    if (ageMinN != null && (p.age == null || p.age < ageMinN)) return false;
    if (ageMaxN != null && (p.age == null || p.age > ageMaxN)) return false;
    if (maxMinutesN != null && (p.minutes == null || p.minutes > maxMinutesN)) return false;
    if (minScoreN != null && (p.score == null || p.score < minScoreN)) return false;
    if (filters.nationality && p.nationality !== filters.nationality) return false;
    if (teamLc && !(p.team || '').toLowerCase().includes(teamLc)) return false;
    if (nameLc) {
      const label = (p.display_name || p.name || '').toLowerCase();
      if (!label.includes(nameLc)) return false;
    }
    return true;
  });
}

export function countActiveFilters(f: PlayerFilterState): number {
  return [f.nameQuery, f.teamQuery, f.nationality, f.ageMin, f.ageMax, f.minScore, f.maxMinutes]
    .filter((v) => v !== '')
    .length;
}

export type PlayerFilterField = keyof PlayerFilterState;

interface PlayerFiltersBarProps {
  value: PlayerFilterState;
  onChange: (next: PlayerFilterState) => void;
  nationalities: string[];
  scoreLabel?: string;
  dense?: boolean;
  /** Fields to omit — useful when the parent already exposes equivalent server-side filters. */
  hiddenFields?: PlayerFilterField[];
}

export default function PlayerFiltersBar({
  value,
  onChange,
  nationalities,
  scoreLabel = 'MIN SSP',
  dense = false,
  hiddenFields = [],
}: PlayerFiltersBarProps) {
  const update = (patch: Partial<PlayerFilterState>) => onChange({ ...value, ...patch });
  const hidden = new Set(hiddenFields);
  const activeCount = countActiveFilters(value);

  return (
    <div className={`flex flex-wrap items-end ${dense ? 'gap-2' : 'gap-3'}`}>
      {!hidden.has('nameQuery') && (
        <Group label="JOGADOR">
          <div className="relative">
            <Search size={12} strokeWidth={1.5} className="absolute left-2.5 top-1/2 -translate-y-1/2" style={{ color: 'var(--color-text-muted)' }} />
            <input
              type="text"
              value={value.nameQuery}
              placeholder="Buscar..."
              onChange={(e) => update({ nameQuery: e.target.value })}
              className="pfb-input pl-7 w-40"
            />
          </div>
        </Group>
      )}

      {!hidden.has('teamQuery') && (
        <Group label="TIME">
          <div className="relative">
            <Search size={12} strokeWidth={1.5} className="absolute left-2.5 top-1/2 -translate-y-1/2" style={{ color: 'var(--color-text-muted)' }} />
            <input
              type="text"
              value={value.teamQuery}
              placeholder="Buscar..."
              onChange={(e) => update({ teamQuery: e.target.value })}
              className="pfb-input pl-7 w-40"
            />
          </div>
        </Group>
      )}

      {!hidden.has('nationality') && (
        <Group label="NACIONALIDADE">
          <select
            value={value.nationality}
            onChange={(e) => update({ nationality: e.target.value })}
            className="pfb-input cursor-pointer"
          >
            <option value="">Todas</option>
            {nationalities.map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </Group>
      )}

      {!hidden.has('ageMin') && (
        <Group label="IDADE MIN">
          <input
            type="number"
            value={value.ageMin}
            placeholder="16"
            min={14}
            max={50}
            onChange={(e) => update({ ageMin: e.target.value })}
            className="pfb-input w-16 pfb-mono"
          />
        </Group>
      )}

      {!hidden.has('ageMax') && (
        <Group label="IDADE MAX">
          <input
            type="number"
            value={value.ageMax}
            placeholder="40"
            min={14}
            max={50}
            onChange={(e) => update({ ageMax: e.target.value })}
            className="pfb-input w-16 pfb-mono"
          />
        </Group>
      )}

      {!hidden.has('maxMinutes') && (
        <Group label="MAX MIN">
          <input
            type="number"
            value={value.maxMinutes}
            placeholder="5000"
            min={0}
            onChange={(e) => update({ maxMinutes: e.target.value })}
            className="pfb-input w-20 pfb-mono"
          />
        </Group>
      )}

      {!hidden.has('minScore') && (
        <Group label={scoreLabel}>
          <input
            type="number"
            value={value.minScore}
            placeholder="50"
            min={0}
            max={100}
            step={1}
            onChange={(e) => update({ minScore: e.target.value })}
            className="pfb-input w-20 pfb-mono"
          />
        </Group>
      )}

      <button
        type="button"
        onClick={() => onChange(EMPTY_PLAYER_FILTERS)}
        disabled={activeCount === 0}
        className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-[11px] font-medium transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
        style={{
          background: activeCount > 0 ? 'var(--color-accent-glow)' : 'var(--color-surface-1)',
          color: activeCount > 0 ? 'var(--color-accent)' : 'var(--color-text-muted)',
          border: `1px solid ${activeCount > 0 ? 'var(--color-accent)' : 'var(--color-border-subtle)'}`,
        }}
        title="Limpar filtros secundários"
      >
        <RotateCcw size={12} strokeWidth={1.5} />
        Limpar{activeCount > 0 ? ` (${activeCount})` : ''}
      </button>

      <style>{`
        .pfb-input {
          background: var(--color-surface-1);
          border-bottom: 1px solid var(--color-surface-3);
          color: var(--color-text-primary);
          padding: 8px 10px;
          border-radius: 8px;
          font-size: 12px;
          outline: none;
          font-family: var(--font-body);
        }
        .pfb-input:focus {
          border-bottom-color: var(--color-accent);
        }
        .pfb-mono { font-family: var(--font-mono); }
      `}</style>
    </div>
  );
}

function Group({ label, children }: { label: string; children: React.ReactNode }) {
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
