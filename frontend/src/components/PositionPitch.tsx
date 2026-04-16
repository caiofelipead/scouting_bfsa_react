interface PositionPitchProps {
  position: string | null;
  width?: number;
  height?: number;
  className?: string;
}

type Slot = { key: string; x: number; y: number; match: (p: string) => boolean };

const hasAny = (p: string, words: string[]) => words.some((w) => p.includes(w));
const isLeft = (p: string) => /\besq|\bleft|gauche/.test(p);
const isRight = (p: string) => /\bdir|\bright|droit/.test(p);

// Pitch coordinates on a 100×62 viewBox (attack → right).
const SLOTS: Slot[] = [
  { key: 'GK', x: 6, y: 31, match: (p) => hasAny(p, ['goleir', 'goalkee', 'gardien']) },
  { key: 'LB', x: 22, y: 8, match: (p) => hasAny(p, ['lateral', 'back', 'latéral']) && isLeft(p) },
  { key: 'LCB', x: 22, y: 22, match: (p) => hasAny(p, ['zagueir', 'central', 'center back', 'centre back', 'défenseur central', 'defensor']) && (isLeft(p) || !isRight(p)) },
  { key: 'RCB', x: 22, y: 40, match: (p) => hasAny(p, ['zagueir', 'central', 'center back', 'centre back', 'défenseur central', 'defensor']) && (isRight(p) || !isLeft(p)) },
  { key: 'RB', x: 22, y: 54, match: (p) => hasAny(p, ['lateral', 'back', 'latéral']) && isRight(p) },
  { key: 'LDM', x: 42, y: 20, match: (p) => hasAny(p, ['volante', 'defensive mid', 'milieu défensif']) && (isLeft(p) || !isRight(p)) },
  { key: 'RDM', x: 42, y: 42, match: (p) => hasAny(p, ['volante', 'defensive mid', 'milieu défensif']) && (isRight(p) || !isLeft(p)) },
  { key: 'CM', x: 55, y: 31, match: (p) => hasAny(p, ['meia', 'midfield', 'milieu', 'mediocampista']) && !hasAny(p, ['volante', 'defensive', 'défensif']) },
  { key: 'LW', x: 78, y: 10, match: (p) => hasAny(p, ['extremo', 'ponta', 'winger', 'ailier']) && (isLeft(p) || !isRight(p)) },
  { key: 'RW', x: 78, y: 52, match: (p) => hasAny(p, ['extremo', 'ponta', 'winger', 'ailier']) && (isRight(p) || !isLeft(p)) },
  { key: 'ST', x: 90, y: 31, match: (p) => hasAny(p, ['atacante', 'centroavante', 'striker', 'avant-centre', 'attaquant']) },
];

function activeKeys(position: string | null): Set<string> {
  if (!position) return new Set();
  const tokens = position
    .toLowerCase()
    .split(/[,/|]+/)
    .map((t) => t.trim())
    .filter(Boolean);
  const active = new Set<string>();
  for (const token of tokens) {
    for (const slot of SLOTS) {
      if (slot.match(token)) active.add(slot.key);
    }
  }
  return active;
}

export default function PositionPitch({ position, width = 96, height = 60, className }: PositionPitchProps) {
  const active = activeKeys(position);
  const accent = 'var(--color-accent)';
  const accentGlow = 'var(--color-accent-glow)';

  return (
    <svg
      viewBox="0 0 100 62"
      width={width}
      height={height}
      className={className}
      role="img"
      aria-label={position ? `Posição: ${position}` : 'Posição não informada'}
      style={{
        background: 'linear-gradient(180deg, rgba(26,94,42,0.35) 0%, rgba(29,107,48,0.35) 100%)',
        borderRadius: 6,
        border: '1px solid rgba(255,255,255,0.1)',
      }}
    >
      {/* Field lines */}
      <g stroke="rgba(255,255,255,0.25)" strokeWidth="0.4" fill="none">
        <line x1="50" y1="2" x2="50" y2="60" />
        <circle cx="50" cy="31" r="7" />
        <rect x="2" y="14" width="14" height="34" />
        <rect x="2" y="22" width="5" height="18" />
        <rect x="84" y="14" width="14" height="34" />
        <rect x="93" y="22" width="5" height="18" />
      </g>

      {/* Position dots */}
      {SLOTS.map((s) => {
        const on = active.has(s.key);
        return (
          <circle
            key={s.key}
            cx={s.x}
            cy={s.y}
            r={on ? 2.6 : 2}
            fill={on ? accent : 'rgba(255,255,255,0.25)'}
            stroke={on ? accentGlow : 'transparent'}
            strokeWidth={on ? 1.8 : 0}
          />
        );
      })}
    </svg>
  );
}
