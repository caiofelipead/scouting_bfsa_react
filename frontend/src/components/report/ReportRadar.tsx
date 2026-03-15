interface ReportRadarProps {
  data: Array<{ name: string; value: number }>;
  size?: number;
}

export default function ReportRadar({ data, size = 380 }: ReportRadarProps) {
  if (!data.length) return null;

  const cx = size / 2;
  const cy = size / 2;
  const maxR = size / 2 - 60;
  const n = data.length;
  const angleStep = (2 * Math.PI) / n;

  function polarToXY(angle: number, r: number): [number, number] {
    return [cx + r * Math.sin(angle), cy - r * Math.cos(angle)];
  }

  function getColor(v: number): string {
    if (v >= 90) return '#1B9E5A';
    if (v >= 65) return '#D97706';
    if (v >= 36) return '#6B7280';
    return '#C8102E';
  }

  // Rings at 25, 50, 75, 100
  const rings = [25, 50, 75, 100];

  // Build polygon for background rings (filled)
  function ringPolygon(pct: number): string {
    const r = (pct / 100) * maxR;
    return data
      .map((_, i) => {
        const angle = i * angleStep;
        const [x, y] = polarToXY(angle, r);
        return `${x},${y}`;
      })
      .join(' ');
  }

  // Data polygon
  const polyPoints = data
    .map((d, i) => {
      const angle = i * angleStep;
      const r = (Math.min(d.value, 100) / 100) * maxR;
      return polarToXY(angle, r);
    })
    .map(([x, y]) => `${x},${y}`)
    .join(' ');

  // Average
  const avg = Math.round(data.reduce((s, d) => s + d.value, 0) / n);

  // Smart label positioning
  function getLabelAnchor(angle: number): string {
    const deg = ((angle * 180) / Math.PI) % 360;
    if (deg > 30 && deg < 150) return 'start';
    if (deg > 210 && deg < 330) return 'end';
    return 'middle';
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center' }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <defs>
          <radialGradient id="radarBg" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#12264a" />
            <stop offset="100%" stopColor="#0C1B37" />
          </radialGradient>
          <linearGradient id="polyGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#C8102E" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#E8213F" stopOpacity="0.15" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Background */}
        <rect width={size} height={size} rx={14} fill="url(#radarBg)" />

        {/* Ring polygons (not circles, matching the axes) */}
        {rings.map((pct, ri) => (
          <polygon
            key={pct}
            points={ringPolygon(pct)}
            fill="none"
            stroke="rgba(255,255,255,0.07)"
            strokeWidth={ri === rings.length - 1 ? 1.5 : 0.8}
          />
        ))}

        {/* Ring percentage labels */}
        {rings.map((pct) => {
          const r = (pct / 100) * maxR;
          return (
            <text
              key={`lbl-${pct}`}
              x={cx + 4}
              y={cy - r + 3}
              fill="rgba(255,255,255,0.2)"
              fontSize={8}
              fontFamily="'JetBrains Mono', monospace"
            >
              {pct}
            </text>
          );
        })}

        {/* Axis lines */}
        {data.map((_, i) => {
          const angle = i * angleStep;
          const [ex, ey] = polarToXY(angle, maxR);
          return (
            <line
              key={i}
              x1={cx}
              y1={cy}
              x2={ex}
              y2={ey}
              stroke="rgba(255,255,255,0.06)"
              strokeWidth={0.8}
            />
          );
        })}

        {/* Data polygon fill + stroke */}
        <polygon
          points={polyPoints}
          fill="url(#polyGrad)"
          stroke="#C8102E"
          strokeWidth={2}
          strokeLinejoin="round"
          filter="url(#glow)"
        />

        {/* Data dots with colored halos */}
        {data.map((d, i) => {
          const angle = i * angleStep;
          const r = (Math.min(d.value, 100) / 100) * maxR;
          const [x, y] = polarToXY(angle, r);
          const color = getColor(d.value);
          return (
            <g key={i}>
              {/* Outer halo */}
              <circle cx={x} cy={y} r={7} fill={color} opacity={0.2} />
              {/* Dot */}
              <circle cx={x} cy={y} r={4} fill={color} stroke="#0C1B37" strokeWidth={1.5} />
              {/* Value near dot */}
              <text
                x={x}
                y={y - 10}
                textAnchor="middle"
                fill={color}
                fontSize={9}
                fontFamily="'JetBrains Mono', monospace"
                fontWeight={700}
              >
                {Math.round(d.value)}
              </text>
            </g>
          );
        })}

        {/* Labels */}
        {data.map((d, i) => {
          const angle = i * angleStep;
          const labelR = maxR + 36;
          const [lx, ly] = polarToXY(angle, labelR);
          const anchor = getLabelAnchor(angle);

          // Truncate long names
          const label = d.name.length > 14 ? d.name.slice(0, 13) + '…' : d.name;

          return (
            <text
              key={`label-${i}`}
              x={lx}
              y={ly}
              textAnchor={anchor}
              dominantBaseline="middle"
              fill="rgba(255,255,255,0.7)"
              fontSize={10}
              fontFamily="'DM Sans', sans-serif"
              fontWeight={500}
            >
              {label}
            </text>
          );
        })}

        {/* Center score circle */}
        <circle cx={cx} cy={cy} r={26} fill="rgba(200, 16, 46, 0.9)" />
        <circle cx={cx} cy={cy} r={26} fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth={1} />
        <text
          x={cx}
          y={cy - 2}
          textAnchor="middle"
          dominantBaseline="middle"
          fill="#fff"
          fontSize={18}
          fontFamily="'JetBrains Mono', monospace"
          fontWeight={700}
        >
          {avg}
        </text>
        <text
          x={cx}
          y={cy + 12}
          textAnchor="middle"
          dominantBaseline="middle"
          fill="rgba(255,255,255,0.5)"
          fontSize={7}
          fontFamily="'DM Sans', sans-serif"
          fontWeight={600}
          letterSpacing="0.1em"
        >
          MÉDIA
        </text>
      </svg>
    </div>
  );
}
