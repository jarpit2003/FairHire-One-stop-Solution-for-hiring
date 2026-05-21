import { useCallback, useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  ArrowLeft, UserCircle, Mail, Phone, FileText,
  CheckCircle2, XCircle, Calendar, Award, Loader2,
  Send, Edit3, ChevronDown, ChevronUp, GitBranch,
} from "lucide-react";
import Layout from "../components/Layout";
import {
  applicationService, interviewService, candidateService,
  type ApplicationRecord, type InterviewRecord, type CandidateRecord,
} from "../services/api";
import { getApiErrorMessage } from "../utils/apiError";

// ── helpers ──────────────────────────────────────────────────────────────────

function ScorePill({ label, value, color }: { label: string; value: number | null; color: string }) {
  if (value === null) return null;
  return (
    <div className={`flex flex-col items-center px-4 py-3 rounded-xl border ${color}`}>
      <span className="text-xl font-bold">{value.toFixed(0)}</span>
      <span className="text-xs font-medium mt-0.5 opacity-75">{label}</span>
    </div>
  );
}

function stageBadgeColor(stage: string) {
  const map: Record<string, string> = {
    applied:      "bg-slate-100 text-slate-700",
    shortlisted:  "bg-cyan-100 text-cyan-800",
    test_sent:    "bg-sky-100 text-sky-800",
    tested:       "bg-blue-100 text-blue-800",
    interview_1:  "bg-amber-100 text-amber-800",
    interview_2:  "bg-purple-100 text-purple-800",
    offered:      "bg-green-100 text-green-800",
    rejected:     "bg-red-100 text-red-700",
    testing:      "bg-sky-100 text-sky-800",
    interviewing: "bg-amber-100 text-amber-800",
  };
  return map[stage] ?? "bg-gray-100 text-gray-700";
}

function stageLabel(stage: string) {
  const map: Record<string, string> = {
    applied: "Applied", shortlisted: "Shortlisted",
    test_sent: "Test Sent", tested: "Assessment Done",
    interview_1: "Round 1 Interview", interview_2: "Round 2 Interview",
    offered: "Offered", rejected: "Rejected",
    testing: "Test Sent", interviewing: "Interviewing",
  };
  return map[stage] ?? stage;
}

// ── Offer draft modal (reused from Pipeline) ─────────────────────────────────

