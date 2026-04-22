import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';

/*
 * Opta-style scatter plot.
 * Props:
 *   points:      array of { x, y, label, category?, team?, age?, minutes?, meta? }
 *   xLabel:      string — x-axis title
 *   yLabel:      string — y-axis title
 *   title:       string — chart title
 *   subtitle:    string — chart subtitle
 *   footnote:    string — lower-right disclaimer (e.g. "*Min. 500 minutes")
 *   categoryColors: map { category -> #hex }
 *   highlightCategories: array of category strings that should render in accent
 *   minOutlierSigma: number (default 1) — label points that exceed mean ± n·SD on either axis
 *   width / height: viewport dimensions in px (default 980 × 560)
 *   onPointClick: (point) => void
 */

const DEFAULT_PALETTE = [
  '#8b5cf6', '#22c55e', '#3b82f6', '#f59e0b', '#06b6d4',
  '#ec4899', '#10b981', '#eab308', '#f97316', '#a855f7',
];

function computeStats(values) {
  const n = values.length;
  if (n === 0) return { mean: 0, sd: 0, min: 0, max: 1 };
  const mean = values.reduce((a, b) => a + b, 0) / n;
  const variance = values.reduce((a, b) => a + (b - mean) ** 2, 0) / Math.max(1, n - 1);
  const sd = Math.sqrt(variance);
  return {
    mean,
    sd,
    min: Math.min(...values),
    max: Math.max(...values),
  };
}

function niceTicks(min, max, count = 5) {
  if (!Number.isFinite(min) || !Number.isFinite(max) || min === max) {
    return [min];
  }
  const range = max - min;
  const rough = range / count;
  const mag = Math.pow(10, Math.floor(Math.log10(rough)));
  const norm = rough / mag;
  let step;
  if (norm < 1.5) step = 1 * mag;
  else if (norm < 3) step = 2 * mag;
  else if (norm < 7) step = 5 * mag;
  else step = 10 * mag;
  const start = Math.ceil(min / step) * step;
  const ticks = [];
  for (let v = start; v <= max + step * 0.0001; v += step) {
    ticks.push(Math.round(v / step) * step);
  }
  return ticks;
}

function formatTick(v) {
  if (v === 0) return '0';
  const abs = Math.abs(v);
  if (abs >= 1000) return `${Math.round(v / 100) / 10}k`;
  if (abs >= 10) return v.toFixed(0);
  if (abs >= 1) return v.toFixed(1);
  return v.toFixed(2);
}

