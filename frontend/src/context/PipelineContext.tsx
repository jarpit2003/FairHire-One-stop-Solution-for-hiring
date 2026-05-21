/**
 * PipelineContext — stub.
 * The legacy in-memory pipeline (runRecruiterPipeline / ReviewQueue) has been removed.
 * This stub keeps imports in Layout and Jobs from breaking while those files still
 * reference setActiveJobId from this context.
 */
import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

interface PipelineContextValue {
  setActiveJobId: (jobId: string) => void;
  activeJobId: string | null;
}

const PipelineContext = createContext<PipelineContextValue | null>(null);

export function PipelineProvider({ children }: { children: ReactNode }) {
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const value = useMemo(() => ({ setActiveJobId, activeJobId }), [setActiveJobId, activeJobId]);
  return <PipelineContext.Provider value={value}>{children}</PipelineContext.Provider>;
}

export function usePipeline() {
  const ctx = useContext(PipelineContext);
  if (!ctx) throw new Error("usePipeline must be used within PipelineProvider");
  return ctx;
}
