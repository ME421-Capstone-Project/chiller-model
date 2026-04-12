import { useSearchParams, useNavigate } from "@remix-run/react";
import { useEffect, useMemo, useRef, useCallback, useState } from "react";
import { useSimulation } from "~/hooks/use-simulation";
import { ChillerGrid } from "~/components/chiller-grid";
import { WorkChart, SavingsChart, WindAngleChart } from "~/components/time-series";
import { ResultsPanel } from "~/components/results-panel";
import { Card, CardContent, CardHeader, CardTitle } from "~/components/ui/card";
import { Button } from "~/components/ui/button";
import { Slider } from "~/components/ui/slider";
import {
  Pause,
  Play,
  SkipBack,
  SkipForward,
  Square,
  ArrowLeft,
  Activity,
  Zap,
  TrendingDown,
  Layers,
  Timer,
  Thermometer,
  Wind,
} from "lucide-react";

function LiveStatCard({
  icon: Icon,
  label,
  value,
  accent,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  accent?: string;
}) {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-border bg-card p-3">
      <Icon className={`h-4 w-4 ${accent ?? "text-muted-foreground"}`} />
      <div>
        <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
          {label}
        </p>
        <p className="text-sm font-semibold">{value}</p>
      </div>
    </div>
  );
}

const SPEED_OPTIONS = [
  { label: "0.5x", ms: 6000 },
  { label: "1x", ms: 3000 },
  { label: "2x", ms: 1500 },
  { label: "4x", ms: 750 },
  { label: "8x", ms: 375 },
];

