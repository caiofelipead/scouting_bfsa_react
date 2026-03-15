interface StatBoxProps {
  label: string;
  value: string | number;
  color: string;
  subtitle?: string;
}

export default function StatBox({ label, value, color, subtitle }: StatBoxProps) {
  return (
    <div style={{ ...styles.box, borderTop: `3px solid ${color}` }}>
      <div style={styles.label}>{label}</div>
      <div style={{ ...styles.value, color }}>{value}</div>
      {subtitle && <div style={styles.subtitle}>{subtitle}</div>}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  box: {
    background: '#FFFFFF',
    border: '1px solid #E5E4E0',
    borderRadius: 10,
    padding: '16px 18px',
    boxShadow: '0 3px 10px rgba(0,0,0,0.05)',
    textAlign: 'center',
    flex: 1,
    minWidth: 100,
  },
  label: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 11,
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
    color: '#8A8A8A',
    marginBottom: 6,
  },
  value: {
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 28,
    fontWeight: 700,
    lineHeight: 1.1,
  },
  subtitle: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 11,
    color: '#4A4A4A',
    marginTop: 4,
  },
};
