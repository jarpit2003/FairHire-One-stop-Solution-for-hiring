import axios from "axios";

/** Best-effort message from FastAPI `{ detail: string | object }` or generic errors. */
export function getApiErrorMessage(error: unknown, fallback = "Request failed"): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { detail?: unknown } | undefined;
    const d = data?.detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d)) {
      const parts = d.map((x: unknown) =>
        typeof x === "object" && x !== null && "msg" in x ? String((x as { msg: string }).msg) : String(x)
      );
      return parts.join("; ");
    }
    if (error.message) return error.message;
  }
  if (error instanceof Error) return error.message;
  return fallback;
}
