/**
 * Pizza / Wedge radar chart inspired by SkillCorner's radar tool.
 * Each metric gets a wedge (slice) whose radius encodes the percentile value.
 */

interface ReportRadarProps {
  data: Array<{ name: string; value: number }>;
  size?: number;
}

export default function ReportRadar({ data, size = 400 }: ReportRadarProps) {
  if (!data.length) return null;

  const pad = 80;
  const svgSize = size + pad * 2;
  const cx = svgSize / 2;
  const cy = svgSize / 2;
  const maxR = size / 2 - 50;
  const innerR = maxR * 0.15;
  const n = data.length;
  const wedgeAngle = (2 * Math.PI) / n;
  const gap = 0.025;

  function getColor(v: number): string {
    if (v >= 90) return '#1B9E5A';
    if (v >= 75) return '#80CBA2';
    if (v >= 50) return '#D97706';
    if (v >= 25) return '#9CA3AF';
    return '#C8102E';
  }

  function describeArc(
    startAngle: number,
    endAngle: number,
    rInner: number,
    rOuter: number,
  ): string {
    const x1o = cx + rOuter * Math.sin(startAngle);
    const y1o = cy - rOuter * Math.cos(startAngle);
    const x2o = cx + rOuter * Math.sin(endAngle);
    const y2o = cy - rOuter * Math.cos(endAngle);
    const x1i = cx + rInner * Math.sin(endAngle);
    const y1i = cy - rInner * Math.cos(endAngle);
    const x2i = cx + rInner * Math.sin(startAngle);
    const y2i = cy - rInner * Math.cos(startAngle);
    const largeArc = endAngle - startAngle > Math.PI ? 1 : 0;

    return [
      `M ${x1o} ${y1o}`,
      `A ${rOuter} ${rOuter} 0 ${largeArc} 1 ${x2o} ${y2o}`,
      `L ${x1i} ${y1i}`,
      `A ${rInner} ${rInner} 0 ${largeArc} 0 ${x2i} ${y2i}`,
      'Z',
    ].join(' ');
  }

  const rings = [25, 50, 75, 100];
  const avg = Math.round(data.reduce((s, d) => s + d.value, 0) / n);

  return (
    <div style={styles.container}>
      <svg width={svgSize} height={svgSize} viewBox={`0 0 ${svgSize} ${svgSize}`} style={{ maxWidth: '100%', height: 'auto' }}>
        {/* Ring guides */}
        {rings.map((pct) => (
          <circle
            key={pct}
            cx={cx}
            cy={cy}
            r={innerR + ((maxR - innerR) * pct) / 100}
            fill="none"
            stroke="#E5E4E0"
            strokeWidth={0.6}
            strokeDasharray={pct === 100 ? 'none' : '3 5'}
          />
        ))}

        {/* Ring labels */}
        {rings.map((pct) => {
          const r = innerR + ((maxR - innerR) * pct) / 100;
          return (
            <text
              key={`lbl-${pct}`}
              x={cx + 4}
              y={cy - r + 3}
              fill="#B0B0B0"
              fontSize={7}
              fontFamily="'JetBrains Mono', monospace"
              fontWeight={500}
            >
              {pct}
            </text>
          );
        })}

        {/* Axis lines */}
        {data.map((_, i) => {
          const angle = i * wedgeAngle;
          const ex = cx + maxR * Math.sin(angle);
          const ey = cy - maxR * Math.cos(angle);
          return (
            <line
              key={`axis-${i}`}
              x1={cx + innerR * Math.sin(angle)}
              y1={cy - innerR * Math.cos(angle)}
              x2={ex}
              y2={ey}
              stroke="#E5E4E0"
              strokeWidth={0.5}
            />
          );
        })}

        {/* Pizza wedges */}
        {data.map((d, i) => {
          const startAngle = i * wedgeAngle + gap;
          const endAngle = (i + 1) * wedgeAngle - gap;
          const pNorm = Math.min(d.value, 100) / 100;
          const rOuter = innerR + (maxR - innerR) * pNorm;
          const color = getColor(d.value);

          return (
            <path
              key={i}
              d={describeArc(startAngle, endAngle, innerR, rOuter)}
              fill={color}
              opacity={0.75}
              stroke="#FFFFFF"
              strokeWidth={1.5}
            />
          );
        })}

        {/* Outer ring */}
        <circle cx={cx} cy={cy} r={maxR} fill="none" stroke="#D4D3D0" strokeWidth={1} />

        {/* Labels */}
        {data.map((d, i) => {
          const midAngle = (i + 0.5) * wedgeAngle;
          const labelR = maxR + 32;
          const lx = cx + labelR * Math.sin(midAngle);
          const ly = cy - labelR * Math.cos(midAngle);

          const deg = ((midAngle * 180) / Math.PI) % 360;
          const anchor = deg > 30 && deg < 150 ? 'start' : deg > 210 && deg < 330 ? 'end' : 'middle';
          const color = getColor(d.value);

          return (
            <g key={`label-${i}`}>
              <text
                x={lx}
                y={ly - 6}
                textAnchor={anchor}
                dominantBaseline="middle"
                fill="#4A4A4A"
                fontSize={10}
                fontFamily="'DM Sans', sans-serif"
                fontWeight={500}
              >
                {d.name}
              </text>
              <text
                x={lx}
                y={ly + 8}
                textAnchor={anchor}
                dominantBaseline="middle"
                fill={color}
                fontSize={12}
                fontFamily="'JetBrains Mono', monospace"
                fontWeight={700}
              >
                {Math.round(d.value)}
              </text>
            </g>
          );
        })}

        {/* Center circle */}
        <circle cx={cx} cy={cy} r={innerR} fill="#FFFFFF" stroke="#E5E4E0" strokeWidth={1} />
        <text
          x={cx}
          y={cy - 4}
          textAnchor="middle"
          dominantBaseline="middle"
          fill="#C8102E"
          fontSize={18}
          fontFamily="'JetBrains Mono', monospace"
          fontWeight={700}
        >
          {avg}
        </text>
        <text
          x={cx}
          y={cy + 10}
          textAnchor="middle"
          dominantBaseline="middle"
          fill="#8A8A8A"
          fontSize={7}
          fontFamily="'DM Sans', sans-serif"
          fontWeight={700}
          letterSpacing="0.15em"
        >
          MÉDIA
        </text>
      </svg>

      {/* Legend */}
      <div style={styles.legend}>
        <div style={styles.legendItem}>
          <span style={{ ...styles.legendDot, background: '#1B9E5A' }} />
          <span style={styles.legendText}>90+ Elite</span>
        </div>
        <div style={styles.legendItem}>
          <span style={{ ...styles.legendDot, background: '#80CBA2' }} />
          <span style={styles.legendText}>75-89 Acima</span>
        </div>
        <div style={styles.legendItem}>
          <span style={{ ...styles.legendDot, background: '#D97706' }} />
          <span style={styles.legendText}>50-74 Médio</span>
        </div>
        <div style={styles.legendItem}>
          <span style={{ ...styles.legendDot, background: '#9CA3AF' }} />
          <span style={styles.legendText}>25-49 Abaixo</span>
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 12,
  },
  legend: {
    display: 'flex',
    gap: 20,
    justifyContent: 'center',
    flexWrap: 'wrap',
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
  },
  legendDot: {
    width: 10,
    height: 10,
    borderRadius: 3,
    display: 'inline-block',
  },
  legendText: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 10,
    color: '#4A4A4A',
  },
};
