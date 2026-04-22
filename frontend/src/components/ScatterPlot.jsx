import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';

/*
 * Opta-style scatter plot.
 *
 * Visual language (inspired by Opta Analyst charts):
 *   - Most points rendered in a neutral gray (the sample).
 *   - "Above-average" outliers (μ + k·σ on either axis) are tinted and labeled.
 *   - "Highlight" points (e.g. TOP SSP) are rendered in the accent color.
 *   - Mean reference lines (dashed) on both axes; optional ±k·σ dashed guides.
 *
 * Props:
 *   points:              array of { x, y, label, category?, team?, meta? }
 *   xLabel / yLabel:     axis titles
 *   title / subtitle:    heading block
 *   footnote:            bottom-right disclaimer
 *   highlightCategories: array of category strings rendered in accent (always labeled)
 *   minOutlierSigma:     numeric threshold for outlier detection (default 1)
 *   maxLabels:           cap on outlier labels to avoid clutter (default 14)
 *   width / height:      viewport dimensions in px
 *   onPointClick:        (point) => void
 */

const HIGHLIGHT_COLOR = 'var(--color-accent)';
const OUTLIER_COLOR = '#8b5cf6'; // soft violet — mirrors Opta's purple above-median tone
const SAMPLE_COLOR = 'rgba(161, 161, 170, 0.28)';

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
  if (!Number.isFinite(min) || !Number.isFinite(max) || min === max) return [min];
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

/**
 * Greedy label placer: given candidate labels with desired (x, y), tries four
 * offset positions (right, left, up-right, down-right) and picks the first that
 * doesn't collide with already-placed labels. Returns { placed, rejected }.
 */
function placeLabels(candidates, innerW, innerH) {
  const placed = [];
  const charW = 5.6;
  const labelH = 12;
  const offsets = [
    { dx: 10, dy: 4, anchor: 'start' },
    { dx: -10, dy: 4, anchor: 'end' },
    { dx: 10, dy: -8, anchor: 'start' },
    { dx: -10, dy: -8, anchor: 'end' },
    { dx: 0, dy: -10, anchor: 'middle' },
    { dx: 0, dy: 14, anchor: 'middle' },
  ];

  for (const c of candidates) {
    let done = false;
    for (const o of offsets) {
      const w = (c.label?.length || 0) * charW;
      let tx = c.cx + o.dx;
      let ty = c.cy + o.dy;
      let x1;
      if (o.anchor === 'start') x1 = tx;
      else if (o.anchor === 'end') x1 = tx - w;
      else x1 = tx - w / 2;
      const y1 = ty - labelH;
      const box = { x1, y1, x2: x1 + w, y2: y1 + 2 };

      // Keep inside plot area with a small margin
      if (box.x1 < 2 || box.x2 > innerW - 2 || box.y1 < 2 || box.y2 > innerH - 2) continue;

      const collides = placed.some((p) => !(box.x2 < p.box.x1 || box.x1 > p.box.x2 || box.y2 < p.box.y1 || box.y1 > p.box.y2));
      if (collides) continue;

      placed.push({ ...c, tx, ty, anchor: o.anchor, box });
      done = true;
      break;
    }
    if (!done) {
      // skip — too crowded
    }
  }
  return placed;
}

