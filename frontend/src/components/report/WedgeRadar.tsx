/**
 * Elite metrics wedge radar — SkillCorner-inspired pizza chart.
 * No background rect, transparent SVG, full labels (no truncation).
 */

interface WedgeRadarProps {
  data: Array<{ metric: string; p: number }>;
  size?: number;
}

export default function WedgeRadar({ data, size = 380 }: WedgeRadarProps) {
  if (!data.length) return null;

  const cx = size / 2;
  const cy = size / 2;
  const maxR = size / 2 - 70;
  const innerR = maxR * 0.22;
  const n = data.length;
  const wedgeAngle = (2 * Math.PI) / n;
  const gap = 0.03;

  function getWedgeColor(p: number): string {
    if (p >= 95) return '#1B9E5A';
    if (p >= 90) return '#80CBA2';
    if (p >= 85) return '#D97706';
    return '#9CA3AF';
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

  return (
    <div style={styles.container}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
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

        {/* Wedges */}
        {data.map((d, i) => {
          const startAngle = i * wedgeAngle + gap;
          const endAngle = (i + 1) * wedgeAngle - gap;
          const pNorm = Math.min(d.p, 100) / 100;
          const rOuter = innerR + (maxR - innerR) * pNorm;
          const color = getWedgeColor(d.p);

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
          const color = getWedgeColor(d.p);

          return (
            <g key={`label-${i}`}>
              <text
                x={lx}
                y={ly - 6}
                textAnchor={anchor}
                dominantBaseline="middle"
                fill="#4A4A4A"
                fontSize={8.5}
                fontFamily="'DM Sans', sans-serif"
                fontWeight={500}
              >
                {d.metric}
              </text>
              <text
                x={lx}
                y={ly + 7}
                textAnchor={anchor}
                dominantBaseline="middle"
                fill={color}
                fontSize={10}
                fontFamily="'JetBrains Mono', monospace"
                fontWeight={700}
              >
                P{d.p}
              </text>
            </g>
          );
        })}

        {/* Center */}
        <circle cx={cx} cy={cy} r={innerR} fill="#FFFFFF" stroke="#E5E4E0" strokeWidth={1} />
        <text
          x={cx}
          y={cy - 4}
          textAnchor="middle"
          dominantBaseline="middle"
          fill="#1B9E5A"
          fontSize={18}
          fontFamily="'JetBrains Mono', monospace"
          fontWeight={700}
        >
          {data.length}
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
          ELITE
        </text>
      </svg>

      {/* Legend */}
      <div style={styles.legend}>
        <div style={styles.legendItem}>
          <span style={{ ...styles.legendDot, background: '#1B9E5A' }} />
          <span style={styles.legendText}>P95+ Elite</span>
        </div>
        <div style={styles.legendItem}>
          <span style={{ ...styles.legendDot, background: '#80CBA2' }} />
          <span style={styles.legendText}>P90-94 Destaque</span>
        </div>
        <div style={styles.legendItem}>
          <span style={{ ...styles.legendDot, background: '#D97706' }} />
          <span style={styles.legendText}>P85-89 Acima</span>
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
