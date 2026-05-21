import { useState } from "react";
import { Link } from "react-router-dom";
import {
  Briefcase, Plus, CheckCircle2, Loader2, ArrowRight,
  Share2, ExternalLink, Copy, Twitter, Linkedin, FileText, Globe,
} from "lucide-react";
import Layout from "../components/Layout";
import { jobService } from "../services/api";
import type { JobRecord } from "../services/api";
import { useJobs } from "../context/JobContext";
import { usePipeline } from "../context/PipelineContext";
import { getApiErrorMessage } from "../utils/apiError";

const api_base = "/api/v1";

interface PlatformResult { platform: string; success: boolean; url: string | null; message: string; }

const PLATFORMS = [
  { id: "linkedin",    label: "LinkedIn",    icon: Linkedin,  color: "text-blue-700",  bg: "bg-blue-50 border-blue-200"  },
  { id: "naukri",      label: "Naukri",      icon: Briefcase, color: "text-green-700", bg: "bg-green-50 border-green-200" },
  { id: "x",           label: "X / Twitter", icon: Twitter,   color: "text-gray-800",  bg: "bg-gray-50 border-gray-200"  },
  { id: "google_form", label: "Google Form", icon: FileText,  color: "text-red-700",   bg: "bg-red-50 border-red-200"    },
];

