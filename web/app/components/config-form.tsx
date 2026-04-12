import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  simulationSchema,
  type SimulationFormData,
  loadProfileOptions,
  windModeOptions,
} from "~/lib/schemas";
import { Button } from "~/components/ui/button";
import { Input } from "~/components/ui/input";
import { Label } from "~/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "~/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "~/components/ui/select";
import { Slider } from "~/components/ui/slider";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "~/components/ui/accordion";
import {
  Grid3X3,
  Thermometer,
  Wind,
  Zap,
  Settings,
  Play,
  Clock,
  RotateCw,
} from "lucide-react";

interface ConfigFormProps {
  onSubmit: (data: SimulationFormData) => void;
  isRunning: boolean;
}

function FieldRow({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs text-muted-foreground">{label}</Label>
      {children}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}

export function ConfigForm({ onSubmit, isRunning }: ConfigFormProps) {
  const {
    register,
    handleSubmit,
    control,
    watch,
    formState: { errors },
  } = useForm<SimulationFormData>({
    resolver: zodResolver(simulationSchema),
    defaultValues: {
      rows: 3,
      cols: 5,
      spacing_m: 10,
      base_cop: 4.0,
      max_cooling_kw: 500,
      alpha: 0.7,
      ages_seed: 42,
      wind_mode: "rotating",
      wind_speed: 5.0,
      wind_angle: 90,
      wind_center_angle: 90,
      wind_amplitude_deg: 60,
      wind_period_hours: 12,
      ambient_temp_c: 25,
      load_profile: "sinusoidal",
      base_load_kw: 1200,
      amplitude_kw: 400,
      period_hours: 12,
      duration_hours: 24,
      time_step_hours: 0.5,
    },
  });

  const loadProfile = watch("load_profile");
  const windMode = watch("wind_mode");
  const rows = watch("rows");
  const cols = watch("cols");

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Grid Setup */}
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-base">
            <Grid3X3 className="h-4 w-4 text-primary" />
            Grid Layout
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <FieldRow label="Rows" error={errors.rows?.message}>
              <Input type="number" {...register("rows")} min={1} max={10} />
            </FieldRow>
            <FieldRow label="Columns" error={errors.cols?.message}>
              <Input type="number" {...register("cols")} min={1} max={10} />
            </FieldRow>
            <FieldRow label="Spacing (m)" error={errors.spacing_m?.message}>
              <Input
                type="number"
                step="0.5"
                {...register("spacing_m")}
                min={1}
                max={100}
              />
            </FieldRow>
          </div>
          <div className="flex items-center justify-between rounded-lg bg-secondary/50 px-3 py-2">
            <span className="text-xs text-muted-foreground">
              {rows} &times; {cols} = {rows * cols} chillers
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Chiller Properties */}
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-base">
            <Settings className="h-4 w-4 text-primary" />
            Chiller Properties
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <FieldRow label="Base COP" error={errors.base_cop?.message}>
              <Input
                type="number"
                step="0.1"
                {...register("base_cop")}
                min={0.1}
                max={10}
              />
            </FieldRow>
            <FieldRow
              label="Max Cooling (kW)"
              error={errors.max_cooling_kw?.message}
            >
              <Input
                type="number"
                {...register("max_cooling_kw")}
                min={1}
                max={5000}
              />
            </FieldRow>
            <FieldRow
              label="Alpha (thermal sensitivity)"
              error={errors.alpha?.message}
            >
              <Input
                type="number"
                step="0.1"
                {...register("alpha")}
                min={0}
                max={5}
              />
            </FieldRow>
          </div>
          <FieldRow
            label="Ages Random Seed (determines chiller ages 0-20 years)"
            error={errors.ages_seed?.message}
          >
            <Input
              type="number"
              {...register("ages_seed")}
              min={0}
              max={999999}
              placeholder="42"
            />
          </FieldRow>
          <p className="text-[10px] text-muted-foreground">
            Each chiller is assigned a random age (0-20 years) using this seed.
            Older chillers have degraded capacity.
          </p>
        </CardContent>
      </Card>

      {/* Wind */}
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-base">
            <Wind className="h-4 w-4 text-primary" />
            Wind Conditions
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <FieldRow label="Wind Mode" error={errors.wind_mode?.message}>
              <Controller
                control={control}
                name="wind_mode"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {windModeOptions.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </FieldRow>
            <FieldRow
              label="Wind Speed (m/s)"
              error={errors.wind_speed?.message}
            >
              <Input
                type="number"
                step="0.5"
                {...register("wind_speed")}
                min={0}
                max={50}
              />
            </FieldRow>
          </div>

          {windMode === "constant" ? (
            <FieldRow
              label="Wind Angle (deg)"
              error={errors.wind_angle?.message}
            >
              <Controller
                control={control}
                name="wind_angle"
                render={({ field }) => (
                  <div className="space-y-2">
                    <Slider
                      min={0}
                      max={360}
                      step={5}
                      value={[field.value]}
                      onValueChange={([v]) => field.onChange(v)}
                    />
                    <span className="text-xs text-muted-foreground">
                      {field.value}°
                    </span>
                  </div>
                )}
              />
            </FieldRow>
          ) : (
            <div className="space-y-3 rounded-lg border border-border bg-secondary/20 p-3">
              <div className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                <RotateCw className="h-3 w-3" />
                Rotating Wind Parameters
              </div>
              <div className="grid grid-cols-3 gap-3">
                <FieldRow
                  label="Center Angle (deg)"
                  error={errors.wind_center_angle?.message}
                >
                  <Controller
                    control={control}
                    name="wind_center_angle"
                    render={({ field }) => (
                      <div className="space-y-1.5">
                        <Slider
                          min={0}
                          max={360}
                          step={5}
                          value={[field.value]}
                          onValueChange={([v]) => field.onChange(v)}
                        />
                        <span className="text-[10px] text-muted-foreground">
                          {field.value}°
                        </span>
                      </div>
                    )}
                  />
                </FieldRow>
                <FieldRow
                  label="Swing (± deg)"
                  error={errors.wind_amplitude_deg?.message}
                >
                  <Input
                    type="number"
                    step="5"
                    {...register("wind_amplitude_deg")}
                    min={0}
                    max={180}
                  />
                </FieldRow>
                <FieldRow
                  label="Period (hours)"
                  error={errors.wind_period_hours?.message}
                >
                  <Input
                    type="number"
                    step="1"
                    {...register("wind_period_hours")}
                    min={1}
                    max={168}
                  />
                </FieldRow>
              </div>
              <p className="text-[10px] text-muted-foreground">
                Wind oscillates ±{watch("wind_amplitude_deg")}° around{" "}
                {watch("wind_center_angle")}° with a{" "}
                {watch("wind_period_hours")}h period. This causes different
                chillers to be thermally impacted over time.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Environment */}
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-base">
            <Thermometer className="h-4 w-4 text-primary" />
            Environment
          </CardTitle>
        </CardHeader>
        <CardContent>
          <FieldRow
            label="Ambient Temperature (°C)"
            error={errors.ambient_temp_c?.message}
          >
            <Input
              type="number"
              step="0.5"
              {...register("ambient_temp_c")}
              min={-50}
              max={60}
            />
          </FieldRow>
        </CardContent>
      </Card>

      {/* Load Profile */}
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-base">
            <Zap className="h-4 w-4 text-primary" />
            Load Profile
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <FieldRow label="Profile Type" error={errors.load_profile?.message}>
            <Controller
              control={control}
              name="load_profile"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {loadProfileOptions.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </FieldRow>
          <div className="grid grid-cols-3 gap-4">
            <FieldRow
              label="Base Load (kW)"
              error={errors.base_load_kw?.message}
            >
              <Input
                type="number"
                {...register("base_load_kw")}
                min={1}
                max={50000}
              />
            </FieldRow>
            {loadProfile !== "constant" && (
              <>
                <FieldRow
                  label="Amplitude (kW)"
                  error={errors.amplitude_kw?.message}
                >
                  <Input
                    type="number"
                    {...register("amplitude_kw")}
                    min={0}
                    max={50000}
                  />
                </FieldRow>
                <FieldRow
                  label="Period (hours)"
                  error={errors.period_hours?.message}
                >
                  <Input
                    type="number"
                    step="0.5"
                    {...register("period_hours")}
                    min={0.5}
                    max={168}
                  />
                </FieldRow>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Simulation Control */}
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-base">
            <Clock className="h-4 w-4 text-primary" />
            Simulation
          </CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-2 gap-4">
          <FieldRow
            label="Duration (hours)"
            error={errors.duration_hours?.message}
          >
            <Input
              type="number"
              step="1"
              {...register("duration_hours")}
              min={1}
              max={168}
            />
          </FieldRow>
          <FieldRow
            label="Time Step (hours)"
            error={errors.time_step_hours?.message}
          >
            <Input
              type="number"
              step="0.25"
              {...register("time_step_hours")}
              min={0.25}
              max={24}
            />
          </FieldRow>
        </CardContent>
      </Card>

      {/* Advanced */}
      <Accordion type="single" collapsible>
        <AccordionItem value="advanced" className="border-none">
          <AccordionTrigger className="text-sm text-muted-foreground hover:no-underline">
            Advanced Settings
          </AccordionTrigger>
          <AccordionContent>
            <div className="grid grid-cols-2 gap-4">
              <FieldRow
                label="Dispersion Coefficient"
                error={errors.dispersion_coeff?.message}
              >
                <Input
                  type="number"
                  step="0.1"
                  {...register("dispersion_coeff")}
                  placeholder="1.2 (default)"
                />
              </FieldRow>
              <FieldRow
                label="Switching Threshold (kW)"
                error={errors.switching_threshold_kw?.message}
              >
                <Input
                  type="number"
                  step="1"
                  {...register("switching_threshold_kw")}
                  placeholder="0 (default)"
                />
              </FieldRow>
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>

      <Button type="submit" size="lg" className="w-full" disabled={isRunning}>
        <Play className="mr-2 h-4 w-4" />
        {isRunning ? "Simulating..." : "Run Simulation"}
      </Button>
    </form>
  );
}
