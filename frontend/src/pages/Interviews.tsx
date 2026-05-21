import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Loader2 } from "lucide-react";
import { interviewService, candidateService, type InterviewRecord, type CandidateRecord } from "../services/api";
import { useJobs } from "../context/JobContext";
import { getApiErrorMessage } from "../utils/apiError";
import Layout from "../components/Layout";

function roundBadge(n: number) {
  const map: Record<number, string> = {
    1: "bg-amber-50 text-amber-800 border-amber-200",
    2: "bg-purple-50 text-purple-800 border-purple-200",
  };
  return map[n] ?? "bg-gray-100 text-gray-700 border-gray-200";
}

function statusBadge(s: string) {
  if (s === "completed") return "bg-green-100 text-green-800 border-green-200";
  if (s === "cancelled") return "bg-red-100 text-red-700 border-red-200";
  return "bg-blue-50 text-blue-800 border-blue-200";
}

function ScoreModal({ interview, onClose, onSaved }: { interview: InterviewRecord; onClose: () => void; onSaved: () => void; }) {
  const [score, setScore] = useState(interview.score?.toString() ?? "");
  const [feedback, setFeedback] = useState(interview.feedback ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async () => {
    const s = parseFloat(score);
    if (isNaN(s) || s < 0 || s > 100) { setError("Score must be 0–100"); return; }
    setSaving(true); setError(null);
    try {
      await interviewService.submitScore(interview.id, s, feedback || undefined);
      onSaved(); onClose();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to save score"));
    } finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 space-y-4">
        <h2 className="text-lg font-bold text-slate-900">Submit Interview Score</h2>
        <p className="text-sm text-slate-500">Round {interview.round_number} · {new Date(interview.scheduled_at ?? "").toLocaleDateString()}</p>
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-1.5">Score (0–100)</label>
          <input type="number" min="0" max="100" value={score} onChange={(e) => setScore(e.target.value)}
            className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500" />
        </div>
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-1.5">Feedback (optional)</label>
          <textarea value={feedback} onChange={(e) => setFeedback(e.target.value)} rows={4}
            placeholder="Technical skills, communication, culture fit…"
            className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-none placeholder:text-slate-400" />
        </div>
        {error && <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl p-3">{error}</p>}
        <div className="flex gap-3 pt-2">
          <button onClick={handleSave} disabled={saving}
            className="btn-glass-dark flex-1 px-4 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-50" style={{ color: '#fff' }}>
            {saving ? "Saving…" : "Save score"}
          </button>
          <button onClick={onClose} className="px-4 py-2.5 rounded-xl border border-slate-200 text-sm font-semibold text-slate-600 hover:bg-slate-50">Cancel</button>
        </div>
      </div>
    </div>
  );
}

export default function Interviews() {
  const { activeJob } = useJobs();
  const [interviews, setInterviews] = useState<InterviewRecord[]>([]);
  const [candidates, setCandidates] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scoreModal, setScoreModal] = useState<InterviewRecord | null>(null);

  const load = useCallback(async () => {
    if (!activeJob) return;
    setLoading(true); setError(null);
    try {
      const [{ data: ivs }, { data: cands }] = await Promise.all([
        interviewService.list(activeJob.id),
        candidateService.list(),
      ]);
      setInterviews(ivs);
      const nameMap: Record<string, string> = {};
      cands.forEach((c: CandidateRecord) => { nameMap[c.id] = c.full_name; });
      setCandidates(nameMap);
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to load interviews"));
    } finally { setLoading(false); }
  }, [activeJob]);

  useEffect(() => { load(); }, [load]);

  const scheduled = interviews.filter((i) => i.status === "scheduled");
  const completed = interviews.filter((i) => i.status === "completed");

  function groupByCandidateId(list: InterviewRecord[]) {
    const map = new Map<string, InterviewRecord[]>();
    list.forEach((iv) => { const arr = map.get(iv.candidate_id) ?? []; arr.push(iv); map.set(iv.candidate_id, arr); });
    return map;
  }

  if (!activeJob) {
    return (
      <Layout>
        <div className="max-w-md mx-auto mt-16">
          <div className="glass rounded-2xl p-10 text-center">
            <h1 className="text-xl font-bold text-slate-900">No active job</h1>
            <p className="mt-2 text-sm text-slate-500">Select a job from the navbar to view its interviews.</p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div className="glass rounded-2xl shadow-card p-6">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Interviews</h1>
              <p className="mt-1 text-sm text-slate-500">{activeJob.title} · {interviews.length} total · {scheduled.length} upcoming</p>
            </div>
            <div className="flex items-center gap-3">
            <Link to="/pipeline" className="btn-glass px-4 py-2 rounded-xl text-sm font-semibold">Pipeline</Link>
              <button onClick={load} disabled={loading} className="btn-glass px-4 py-2 rounded-xl text-sm font-semibold disabled:opacity-50">
                {loading ? <Loader2 className="h-4 w-4 animate-spin inline" /> : "Refresh"}
              </button>
            </div>
          </div>
        </div>

        {error && <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-sm text-red-600">{error}</div>}

        {loading && interviews.length === 0 ? (
          <div className="flex justify-center py-16"><Loader2 className="h-8 w-8 text-emerald-500 animate-spin" /></div>
        ) : interviews.length === 0 ? (
          <div className="glass rounded-2xl shadow-card p-10 text-center">
            <p className="text-slate-500 mb-4">No interviews scheduled yet for this job.</p>
            <Link to="/pipeline" className="btn-glass-dark inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold" style={{ color: '#fff' }}>
              Go to Pipeline <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        ) : (
          <div className="space-y-6">
            {scheduled.length > 0 && (
              <div className="glass rounded-2xl shadow-card overflow-hidden">
                <div className="px-6 py-4 border-b border-black/8 flex items-center gap-2">
                  <h2 className="text-base font-semibold text-slate-900">Upcoming</h2>
                  <span className="ml-auto text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-0.5 rounded-full">{scheduled.length}</span>
                </div>
                <ul className="divide-y divide-black/5">
                  {Array.from(groupByCandidateId(scheduled)).map(([candidateId, ivs]) => (
                    <CandidateInterviewGroup key={candidateId} candidateName={candidates[candidateId] ?? ""} candidateId={candidateId} interviews={ivs} onScore={setScoreModal} />
                  ))}
                </ul>
              </div>
            )}
            {completed.length > 0 && (
              <div className="glass rounded-2xl shadow-card overflow-hidden">
                <div className="px-6 py-4 border-b border-black/8 flex items-center gap-2">
                  <h2 className="text-base font-semibold text-slate-900">Completed</h2>
                  <span className="ml-auto text-xs font-bold bg-slate-100 text-slate-600 px-2.5 py-0.5 rounded-full">{completed.length}</span>
                </div>
                <ul className="divide-y divide-black/5">
                  {Array.from(groupByCandidateId(completed)).map(([candidateId, ivs]) => (
                    <CandidateInterviewGroup key={candidateId} candidateName={candidates[candidateId] ?? ""} candidateId={candidateId} interviews={ivs} onScore={setScoreModal} />
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      {scoreModal && (
        <ScoreModal interview={scoreModal} onClose={() => setScoreModal(null)} onSaved={() => { load(); setScoreModal(null); }} />
      )}
    </Layout>
  );
}

function CandidateInterviewGroup({ candidateName, candidateId, interviews, onScore }: {
  candidateName: string; candidateId: string; interviews: InterviewRecord[]; onScore: (iv: InterviewRecord) => void;
}) {
  return (
    <li className="px-6 py-4 hover:bg-black/3 transition-colors">
      <div className="flex items-center gap-3 mb-3">
        <Link to={`/candidates/${candidateId}`} className="text-sm font-semibold text-emerald-600 hover:underline">
          {candidateName || "Unknown Candidate"}
        </Link>
        <span className="text-xs text-slate-400">{interviews.length} session{interviews.length > 1 ? "s" : ""}</span>
      </div>
      <div className="ml-4 space-y-2">
        {interviews.map((iv) => (
          <div key={iv.id} className="flex items-center justify-between gap-4 flex-wrap bg-black/3 rounded-xl px-4 py-2.5">
            <div className="flex items-center gap-2 flex-wrap min-w-0">
              <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${roundBadge(iv.round_number)}`}>Round {iv.round_number}</span>
              <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${statusBadge(iv.status)}`}>{iv.status}</span>
              <span className="text-xs text-slate-500">{iv.scheduled_at ? new Date(iv.scheduled_at).toLocaleString() : "—"}</span>
              {iv.meet_link && <a href={iv.meet_link} target="_blank" rel="noopener noreferrer" className="text-xs text-emerald-600 hover:underline truncate max-w-xs">{iv.meet_link}</a>}
              {iv.score !== null && <span className="text-xs font-semibold text-emerald-600">Score: {iv.score}/100</span>}
              {iv.feedback && <span className="text-xs text-slate-400 italic truncate max-w-sm">"{iv.feedback}"</span>}
            </div>
            <button onClick={() => onScore(iv)} className="px-3 py-1.5 rounded-lg border border-emerald-200 bg-emerald-50 text-xs font-semibold text-emerald-700 hover:bg-emerald-100 flex-shrink-0">
              {iv.score !== null ? "Update score" : "Submit score"}
            </button>
          </div>
        ))}
      </div>
    </li>
  );
}