export default function ScatterPlot({
  points = [],
  xLabel = 'X',
  yLabel = 'Y',
  title = 'Scatter',
  subtitle = '',
  footnote = '',
  highlightCategories = [],
  minOutlierSigma = 1,
  maxLabels = 14,
  width = 980,
  height = 560,
  onPointClick,
}) {
  const [hover, setHover] = useState(null);

  const margin = { top: 70, right: 40, bottom: 60, left: 60 };
  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;

  const xs = useMemo(() => points.map((p) => p.x).filter(Number.isFinite), [points]);
  const ys = useMemo(() => points.map((p) => p.y).filter(Number.isFinite), [points]);
  const xStats = useMemo(() => computeStats(xs), [xs]);
  const yStats = useMemo(() => computeStats(ys), [ys]);

  const xPad = (xStats.max - xStats.min) * 0.05 || 1;
  const yPad = (yStats.max - yStats.min) * 0.05 || 1;
  const xDomain = [Math.max(0, xStats.min - xPad), xStats.max + xPad];
  const yDomain = [Math.max(0, yStats.min - yPad), yStats.max + yPad];

  const xScale = (v) => ((v - xDomain[0]) / (xDomain[1] - xDomain[0])) * innerW;
  const yScale = (v) => innerH - ((v - yDomain[0]) / (yDomain[1] - yDomain[0])) * innerH;

  const xTicks = useMemo(() => niceTicks(xDomain[0], xDomain[1], 6), [xDomain[0], xDomain[1]]);
  const yTicks = useMemo(() => niceTicks(yDomain[0], yDomain[1], 6), [yDomain[0], yDomain[1]]);

  const k = minOutlierSigma;

  // Classify each point and compute its screen position + a ranking score so
  // we can pick only the most extreme outliers for labeling.
  const classified = useMemo(() => {
    const zx = (v) => (xStats.sd > 0 ? (v - xStats.mean) / xStats.sd : 0);
    const zy = (v) => (yStats.sd > 0 ? (v - yStats.mean) / yStats.sd : 0);
    return points.map((p, i) => {
      const highlight = highlightCategories.includes(p.category);
      const valid = Number.isFinite(p.x) && Number.isFinite(p.y);
      const aboveX = valid && p.x > xStats.mean + k * xStats.sd;
      const aboveY = valid && p.y > yStats.mean + k * yStats.sd;
      const outlier = aboveX || aboveY;
      const score = valid ? Math.hypot(zx(p.x), zy(p.y)) : 0;
      return {
        ...p,
        _i: i,
        _valid: valid,
        _highlight: highlight,
        _outlier: outlier,
        _score: score,
        _cx: valid ? xScale(p.x) : 0,
        _cy: valid ? yScale(p.y) : 0,
      };
    });
  }, [points, xStats.mean, xStats.sd, yStats.mean, yStats.sd, k, innerW, innerH, highlightCategories.join(',')]);

  // Labels: all highlights + top-N outliers ranked by z-score magnitude.
  const labelCandidates = useMemo(() => {
    const highlights = classified.filter((p) => p._valid && p._highlight);
    const outliers = classified
      .filter((p) => p._valid && p._outlier && !p._highlight)
      .sort((a, b) => b._score - a._score)
      .slice(0, Math.max(0, maxLabels - highlights.length));
    return [...highlights, ...outliers].map((p) => ({
      id: p._i,
      cx: p._cx,
      cy: p._cy,
      label: p.label,
      highlight: p._highlight,
    }));
  }, [classified, maxLabels]);

  const placedLabels = useMemo(
    () => placeLabels(labelCandidates, innerW, innerH),
    [labelCandidates, innerW, innerH],
  );
  const labeledIds = useMemo(() => new Set(placedLabels.map((l) => l.id)), [placedLabels]);

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
          overflow: 'hidden',
        }}
      >
        {/* Title / subtitle / brand */}
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
        <g transform={`translate(${width - margin.right - 108}, 24)`}>
          <rect x={0} y={-10} width={10} height={10} fill={HIGHLIGHT_COLOR} rx={1} />
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

        {/* Plot area */}
        <g transform={`translate(${margin.left}, ${margin.top})`}>
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
                stroke="rgba(255,255,255,0.04)"
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
                stroke="rgba(255,255,255,0.04)"
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

          {/* Mean lines (dashed) */}
          <line
            x1={xScale(xStats.mean)}
            x2={xScale(xStats.mean)}
            y1={0}
            y2={innerH}
            stroke="rgba(255,255,255,0.28)"
            strokeWidth={1}
            strokeDasharray="4 4"
          />
          <line
            x1={0}
            x2={innerW}
            y1={yScale(yStats.mean)}
            y2={yScale(yStats.mean)}
            stroke="rgba(255,255,255,0.28)"
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

          {/* Sample points (muted) */}
          {classified.map((p) => {
            if (!p._valid || p._highlight || p._outlier) return null;
            return (
              <circle
                key={`s-${p._i}`}
                cx={p._cx}
                cy={p._cy}
                r={3.2}
                fill={SAMPLE_COLOR}
                onMouseEnter={() => setHover(p)}
                onMouseLeave={() => setHover(null)}
                onClick={() => onPointClick && onPointClick(p)}
                style={{ cursor: onPointClick ? 'pointer' : 'default' }}
              />
            );
          })}

          {/* Outlier points (violet) */}
          {classified.map((p) => {
            if (!p._valid || p._highlight || !p._outlier) return null;
            const labeled = labeledIds.has(p._i);
            return (
              <motion.circle
                key={`o-${p._i}`}
                cx={p._cx}
                cy={p._cy}
                r={labeled ? 5 : 4}
                fill={OUTLIER_COLOR}
                fillOpacity={labeled ? 0.95 : 0.65}
                stroke="var(--color-void)"
                strokeWidth={1}
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.4, delay: Math.min(0.3, p._i * 0.003) }}
                onMouseEnter={() => setHover(p)}
                onMouseLeave={() => setHover(null)}
                onClick={() => onPointClick && onPointClick(p)}
                style={{ cursor: onPointClick ? 'pointer' : 'default' }}
              />
            );
          })}

          {/* Highlighted points (accent) */}
          {classified.map((p) => {
            if (!p._valid || !p._highlight) return null;
            return (
              <motion.circle
                key={`h-${p._i}`}
                cx={p._cx}
                cy={p._cy}
                r={6.5}
                fill={HIGHLIGHT_COLOR}
                stroke="var(--color-void)"
                strokeWidth={1.5}
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 300, damping: 20, delay: Math.min(0.35, p._i * 0.003) }}
                onMouseEnter={() => setHover(p)}
                onMouseLeave={() => setHover(null)}
                onClick={() => onPointClick && onPointClick(p)}
                style={{ cursor: onPointClick ? 'pointer' : 'default' }}
              />
            );
          })}

          {/* Labels — placed with anti-collision */}
          {placedLabels.map((l) => (
            <text
              key={`lbl-${l.id}`}
              x={l.tx}
              y={l.ty}
              textAnchor={l.anchor}
              fontSize={l.highlight ? 11 : 10}
              fontFamily="var(--font-body)"
              fontWeight={l.highlight ? 700 : 500}
              fill={l.highlight ? HIGHLIGHT_COLOR : 'var(--color-text-primary)'}
              style={{ pointerEvents: 'none' }}
            >
              {l.label}
            </text>
          ))}

          {/* Hover crosshair */}
          {hover && hover._valid && (
            <>
              <line
                x1={0}
                x2={innerW}
                y1={hover._cy}
                y2={hover._cy}
                stroke="rgba(227, 6, 19, 0.35)"
                strokeWidth={1}
                strokeDasharray="2 3"
                pointerEvents="none"
              />
              <line
                x1={hover._cx}
                x2={hover._cx}
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

      {/* Compact legend + hover readout */}
      <div className="flex items-center justify-between mt-3 px-1">
        <div className="flex items-center gap-4">
          {highlightCategories.length > 0 && (
            <LegendDot color="var(--color-accent)" label="Destaque" />
          )}
          <LegendDot color={OUTLIER_COLOR} label={`Acima da média (+${minOutlierSigma}σ)`} />
          <LegendDot color="rgba(161, 161, 170, 0.7)" label="Amostra" />
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

function LegendDot({ color, label }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: color }} />
      <span
        className="text-[10px] font-[var(--font-display)] tracking-[0.12em] uppercase"
        style={{ color: 'var(--color-text-secondary)' }}
      >
        {label}
      </span>
    </div>
  );
}
