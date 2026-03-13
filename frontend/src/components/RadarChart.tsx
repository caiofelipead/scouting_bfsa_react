import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { getScoreColor } from '../lib/utils';

interface RadarChartProps {
  labels: string[];
  values: number[];
  values2?: number[];
  color1?: string;
  color2?: string;
  size?: number;
  playerName?: string;
  className?: string;
}

export default function RadarChart({
  labels,
  values,
  values2,
  color1,
  color2 = '#3b82f6',
  size = 320,
  playerName,
  className = '',
}: RadarChartProps) {
  const pad = size * 0.12;          // extra padding for labels
  const fullSize = size + pad * 2;  // expanded viewBox
  const center = fullSize / 2;
  const radius = size * 0.34;
  const rings = [0.25, 0.5, 0.75, 1.0];
  const n = labels.length;

  const points = useMemo(() => {
    return values.map((val, i) => {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      const r = (val / 100) * radius;
      return {
        x: center + r * Math.cos(angle),
        y: center + r * Math.sin(angle),
        val,
        label: labels[i],
        angle,
      };
    });
  }, [values, labels, n, center, radius]);

  const points2 = useMemo(() => {
    if (!values2) return null;
    return values2.map((val, i) => {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      const r = (val / 100) * radius;
      return {
        x: center + r * Math.cos(angle),
        y: center + r * Math.sin(angle),
        val,
        label: labels[i],
        angle,
      };
    });
  }, [values2, labels, n, center, radius]);

  const isDual = !!values2 && !!points2;
  const polygonPath = points.map((p) => `${p.x},${p.y}`).join(' ');
  const polygonPath2 = points2 ? points2.map((p) => `${p.x},${p.y}`).join(' ') : '';

  const avgScore = values.length > 0 ? values.reduce((a, b) => a + b, 0) / values.length : 0;
  const avgScore2 = values2 && values2.length > 0 ? values2.reduce((a, b) => a + b, 0) / values2.length : 0;
  const fillColor = color1 || getScoreColor(avgScore);
  const fillColor2 = color2;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className={`relative ${className}`}
    >
      {playerName && (
        <div className="absolute top-0 left-0 right-0 text-center z-10">
          <span
            className="font-[var(--font-display)] text-xs tracking-[0.2em] uppercase"
            style={{ color: 'var(--color-text-muted)' }}
          >
            RADAR
          </span>
        </div>
      )}

      <svg
        viewBox={`0 0 ${fullSize} ${fullSize}`}
        width="100%"
        height="100%"
        className="drop-shadow-lg"
        style={{ overflow: 'visible' }}
      >
        {/* Ring grid lines */}
        {rings.map((ringPct, ri) => {
          const ringR = ringPct * radius;
          const ringPoints = Array.from({ length: n }, (_, i) => {
            const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
            return `${center + ringR * Math.cos(angle)},${center + ringR * Math.sin(angle)}`;
          }).join(' ');
          return (
            <polygon
              key={ri}
              points={ringPoints}
              fill="none"
              stroke="rgba(255,255,255,0.06)"
              strokeWidth="1"
            />
          );
        })}

        {/* Axis lines */}
        {labels.map((_, i) => {
          const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
          return (
            <line
              key={i}
              x1={center}
              y1={center}
              x2={center + radius * Math.cos(angle)}
              y2={center + radius * Math.sin(angle)}
              stroke="rgba(255,255,255,0.04)"
              strokeWidth="1"
            />
          );
        })}

        {/* Data polygon fill — Player 1 */}
        <motion.polygon
          points={polygonPath}
          fill={fillColor}
          fillOpacity={isDual ? 0.4 : 0.12}
          stroke={fillColor}
          strokeWidth="2"
          strokeLinejoin="round"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.3 }}
        />

        {/* Data polygon fill — Player 2 */}
        {isDual && (
          <motion.polygon
            points={polygonPath2}
            fill={fillColor2}
            fillOpacity={0.4}
            stroke={fillColor2}
            strokeWidth="2"
            strokeLinejoin="round"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.4 }}
          />
        )}

        {/* Data points — Player 1 */}
        {points.map((p, i) => (
          <motion.circle
            key={i}
            cx={p.x}
            cy={p.y}
            r={isDual ? 3.5 : 4}
            fill={isDual ? fillColor : getScoreColor(p.val)}
            stroke="var(--color-void)"
            strokeWidth="2"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.4 + i * 0.05, type: 'spring', stiffness: 300 }}
          />
        ))}

        {/* Data points — Player 2 */}
        {isDual && points2!.map((p, i) => (
          <motion.circle
            key={`p2-${i}`}
            cx={p.x}
            cy={p.y}
            r={3.5}
            fill={fillColor2}
            stroke="var(--color-void)"
            strokeWidth="2"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.5 + i * 0.05, type: 'spring', stiffness: 300 }}
          />
        ))}

        {/* Labels */}
        {labels.map((label, i) => {
          const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
          const labelR = radius + 32;
          const lx = center + labelR * Math.cos(angle);
          const ly = center + labelR * Math.sin(angle);
          const val = values[i];
          const anchor =
            Math.abs(Math.cos(angle)) < 0.1
              ? 'middle'
              : Math.cos(angle) > 0
                ? 'start'
                : 'end';

          const val2 = values2?.[i];
          return (
            <g key={i}>
              <text
                x={lx}
                y={ly - 6}
                textAnchor={anchor}
                fill="var(--color-text-secondary)"
                fontSize="9"
                fontFamily="var(--font-body)"
                fontWeight="400"
              >
                {label.length > 18 ? label.slice(0, 18) + '...' : label}
              </text>
              {isDual ? (
                <>
                  <text x={lx} y={ly + 8} textAnchor={anchor} fill={fillColor} fontSize="10" fontFamily="var(--font-mono)" fontWeight="600">
                    {val.toFixed(0)}
                  </text>
                  <text x={lx} y={ly + 20} textAnchor={anchor} fill={fillColor2} fontSize="10" fontFamily="var(--font-mono)" fontWeight="600">
                    {val2 != null ? val2.toFixed(0) : '—'}
                  </text>
                </>
              ) : (
                <text x={lx} y={ly + 8} textAnchor={anchor} fill={getScoreColor(val)} fontSize="11" fontFamily="var(--font-mono)" fontWeight="600">
                  {val.toFixed(0)}
                </text>
              )}
            </g>
          );
        })}

        {/* Center score */}
        {isDual ? (
          <>
            <text x={center} y={center - 10} textAnchor="middle" fill={fillColor} fontSize="18" fontFamily="var(--font-mono)" fontWeight="700">
              {avgScore.toFixed(0)}
            </text>
            <text x={center} y={center + 4} textAnchor="middle" fill="var(--color-text-muted)" fontSize="8" fontFamily="var(--font-display)" letterSpacing="0.1em">
              vs
            </text>
            <text x={center} y={center + 18} textAnchor="middle" fill={fillColor2} fontSize="18" fontFamily="var(--font-mono)" fontWeight="700">
              {avgScore2.toFixed(0)}
            </text>
          </>
        ) : (
          <>
            <text x={center} y={center - 4} textAnchor="middle" fill={fillColor} fontSize="24" fontFamily="var(--font-mono)" fontWeight="700">
              {avgScore.toFixed(0)}
            </text>
            <text x={center} y={center + 14} textAnchor="middle" fill="var(--color-text-muted)" fontSize="8" fontFamily="var(--font-display)" letterSpacing="0.15em">
              AVG PERCENTIL
            </text>
          </>
        )}
      </svg>
    </motion.div>
  );
}
