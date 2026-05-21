import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Loader2 } from "lucide-react";
import { applicationService, type ApplicationRecord } from "../services/api";
import { useJobs } from "../context/JobContext";
import { getApiErrorMessage } from "../utils/apiError";
import Layout from "../components/Layout";

function stagePillStyle(stage: string) {
  if (stage === 'rejected' || stage === 'offered') 
    return { background: '#f1f5f9', boxShadow: 'inset 0 0 12px rgba(0,0,0,0.09), 0px 0px 1px rgba(0,0,0,0.2)', color: stage === 'offered' ? '#047857' : '#94a3b8' };
  if (stage === 'shortlisted')
    return { background: '#131313', boxShadow: 'inset 0 0 12px rgba(255,255,255,1), 0px 0px 2px rgba(0,0,0,0.1)', color: '#fff' };
  if (stage === 'test_sent' || stage === 'testing')
    return { background: '#1e3a5f', boxShadow: 'inset 0 0 12px rgba(255,255,255,0.6), 0px 0px 2px rgba(0,0,0,0.1)', color: '#fff' };
  if (stage === 'tested')
    return { background: '#1e293b', boxShadow: 'inset 0 0 12px rgba(255,255,255,0.5), 0px 0px 2px rgba(0,0,0,0.1)', color: '#fff' };
  if (stage === 'interview_1' || stage === 'interviewing')
    return { background: '#292524', boxShadow: 'inset 0 0 12px rgba(255,255,255,0.4), 0px 0px 2px rgba(0,0,0,0.1)', color: '#fcd34d' };
  if (stage === 'interview_2')
    return { background: '#1e1b4b', boxShadow: 'inset 0 0 12px rgba(255,255,255,0.4), 0px 0px 2px rgba(0,0,0,0.1)', color: '#c4b5fd' };
  return { background: '#131313', boxShadow: 'inset 0 0 12px rgba(255,255,255,1), 0px 0px 2px rgba(0,0,0,0.1)', color: '#fff' };
}

function stageBadge(stage: string) {
  const map: Record<string, string> = {
    applied: "bg-slate-100 text-slate-700", shortlisted: "bg-cyan-100 text-cyan-800",
    test_sent: "bg-sky-100 text-sky-800", tested: "bg-blue-100 text-blue-800",
    interview_1: "bg-amber-100 text-amber-800", interview_2: "bg-purple-100 text-purple-800",
    offered: "bg-green-100 text-green-800", rejected: "bg-red-100 text-red-700",
    testing: "bg-sky-100 text-sky-800", interviewing: "bg-amber-100 text-amber-800",
  };
  return map[stage] ?? "bg-gray-100 text-gray-700";
}

function stageLabel(stage: string) {
  const map: Record<string, string> = {
    applied: "Applied", shortlisted: "Shortlisted", test_sent: "Test Sent", tested: "Assessment",
    interview_1: "Round 1", interview_2: "Round 2", offered: "Offered", rejected: "Rejected",
    testing: "Test Sent", interviewing: "Interviewing",
  };
  return map[stage] ?? stage;
}

