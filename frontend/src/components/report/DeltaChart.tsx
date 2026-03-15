interface DeltaChartProps {
  data: Array<{ metric: string; player: number; incumbent: number }>;
  playerName: string;
  incumbentName: string;
  fill?: boolean;
}

export default function DeltaChart({ data, playerName, incumbentName, fill }: DeltaChartProps) {
  if (!data.length) return null;

  const maxVal = Math.max(
    ...data.map((d) => Math.max(d.player, d.incumbent)),
    1,
  );

  const avgDelta =
    data.reduce((sum, d) => sum + (d.player - d.incumbent), 0) / data.length;
  const avgDeltaRounded = Math.round(avgDelta * 10) / 10;
  const deltaPositive = avgDeltaRounded >= 0;

  return (
    <div style={fill ? { display: 'flex', flexDirection: 'column', flex: 1 } : undefined}>
      {/* Delta summary + Legend row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 20, marginBottom: fill ? 12 : 20 }}>
        <div
          style={{
            ...styles.deltaCard,
            marginBottom: 0,
            padding: fill ? '12px 20px' : '20px 24px',
            background: deltaPositive
              ? 'linear-gradient(135deg, #1B9E5A, #15803d)'
              : 'linear-gradient(135deg, #C8102E, #A00D24)',
          }}
        >
          <div style={styles.deltaLabel}>DELTA MÉDIO</div>
          <div style={{ ...styles.deltaValue, fontSize: fill ? 28 : 36 }}>
            {deltaPositive ? '+' : ''}
            {avgDeltaRounded}
          </div>
          <div style={styles.deltaSubtext}>
            vs. {incumbentName}
          </div>
        </div>

        {/* Legend */}
        <div style={{ ...styles.legend, marginBottom: 0, flexDirection: 'column', gap: 6 }}>
          <div style={styles.legendItem}>
            <span style={{ ...styles.legendDot, background: '#C8102E' }} />
            <span style={styles.legendText}>{playerName}</span>
          </div>
          <div style={styles.legendItem}>
            <span style={{ ...styles.legendDot, background: '#B0B0B0' }} />
            <span style={styles.legendText}>{incumbentName}</span>
          </div>
        </div>
      </div>

      {/* Bars */}
      <div style={{
        ...styles.barList,
        flex: fill ? 1 : undefined,
        justifyContent: fill ? 'space-around' : undefined,
      }}>
        {data.map((d, i) => {
          const playerPct = (d.player / maxVal) * 100;
          const incumbentPct = (d.incumbent / maxVal) * 100;
          const diff = Math.round((d.player - d.incumbent) * 10) / 10;

          return (
            <div key={i} style={styles.barRow}>
              <div style={styles.metricLabel}>{d.metric}</div>
              <div style={styles.barContainer}>
                <div style={{ ...styles.barTrack, height: fill ? 10 : 8 }}>
                  <div
                    style={{
                      ...styles.bar,
                      width: `${incumbentPct}%`,
                      background: '#D4D4D4',
                    }}
                  />
                </div>
                <div style={{ ...styles.barTrack, height: fill ? 10 : 8 }}>
                  <div
                    style={{
                      ...styles.bar,
                      width: `${playerPct}%`,
                      background: '#C8102E',
                    }}
                  />
                </div>
              </div>
              <div
                style={{
                  ...styles.diffLabel,
                  color: diff >= 0 ? '#1B9E5A' : '#C8102E',
                }}
              >
                {diff >= 0 ? '+' : ''}
                {diff}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  deltaCard: {
    borderRadius: 10,
    padding: '20px 24px',
    color: '#fff',
    textAlign: 'center',
    marginBottom: 20,
    boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
  },
  deltaLabel: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 10,
    fontWeight: 600,
    letterSpacing: '0.12em',
    opacity: 0.7,
    marginBottom: 4,
  },
  deltaValue: {
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 36,
    fontWeight: 700,
    lineHeight: 1.1,
  },
  deltaSubtext: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 11,
    opacity: 0.6,
    marginTop: 4,
  },
  legend: {
    display: 'flex',
    gap: 20,
    marginBottom: 16,
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
  barList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
  },
  barRow: {
    display: 'grid',
    gridTemplateColumns: '120px 1fr 50px',
    alignItems: 'center',
    gap: 12,
  },
  metricLabel: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 11,
    fontWeight: 500,
    color: '#4A4A4A',
    textAlign: 'right',
  },
  barContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: 3,
  },
  barTrack: {
    height: 8,
    background: '#F7F6F3',
    borderRadius: 4,
    overflow: 'hidden',
  },
  bar: {
    height: '100%',
    borderRadius: 4,
    transition: 'width 0.6s ease',
  },
  diffLabel: {
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 12,
    fontWeight: 700,
    textAlign: 'right',
  },
};
