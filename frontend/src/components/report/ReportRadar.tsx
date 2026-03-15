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

  const rings = [25, 50, 75, 100];

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

  const polyPoints = data
    .map((d, i) => {
      const angle = i * angleStep;
      const r = (Math.min(d.value, 100) / 100) * maxR;
      return polarToXY(angle, r);
    })
    .map(([x, y]) => `${x},${y}`)
    .join(' ');

  const avg = Math.round(data.reduce((s, d) => s + d.value, 0) / n);

  function getLabelAnchor(angle: number): string {
    const deg = ((angle * 180) / Math.PI) % 360;
    if (deg > 30 && deg < 150) return 'start';
    if (deg > 210 && deg < 330) return 'end';
    return 'middle';
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center' }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Light background */}
        <rect width={size} height={size} rx={12} fill="#FAFAF8" />

        {/* Ring polygons */}
        {rings.map((pct, ri) => (
          <polygon
            key={pct}
            points={ringPolygon(pct)}
            fill={ri % 2 === 0 ? 'rgba(0,0,0,0.015)' : 'none'}
            stroke={ri === rings.length - 1 ? '#D4D3D0' : '#E5E4E0'}
            strokeWidth={ri === rings.length - 1 ? 1.2 : 0.6}
          />
        ))}

        {/* Ring labels */}
        {rings.map((pct) => {
          const r = (pct / 100) * maxR;
          return (
            <text
              key={`lbl-${pct}`}
              x={cx + 4}
              y={cy - r + 3}
              fill="#B0B0B0"
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
              stroke="#E5E4E0"
              strokeWidth={0.6}
            />
          );
        })}

        {/* Data polygon */}
        <polygon
          points={polyPoints}
          fill="rgba(200, 16, 46, 0.12)"
          stroke="#C8102E"
          strokeWidth={2}
          strokeLinejoin="round"
        />

        {/* Data dots */}
        {data.map((d, i) => {
          const angle = i * angleStep;
          const r = (Math.min(d.value, 100) / 100) * maxR;
          const [x, y] = polarToXY(angle, r);
          const color = getColor(d.value);
          return (
            <g key={i}>
              <circle cx={x} cy={y} r={6} fill={color} opacity={0.15} />
              <circle cx={x} cy={y} r={3.5} fill={color} stroke="#FAFAF8" strokeWidth={1.5} />
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
          const label = d.name.length > 14 ? d.name.slice(0, 13) + '…' : d.name;

          return (
            <text
              key={`label-${i}`}
              x={lx}
              y={ly}
              textAnchor={anchor}
              dominantBaseline="middle"
              fill="#4A4A4A"
              fontSize={10}
              fontFamily="'DM Sans', sans-serif"
              fontWeight={500}
            >
              {label}
            </text>
          );
        })}

        {/* Center score */}
        <circle cx={cx} cy={cy} r={24} fill="#C8102E" />
        <text
          x={cx}
          y={cy - 2}
          textAnchor="middle"
          dominantBaseline="middle"
          fill="#fff"
          fontSize={16}
          fontFamily="'JetBrains Mono', monospace"
          fontWeight={700}
        >
          {avg}
        </text>
        <text
          x={cx}
          y={cy + 11}
          textAnchor="middle"
          dominantBaseline="middle"
          fill="rgba(255,255,255,0.6)"
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
