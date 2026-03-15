interface SectionDividerProps {
  number: number;
  title: string;
}

export default function SectionDivider({ number, title }: SectionDividerProps) {
  return (
    <div style={styles.wrapper}>
      <div style={styles.badge}>{number}</div>
      <span style={styles.title}>{title}</span>
      <div style={styles.line} />
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrapper: {
    display: 'flex',
    alignItems: 'center',
    gap: 16,
    margin: '0 0 24px',
  },
  badge: {
    width: 36,
    height: 36,
    borderRadius: 8,
    background: '#C8102E',
    color: '#fff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 16,
    fontWeight: 700,
    fontFamily: "'DM Sans', sans-serif",
    flexShrink: 0,
  },
  title: {
    fontFamily: "'DM Sans', sans-serif",
    fontSize: 22,
    fontWeight: 600,
    color: '#1A1A1A',
    whiteSpace: 'nowrap',
  },
  line: {
    flex: 1,
    height: 2,
    background: 'linear-gradient(90deg, #C8102E 0%, transparent 100%)',
  },
};
