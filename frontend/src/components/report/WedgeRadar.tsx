interface WedgeRadarProps {
  data: Array<{ metric: string; p: number }>;
  size?: number;
}

export default function WedgeRadar({ data, size = 400 }: WedgeRadarProps) {
  if (!data.length) return null;

  const cx = size / 2;
  const cy = size / 2;
  const maxR = size / 2 - 65;
  const innerR = maxR * 0.22;
  const n = data.length;
  const wedgeAngle = (2 * Math.PI) / n;
  const gap = 0.03;

  function getWedgeColor(p: number): string {
    if (p >= 95) return '#1B9E5A';
    if (p >= 85) return '#80CBA2';
    if (p >= 65) return '#D97706';
    return '#6B7280';
  }

  function getWedgeGlow(p: number): string {
    if (p >= 95) return 'rgba(27, 158, 90, 0.4)';
    if (p >= 85) return 'rgba(128, 203, 162, 0.3)';
    return 'rgba(217, 119, 6, 0.25)';
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
        <defs>
          <radialGradient id="wedgeBg" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#12264a" />
            <stop offset="100%" stopColor="#0C1B37" />
          </radialGradient>
          <filter id="wedgeGlow">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        <rect width={size} height={size} rx={14} fill="url(#wedgeBg)" />

        {/* Background rings */}
        {rings.map((pct) => (
          <circle
            key={pct}
            cx={cx}
            cy={cy}
            r={innerR + ((maxR - innerR) * pct) / 100}
            fill="none"
            stroke="rgba(255,255,255,0.05)"
            strokeWidth={0.8}
            strokeDasharray={pct === 100 ? 'none' : '2 4'}
          />
        ))}

        {/* Axis lines (subtle) */}
        {data.map((_, i) => {
          const midAngle = (i + 0.5) * wedgeAngle;
          const x2 = cx + maxR * Math.sin(midAngle);
          const y2 = cy - maxR * Math.cos(midAngle);
          return (
            <line
              key={`axis-${i}`}
              x1={cx}
              y1={cy}
              x2={x2}
              y2={y2}
              stroke="rgba(255,255,255,0.03)"
              strokeWidth={0.5}
            />
          );
        })}

        {/* Wedges */}
        {data.map((d, i) => {
          const startAngle = i * wedgeAngle + gap;
          const endAngle = (i + 1) * wedgeAngle - gap;
          const pNorm = Math.min(d.p, 100) / 100;
          const rOuter = innerR + (maxR - innerR) * pNorm;
          const color = getWedgeColor(d.p);

          return (
            <g key={i}>
              {/* Glow layer */}
              <path
                d={describeArc(startAngle, endAngle, innerR, rOuter)}
                fill={getWedgeGlow(d.p)}
                filter="url(#wedgeGlow)"
              />
              {/* Main wedge */}
              <path
                d={describeArc(startAngle, endAngle, innerR, rOuter)}
                fill={color}
                opacity={0.8}
                stroke="rgba(255,255,255,0.1)"
                strokeWidth={0.5}
              />
              {/* Outer cap line for emphasis */}
              <path
                d={describeArc(startAngle, endAngle, rOuter - 2, rOuter)}
                fill={color}
                opacity={1}
              />
            </g>
          );
        })}

        {/* Max ring outline */}
        <circle
          cx={cx}
          cy={cy}
          r={maxR}
          fill="none"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth={1}
        />

        {/* Labels */}
        {data.map((d, i) => {
          const midAngle = (i + 0.5) * wedgeAngle;
          const labelR = maxR + 28;
          const lx = cx + labelR * Math.sin(midAngle);
          const ly = cy - labelR * Math.cos(midAngle);

          // Smart text anchor
          const deg = ((midAngle * 180) / Math.PI) % 360;
          const anchor = deg > 30 && deg < 150 ? 'start' : deg > 210 && deg < 330 ? 'end' : 'middle';

          const truncated = d.metric.length > 16 ? d.metric.slice(0, 15) + '…' : d.metric;

          return (
            <g key={`label-${i}`}>
              <text
                x={lx}
                y={ly - 7}
                textAnchor={anchor}
                dominantBaseline="middle"
                fill="rgba(255,255,255,0.65)"
                fontSize={9}
                fontFamily="'DM Sans', sans-serif"
                fontWeight={500}
              >
                {truncated}
              </text>
              <text
                x={lx}
                y={ly + 7}
                textAnchor={anchor}
                dominantBaseline="middle"
                fill={getWedgeColor(d.p)}
                fontSize={11}
                fontFamily="'JetBrains Mono', monospace"
                fontWeight={700}
              >
                P{d.p}
              </text>
            </g>
          );
        })}

        {/* Center circle */}
        <circle cx={cx} cy={cy} r={innerR} fill="#0C1B37" stroke="rgba(255,255,255,0.08)" strokeWidth={1} />
        <text
          x={cx}
          y={cy - 6}
          textAnchor="middle"
          dominantBaseline="middle"
          fill="#80CBA2"
          fontSize={20}
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
          fill="rgba(255,255,255,0.4)"
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
          <span style={styles.legendText}>P95+ Elite absoluta</span>
        </div>
        <div style={styles.legendItem}>
          <span style={{ ...styles.legendDot, background: '#80CBA2' }} />
          <span style={styles.legendText}>P85-94 Destaque</span>
        </div>
        <div style={styles.legendItem}>
          <span style={{ ...styles.legendDot, background: '#D97706' }} />
          <span style={styles.legendText}>P65-84 Acima da média</span>
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
    gap: 20,
  },
  legend: {
    display: 'flex',
    gap: 24,
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
    fontSize: 11,
    color: '#4A4A4A',
  },
};
