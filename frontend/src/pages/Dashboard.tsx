import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Loader2 } from "lucide-react";
import Layout from "../components/Layout";
import { applicationService, interviewService, type ApplicationRecord, type InterviewRecord } from "../services/api";
import { useJobs } from "../context/JobContext";
import { useAuth } from "../context/AuthContext";
import { getApiErrorMessage } from "../utils/apiError";

function stageLabel(stage: string) {
  const map: Record<string, string> = {
    applied: "Applied", shortlisted: "Shortlisted", test_sent: "Test Sent",
    testing: "Testing", assessed: "Assessed", interview_1: "Round 1",
    interview_2: "Round 2", interviewing: "Interviewing", offered: "Offered", rejected: "Rejected",
  };
  return map[stage] ?? stage;
}

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}

function MetricCard({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="glass rounded-2xl p-5">
      <p className="text-2xl font-bold text-slate-900">{value}</p>
      <p className="text-xs font-medium text-slate-500 mt-0.5">{label}</p>
    </div>
  );
}

export default function Dashboard() {
  const { activeJob, jobs } = useJobs();
  const { user } = useAuth();
  const [applications, setApplications] = useState<ApplicationRecord[]>([]);
  const [interviews, setInterviews] = useState<InterviewRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!activeJob) return;
    setLoading(true); setError(null);
    try {
      const [{ data: apps }, { data: ivs }] = await Promise.all([
        applicationService.list(activeJob.id),
        interviewService.list(activeJob.id),
      ]);
      setApplications(apps); setInterviews(ivs);
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to load dashboard"));
    } finally { setLoading(false); }
  }, [activeJob]);

  useEffect(() => { load(); }, [load]);

  if (jobs.length === 0) {
    return (
      <Layout>
        <div className="max-w-md mx-auto mt-16">
          <div className="glass rounded-2xl p-10 text-center">
            <h1 className="text-xl font-bold text-slate-900">Welcome to QuantumLogic Labs</h1>
            <p className="mt-2 text-sm text-slate-500 leading-relaxed">Start by creating a job requisition. Then upload resumes and let AI rank your candidates automatically.</p>
            <Link to="/jobs" className="btn-glass-dark mt-6 inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold" style={{ color: '#fff' }}>
              Create your first job <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </Layout>
    );
  }

  if (!activeJob) {
    return (
      <Layout>
        <div className="max-w-md mx-auto mt-16">
          <div className="glass rounded-2xl p-10 text-center">
            <h1 className="text-xl font-bold text-slate-900">Select a job</h1>
            <p className="mt-2 text-sm text-slate-500">Use the job switcher in the navbar to select an active job.</p>
          </div>
        </div>
      </Layout>
    );
  }

  const active = applications.filter((a) => a.status !== "rejected");
  const avgScore = active.length > 0
    ? Math.round(active.reduce((s, a) => s + (a.final_score ?? a.resume_score ?? 0), 0) / active.length) : 0;
  const interviewReady = applications.filter((a) => (a.final_score ?? a.resume_score ?? 0) >= 70 && a.status !== "rejected").length;
  const upcomingInterviews = interviews.filter((i) => i.status === "scheduled").length;
  const topCandidates = [...applications]
    .filter((a) => a.status !== "rejected")
    .sort((a, b) => (b.final_score ?? b.resume_score ?? 0) - (a.final_score ?? a.resume_score ?? 0))
    .slice(0, 5);
  const stageCounts = ["applied", "shortlisted", "testing", "interviewing", "offered", "rejected"].map((s) => ({
    stage: s, count: applications.filter((a) => a.stage === s).length,
  }));
  const stagePillStyle = (stage: string) => {
    if (stage === 'rejected') return { background: '#f1f5f9', boxShadow: 'inset 0 0 12px rgba(0,0,0,0.09), 0px 0px 1px rgba(0,0,0,0.2)', color: '#94a3b8' };
    if (stage === 'offered') return { background: '#f1f5f9', boxShadow: 'inset 0 0 12px rgba(0,0,0,0.09), 0px 0px 1px rgba(0,0,0,0.2)', color: '#047857' };
    if (stage === 'shortlisted') return { background: '#131313', boxShadow: 'inset 0 0 12px rgba(255,255,255,1), 0px 0px 2px rgba(0,0,0,0.1)', color: '#fff' };
    if (stage === 'test_sent' || stage === 'testing') return { background: '#1e3a5f', boxShadow: 'inset 0 0 12px rgba(255,255,255,0.6), 0px 0px 2px rgba(0,0,0,0.1)', color: '#fff' };
    if (stage === 'interview_1' || stage === 'interview_2' || stage === 'interviewing') return { background: '#292524', boxShadow: 'inset 0 0 12px rgba(255,255,255,0.4), 0px 0px 2px rgba(0,0,0,0.1)', color: '#fcd34d' };
    return { background: '#131313', boxShadow: 'inset 0 0 12px rgba(255,255,255,1), 0px 0px 2px rgba(0,0,0,0.1)', color: '#fff' };
  };
  const upcoming = interviews.filter((i) => i.status === "scheduled").slice(0, 3);

  return (
    <Layout>
      <div className="space-y-6">

        <div className="mb-2 mt-4">
          <h1 className="text-3xl font-bold text-slate-900">{getGreeting()}, {user?.full_name ?? "Recruiter"}</h1>
        </div>

        <div className="glass rounded-2xl p-6">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-semibold text-slate-700 bg-slate-100 border border-slate-200 px-2.5 py-1 rounded-full">{activeJob.title}</span>
              <span className="text-xs text-slate-500">{applications.length} total applicants</span>
            </div>
            <div className="flex gap-2">
              <Link to="/process-resumes" className="btn-glass-dark inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold" style={{ color: '#fff' }}>Upload Resumes</Link>
              <button onClick={load} disabled={loading} className="btn-glass px-4 py-2 rounded-xl text-sm font-semibold disabled:opacity-50">
                {loading ? <Loader2 className="h-4 w-4 animate-spin inline" /> : "Refresh"}
              </button>
            </div>
          </div>
        </div>

        {error && <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-sm text-slate-600">{error}</div>}

        {loading && applications.length === 0 ? (
          <div className="flex justify-center py-24"><Loader2 className="h-8 w-8 text-slate-400 animate-spin" /></div>
        ) : applications.length === 0 ? (
          <div className="glass rounded-2xl p-12 text-center">
            <h2 className="text-lg font-bold text-slate-900">No applications yet</h2>
            <p className="mt-2 text-sm text-slate-500">Upload resumes to start scoring and ranking candidates.</p>
            <Link to="/process-resumes" className="btn-glass-dark mt-6 inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold" style={{ color: '#fff' }}>
              Upload Resumes <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <MetricCard label="Total Applicants" value={applications.length} />
              <MetricCard label="Avg Resume Score" value={`${avgScore}%`} />
              <MetricCard label="Interview Ready" value={interviewReady} />
              <MetricCard label="Upcoming Interviews" value={upcomingInterviews} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 glass rounded-2xl overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
                  <h2 className="text-sm font-bold text-slate-900">Top Candidates</h2>
                  <Link to="/pipeline" className="text-xs font-semibold text-slate-500 hover:text-slate-900 flex items-center gap-1">
                    View all <ArrowRight className="h-3 w-3" />
                  </Link>
                </div>
                <ul className="divide-y divide-slate-100">
                  {topCandidates.map((app, i) => {
                    const score = app.final_score ?? app.resume_score ?? 0;
                    return (
                      <li key={app.id} className="px-6 py-4 flex items-center gap-4 hover:bg-slate-50 transition-colors">
                        <span className="text-xs font-bold text-slate-400 w-4 flex-shrink-0">#{i + 1}</span>
                        <div className="flex-1 min-w-0">
                          <Link to={`/candidates/${app.candidate_id}`} className="text-sm font-semibold text-slate-900 hover:underline truncate block">
                            {app.candidate_name}
                          </Link>
                          <div className="flex items-center gap-1.5 mt-1.5 flex-wrap">
                            <span className="text-xs font-medium px-2.5 py-1 rounded-full" style={stagePillStyle(app.stage)}>
                              {stageLabel(app.stage)}
                            </span>
                            {app.matched_skills.slice(0, 2).map((s) => (
                              <span key={s} className="text-xs font-medium px-2.5 py-1 rounded-full text-slate-600" style={{ background: '#f1f5f9', boxShadow: 'inset 0 0 12px rgba(0,0,0,0.09), 0px 0px 1px rgba(0,0,0,0.2)' }}>{s}</span>
                            ))}
                          </div>
                        </div>
                        <span className="text-sm font-bold text-slate-700 flex-shrink-0" style={{ background: '#f1f5f9', boxShadow: 'inset 0 0 12px rgba(0,0,0,0.09), 0px 0px 1px rgba(0,0,0,0.2)', padding: '4px 12px', borderRadius: '999px' }}>
                          {score.toFixed(0)}%
                        </span>
                      </li>
                    );
                  })}
                </ul>
              </div>

              <div className="space-y-6">
                <div className="glass rounded-2xl overflow-hidden">
                  <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
                    <h2 className="text-sm font-bold text-slate-900">Pipeline Stages</h2>
                    <Link to="/pipeline" className="text-xs font-semibold text-slate-500 hover:text-slate-900 flex items-center gap-1">
                      View <ArrowRight className="h-3 w-3" />
                    </Link>
                  </div>
                  <div className="p-6 space-y-3">
                    {stageCounts.map(({ stage, count }) => (
                      <div key={stage} className="flex items-center gap-3">
                        <span className="text-xs font-medium text-slate-600 w-24 flex-shrink-0">{stageLabel(stage)}</span>
                        <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                          <div className="h-full bg-slate-400 rounded-full transition-all"
                            style={{ width: applications.length > 0 ? `${(count / applications.length) * 100}%` : "0%" }} />
                        </div>
                        <span className="text-xs font-bold text-slate-500 w-4 text-right flex-shrink-0">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="glass rounded-2xl overflow-hidden">
                  <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
                    <h2 className="text-sm font-bold text-slate-900">Upcoming Interviews</h2>
                    <Link to="/interviews" className="text-xs font-semibold text-slate-500 hover:text-slate-900 flex items-center gap-1">
                      View all <ArrowRight className="h-3 w-3" />
                    </Link>
                  </div>
                  {upcoming.length === 0 ? (
                    <div className="p-6 text-center">
                      <p className="text-xs text-slate-400">No upcoming interviews</p>
                      <Link to="/pipeline" className="mt-2 text-xs font-semibold text-slate-600 hover:underline block">Schedule from Pipeline →</Link>
                    </div>
                  ) : (
                    <ul className="divide-y divide-slate-100">
                      {upcoming.map((iv) => (
                        <li key={iv.id} className="px-6 py-4 hover:bg-slate-50 transition-colors">
                          <p className="text-xs font-semibold text-slate-700">Round {iv.round_number}</p>
                          <p className="text-xs text-slate-400 mt-0.5">
                            {iv.scheduled_at ? new Date(iv.scheduled_at).toLocaleString(undefined, { dateStyle: "short", timeStyle: "short" }) : "—"}
                          </p>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {[
                { to: "/process-resumes", label: "Upload Resumes",  desc: "Add candidates to this job" },
                { to: "/pipeline",        label: "Manage Pipeline", desc: "Shortlist, test, interview" },
                { to: "/interviews",      label: "View Interviews", desc: "Scheduled & completed"      },
              ].map(({ to, label, desc }) => (
                <Link key={to} to={to}
                  className="btn-glass-dark inline-flex items-center justify-between gap-4 px-5 py-4 rounded-2xl group"
                  style={{ color: '#fff' }}
                >
                  <div className="min-w-0">
                    <p className="text-sm font-semibold" style={{ color: '#fff' }}>{label}</p>
                    <p className="text-xs mt-0.5" style={{ color: 'rgba(255,255,255,0.6)' }}>{desc}</p>
                  </div>
                  <ArrowRight className="h-4 w-4 flex-shrink-0" style={{ color: 'rgba(255,255,255,0.7)' }} />
                </Link>
              ))}
            </div>
          </>
        )}
      </div>
    </Layout>
  );
}
