import { useNavigate } from "@remix-run/react";
import { useCallback, useState } from "react";
import { ConfigForm } from "~/components/config-form";
import type { SimulationFormData } from "~/lib/schemas";
import { formToApiPayload } from "~/lib/schemas";

export default function Index() {
  const navigate = useNavigate();
  const [isRunning, setIsRunning] = useState(false);

  const handleSubmit = useCallback(
    (data: SimulationFormData) => {
      setIsRunning(true);
      const payload = formToApiPayload(data);
      const encoded = encodeURIComponent(JSON.stringify(payload));
      navigate(`/simulate?config=${encoded}`);
    },
    [navigate]
  );

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border">
        <div className="mx-auto max-w-3xl px-4 py-6">
          <h1 className="text-2xl font-bold tracking-tight">
            Chiller Array Simulator
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Configure your chiller plant layout and environment, then run the
            optimization to see how intelligent scheduling reduces energy
            consumption compared to running all chillers simultaneously.
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-4 py-8">
        <ConfigForm onSubmit={handleSubmit} isRunning={isRunning} />
      </main>
    </div>
  );
}