export default function ScatterPlot({
  points = [],
  xLabel = 'X',
  yLabel = 'Y',
  title = 'Scatter',
  subtitle = '',
  footnote = '',
  categoryColors,
  highlightCategories = [],
  minOutlierSigma = 1,
  width = 980,
  height = 560,
  onPointClick,
}) {
  const [hover, setHover] = useState(null);

  const margin = { top: 70, right: 40, bottom: 60, left: 60 };
  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;

  // Build category -> color map (stable)
  const colorMap = useMemo(() => {
    if (categoryColors) return categoryColors;
    const seen = new Map();
    let i = 0;
    for (const p of points) {
      const cat = p.category || 'default';
      if (!seen.has(cat)) {
        seen.set(cat, DEFAULT_PALETTE[i % DEFAULT_PALETTE.length]);
        i += 1;
      }
    }
    return Object.fromEntries(seen);
  }, [points, categoryColors]);

  const xs = useMemo(() => points.map((p) => p.x).filter(Number.isFinite), [points]);
  const ys = useMemo(() => points.map((p) => p.y).filter(Number.isFinite), [points]);
  const xStats = useMemo(() => computeStats(xs), [xs]);
  const yStats = useMemo(() => computeStats(ys), [ys]);

  // Axis domains padded a bit beyond min/max
  const xPad = (xStats.max - xStats.min) * 0.05 || 1;
  const yPad = (yStats.max - yStats.min) * 0.05 || 1;
  const xDomain = [Math.max(0, xStats.min - xPad), xStats.max + xPad];
  const yDomain = [Math.max(0, yStats.min - yPad), yStats.max + yPad];

  const xScale = (v) => ((v - xDomain[0]) / (xDomain[1] - xDomain[0])) * innerW;
  const yScale = (v) => innerH - ((v - yDomain[0]) / (yDomain[1] - yDomain[0])) * innerH;

  const xTicks = useMemo(() => niceTicks(xDomain[0], xDomain[1], 6), [xDomain[0], xDomain[1]]);
  const yTicks = useMemo(() => niceTicks(yDomain[0], yDomain[1], 6), [yDomain[0], yDomain[1]]);

  // Outlier = exceeds mean + k·SD on x or y
  const k = minOutlierSigma;
  const isOutlier = (p) => {
    if (!Number.isFinite(p.x) || !Number.isFinite(p.y)) return false;
    const xOut = p.x > xStats.mean + k * xStats.sd;
    const yOut = p.y > yStats.mean + k * yStats.sd;
    return xOut || yOut;
  };
  const isHighlighted = (p) => highlightCategories.includes(p.category);

  // Pre-compute label positions; simple anti-overlap by offsetting slightly based on index parity
  const labeledPoints = useMemo(
    () => points.map((p, i) => ({ ...p, _i: i, _outlier: isOutlier(p), _highlight: isHighlighted(p) })),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [points, xStats.mean, xStats.sd, yStats.mean, yStats.sd, highlightCategories.join(',')]
  );

  const legendEntries = Object.entries(colorMap);

  return (
    <div className="w-full">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        width="100%"
        preserveAspectRatio="xMidYMid meet"
        style={{
          background: 'linear-gradient(180deg, var(--color-surface-1) 0%, var(--color-surface-0) 100%)',
          borderRadius: 12,
          border: '1px solid var(--color-border-subtle)',
          fontFamily: 'var(--font-body)',
          overflow: 'visible',
        }}
      >
        {/* ── Title / subtitle / brand ─────────────────────────── */}
        <text
          x={margin.left}
          y={28}
          fill="var(--color-text-primary)"
          fontFamily="var(--font-display)"
          fontSize="18"
          fontWeight="700"
          letterSpacing="-0.01em"
        >
          {title}
        </text>
        {subtitle && (
          <text
            x={margin.left}
            y={48}
            fill="var(--color-text-secondary)"
            fontSize="11"
            fontFamily="var(--font-body)"
          >
            {subtitle}
          </text>
        )}
        <g transform={`translate(${width - margin.right - 90}, 24)`}>
          <rect x={0} y={-10} width={10} height={10} fill="var(--color-accent)" rx={1} />
          <text
            x={14}
            y={-1}
            fill="var(--color-text-secondary)"
            fontSize="10"
            fontFamily="var(--font-display)"
            fontWeight="600"
            letterSpacing="0.1em"
          >
            SCOUTING · BFSA
          </text>
        </g>

        {/* ── Plot area ────────────────────────────────────────── */}
        <g transform={`translate(${margin.left}, ${margin.top})`}>
          {/* Frame */}
          <rect
            x={0}
            y={0}
            width={innerW}
            height={innerH}
            fill="transparent"
            stroke="var(--color-border-subtle)"
            strokeWidth={1}
          />

          {/* Horizontal grid */}
          {yTicks.map((t, i) => (
            <g key={`gy-${i}`}>
              <line
                x1={0}
                x2={innerW}
                y1={yScale(t)}
                y2={yScale(t)}
                stroke="rgba(255,255,255,0.05)"
                strokeWidth={1}
              />
              <text
                x={-10}
                y={yScale(t) + 3}
                textAnchor="end"
                fontSize="10"
                fontFamily="var(--font-mono)"
                fill="var(--color-text-muted)"
              >
                {formatTick(t)}
              </text>
            </g>
          ))}

          {/* Vertical grid */}
          {xTicks.map((t, i) => (
            <g key={`gx-${i}`}>
              <line
                x1={xScale(t)}
                x2={xScale(t)}
                y1={0}
                y2={innerH}
                stroke="rgba(255,255,255,0.05)"
                strokeWidth={1}
              />
              <text
                x={xScale(t)}
                y={innerH + 18}
                textAnchor="middle"
                fontSize="10"
                fontFamily="var(--font-mono)"
                fill="var(--color-text-muted)"
              >
                {formatTick(t)}
              </text>
            </g>
          ))}

          {/* Mean lines */}
          <line
            x1={xScale(xStats.mean)}
            x2={xScale(xStats.mean)}
            y1={0}
            y2={innerH}
            stroke="rgba(255,255,255,0.35)"
            strokeWidth={1}
            strokeDasharray="4 4"
          />
          <line
            x1={0}
            x2={innerW}
            y1={yScale(yStats.mean)}
            y2={yScale(yStats.mean)}
            stroke="rgba(255,255,255,0.35)"
            strokeWidth={1}
            strokeDasharray="4 4"
          />
          <text
            x={xScale(xStats.mean) + 6}
            y={12}
            fill="var(--color-text-muted)"
            fontSize="9"
            fontFamily="var(--font-body)"
            fontStyle="italic"
          >
            média {xLabel}
          </text>
          <text
            x={innerW - 6}
            y={yScale(yStats.mean) - 4}
            textAnchor="end"
            fill="var(--color-text-muted)"
            fontSize="9"
            fontFamily="var(--font-body)"
            fontStyle="italic"
          >
            média {yLabel}
          </text>

          {/* ± 1 SD lines (softer) */}
          {xStats.sd > 0 && [xStats.mean + k * xStats.sd, xStats.mean - k * xStats.sd].map((v, i) =>
            v >= xDomain[0] && v <= xDomain[1] ? (
              <line
                key={`xsd-${i}`}
                x1={xScale(v)}
                x2={xScale(v)}
                y1={0}
                y2={innerH}
                stroke="rgba(255,255,255,0.10)"
                strokeWidth={1}
                strokeDasharray="2 4"
              />
            ) : null
          )}
          {yStats.sd > 0 && [yStats.mean + k * yStats.sd, yStats.mean - k * yStats.sd].map((v, i) =>
            v >= yDomain[0] && v <= yDomain[1] ? (
              <line
                key={`ysd-${i}`}
                x1={0}
                x2={innerW}
                y1={yScale(v)}
                y2={yScale(v)}
                stroke="rgba(255,255,255,0.10)"
                strokeWidth={1}
                strokeDasharray="2 4"
              />
            ) : null
          )}

          {/* Points — non-outliers first (muted) */}
          {labeledPoints.map((p) => {
            if (!Number.isFinite(p.x) || !Number.isFinite(p.y)) return null;
            const highlight = p._highlight;
            const outlier = p._outlier;
            if (highlight || outlier) return null;
            const cx = xScale(p.x);
            const cy = yScale(p.y);
            return (
              <motion.circle
                key={`pt-${p._i}`}
                cx={cx}
                cy={cy}
                r={4}
                fill="rgba(161, 161, 170, 0.35)"
                stroke="rgba(255,255,255,0.08)"
                strokeWidth={0.5}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.4, delay: Math.min(0.3, p._i * 0.003) }}
                onMouseEnter={() => setHover(p)}
                onMouseLeave={() => setHover(null)}
                onClick={() => onPointClick && onPointClick(p)}
                style={{ cursor: onPointClick ? 'pointer' : 'default' }}
              />
            );
          })}

          {/* Points — outliers (colored + labeled) */}
          {labeledPoints.map((p) => {
            if (!Number.isFinite(p.x) || !Number.isFinite(p.y)) return null;
            const highlight = p._highlight;
            const outlier = p._outlier;
            if (!(highlight || outlier)) return null;
            const cx = xScale(p.x);
            const cy = yScale(p.y);
            const color = highlight
              ? 'var(--color-accent)'
              : colorMap[p.category] || DEFAULT_PALETTE[0];
            return (
              <g key={`ptH-${p._i}`}>
                <motion.circle
                  cx={cx}
                  cy={cy}
                  r={highlight ? 6.5 : 5.5}
                  fill={color}
                  stroke="var(--color-void)"
                  strokeWidth={1.5}
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ type: 'spring', stiffness: 300, damping: 20, delay: Math.min(0.4, p._i * 0.003) }}
                  onMouseEnter={() => setHover(p)}
                  onMouseLeave={() => setHover(null)}
                  onClick={() => onPointClick && onPointClick(p)}
                  style={{ cursor: onPointClick ? 'pointer' : 'default' }}
                />
                <text
                  x={cx + 9}
                  y={cy + 3}
                  fontSize={highlight ? 11 : 10}
                  fontFamily="var(--font-body)"
                  fontWeight={highlight ? 700 : 500}
                  fill={highlight ? color : 'var(--color-text-primary)'}
                  style={{ pointerEvents: 'none' }}
                >
                  {p.label}
                </text>
              </g>
            );
          })}

          {/* Hover cursor crosshair */}
          {hover && Number.isFinite(hover.x) && Number.isFinite(hover.y) && (
            <>
              <line
                x1={0}
                x2={innerW}
                y1={yScale(hover.y)}
                y2={yScale(hover.y)}
                stroke="rgba(227, 6, 19, 0.35)"
                strokeWidth={1}
                strokeDasharray="2 3"
                pointerEvents="none"
              />
              <line
                x1={xScale(hover.x)}
                x2={xScale(hover.x)}
                y1={0}
                y2={innerH}
                stroke="rgba(227, 6, 19, 0.35)"
                strokeWidth={1}
                strokeDasharray="2 3"
                pointerEvents="none"
              />
            </>
          )}

          {/* Axis titles */}
          <text
            x={innerW / 2}
            y={innerH + 42}
            textAnchor="middle"
            fontFamily="var(--font-display)"
            fontWeight="700"
            fontSize="12"
            fill="var(--color-text-primary)"
            letterSpacing="0.02em"
          >
            {xLabel}
          </text>
          <text
            transform={`translate(${-40}, ${innerH / 2}) rotate(-90)`}
            textAnchor="middle"
            fontFamily="var(--font-display)"
            fontWeight="700"
            fontSize="12"
            fill="var(--color-text-primary)"
            letterSpacing="0.02em"
          >
            {yLabel}
          </text>
        </g>

        {/* Footnote */}
        {footnote && (
          <text
            x={width - margin.right}
            y={height - 10}
            textAnchor="end"
            fontSize="10"
            fontFamily="var(--font-body)"
            fontStyle="italic"
            fill="var(--color-text-muted)"
          >
            {footnote}
          </text>
        )}
      </svg>

      {/* ── Legend + hover tooltip ───────────────────────────── */}
      <div className="flex items-center justify-between mt-3 px-1">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5">
          {highlightCategories.length > 0 && (
            <div className="flex items-center gap-1.5">
              <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: 'var(--color-accent)' }} />
              <span className="text-[10px] font-[var(--font-display)] tracking-[0.12em] uppercase" style={{ color: 'var(--color-text-secondary)' }}>
                Destaque
              </span>
            </div>
          )}
          {legendEntries.map(([cat, color]) => (
            <div key={cat} className="flex items-center gap-1.5">
              <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: color }} />
              <span className="text-[10px] font-[var(--font-display)] tracking-[0.12em] uppercase" style={{ color: 'var(--color-text-secondary)' }}>
                {cat}
              </span>
            </div>
          ))}
          <div className="flex items-center gap-1.5">
            <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: 'rgba(161, 161, 170, 0.6)' }} />
            <span className="text-[10px] font-[var(--font-display)] tracking-[0.12em] uppercase" style={{ color: 'var(--color-text-muted)' }}>
              Amostra
            </span>
          </div>
        </div>
        <div className="text-[10px] font-[var(--font-mono)]" style={{ color: 'var(--color-text-muted)' }}>
          {hover ? (
            <span>
              <span style={{ color: 'var(--color-text-primary)', fontWeight: 600 }}>{hover.label}</span>
              {' · '}
              {xLabel} {formatTick(hover.x)} · {yLabel} {formatTick(hover.y)}
              {hover.team ? ` · ${hover.team}` : ''}
            </span>
          ) : (
            <span>n = {points.length} · μ<sub>x</sub> {formatTick(xStats.mean)} · σ<sub>x</sub> {formatTick(xStats.sd)} · μ<sub>y</sub> {formatTick(yStats.mean)} · σ<sub>y</sub> {formatTick(yStats.sd)}</span>
          )}
        </div>
      </div>
    </div>
  );
}
