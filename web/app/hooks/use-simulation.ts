import { useCallback, useRef, useState } from "react";
import {
  streamSimulation,
  type StepResult,
  type SimMeta,
} from "~/lib/api";
import { formToApiPayload, type SimulationFormData } from "~/lib/schemas";

export type SimPhase = "idle" | "running" | "done";

export interface SimulationState {
  phase: SimPhase;
  meta: SimMeta | null;
  steps: StepResult[];
  currentStepIndex: number;
  error: string | null;
}

export function useSimulation() {
  const [state, setState] = useState<SimulationState>({
    phase: "idle",
    meta: null,
    steps: [],
    currentStepIndex: 0,
    error: null,
  });

  const abortRef = useRef<AbortController | null>(null);
  const playbackRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [isPlaying, setIsPlaying] = useState(true);

  const start = useCallback(async (formData: SimulationFormData) => {
    abortRef.current?.abort();
    if (playbackRef.current) clearInterval(playbackRef.current);

    const controller = new AbortController();
    abortRef.current = controller;

    setState({
      phase: "running",
      meta: null,
      steps: [],
      currentStepIndex: 0,
      error: null,
    });
    setIsPlaying(true);

    const payload = formToApiPayload(formData);

    try {
      await streamSimulation(
        payload,
        {
          onMeta: (meta) => {
            setState((prev) => ({ ...prev, meta }));
          },
          onStep: (step) => {
            setState((prev) => ({
              ...prev,
              steps: [...prev.steps, step],
              currentStepIndex: prev.steps.length,
            }));
          },
          onDone: () => {
            setState((prev) => ({ ...prev, phase: "done" }));
          },
          onError: (error) => {
            setState((prev) => ({
              ...prev,
              phase: "idle",
              error: error.message,
            }));
          },
        },
        controller.signal
      );
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setState((prev) => ({
          ...prev,
          phase: "idle",
          error: (err as Error).message,
        }));
      }
    }
  }, []);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    if (playbackRef.current) clearInterval(playbackRef.current);
    setState((prev) => ({ ...prev, phase: "done" }));
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    if (playbackRef.current) clearInterval(playbackRef.current);
    setState({
      phase: "idle",
      meta: null,
      steps: [],
      currentStepIndex: 0,
      error: null,
    });
  }, []);

  const goToStep = useCallback((index: number) => {
    setState((prev) => ({
      ...prev,
      currentStepIndex: Math.max(0, Math.min(index, prev.steps.length - 1)),
    }));
  }, []);

  return {
    ...state,
    isPlaying,
    playbackSpeed,
    setPlaybackSpeed,
    setIsPlaying,
    start,
    stop,
    reset,
    goToStep,
  };
}
