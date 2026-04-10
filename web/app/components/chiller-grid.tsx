import { useMemo } from "react";
import type { StepResult, SimMeta } from "~/lib/api";

interface ChillerGridProps {
  step: StepResult;
  meta: SimMeta;
  prevStep?: StepResult | null;
  baseCop?: number;
  spacingM?: number;
}

const RDYLGN_STOPS = [
  [0.0, "#a50026"],
  [0.1, "#d73027"],
  [0.2, "#f46d43"],
  [0.3, "#fdae61"],
  [0.4, "#fee08b"],
  [0.5, "#ffffbf"],
  [0.6, "#d9ef8b"],
  [0.7, "#a6d96a"],
  [0.8, "#66bd63"],
  [0.9, "#1a9850"],
  [1.0, "#006837"],
] as const;

function interpolateRdYlGn(t: number): string {
  const clamped = Math.max(0, Math.min(1, t));
  for (let i = 0; i < RDYLGN_STOPS.length - 1; i++) {
    const [t0, c0] = RDYLGN_STOPS[i];
    const [t1, c1] = RDYLGN_STOPS[i + 1];
    if (clamped >= t0 && clamped <= t1) {
      const frac = (clamped - t0) / (t1 - t0);
      const r0 = parseInt(c0.slice(1, 3), 16);
      const g0 = parseInt(c0.slice(3, 5), 16);
      const b0 = parseInt(c0.slice(5, 7), 16);
      const r1 = parseInt(c1.slice(1, 3), 16);
      const g1 = parseInt(c1.slice(3, 5), 16);
      const b1 = parseInt(c1.slice(5, 7), 16);
      const r = Math.round(r0 + frac * (r1 - r0));
      const g = Math.round(g0 + frac * (g1 - g0));
      const b = Math.round(b0 + frac * (b1 - b0));
      return `rgb(${r},${g},${b})`;
    }
  }
  return RDYLGN_STOPS[RDYLGN_STOPS.length - 1][1];
}

function generateParticles(
  count: number,
  svgWidth: number,
  svgHeight: number,
  padding: number
) {
  const particles = [];
  const margin = padding * 0.5;
  for (let i = 0; i < count; i++) {
    particles.push({
      id: i,
      startX: -margin + Math.random() * (svgWidth + margin * 2),
      startY: -margin + Math.random() * (svgHeight + margin * 2),
      delay: Math.random() * 3,
      size: 2 + Math.random() * 1.5,
      opacity: 0.3 + Math.random() * 0.45,
    });
  }
  return particles;
}