function OfferDraftModal({ app, onClose, onSent }: {
  app: ApplicationRecord;
  onClose: () => void;
  onSent: (updated: ApplicationRecord) => void;
}) {
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    applicationService.getOfferDraft(app.id)
      .then(({ data }) => setDraft(data.draft))
      .catch(() => setDraft(`Dear ${app.candidate_name},\n\nCongratulations! We are pleased to offer you this position.\n\nBest regards,\nQuantumLogic Labs Recruitment Team`))
      .finally(() => setLoading(false));
  }, [app.id]);

  const handleSend = async () => {
    setSending(true);
    setError(null);
    try {
      const { data } = await applicationService.offer(app.id, draft);
      onSent(data);
      onClose();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to send offer"));
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="glass rounded-2xl shadow-card w-full max-w-lg p-6 space-y-4">
        <div className="flex items-center gap-2">
          <Edit3 className="h-5 w-5 text-emerald-400" />
          <h2 className="text-lg font-bold text-white">Offer Letter Draft</h2>
        </div>
        <p className="text-sm text-slate-400">AI-generated for <strong className="text-white">{app.candidate_name}</strong>. Edit before sending.</p>
        {loading ? (
          <div className="flex justify-center py-8"><Loader2 className="h-6 w-6 animate-spin text-emerald-400" /></div>
        ) : (
          <textarea value={draft} onChange={(e) => setDraft(e.target.value)} rows={12}
            className="w-full px-4 py-3 rounded-xl border border-white/10 bg-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-y" />
        )}
        {error && <p className="text-sm text-red-300 bg-red-500/20 border border-red-500/30 rounded-xl p-3">{error}</p>}
        <div className="flex gap-3 pt-2">
          <button onClick={handleSend} disabled={sending || loading}
            className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 text-white text-sm font-semibold hover:bg-emerald-700 disabled:opacity-50">
            {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
            {sending ? "Sending offer…" : "Send offer email"}
          </button>
          <button onClick={onClose} className="px-4 py-2.5 rounded-xl border border-white/10 text-sm font-semibold text-slate-300 hover:bg-white/10">Cancel</button>
        </div>
      </div>
    </div>
  );
}

// ── Reject confirmation modal ─────────────────────────────────────────────────

function RejectConfirmModal({ name, onConfirm, onClose, loading }: {
  name: string;
  onConfirm: () => void;
  onClose: () => void;
  loading: boolean;
}) {
  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="glass rounded-2xl shadow-card w-full max-w-sm p-6 space-y-4">
        <div className="flex items-center gap-3">
          <div className="bg-red-500/20 rounded-full p-2"><XCircle className="h-5 w-5 text-red-400" /></div>
          <h2 className="text-lg font-bold text-white">Reject Candidate?</h2>
        </div>
        <p className="text-sm text-slate-400">A rejection email will be sent to <strong className="text-white">{name}</strong>. This cannot be undone.</p>
        <div className="flex gap-3 pt-2">
          <button onClick={onConfirm} disabled={loading}
            className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-red-600 text-white text-sm font-semibold hover:bg-red-700 disabled:opacity-50">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <XCircle className="h-4 w-4" />}
            {loading ? "Rejecting…" : "Yes, reject & notify"}
          </button>
          <button onClick={onClose} className="px-4 py-2.5 rounded-xl border border-white/10 text-sm font-semibold text-slate-300 hover:bg-white/10">Cancel</button>
        </div>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function CandidateProfile() {
  const { candidateId } = useParams<{ candidateId: string }>();
  const navigate = useNavigate();

  const [candidate, setCandidate] = useState<CandidateRecord | null>(null);
  const [applications, setApplications] = useState<ApplicationRecord[]>([]);
  const [interviews, setInterviews] = useState<InterviewRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showResume, setShowResume] = useState(false);
  const [offerModal, setOfferModal] = useState<ApplicationRecord | null>(null);
  const [rejectModal, setRejectModal] = useState<ApplicationRecord | null>(null);
  const [rejectLoading, setRejectLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!candidateId) return;
    setLoading(true);
    setError(null);
    try {
      const [{ data: cand }, { data: allInterviews }, { data: apps }] = await Promise.all([
        candidateService.get(candidateId),
        interviewService.list(),
        applicationService.listByCandidate(candidateId),
      ]);
      setCandidate(cand);
      setInterviews(allInterviews.filter((iv) => iv.candidate_id === candidateId));
      setApplications(apps);
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to load candidate"));
    } finally {
      setLoading(false);
    }
  }, [candidateId]);

  useEffect(() => { load(); }, [load]);

  const handleReject = async () => {
    if (!rejectModal) return;
    setRejectLoading(true);
    setActionError(null);
    try {
      const { data } = await applicationService.reject(rejectModal.id);
      setApplications((prev) => prev.map((a) => a.id === data.id ? data : a));
      setRejectModal(null);
    } catch (e) {
      setActionError(getApiErrorMessage(e, "Failed to reject"));
    } finally {
      setRejectLoading(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex justify-center py-24">
          <Loader2 className="h-8 w-8 text-blue-600 animate-spin" />
        </div>
      </Layout>
    );
  }

  if (error || !candidate) {
    return (
      <Layout>
        <div className="max-w-md mx-auto text-center py-16">
          <p className="text-red-600 mb-4">{error ?? "Candidate not found"}</p>
          <button onClick={() => navigate(-1)} className="text-sm text-blue-600 hover:underline">← Go back</button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-6">

        {/* Back */}
        <button onClick={() => navigate(-1)}
          className="inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-white font-medium">
          <ArrowLeft className="h-4 w-4" /> Back
        </button>

        {/* Header card */}
        <div className="glass rounded-2xl shadow-card p-6">
          <div className="flex items-start gap-5 flex-wrap">
            <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-cyan-600 flex items-center justify-center flex-shrink-0">
              <span className="text-2xl font-bold text-white">
                {candidate.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <h1 className="text-2xl font-bold text-white">{candidate.full_name}</h1>
              <div className="flex flex-wrap gap-4 mt-2 text-sm text-slate-400">
                <span className="flex items-center gap-1.5"><Mail className="h-4 w-4" />{candidate.email}</span>
                {candidate.phone && <span className="flex items-center gap-1.5"><Phone className="h-4 w-4" />{candidate.phone}</span>}
              </div>
            </div>
            <Link to="/pipeline"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-white/10 text-sm font-semibold text-slate-300 hover:bg-white/10">
              <GitBranch className="h-4 w-4" /> View Pipeline
            </Link>
          </div>
        </div>

        {actionError && <div className="p-3 rounded-xl bg-red-500/20 border border-red-500/30 text-sm text-red-300">{actionError}</div>}

        {applications.length === 0 ? (
          <div className="glass rounded-2xl shadow-card p-8 text-center">
            <UserCircle className="h-10 w-10 text-slate-500 mx-auto mb-3" />
            <p className="text-slate-400 text-sm">No applications found for this candidate.</p>
          </div>
        ) : (
          applications.map((app) => {
            const appInterviews = interviews.filter((iv) => iv.application_id === app.id);
            return (
              <div key={app.id} className="glass rounded-2xl shadow-card overflow-hidden">
                <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between gap-4 flex-wrap">
                  <div>
                    <p className="text-xs text-slate-500 font-medium uppercase tracking-wide">Application</p>
                    <p className="text-sm font-semibold text-white mt-0.5">Applied {new Date(app.applied_at).toLocaleDateString(undefined, { dateStyle: "medium" })}</p>
                  </div>
                  <span className="text-xs font-medium px-3 py-1 rounded-full" style={app.stage === 'rejected' ? { background: '#f1f5f9', boxShadow: 'inset 0 0 12px rgba(0,0,0,0.09), 0px 0px 1px rgba(0,0,0,0.2)', color: '#94a3b8' } : { background: '#131313', boxShadow: 'inset 0 0 12px rgba(255,255,255,1), 0px 0px 2px rgba(0,0,0,0.1)', color: '#fff' }}>{stageLabel(app.stage)}</span>
                </div>

                <div className="p-6 space-y-6">
                  {/* Score pills */}
                  <div>
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">Score Breakdown</p>
                    <div className="flex flex-wrap gap-3">
                      <ScorePill label="Resume" value={app.resume_score} color="bg-white/10 border-white/20 text-slate-200" />
                      <ScorePill label="Assessment" value={app.test_score} color="bg-cyan-500/15 border-cyan-500/30 text-cyan-300" />
                      <ScorePill label="Round 1" value={app.interview_score} color="bg-amber-500/15 border-amber-500/30 text-amber-300" />
                      <ScorePill label="Round 2" value={app.hr_interview_score} color="bg-purple-500/15 border-purple-500/30 text-purple-300" />
                      {app.final_score !== null && (
                        <div className="flex flex-col items-center px-4 py-3 rounded-xl border bg-emerald-500/15 border-emerald-500/30 text-emerald-300">
                          <span className="text-xl font-bold">{app.final_score.toFixed(0)}</span>
                          <span className="text-xs font-semibold mt-0.5">Final ★</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Skills */}
                  {(app.matched_skills.length > 0 || app.missing_skills.length > 0) && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {app.matched_skills.length > 0 && (
                        <div>
                          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2">Matched Skills</p>
                          <div className="flex flex-wrap gap-1.5">
                            {app.matched_skills.map((s) => (
                              <span key={s} className="text-xs font-medium px-2.5 py-1 rounded-full text-slate-600" style={{ background: '#f1f5f9', boxShadow: 'inset 0 0 12px rgba(0,0,0,0.09), 0px 0px 1px rgba(0,0,0,0.2)' }}>{s}</span>
                            ))}
                          </div>
                        </div>
                      )}
                      {app.missing_skills.length > 0 && (
                        <div>
                          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2">Missing Skills</p>
                          <div className="flex flex-wrap gap-1.5">
                            {app.missing_skills.map((s) => (
                              <span key={s} className="text-xs font-medium px-2.5 py-1 rounded-full text-slate-500" style={{ background: '#f1f5f9', boxShadow: 'inset 0 0 12px rgba(0,0,0,0.09), 0px 0px 1px rgba(0,0,0,0.2)' }}>{s}</span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Interview history */}
                  {appInterviews.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">Interview History</p>
                      <div className="space-y-2">
                        {appInterviews.map((iv) => (
                          <div key={iv.id} className="flex items-start gap-3 p-3 rounded-xl bg-white/5 border border-white/10">
                            <Calendar className="h-4 w-4 text-slate-400 mt-0.5 flex-shrink-0" />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-xs font-semibold text-slate-200">Round {iv.round_number}</span>
                                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                                  iv.status === "completed" ? "bg-green-100 text-green-700" :
                                  iv.status === "cancelled" ? "bg-red-100 text-red-700" :
                                  "bg-blue-100 text-blue-700"
                                }`}>{iv.status}</span>
                                {iv.score !== null && (
                                  <span className="text-xs font-bold text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full">
                                    <Award className="h-3 w-3 inline mr-0.5" />{iv.score}/100
                                  </span>
                                )}
                              </div>
                              {iv.scheduled_at && <p className="text-xs text-slate-500 mt-1">{new Date(iv.scheduled_at).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" })}</p>}
                              {iv.meet_link && <a href={iv.meet_link} target="_blank" rel="noopener noreferrer" className="text-xs text-emerald-400 hover:underline mt-0.5 block truncate">{iv.meet_link}</a>}
                              {iv.feedback && <p className="text-xs text-slate-500 mt-1 italic">"{iv.feedback}"</p>}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  {app.stage !== "rejected" && app.stage !== "offered" && (
                    <div className="flex flex-wrap gap-2 pt-2 border-t border-white/10">
                      {(app.stage === "interview_1" || app.stage === "interview_2" || app.stage === "interviewing") && (
                        <button onClick={() => setOfferModal(app)}
                          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-green-600 text-white text-sm font-semibold hover:bg-green-700">
                          <CheckCircle2 className="h-4 w-4" /> Send Offer
                        </button>
                      )}
                      <button onClick={() => setRejectModal(app)}
                        className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl border border-red-200 bg-red-50 text-sm font-semibold text-red-700 hover:bg-red-100">
                        <XCircle className="h-4 w-4" /> Reject
                      </button>
                      <Link to="/pipeline"
                        className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl border border-white/10 text-sm font-semibold text-slate-300 hover:bg-white/10">
                        <Send className="h-4 w-4" /> Manage in Pipeline
                      </Link>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}

        {candidate.resume_text && (
          <div className="glass rounded-2xl shadow-card overflow-hidden">
            <button onClick={() => setShowResume((s) => !s)}
              className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-white/5 transition-colors">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-slate-400" />
                <span className="text-sm font-semibold text-white">Resume Text</span>
              </div>
              {showResume ? <ChevronUp className="h-4 w-4 text-slate-400" /> : <ChevronDown className="h-4 w-4 text-slate-400" />}
            </button>
            {showResume && (
              <div className="px-6 pb-6 space-y-4">
                {(() => {
                  const urls = [...candidate.resume_text.matchAll(/https?:\/\/[^\s"'<>(){}\[\]\\,;]+/g)]
                    .map(m => m[0].replace(/[.,;:!?)]+$/, "")).filter((u, i, a) => a.indexOf(u) === i).slice(0, 8);
                  if (!urls.length) return null;
                  return (
                    <div>
                      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2">Links from Resume</p>
                      <div className="flex flex-wrap gap-2">
                        {urls.map(u => (
                          <a key={u} href={u} target="_blank" rel="noopener noreferrer"
                            className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/25 truncate max-w-[220px]">
                            {u.includes("github") ? "⭐ " : u.includes("linkedin") ? "💼 " : "🔗 "}{u.replace(/https?:\/\/(www\.)?/, "")}
                          </a>
                        ))}
                      </div>
                    </div>
                  );
                })()}
                <pre className="text-xs text-slate-300 bg-white/5 border border-white/10 rounded-xl p-4 whitespace-pre-wrap max-h-96 overflow-y-auto font-mono leading-relaxed">
                  {candidate.resume_text}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>

      {offerModal && (
        <OfferDraftModal
          app={offerModal}
          onClose={() => setOfferModal(null)}
          onSent={(updated) => {
            setApplications((prev) => prev.map((a) => a.id === updated.id ? updated : a));
            setOfferModal(null);
          }}
        />
      )}

      {rejectModal && (
        <RejectConfirmModal
          name={rejectModal.candidate_name}
          onConfirm={handleReject}
          onClose={() => setRejectModal(null)}
          loading={rejectLoading}
        />
      )}
    </Layout>
  );
}
