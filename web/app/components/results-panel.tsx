import { useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "~/components/ui/card";
import { WorkChart, SavingsChart, CopChart, LoadChart, WindAngleChart } from "~/components/time-series";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "~/components/ui/tabs";
import { Button } from "~/components/ui/button";
import { RotateCcw, Zap, TrendingDown, Gauge, Clock } from "lucide-react";
import type { StepResult } from "~/lib/api";

interface ResultsPanelProps {
  steps: StepResult[];
  numChillers: number;
  onReset: () => void;
}

function StatCard({
  icon: Icon,
  label,
  value,
  sub,
  accent,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  sub?: string;
  accent?: string;
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4 p-5">
        <div className={`rounded-lg p-2.5 ${accent ?? "bg-primary/10"}`}>
          <Icon className="h-5 w-5 text-primary" />
        </div>
        <div>
          <p className="text-xs text-muted-foreground">{label}</p>
          <p className="text-xl font-bold">{value}</p>
          {sub && <p className="text-xs text-muted-foreground">{sub}</p>}
        </div>
      </CardContent>
    </Card>
  );
}

export function ResultsPanel({ steps, numChillers, onReset }: ResultsPanelProps) {
  const hasRotatingWind = useMemo(() => {
    if (steps.length < 2) return false;
    return steps[0].wind_angle !== steps[1].wind_angle;
  }, [steps]);

  const stats = useMemo(() => {
    if (steps.length === 0) return null;

    const timeStep =
      steps.length > 1
        ? steps[1].time_hours - steps[0].time_hours
        : 1;

    const totalOptimizedKwh = steps.reduce(
      (sum, s) => sum + s.total_work_kw * timeStep,
      0
    );
    const totalBaselineKwh = steps.reduce(
      (sum, s) => sum + s.baseline_work_kw * timeStep,
      0
    );
    const savedKwh = totalBaselineKwh - totalOptimizedKwh;
    const savingsPct =
      totalBaselineKwh > 0 ? (savedKwh / totalBaselineKwh) * 100 : 0;

    const avgSavings =
      steps.reduce((sum, s) => sum + s.savings_fraction, 0) / steps.length;

    const activeCops = steps.flatMap((s) =>
      s.cop_array.filter((c) => c > 0)
    );
    const avgCop =
      activeCops.length > 0
        ? activeCops.reduce((a, b) => a + b, 0) / activeCops.length
        : 0;

    // Per-chiller utilization: fraction of steps each chiller was active
    const utilization = Array.from({ length: numChillers }, (_, i) => {
      const activeCount = steps.filter((s) => s.active_mask[i]).length;
      return {
        name: `C${i}`,
        utilization: Number(((activeCount / steps.length) * 100).toFixed(1)),
      };
    });

    const totalHours = steps[steps.length - 1].time_hours - steps[0].time_hours + timeStep;

    return {
      totalOptimizedKwh,
      totalBaselineKwh,
      savedKwh,
      savingsPct,
      avgSavings,
      avgCop,
      utilization,
      totalHours,
    };
  }, [steps, numChillers]);

  if (!stats) return null;

  const comparisonData = [
    { name: "All-On Baseline", energy: Number(stats.totalBaselineKwh.toFixed(0)) },
    { name: "Optimized", energy: Number(stats.totalOptimizedKwh.toFixed(0)) },
  ];

  return (
    <div className="space-y-6">
      {/* Hero Stats */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          icon={Zap}
          label="Energy Saved"
          value={`${stats.savedKwh.toFixed(0)} kWh`}
          sub={`${stats.savingsPct.toFixed(1)}% reduction`}
          accent="bg-green-500/10"
        />
        <StatCard
          icon={TrendingDown}
          label="Avg Savings / Step"
          value={`${(stats.avgSavings * 100).toFixed(1)}%`}
        />
        <StatCard
          icon={Gauge}
          label="Average COP"
          value={stats.avgCop.toFixed(2)}
          sub="Active chillers only"
        />
        <StatCard
          icon={Clock}
          label="Simulation Duration"
          value={`${stats.totalHours.toFixed(1)} h`}
          sub={`${steps.length} steps`}
        />
      </div>

      {/* Energy Comparison */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Total Energy Comparison
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart
              data={comparisonData}
              layout="vertical"
              margin={{ top: 5, right: 30, bottom: 5, left: 80 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis
                type="number"
                stroke="#71717a"
                tick={{ fill: "#e4e4e7", fontSize: 11 }}
                label={{ value: "Energy (kWh)", position: "insideBottom", offset: -2, fill: "#a1a1aa", fontSize: 11 }}
              />
              <YAxis
                type="category"
                dataKey="name"
                stroke="#71717a"
                tick={{ fill: "#e4e4e7", fontSize: 12 }}
                width={100}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#18181b",
                  border: "1px solid #27272a",
                  borderRadius: 8,
                  fontSize: 12,
                  color: "#e4e4e7",
                }}
                labelStyle={{ color: "#a1a1aa" }}
                itemStyle={{ color: "#e4e4e7" }}
                formatter={(value: number) => [`${value} kWh`, "Energy"]}
              />
              <Bar dataKey="energy" radius={[0, 4, 4, 0]}>
                <Cell fill="#ef4444" />
                <Cell fill="#3b82f6" />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Per-Chiller Utilization */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Chiller Utilization</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={Math.max(120, numChillers * 36)}>
            <BarChart
              data={stats.utilization}
              layout="vertical"
              margin={{ top: 5, right: 30, bottom: 5, left: 40 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis
                type="number"
                domain={[0, 100]}
                stroke="#71717a"
                tick={{ fill: "#e4e4e7", fontSize: 11 }}
                label={{ value: "% Active", position: "insideBottom", offset: -2, fill: "#a1a1aa", fontSize: 11 }}
              />
              <YAxis
                type="category"
                dataKey="name"
                stroke="#71717a"
                tick={{ fill: "#e4e4e7", fontSize: 12 }}
                width={40}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#18181b",
                  border: "1px solid #27272a",
                  borderRadius: 8,
                  fontSize: 12,
                  color: "#e4e4e7",
                }}
                labelStyle={{ color: "#a1a1aa" }}
                itemStyle={{ color: "#e4e4e7" }}
                formatter={(value: number) => [`${value}%`, "Utilization"]}
              />
              <Bar dataKey="utilization" fill="#3b82f6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Detailed Charts */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Detailed Time Series</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="work">
            <TabsList className="mb-4">
              <TabsTrigger value="work">Power</TabsTrigger>
              <TabsTrigger value="savings">Savings</TabsTrigger>
              <TabsTrigger value="cop">COP</TabsTrigger>
              <TabsTrigger value="load">Load</TabsTrigger>
              {hasRotatingWind && (
                <TabsTrigger value="wind">Wind</TabsTrigger>
              )}
            </TabsList>
            <TabsContent value="work">
              <WorkChart steps={steps} />
            </TabsContent>
            <TabsContent value="savings">
              <SavingsChart steps={steps} />
            </TabsContent>
            <TabsContent value="cop">
              <CopChart steps={steps} numChillers={numChillers} />
            </TabsContent>
            <TabsContent value="load">
              <LoadChart steps={steps} />
            </TabsContent>
            {hasRotatingWind && (
              <TabsContent value="wind">
                <WindAngleChart steps={steps} />
              </TabsContent>
            )}
          </Tabs>
        </CardContent>
      </Card>

      <Button variant="outline" size="lg" className="w-full" onClick={onReset}>
        <RotateCcw className="mr-2 h-4 w-4" />
        Run Another Simulation
      </Button>
    </div>
  );
}
