import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { jobService } from "../services/api";
import { useAuth } from "./AuthContext";

export interface Job {
  id: string;
  title: string;
  description: string | null;
}

const STORAGE_KEY = "quantumlogic_active_job_id";

interface JobContextValue {
  jobs: Job[];
  activeJob: Job | null;
  setActiveJobId: (id: string) => void;
  reloadJobs: () => Promise<void>;
  loading: boolean;
}

const JobContext = createContext<JobContextValue | null>(null);

export function JobProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [activeJobId, setActiveJobIdState] = useState<string | null>(
    () => localStorage.getItem(STORAGE_KEY)
  );
  const [loading, setLoading] = useState(false);

  const reloadJobs = useCallback(async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    try {
      const { data } = await jobService.list();
      const fetched: Job[] = data;
      setJobs(fetched);
      setActiveJobIdState((prev) => {
        if (prev && fetched.find((j) => j.id === prev)) return prev;
        const first = fetched[0]?.id ?? null;
        if (first) localStorage.setItem(STORAGE_KEY, first);
        else localStorage.removeItem(STORAGE_KEY);
        return first;
      });
    } catch {
      // silently keep stale state
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (isAuthenticated) reloadJobs();
  }, [isAuthenticated, reloadJobs]);

  const setActiveJobId = useCallback((id: string) => {
    localStorage.setItem(STORAGE_KEY, id);
    setActiveJobIdState(id);
  }, []);

  const activeJob = useMemo(
    () => jobs.find((j) => j.id === activeJobId) ?? null,
    [jobs, activeJobId]
  );

  const value = useMemo(
    () => ({ jobs, activeJob, setActiveJobId, reloadJobs, loading }),
    [jobs, activeJob, setActiveJobId, reloadJobs, loading]
  );

  return <JobContext.Provider value={value}>{children}</JobContext.Provider>;
}

export function useJobs() {
  const ctx = useContext(JobContext);
  if (!ctx) throw new Error("useJobs must be used within JobProvider");
  return ctx;
}