export function ChillerGrid({
  step,
  meta,
  prevStep,
  baseCop = 4,
  spacingM = 10,
}: ChillerGridProps) {
  const windSpeed = step.wind_speed;
  const windAngle = step.wind_angle;
  const { rows, cols } = meta;

  const layout = useMemo(() => {
    const positions: Array<{ x: number; y: number; row: number; col: number }> = [];
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        positions.push({ x: c * spacingM, y: r * spacingM, row: r, col: c });
      }
    }
    return positions;
  }, [rows, cols, spacingM]);

  const maxRadius = 22;
  const minRadius = 8;
  const padding = 60;
  const plotWidth = (cols - 1) * spacingM;
  const plotHeight = (rows - 1) * spacingM;
  const scale = Math.min(
    400 / Math.max(plotWidth, 1),
    400 / Math.max(plotHeight, 1)
  );
  const svgWidth = plotWidth * scale + padding * 2;
  const svgHeight = plotHeight * scale + padding * 2 + 30;

  const wasActive = useMemo(() => {
    if (!prevStep) return new Set<number>();
    return new Set(
      prevStep.active_mask
        .map((v, i) => (v ? i : -1))
        .filter((i) => i >= 0)
    );
  }, [prevStep]);

  const windRadians = (windAngle * Math.PI) / 180;
  const windDx = Math.cos(windRadians);
  const windDy = -Math.sin(windRadians);

  // Travel distance for particles scales with wind speed
  const travelDist = Math.min(windSpeed * 30, svgWidth * 0.8);
  const particleCount = Math.max(60, Math.min(Math.round(windSpeed * 25), 200));

  const particles = useMemo(
    () => generateParticles(particleCount, svgWidth, svgHeight, padding * 0.3),
    // Re-seed particles when wind angle crosses major thresholds
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [particleCount, svgWidth, svgHeight, Math.round(windAngle / 30)]
  );

  return (
    <div className="flex flex-col items-center">
      <svg
        viewBox={`0 0 ${svgWidth} ${svgHeight}`}
        className="w-full"
        style={{ maxWidth: Math.max(svgWidth, 320) }}
      >
        <defs>
          <radialGradient id="heatGlow">
            <stop offset="0%" stopColor="#ef4444" stopOpacity="0.4" />
            <stop offset="50%" stopColor="#f97316" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#f97316" stopOpacity="0" />
          </radialGradient>
          <radialGradient id="rampGlow">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.6" />
            <stop offset="60%" stopColor="#3b82f6" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="copColorbar" x1="0" y1="1" x2="0" y2="0">
            {RDYLGN_STOPS.map(([t, color]) => (
              <stop key={t} offset={`${t * 100}%`} stopColor={color} />
            ))}
          </linearGradient>
        </defs>

        {/* Axis labels */}
        <text
          x={svgWidth / 2}
          y={svgHeight - 4}
          textAnchor="middle"
          fill="#71717a"
          fontSize={10}
        >
          X Position (m)
        </text>
        <text
          x={12}
          y={svgHeight / 2 - 10}
          textAnchor="middle"
          fill="#71717a"
          fontSize={10}
          transform={`rotate(-90, 12, ${svgHeight / 2 - 10})`}
        >
          Y Position (m)
        </text>

        {/* Grid lines */}
        {Array.from({ length: cols }, (_, c) => {
          const sx = padding + c * spacingM * scale;
          return (
            <g key={`gx-${c}`}>
              <line
                x1={sx} y1={padding - 10}
                x2={sx} y2={padding + plotHeight * scale + 10}
                stroke="#27272a" strokeWidth={0.5} strokeDasharray="3,3"
              />
              <text
                x={sx} y={padding + plotHeight * scale + 24}
                textAnchor="middle" fill="#71717a" fontSize={9}
              >
                {c * spacingM}
              </text>
            </g>
          );
        })}
        {Array.from({ length: rows }, (_, r) => {
          const sy = padding + (rows - 1 - r) * spacingM * scale;
          return (
            <g key={`gy-${r}`}>
              <line
                x1={padding - 10} y1={sy}
                x2={padding + plotWidth * scale + 10} y2={sy}
                stroke="#27272a" strokeWidth={0.5} strokeDasharray="3,3"
              />
              <text
                x={padding - 16} y={sy + 3}
                textAnchor="end" fill="#71717a" fontSize={9}
              >
                {r * spacingM}
              </text>
            </g>
          );
        })}

        {/* Wind particles -- flowing dots */}
        {windSpeed > 0 &&
          particles.map((p) => {
            const dur = 1.5 + Math.random() * 1;
            return (
              <circle
                key={p.id}
                r={p.size}
                fill="#93c5fd"
                opacity={0}
              >
                <animate
                  attributeName="cx"
                  from={String(p.startX)}
                  to={String(p.startX + windDx * travelDist)}
                  dur={`${dur}s`}
                  begin={`${p.delay}s`}
                  repeatCount="indefinite"
                />
                <animate
                  attributeName="cy"
                  from={String(p.startY)}
                  to={String(p.startY + windDy * travelDist)}
                  dur={`${dur}s`}
                  begin={`${p.delay}s`}
                  repeatCount="indefinite"
                />
                <animate
                  attributeName="opacity"
                  values={`0;${p.opacity};${p.opacity};0`}
                  keyTimes="0;0.08;0.75;1"
                  dur={`${dur}s`}
                  begin={`${p.delay}s`}
                  repeatCount="indefinite"
                />
              </circle>
            );
          })}

        {/* Wind speed label */}
        {windSpeed > 0 && (
          <text
            x={svgWidth - 12}
            y={16}
            textAnchor="end"
            fill="#60a5fa"
            fontSize={9}
            fontWeight={600}
          >
            {windSpeed.toFixed(1)} m/s @ {windAngle.toFixed(0)}°
          </text>
        )}

        {/* Chillers */}
        {layout.map((pos, i) => {
          const cx = padding + pos.x * scale;
          const cy = padding + (plotHeight - pos.y) * scale;
          const active = step.active_mask[i];
          const cop = step.cop_array[i];
          const tempRise = step.temp_rise_array[i];
          const maxObservedCop = Math.max(...step.cop_array.filter((c) => c > 0), baseCop * 0.5);
          const normalizedCop = maxObservedCop > 0 ? cop / maxObservedCop : 0;
          const rampFactor = step.ramp_factors?.[i] ?? 1;
          const isRamping = active && rampFactor < 1;

          const justTurnedOn = active && !wasActive.has(i);
          const justTurnedOff = !active && wasActive.has(i);

          const radius = active
            ? minRadius + (maxRadius - minRadius) * Math.min(normalizedCop, 1)
            : minRadius;

          const color = active ? interpolateRdYlGn(normalizedCop) : "#3f3f46";

          return (
            <g key={i}>
              {/* Heat plume for active chillers */}
              {active && tempRise > 0 && (
                <circle
                  cx={cx} cy={cy}
                  r={radius + 8 + tempRise * 6}
                  fill="url(#heatGlow)"
                  className="transition-all duration-700"
                >
                  <animate
                    attributeName="r"
                    values={`${radius + 6 + tempRise * 4};${radius + 12 + tempRise * 8};${radius + 6 + tempRise * 4}`}
                    dur="3s" repeatCount="indefinite"
                  />
                  <animate
                    attributeName="opacity"
                    values="0.7;0.4;0.7"
                    dur="3s" repeatCount="indefinite"
                  />
                </circle>
              )}

              {/* Ramp-up glow for chillers still starting */}
              {isRamping && (
                <circle cx={cx} cy={cy} r={radius + 10} fill="url(#rampGlow)">
                  <animate
                    attributeName="r"
                    values={`${radius + 6};${radius + 14};${radius + 6}`}
                    dur="1.2s" repeatCount="indefinite"
                  />
                  <animate
                    attributeName="opacity"
                    values="0.8;0.3;0.8"
                    dur="1.2s" repeatCount="indefinite"
                  />
                </circle>
              )}

              {/* Startup burst for just-activated */}
              {justTurnedOn && (
                <circle cx={cx} cy={cy} r={radius} fill="url(#rampGlow)">
                  <animate
                    attributeName="r"
                    from={String(radius)} to={String(radius + 30)}
                    dur="0.8s" repeatCount="2"
                  />
                  <animate
                    attributeName="opacity"
                    from="0.9" to="0"
                    dur="0.8s" repeatCount="2"
                  />
                </circle>
              )}

              {/* Shutdown fade */}
              {justTurnedOff && (
                <circle
                  cx={cx} cy={cy} r={maxRadius}
                  fill="none" stroke="#ef4444"
                  strokeWidth={1.5} strokeDasharray="4,3" opacity={0.5}
                >
                  <animate
                    attributeName="opacity" from="0.6" to="0"
                    dur="2s" fill="freeze"
                  />
                </circle>
              )}

              {/* Main chiller circle */}
              <circle
                cx={cx} cy={cy} r={radius}
                fill={color}
                stroke={
                  isRamping
                    ? "#60a5fa"
                    : active
                      ? "#ffffff30"
                      : "#52525b"
                }
                strokeWidth={isRamping ? 2 : active ? 1.5 : 1}
                strokeDasharray={isRamping ? "3,2" : undefined}
                opacity={active ? 1 : 0.35}
                className="transition-all duration-500"
              />

              {/* Label inside circle */}
              {active && radius > 14 && (
                <text
                  x={cx} y={cy - (isRamping ? 2 : 0)}
                  textAnchor="middle" dominantBaseline="central"
                  fill="#fff" fontSize={8} fontWeight={600}
                  className="pointer-events-none"
                >
                  {isRamping
                    ? `${Math.round(rampFactor * 100)}%`
                    : cop.toFixed(2)}
                </text>
              )}

              {/* "RAMP" label for ramping chillers */}
              {isRamping && radius > 14 && (
                <text
                  x={cx} y={cy + 9}
                  textAnchor="middle" dominantBaseline="central"
                  fill="#60a5fa" fontSize={6} fontWeight={600}
                  className="pointer-events-none"
                >
                  RAMP
                </text>
              )}

              {/* Age label below chiller */}
              {meta.ages_years?.[i] != null && (
                <text
                  x={cx} y={cy + radius + 10}
                  textAnchor="middle" dominantBaseline="central"
                  fill="#71717a" fontSize={7}
                  className="pointer-events-none"
                >
                  {meta.ages_years[i].toFixed(0)}yr
                </text>
              )}
            </g>
          );
        })}

        {/* Colorbar */}
        {(() => {
          const cbX = svgWidth - 28;
          const cbY = padding;
          const cbH = plotHeight * scale;
          const cbW = 10;
          return (
            <g>
              <rect
                x={cbX} y={cbY} width={cbW} height={cbH}
                fill="url(#copColorbar)" rx={2}
              />
              <text x={cbX + cbW + 4} y={cbY + 4} fill="#a1a1aa" fontSize={7}>
                1.0
              </text>
              <text x={cbX + cbW + 4} y={cbY + cbH / 2 + 2} fill="#a1a1aa" fontSize={7}>
                0.5
              </text>
              <text x={cbX + cbW + 4} y={cbY + cbH} fill="#a1a1aa" fontSize={7}>
                0.0
              </text>
              <text
                x={cbX + cbW / 2} y={cbY - 8}
                textAnchor="middle" fill="#a1a1aa" fontSize={7}
              >
                COP / COP_base
              </text>
            </g>
          );
        })()}

        {/* Stats overlay */}
        {(() => {
          const boxX = padding;
          const boxY = padding + plotHeight * scale + 34;
          const activeCops = step.cop_array.filter((c) => c > 0);
          const meanCop =
            activeCops.length > 0
              ? activeCops.reduce((a, b) => a + b, 0) / activeCops.length
              : 0;
          return (
            <g>
              <rect
                x={boxX} y={boxY}
                width={plotWidth * scale} height={22}
                rx={4} fill="#18181b" stroke="#27272a" strokeWidth={1}
              />
              <text x={boxX + 8} y={boxY + 14} fill="#a1a1aa" fontSize={9}>
                Total Work: {step.total_work_kw.toFixed(1)} kW
              </text>
              <text
                x={boxX + plotWidth * scale / 2} y={boxY + 14}
                fill="#a1a1aa" fontSize={9}
              >
                Mean COP: {meanCop.toFixed(2)}
              </text>
              <text
                x={boxX + plotWidth * scale - 8} y={boxY + 14}
                textAnchor="end" fill="#22c55e" fontSize={9} fontWeight={600}
              >
                Savings: {(step.savings_fraction * 100).toFixed(1)}%
              </text>
            </g>
          );
        })()}
      </svg>

      {/* Legend */}
      <div className="mt-2 flex flex-wrap items-center justify-center gap-3 text-[10px] text-muted-foreground">
        <div className="flex items-center gap-1">
          <div className="h-3 w-3 rounded-full bg-[#006837]" />
          <span>High COP</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="h-3 w-3 rounded-full bg-[#ffffbf]" />
          <span>Mid COP</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="h-3 w-3 rounded-full bg-[#a50026]" />
          <span>Low COP</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="h-2.5 w-2.5 rounded-full bg-zinc-700 opacity-40" />
          <span>Off</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="h-3 w-3 rounded-full border-2 border-dashed border-blue-400 bg-blue-400/20" />
          <span>Ramping Up</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="h-2 w-2 rounded-full bg-blue-400" />
          <span>Wind</span>
        </div>
      </div>
    </div>
  );
}