export default function Candidates() {
  const { activeJob } = useJobs();
  const [applications, setApplications] = useState<ApplicationRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!activeJob) return;
    setLoading(true); setError(null);
    try {
      const { data } = await applicationService.list(activeJob.id);
      setApplications(data);
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to load candidates"));
    } finally { setLoading(false); }
  }, [activeJob]);

  useEffect(() => { load(); }, [load]);

  if (!activeJob) {
    return (
      <Layout>
        <div className="max-w-md mx-auto mt-16">
          <div className="glass rounded-2xl p-10 text-center">
            <h1 className="text-xl font-bold text-slate-900">No active job</h1>
            <p className="mt-2 text-sm text-slate-500">Select a job from the navbar to view its candidates.</p>
          </div>
        </div>
      </Layout>
    );
  }

  const sorted = [...applications].sort((a, b) =>
    (b.final_score ?? b.resume_score ?? 0) - (a.final_score ?? a.resume_score ?? 0)
  );

  return (
    <Layout>
      <div className="space-y-6">
        <div className="glass rounded-2xl p-6">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Candidates</h1>
              <p className="mt-1 text-sm text-slate-500">{activeJob.title} · {sorted.length} applicants · sorted by AI score</p>
            </div>
            <button onClick={load} disabled={loading} className="btn-glass px-4 py-2 rounded-xl text-sm font-semibold disabled:opacity-50">
              {loading ? <Loader2 className="h-4 w-4 animate-spin inline" /> : "Refresh"}
            </button>
          </div>
        </div>

        {error && <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-sm text-red-600">{error}</div>}

        {loading && applications.length === 0 ? (
          <div className="flex justify-center py-24"><Loader2 className="h-8 w-8 text-emerald-500 animate-spin" /></div>
        ) : applications.length === 0 ? (
          <div className="glass rounded-2xl p-12 text-center">
            <h2 className="text-lg font-bold text-slate-900">No candidates yet</h2>
            <p className="mt-2 text-sm text-slate-500">Upload resumes to start scoring candidates for <strong>{activeJob.title}</strong>.</p>
            <Link to="/process-resumes" className="btn-glass-dark mt-6 inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold" style={{ color: '#fff' }}>
              Upload Resumes <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        ) : (
          <div className="glass rounded-2xl overflow-hidden">
            <div className="overflow-x-auto" data-lenis-prevent>
              <table className="min-w-full divide-y divide-black/8">
                <thead style={{ background: "rgba(0,0,0,0.03)" }}>
                  <tr>
                    {["Candidate", "Stage", "Resume", "Test", "Interview", "Final Score", "Matched Skills"].map((h) => (
                      <th key={h} className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-black/5">
                  {sorted.map((app, i) => {
                    const finalScore = app.final_score ?? app.resume_score;
                    return (
                      <tr key={app.id} className={`hover:bg-black/3 transition-colors ${i % 2 === 1 ? "bg-black/[0.02]" : ""}`}>
                        <td className="px-6 py-4">
                          <Link to={`/candidates/${app.candidate_id}`} className="text-sm font-semibold text-emerald-600 hover:underline block">{app.candidate_name}</Link>
                          <p className="text-xs text-slate-500 truncate">{app.candidate_email}</p>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-xs font-medium px-2.5 py-1 rounded-full" style={stagePillStyle(app.stage)}>{stageLabel(app.stage)}</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {app.resume_score !== null ? <span className="text-xs font-bold px-2.5 py-1 rounded-full text-slate-700" style={{ background: '#f1f5f9', boxShadow: 'inset 0 0 12px rgba(0,0,0,0.09), 0px 0px 1px rgba(0,0,0,0.2)' }}>{app.resume_score.toFixed(0)}%</span> : <span className="text-xs text-slate-400">—</span>}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {app.test_score !== null ? <span className="text-xs font-bold px-2.5 py-1 rounded-full text-slate-700" style={{ background: '#f1f5f9', boxShadow: 'inset 0 0 12px rgba(0,0,0,0.09), 0px 0px 1px rgba(0,0,0,0.2)' }}>{app.test_score.toFixed(0)}%</span> : <span className="text-xs text-slate-400">—</span>}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {(app.interview_score !== null || app.hr_interview_score !== null) ? (
                            <div className="flex gap-1">
                              {app.interview_score !== null && <span className="text-xs font-bold px-2.5 py-1 rounded-full text-slate-700" style={{ background: '#f1f5f9', boxShadow: 'inset 0 0 12px rgba(0,0,0,0.09), 0px 0px 1px rgba(0,0,0,0.2)' }}>R1: {app.interview_score.toFixed(0)}%</span>}
                              {app.hr_interview_score !== null && <span className="text-xs font-bold px-2.5 py-1 rounded-full text-slate-700" style={{ background: '#f1f5f9', boxShadow: 'inset 0 0 12px rgba(0,0,0,0.09), 0px 0px 1px rgba(0,0,0,0.2)' }}>R2: {app.hr_interview_score.toFixed(0)}%</span>}
                            </div>
                          ) : <span className="text-xs text-slate-400">—</span>}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {finalScore !== null ? <span className="text-sm font-bold px-2.5 py-1.5 rounded-full text-slate-700" style={{ background: '#f1f5f9', boxShadow: 'inset 0 0 12px rgba(0,0,0,0.09), 0px 0px 1px rgba(0,0,0,0.2)' }}>{finalScore.toFixed(0)}%</span> : <span className="text-xs text-slate-400">—</span>}
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex flex-wrap gap-1 max-w-xs">
                            {app.matched_skills.slice(0, 4).map((s) => (
                              <span key={s} className="text-xs font-medium px-2.5 py-1 rounded-full text-slate-600" style={{ background: '#f1f5f9', boxShadow: 'inset 0 0 12px rgba(0,0,0,0.09), 0px 0px 1px rgba(0,0,0,0.2)' }}>{s}</span>
                            ))}
                            {app.matched_skills.length > 4 && <span className="text-xs text-slate-400">+{app.matched_skills.length - 4}</span>}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