export default function Simulate() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const sim = useSimulation();
  const startedRef = useRef(false);
  const [speedIndex, setSpeedIndex] = useState(1);
  const [isAnimating, setIsAnimating] = useState(true);
  const animFrameRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [displayStepIndex, setDisplayStepIndex] = useState(0);

  const config = useMemo(() => {
    const raw = searchParams.get("config");
    if (!raw) return null;
    try {
      return JSON.parse(decodeURIComponent(raw));
    } catch {
      return null;
    }
  }, [searchParams]);

  // Auto-start the simulation once
  useEffect(() => {
    if (config && !startedRef.current) {
      startedRef.current = true;
      const formData = {
        ...config,
        ambient_temp_c: config.ambient_temp_k - 273.15,
      };
      sim.start(formData);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [config]);

  // Auto-advance animation timer
  useEffect(() => {
    if (animFrameRef.current) clearInterval(animFrameRef.current);

    if (isAnimating && sim.steps.length > 0) {
      const intervalMs = SPEED_OPTIONS[speedIndex].ms;
      animFrameRef.current = setInterval(() => {
        setDisplayStepIndex((prev) => {
          const maxIdx = sim.steps.length - 1;
          if (prev >= maxIdx) {
            if (sim.phase === "done") {
              // Animation finished, stop
              setIsAnimating(false);
              return maxIdx;
            }
            return prev;
          }
          return prev + 1;
        });
      }, intervalMs);
    }

    return () => {
      if (animFrameRef.current) clearInterval(animFrameRef.current);
    };
  }, [isAnimating, speedIndex, sim.steps.length, sim.phase]);

  // Keep display index in bounds when new steps arrive
  useEffect(() => {
    if (sim.steps.length > 0 && displayStepIndex >= sim.steps.length) {
      setDisplayStepIndex(sim.steps.length - 1);
    }
  }, [sim.steps.length, displayStepIndex]);

  const currentStep =
    sim.steps.length > 0
      ? sim.steps[Math.min(displayStepIndex, sim.steps.length - 1)]
      : null;

  const prevStep =
    displayStepIndex > 0 && sim.steps.length > 1
      ? sim.steps[Math.min(displayStepIndex - 1, sim.steps.length - 2)]
      : null;

  const handleReset = useCallback(() => {
    if (animFrameRef.current) clearInterval(animFrameRef.current);
    sim.reset();
    setDisplayStepIndex(0);
    setIsAnimating(true);
    navigate("/");
  }, [sim, navigate]);

  const handleGoToStep = useCallback((idx: number) => {
    setDisplayStepIndex(idx);
    setIsAnimating(false);
  }, []);

  const totalSteps = config
    ? Math.ceil(config.duration_hours / config.time_step_hours)
    : 0;

  // Show results when animation has played through all steps and sim is done
  const animationComplete =
    sim.phase === "done" &&
    sim.steps.length > 0 &&
    !isAnimating &&
    displayStepIndex >= sim.steps.length - 1;

  if (!config) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-center">
          <p className="text-lg text-muted-foreground">
            No simulation configuration found.
          </p>
          <Button variant="outline" className="mt-4" onClick={() => navigate("/")}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Configuration
          </Button>
        </div>
      </div>
    );
  }

  if (sim.error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Card className="max-w-md">
          <CardContent className="p-6 text-center">
            <p className="text-destructive font-medium">Simulation Error</p>
            <p className="mt-2 text-sm text-muted-foreground">{sim.error}</p>
            <Button variant="outline" className="mt-4" onClick={handleReset}>
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Results view after animation finishes
  if (animationComplete) {
    return (
      <div className="min-h-screen bg-background">
        <header className="border-b border-border">
          <div className="mx-auto max-w-5xl px-4 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-xl font-bold tracking-tight">
                  Simulation Results
                </h1>
                <p className="text-sm text-muted-foreground">
                  {config.rows}&times;{config.cols} grid &mdash;{" "}
                  {config.duration_hours}h simulation
                </p>
              </div>
              <Button variant="ghost" size="sm" onClick={handleReset}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                New Simulation
              </Button>
            </div>
          </div>
        </header>
        <main className="mx-auto max-w-5xl px-4 py-8">
          <ResultsPanel
            steps={sim.steps}
            numChillers={sim.meta?.num_chillers ?? config.rows * config.cols}
            onReset={handleReset}
          />
        </main>
      </div>
    );
  }

  // Loading / Running / Animating view
  const progress =
    sim.steps.length > 0 && totalSteps > 0
      ? Math.min(((displayStepIndex + 1) / totalSteps) * 100, 100)
      : 0;

  const dataProgress =
    sim.steps.length > 0 && totalSteps > 0
      ? Math.min((sim.steps.length / totalSteps) * 100, 100)
      : 0;

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border">
        <div className="mx-auto max-w-6xl px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold tracking-tight">
                {sim.phase === "running"
                  ? "Simulating..."
                  : "Simulation Playback"}
              </h1>
              <p className="text-sm text-muted-foreground">
                {config.rows}&times;{config.cols} grid &mdash; t ={" "}
                {currentStep
                  ? `${currentStep.time_hours.toFixed(1)}h`
                  : "0.0h"}{" "}
                / {config.duration_hours}h
              </p>
            </div>
            <div className="flex items-center gap-2">
              {sim.phase === "done" && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setDisplayStepIndex(sim.steps.length - 1);
                    setIsAnimating(false);
                  }}
                >
                  Skip to Results
                </Button>
              )}
              <Button variant="destructive" size="sm" onClick={sim.stop}>
                <Square className="mr-2 h-3 w-3" />
                Stop
              </Button>
            </div>
          </div>
          {/* Progress bars */}
          <div className="mt-3 space-y-1">
            <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
              <span>Animation</span>
              <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-secondary">
                <div
                  className="h-full rounded-full bg-primary transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <span>{Math.round(progress)}%</span>
            </div>
            {sim.phase === "running" && (
              <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                <span>Data</span>
                <div className="h-1 flex-1 overflow-hidden rounded-full bg-secondary">
                  <div
                    className="h-full rounded-full bg-green-500/60 transition-all duration-300"
                    style={{ width: `${dataProgress}%` }}
                  />
                </div>
                <span>
                  {sim.steps.length}/{totalSteps} steps
                </span>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6">
        {currentStep && sim.meta ? (
          <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
            {/* Left: Animated Grid */}
            <div className="space-y-4">
              <Card className="overflow-hidden">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm">
                      Chiller Array &mdash; t ={" "}
                      {currentStep.time_hours.toFixed(1)} h
                    </CardTitle>
                    <span className="rounded bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                      Step {displayStepIndex + 1} / {sim.steps.length}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="pb-4">
                  <ChillerGrid
                    step={currentStep}
                    meta={sim.meta}
                    prevStep={prevStep}
                    baseCop={config.base_cop}
                    spacingM={config.spacing_m}
                  />
                </CardContent>
              </Card>

              {/* Playback controls */}
              <Card>
                <CardContent className="space-y-3 p-4">
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => handleGoToStep(0)}
                    >
                      <SkipBack className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() =>
                        handleGoToStep(Math.max(0, displayStepIndex - 1))
                      }
                    >
                      <ArrowLeft className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant={isAnimating ? "secondary" : "default"}
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => setIsAnimating(!isAnimating)}
                    >
                      {isAnimating ? (
                        <Pause className="h-3.5 w-3.5" />
                      ) : (
                        <Play className="h-3.5 w-3.5" />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() =>
                        handleGoToStep(
                          Math.min(
                            displayStepIndex + 1,
                            sim.steps.length - 1
                          )
                        )
                      }
                    >
                      <SkipForward className="h-3.5 w-3.5" />
                    </Button>

                    {/* Speed selector */}
                    <div className="ml-auto flex items-center gap-1.5">
                      <Timer className="h-3.5 w-3.5 text-muted-foreground" />
                      {SPEED_OPTIONS.map((opt, i) => (
                        <button
                          key={opt.label}
                          onClick={() => setSpeedIndex(i)}
                          className={`rounded px-1.5 py-0.5 text-[10px] font-medium transition-colors ${
                            i === speedIndex
                              ? "bg-primary text-primary-foreground"
                              : "text-muted-foreground hover:bg-secondary"
                          }`}
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Timeline scrubber */}
                  <Slider
                    min={0}
                    max={Math.max(sim.steps.length - 1, 0)}
                    step={1}
                    value={[displayStepIndex]}
                    onValueChange={([v]) => handleGoToStep(v)}
                  />
                  <div className="flex justify-between text-[10px] text-muted-foreground">
                    <span>0h</span>
                    <span>
                      {SPEED_OPTIONS[speedIndex].ms / 1000}s per step
                    </span>
                    <span>{config.duration_hours}h</span>
                  </div>
                </CardContent>
              </Card>

              {/* Live stats */}
              <div className="grid grid-cols-2 gap-2">
                <LiveStatCard
                  icon={Zap}
                  label="Facility Load"
                  value={`${currentStep.load_kw.toFixed(0)} kW`}
                  accent="text-yellow-400"
                />
                <LiveStatCard
                  icon={Activity}
                  label="Optimized Work"
                  value={`${currentStep.total_work_kw.toFixed(0)} kW`}
                  accent="text-blue-400"
                />
                <LiveStatCard
                  icon={TrendingDown}
                  label="Energy Savings"
                  value={`${(currentStep.savings_fraction * 100).toFixed(1)}%`}
                  accent="text-green-400"
                />
                <LiveStatCard
                  icon={Layers}
                  label="Active Chillers"
                  value={`${currentStep.active_mask.filter(Boolean).length} / ${sim.meta.num_chillers}${
                    currentStep.ramp_factors?.filter((r, i) => currentStep.active_mask[i] && r < 1).length
                      ? ` (${currentStep.ramp_factors.filter((r, i) => currentStep.active_mask[i] && r < 1).length} ramping)`
                      : ""
                  }`}
                />
                <LiveStatCard
                  icon={Wind}
                  label="Wind"
                  value={`${currentStep.wind_angle.toFixed(0)}° @ ${currentStep.wind_speed.toFixed(1)} m/s`}
                  accent="text-blue-400"
                />
                <LiveStatCard
                  icon={Thermometer}
                  label="Baseline Work"
                  value={`${currentStep.baseline_work_kw.toFixed(0)} kW`}
                  accent="text-red-400"
                />
              </div>
            </div>

            {/* Right: Live charts */}
            <div className="space-y-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">
                    Power: Optimized vs Baseline
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <WorkChart
                    steps={sim.steps.slice(0, displayStepIndex + 1)}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Energy Savings</CardTitle>
                </CardHeader>
                <CardContent>
                  <SavingsChart
                    steps={sim.steps.slice(0, displayStepIndex + 1)}
                  />
                </CardContent>
              </Card>

              {/* Wind angle chart -- only shown if wind is rotating */}
              {sim.steps.length > 1 &&
                sim.steps[0].wind_angle !== sim.steps[Math.min(1, sim.steps.length - 1)].wind_angle && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Wind Direction</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <WindAngleChart
                        steps={sim.steps.slice(0, displayStepIndex + 1)}
                      />
                    </CardContent>
                  </Card>
                )}
            </div>
          </div>
        ) : (
          <div className="flex h-64 items-center justify-center">
            <div className="text-center">
              <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              <p className="mt-4 text-sm text-muted-foreground">
                Starting simulation...
              </p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
