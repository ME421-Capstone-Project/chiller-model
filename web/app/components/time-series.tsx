import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts";
import type { StepResult } from "~/lib/api";

interface TimeSeriesProps {
  steps: StepResult[];
}

export function WorkChart({ steps }: TimeSeriesProps) {
  const data = steps.map((s) => ({
    time: Number(s.time_hours.toFixed(2)),
    optimized: Number(s.total_work_kw.toFixed(1)),
    baseline: Number(s.baseline_work_kw.toFixed(1)),
  }));

  return (
    <ResponsiveContainer width="100%" height={240}>
      <AreaChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
        <XAxis
          dataKey="time"
          stroke="#71717a"
          fontSize={11}
          label={{ value: "Time (h)", position: "insideBottom", offset: -2, fill: "#71717a", fontSize: 11 }}
        />
        <YAxis
          stroke="#71717a"
          fontSize={11}
          label={{ value: "Power (kW)", angle: -90, position: "insideLeft", fill: "#71717a", fontSize: 11 }}
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
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Area
          type="monotone"
          dataKey="baseline"
          stroke="#ef4444"
          fill="#ef444420"
          strokeWidth={2}
          name="All-On Baseline"
          dot={false}
        />
        <Area
          type="monotone"
          dataKey="optimized"
          stroke="#3b82f6"
          fill="#3b82f620"
          strokeWidth={2}
          name="Optimized"
          dot={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function SavingsChart({ steps }: TimeSeriesProps) {
  const data = steps.map((s) => ({
    time: Number(s.time_hours.toFixed(2)),
    savings: Number((s.savings_fraction * 100).toFixed(1)),
  }));

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
        <XAxis
          dataKey="time"
          stroke="#71717a"
          fontSize={11}
          label={{ value: "Time (h)", position: "insideBottom", offset: -2, fill: "#71717a", fontSize: 11 }}
        />
        <YAxis
          stroke="#71717a"
          fontSize={11}
          domain={[0, "auto"]}
          label={{ value: "Savings (%)", angle: -90, position: "insideLeft", fill: "#71717a", fontSize: 11 }}
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
          formatter={(value: number) => [`${value}%`, "Savings"]}
        />
        <Line
          type="monotone"
          dataKey="savings"
          stroke="#22c55e"
          strokeWidth={2}
          dot={false}
          name="Energy Savings"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function WindAngleChart({ steps }: TimeSeriesProps) {
  const data = steps.map((s) => ({
    time: Number(s.time_hours.toFixed(2)),
    angle: Number(s.wind_angle.toFixed(1)),
  }));

  return (
    <ResponsiveContainer width="100%" height={160}>
      <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
        <XAxis dataKey="time" stroke="#71717a" fontSize={11} />
        <YAxis
          stroke="#71717a"
          fontSize={11}
          label={{ value: "Angle (°)", angle: -90, position: "insideLeft", fill: "#71717a", fontSize: 11 }}
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
          formatter={(value: number) => [`${value}°`, "Wind Angle"]}
        />
        <Line
          type="monotone"
          dataKey="angle"
          stroke="#60a5fa"
          strokeWidth={2}
          dot={false}
          name="Wind Angle"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function LoadChart({ steps }: TimeSeriesProps) {
  const data = steps.map((s) => ({
    time: Number(s.time_hours.toFixed(2)),
    load: Number(s.load_kw.toFixed(1)),
  }));

  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
        <XAxis dataKey="time" stroke="#71717a" fontSize={11} />
        <YAxis stroke="#71717a" fontSize={11} />
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
        />
        <Area
          type="monotone"
          dataKey="load"
          stroke="#eab308"
          fill="#eab30820"
          strokeWidth={2}
          dot={false}
          name="Facility Load (kW)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

interface CopChartProps {
  steps: StepResult[];
  numChillers: number;
}

export function CopChart({ steps, numChillers }: CopChartProps) {
  const colors = [
    "#3b82f6", "#22c55e", "#ef4444", "#eab308",
    "#a855f7", "#ec4899", "#06b6d4", "#f97316",
    "#14b8a6", "#8b5cf6", "#f43f5e", "#84cc16",
    "#0ea5e9", "#d946ef", "#fb923c",
  ];

  const data = steps.map((s) => {
    const point: Record<string, number> = {
      time: Number(s.time_hours.toFixed(2)),
    };
    for (let i = 0; i < numChillers; i++) {
      point[`c${i}`] = Number(s.cop_array[i].toFixed(3));
    }
    return point;
  });

  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
        <XAxis dataKey="time" stroke="#71717a" fontSize={11} />
        <YAxis stroke="#71717a" fontSize={11} />
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
        />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        {Array.from({ length: numChillers }, (_, i) => (
          <Line
            key={i}
            type="monotone"
            dataKey={`c${i}`}
            stroke={colors[i % colors.length]}
            strokeWidth={1.5}
            dot={false}
            name={`C${i}`}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