function PlatformBadge({ platform }: { platform: string }) {
  const p = PLATFORMS.find((x) => x.id === platform);
  if (!p) return null;
  const Icon = p.icon;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold border ${p.bg} ${p.color}`}>
      <Icon className="h-3 w-3" /> {p.label}
    </span>
  );
}

function PublishPanel({ job, onDone }: { job: JobRecord; onDone: () => void }) {
  const [selected, setSelected] = useState<Set<string>>(new Set(["linkedin"]));
  const [publishing, setPublishing] = useState(false);
  const [results, setResults] = useState<PlatformResult[]>([]);
  const [copied, setCopied] = useState<string | null>(null);

  const toggle = (id: string) =>
    setSelected((prev) => { const next = new Set(prev); next.has(id) ? next.delete(id) : next.add(id); return next; });

  const handlePublish = async () => {
    if (selected.size === 0) return;
    setPublishing(true); setResults([]);
    try {
      const token = localStorage.getItem("quantumlogic_token");
      const resp = await fetch(`${api_base}/jobs/${job.id}/publish`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({ platforms: Array.from(selected) }),
      });
      const data = await resp.json();
      setResults(data.results ?? []);
      onDone();
    } catch (e) {
      setResults([{ platform: "error", success: false, url: null, message: String(e) }]);
    } finally { setPublishing(false); }
  };

  const copyText = (text: string, key: string) => {
    navigator.clipboard.writeText(text); setCopied(key);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <div className="mt-4 p-5 rounded-xl bg-white/5 border border-white/10 space-y-4">
      <p className="text-sm font-semibold text-white">Publish to platforms</p>
      <div className="flex flex-wrap gap-2">
        {PLATFORMS.map(({ id, label, icon: Icon }) => (
          <button key={id} type="button" onClick={() => toggle(id)}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold transition-all ${
              selected.has(id)
                ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-300"
                : "bg-white/5 border-white/10 text-slate-400 hover:bg-white/10"
            }`}>
            <Icon className="h-3.5 w-3.5" />{label}
          </button>
        ))}
      </div>
      <button type="button" onClick={handlePublish} disabled={publishing || selected.size === 0}
        className="btn-glass-dark inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold disabled:opacity-50" style={{ color: '#fff' }}>
        {publishing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Share2 className="h-4 w-4" />}
        {publishing ? "Publishing…" : "Publish selected"}
      </button>
      {results.length > 0 && (
        <div className="space-y-3">
          {results.map((r) => (
            <div key={r.platform} className={`p-3 rounded-xl border text-sm ${r.success ? "bg-emerald-500/15 border-emerald-500/30" : "bg-amber-500/15 border-amber-500/30"}`}>
              <div className="flex items-center justify-between gap-2 flex-wrap">
                <div className="flex items-center gap-2">
                  <PlatformBadge platform={r.platform} />
                  <span className={r.success ? "text-emerald-300" : "text-amber-300"}>{r.success ? "Published" : "Not published"}</span>
                </div>
                {r.url && (
                  <a href={r.url} target="_blank" rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-400 hover:underline">
                    Open <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </div>
              {r.platform === "x" && !r.success && r.message.includes("Draft tweet") && (
                <div className="mt-2">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-slate-400">Draft tweet:</span>
                    <button type="button" onClick={() => copyText(r.message.split("Draft tweet:\n\n")[1] ?? r.message, "x")}
                      className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:underline">
                      <Copy className="h-3 w-3" />{copied === "x" ? "Copied!" : "Copy"}
                    </button>
                  </div>
                  <pre className="text-xs text-slate-300 bg-white/5 border border-white/10 rounded-lg p-2 whitespace-pre-wrap">{r.message.split("Draft tweet:\n\n")[1] ?? r.message}</pre>
                </div>
              )}
              {r.platform === "google_form" && !r.success && (
                <p className="mt-1 text-xs text-amber-300">{r.message}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Jobs() {
  const { jobs, activeJob, setActiveJobId, reloadJobs, loading } = useJobs();
  const { setActiveJobId: setPipelineJobId } = usePipeline();
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [publishingJobId, setPublishingJobId] = useState<string | null>(null);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    setSaving(true); setError(null);
    try {
      const { data } = await jobService.create({ title: title.trim(), description: description.trim() || null });
      setActiveJobId(data.id); setPipelineJobId(data.id);
      await reloadJobs();
      setTitle(""); setDescription(""); setShowForm(false);
    } catch (err) {
      setError(getApiErrorMessage(err, "Failed to create job"));
    } finally { setSaving(false); }
  };

  const handleSelect = (id: string) => { setActiveJobId(id); setPipelineJobId(id); };

  return (
    <Layout>
      <div className="space-y-6">

        {/* Page header */}
        <div className="glass rounded-2xl p-6">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-4">
              <div className="bg-emerald-500/20 rounded-xl p-3 flex-shrink-0">
                <Briefcase className="h-6 w-6 text-emerald-400" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Jobs</h1>
                <p className="mt-1 text-sm text-slate-400">
                  Create a job, publish to LinkedIn / Naukri / X, and collect applications automatically.
                </p>
              </div>
            </div>
            <button type="button" onClick={() => setShowForm((s) => !s)}
              className="btn-glass-dark inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold" style={{ color: '#fff' }}>
              <Plus className="h-4 w-4" /> New job
            </button>
          </div>
        </div>

        {/* Create form */}
        {showForm && (
          <div className="glass rounded-2xl p-6">
            <h2 className="text-base font-semibold text-white mb-5">Create job requisition</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-slate-300 mb-1.5">Job title</label>
                <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} required
                  placeholder="e.g. Senior Software Engineer"
                  className="w-full px-4 py-2.5 rounded-xl border border-white/10 bg-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 placeholder:text-slate-500" />
              </div>
              <div>
                <label className="block text-sm font-semibold text-slate-300 mb-1.5">
                  Job description <span className="font-normal text-slate-500">(paste full JD)</span>
                </label>
                <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={7}
                  placeholder="Paste the full job description here…"
                  className="w-full px-4 py-3 rounded-xl border border-white/10 bg-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-y min-h-[120px] placeholder:text-slate-500" />
              </div>
              {error && <div className="p-3 rounded-xl bg-red-500/20 border border-red-500/30 text-sm text-red-300">{error}</div>}
              <div className="flex gap-3">
                <button type="submit" disabled={saving || !title.trim()}
                  className="btn-glass-dark inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-50" style={{ color: '#fff' }}>
                  {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                  {saving ? "Creating…" : "Create & activate"}
                </button>
                <button type="button" onClick={() => setShowForm(false)}
                  className="btn-glass px-5 py-2.5 rounded-xl text-sm font-semibold">
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Jobs list */}
        {loading && jobs.length === 0 ? (
          <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 text-emerald-400 animate-spin" /></div>
        ) : jobs.length === 0 ? (
          <div className="glass rounded-2xl p-12 text-center">
            <Briefcase className="h-10 w-10 text-slate-500 mx-auto mb-4" />
            <p className="text-slate-400 mb-4">No job requisitions yet.</p>
            <button type="button" onClick={() => setShowForm(true)}
              className="btn-glass-dark inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold" style={{ color: '#fff' }}>
              <Plus className="h-4 w-4" /> Create your first job
            </button>
          </div>
        ) : (
          <div className="glass rounded-2xl overflow-hidden">
            <ul className="divide-y divide-white/5">
              {jobs.map((job) => {
                const isActive = job.id === activeJob?.id;
                const firstLine = job.description?.trim().split("\n").find((l) => l.trim()) ?? "";
                const published: string[] = (job as any).published_platforms ?? [];
                const isPublishing = publishingJobId === job.id;
                return (
                  <li key={job.id} className={`px-6 py-5 transition-colors ${isActive ? "bg-emerald-500/10" : "hover:bg-white/5"}`}>
                    <div className="flex items-center justify-between gap-4 flex-wrap">
                      <div className="flex items-center gap-3 min-w-0">
                        {isActive
                          ? <CheckCircle2 className="h-5 w-5 text-emerald-400 flex-shrink-0" />
                          : <Briefcase className="h-5 w-5 text-slate-500 flex-shrink-0" />}
                        <div className="min-w-0">
                          <p className={`text-sm font-semibold truncate ${isActive ? "text-emerald-300" : "text-white"}`}>
                            {job.title}
                            {isActive && (
                              <span className="ml-2 text-xs font-medium text-emerald-300 bg-emerald-500/20 px-2 py-0.5 rounded-full">Active</span>
                            )}
                          </p>
                          {firstLine && <p className="text-xs text-slate-500 truncate mt-0.5">{firstLine.slice(0, 100)}</p>}
                          {published.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-1.5">
                              {published.map((p) => <PlatformBadge key={p} platform={p} />)}
                            </div>
                          )}
                          {(job as any).form_url && (
                            <a href={(job as any).form_url} target="_blank" rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 mt-1 text-xs text-emerald-400 hover:underline">
                              <Globe className="h-3 w-3" /> Application form <ExternalLink className="h-3 w-3" />
                            </a>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0 flex-wrap">
                        {!isActive && (
                          <button type="button" onClick={() => handleSelect(job.id)}
                            className="px-3 py-1.5 rounded-lg border border-white/10 text-xs font-semibold text-slate-300 hover:bg-white/10">
                            Activate
                          </button>
                        )}
                        <button type="button" onClick={() => setPublishingJobId(isPublishing ? null : job.id)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-xs font-semibold text-emerald-300 hover:bg-emerald-500/20">
                          <Share2 className="h-3.5 w-3.5" />{isPublishing ? "Close" : "Publish"}
                        </button>
                        <Link to="/process-resumes" onClick={() => handleSelect(job.id)}
                          className="btn-glass-dark inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold" style={{ color: '#fff' }}>
                          Upload Resumes <ArrowRight className="h-3.5 w-3.5" />
                        </Link>
                      </div>
                    </div>
                    {isPublishing && <PublishPanel job={job as any} onDone={() => reloadJobs()} />}
                  </li>
                );
              })}
            </ul>
          </div>
        )}
      </div>
    </Layout>
  );
}
