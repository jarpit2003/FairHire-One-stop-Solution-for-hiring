import { useCallback, useEffect, useState } from "react";
import { ArrowRight, Loader2, Users } from "lucide-react";
import Layout from "../components/Layout";
import { Link } from "react-router-dom";
import { applicationService, interviewService, type ApplicationRecord } from "../services/api";
import { useJobs } from "../context/JobContext";
import { getApiErrorMessage } from "../utils/apiError";

// ── Toast notification ────────────────────────────────────────────────────────

interface Toast { id: number; message: string; type: "success" | "error" | "info"; }

function ToastContainer({ toasts, onDismiss }: { toasts: Toast[]; onDismiss: (id: number) => void }) {
  return (
    <div className="fixed bottom-6 right-6 z-[100] flex flex-col gap-2 pointer-events-none">
      {toasts.map((t) => (
        <div key={t.id}
          className={`pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg text-sm font-semibold ${
            t.type === "success" ? "bg-emerald-600 text-white" :
            t.type === "error"   ? "bg-red-600 text-white" :
                                   "bg-slate-700 text-white"
          }`}>
          {t.message}
          <button onClick={() => onDismiss(t.id)} className="ml-2 opacity-70 hover:opacity-100">✕</button>
        </div>
      ))}
    </div>
  );
}

// ── Offer draft modal ────────────────────────────────────────────────────────

function OfferDraftModal({
  app,
  onClose,
  onSent,
}: {
  app: ApplicationRecord;
  onClose: () => void;
  onSent: (updatedApp: ApplicationRecord) => void;
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
      const { data: updatedApp } = await applicationService.offer(app.id, draft);
      onSent(updatedApp);
      onClose();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to send offer"));
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="glass rounded-2xl shadow-card w-full max-w-lg p-6 space-y-4">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-bold text-slate-900">Offer Letter Draft</h2>
        </div>
        <p className="text-sm text-slate-500">AI-generated for <strong className="text-slate-900">{app.candidate_name}</strong>. Edit before sending.</p>
        {loading ? (
          <div className="flex justify-center py-8"><Loader2 className="h-6 w-6 animate-spin text-emerald-400" /></div>
        ) : (
          <textarea value={draft} onChange={(e) => setDraft(e.target.value)} rows={12}
            className="w-full px-4 py-3 rounded-xl border border-white/10 bg-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-y" />
        )}
        {error && <p className="text-sm text-red-300 bg-red-500/20 border border-red-500/30 rounded-xl p-3">{error}</p>}
        <div className="flex gap-3 pt-2">
          <button onClick={handleSend} disabled={sending || loading}
            className="btn-glass-dark flex-1 px-4 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-50" style={{ color: '#fff' }}>
            {sending ? "Sending offer…" : "Send offer email"}
          </button>
          <button onClick={onClose} className="px-4 py-2.5 rounded-xl border border-slate-200 text-sm font-semibold text-slate-600 hover:bg-slate-50">Cancel</button>
        </div>
      </div>
    </div>
  );
}

// ── Stage config ─────────────────────────────────────────────────────────────

const STAGES = [
  { key: "applied",      label: "Applied",      color: "border-t-slate-400",  bg: "bg-slate-50"  },
  { key: "shortlisted",  label: "Shortlisted",  color: "border-t-cyan-400",   bg: "bg-cyan-50"   },
  { key: "test_sent",    label: "Test Sent",    color: "border-t-sky-400",    bg: "bg-sky-50"    },
  { key: "tested",       label: "Assessed",     color: "border-t-blue-400",   bg: "bg-blue-50"   },
  { key: "interview_1",  label: "Round 1",      color: "border-t-amber-400",  bg: "bg-amber-50"  },
  { key: "interview_2",  label: "Round 2",      color: "border-t-purple-400", bg: "bg-purple-50" },
  { key: "offered",      label: "Offered",      color: "border-t-green-400",  bg: "bg-green-50"  },
  { key: "rejected",     label: "Rejected",     color: "border-t-red-300",    bg: "bg-red-50"    },
] as const;

type Stage = typeof STAGES[number]["key"];

// ── Reject confirmation modal ─────────────────────────────────────────────────

function RejectConfirmModal({ name, onConfirm, onClose, loading }: {
  name: string;
  onConfirm: () => void;
  onClose: () => void;
  loading: boolean;
}) {
  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="glass rounded-2xl shadow-card w-full max-w-sm p-6 space-y-4">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-bold text-slate-900">Reject Candidate?</h2>
        </div>
        <p className="text-sm text-slate-500">A rejection email will be sent to <strong className="text-slate-900">{name}</strong>. This cannot be undone.</p>
        <div className="flex gap-3 pt-2">
          <button onClick={onConfirm} disabled={loading}
            className="btn-glass px-4 py-2.5 rounded-xl flex-1 text-sm font-semibold border border-red-200 text-red-600 disabled:opacity-50">
            {loading ? "Rejecting…" : "Yes, reject & notify"}
          </button>
          <button onClick={onClose} className="px-4 py-2.5 rounded-xl border border-slate-200 text-sm font-semibold text-slate-600 hover:bg-slate-50">Cancel</button>
        </div>
      </div>
    </div>
  );
}

function scoreColor(s: number | null) {
  if (s === null) return "text-gray-400";
  if (s >= 80) return "text-green-700 bg-green-50 border-green-200";
  if (s >= 60) return "text-blue-700 bg-blue-50 border-blue-200";
  if (s >= 40) return "text-amber-700 bg-amber-50 border-amber-200";
  return "text-red-700 bg-red-50 border-red-200";
}

// ── Test score modal ────────────────────────────────────────────────────────

function TestScoreModal({
  app,
  onClose,
  onSaved,
}: {
  app: ApplicationRecord;
  onClose: () => void;
  onSaved: (updated: ApplicationRecord) => void;
}) {
  const [score, setScore] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async () => {
    const s = parseFloat(score);
    if (isNaN(s) || s < 0 || s > 100) { setError("Score must be 0–100"); return; }
    setSaving(true);
    setError(null);
    try {
      const { data } = await applicationService.recordTestScore(app.id, s);
      onSaved(data);
      onClose();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to save score"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="glass rounded-2xl shadow-card w-full max-w-sm p-6 space-y-4">
        <h2 className="text-lg font-bold text-white">Enter Test Score</h2>
        <p className="text-sm text-slate-400">Candidate: <strong className="text-white">{app.candidate_name}</strong></p>
        <div>
          <label className="block text-sm font-semibold text-slate-300 mb-1.5">Score (0–100)</label>
          <input type="number" min="0" max="100" value={score}
            onChange={(e) => setScore(e.target.value)}
            placeholder="e.g. 78"
            className="w-full px-4 py-2.5 rounded-xl border border-white/10 bg-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 placeholder:text-slate-500"
            autoFocus />
        </div>
        {error && <p className="text-sm text-red-300 bg-red-500/20 border border-red-500/30 rounded-xl p-3">{error}</p>}
        <div className="flex gap-3 pt-2">
          <button onClick={handleSave} disabled={saving || !score}
            className="btn-glass-dark flex-1 px-4 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-50" style={{ color: '#fff' }}>
            {saving ? "Saving…" : "Save & re-rank"}
          </button>
          <button onClick={onClose} className="px-4 py-2.5 rounded-xl border border-slate-200 text-sm font-semibold text-slate-600 hover:bg-slate-50">Cancel</button>
        </div>
      </div>
    </div>
  );
}

// ── Test link modal ───────────────────────────────────────────────────────────

function TestLinkModal({
  app,
  onClose,
  onSent,
}: {
  app: ApplicationRecord;
  onClose: () => void;
  onSent: (updated: ApplicationRecord) => void;
}) {
  const [link, setLink] = useState("");
  const [deadline, setDeadline] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSend = async () => {
    if (!link.trim()) return;
    setSending(true);
    setError(null);
    try {
      const { data } = await applicationService.sendTestLink(app.id, link.trim(), deadline || undefined);
      onSent(data);
      onClose();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to send test link"));
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="glass rounded-2xl shadow-card w-full max-w-md p-6 space-y-4">
        <h2 className="text-lg font-bold text-white">Send Assessment Link</h2>
        <p className="text-sm text-slate-400">Sending to <strong className="text-white">{app.candidate_name}</strong></p>
        <div>
          <label className="block text-sm font-semibold text-slate-300 mb-1.5">Test / Assessment URL</label>
          <input type="url" value={link} onChange={(e) => setLink(e.target.value)}
            placeholder="https://hackerrank.com/test/..."
            className="w-full px-4 py-2.5 rounded-xl border border-white/10 bg-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 placeholder:text-slate-500" />
        </div>
        <div>
          <label className="block text-sm font-semibold text-slate-300 mb-1.5">Deadline (optional)</label>
          <input type="date" value={deadline} onChange={(e) => setDeadline(e.target.value)}
            className="w-full px-4 py-2.5 rounded-xl border border-white/10 bg-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500" />
        </div>
        {error && <p className="text-sm text-red-300 bg-red-500/20 border border-red-500/30 rounded-xl p-3">{error}</p>}
        <div className="flex gap-3 pt-2">
          <button onClick={handleSend} disabled={sending || !link.trim()}
            className="btn-glass-dark flex-1 px-4 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-50" style={{ color: '#fff' }}>
            {sending ? "Sending…" : "Send link"}
          </button>
          <button onClick={onClose} className="px-4 py-2.5 rounded-xl border border-slate-200 text-sm font-semibold text-slate-600 hover:bg-slate-50">Cancel</button>
        </div>
      </div>
    </div>
  );
}

// ── Schedule interview modal ──────────────────────────────────────────────────

function ScheduleModal({
  app,
  roundNumber,
  onClose,
  onScheduled,
}: {
  app: ApplicationRecord;
  roundNumber: number;
  onClose: () => void;
  onScheduled: (updatedApp: ApplicationRecord) => void;
}) {
  const tomorrow = () => { const d = new Date(); d.setDate(d.getDate() + 1); return d.toISOString().slice(0, 10); };
  const [date, setDate] = useState(tomorrow());
  const [time, setTime] = useState("10:00");
  const [meetLink, setMeetLink] = useState("");
  const [interviewerId, setInterviewerId] = useState("");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSchedule = async () => {
    setSaving(true);
    setError(null);
    try {
      await interviewService.schedule({
        candidate_id: app.candidate_id,
        job_id: app.job_id,
        application_id: app.id,
        round_number: roundNumber,
        scheduled_at: `${date}T${time}:00`,
        meet_link: meetLink || null,
        interviewer_id: interviewerId.trim() || null,
        notes: notes || null,
      });
      const { data: updatedApp } = await applicationService.advanceStage(app.id, "interview_1");
      onScheduled(updatedApp);
      onClose();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to schedule interview"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="glass rounded-2xl shadow-card w-full max-w-md p-6 space-y-4">
        <h2 className="text-lg font-bold text-white">Schedule Round {roundNumber} Interview</h2>
        <p className="text-sm text-slate-400">Candidate: <strong className="text-white">{app.candidate_name}</strong></p>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-semibold text-slate-300 mb-1.5">Date</label>
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl border border-white/10 bg-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500" />
          </div>
          <div>
            <label className="block text-sm font-semibold text-slate-300 mb-1.5">Time</label>
            <input type="time" value={time} onChange={(e) => setTime(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl border border-white/10 bg-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500" />
          </div>
        </div>
        <div>
          <label className="block text-sm font-semibold text-slate-300 mb-1.5">Interviewer Name (optional)</label>
          <input type="text" value={interviewerId} onChange={(e) => setInterviewerId(e.target.value)}
            placeholder="e.g. John Smith"
            className="w-full px-4 py-2.5 rounded-xl border border-white/10 bg-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 placeholder:text-slate-500" />
        </div>
        <div>
          <label className="block text-sm font-semibold text-slate-300 mb-1.5">Meet link (optional)</label>
          <input type="url" value={meetLink} onChange={(e) => setMeetLink(e.target.value)}
            placeholder="https://meet.google.com/..."
            className="w-full px-4 py-2.5 rounded-xl border border-white/10 bg-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 placeholder:text-slate-500" />
        </div>
        <div>
          <label className="block text-sm font-semibold text-slate-300 mb-1.5">Notes</label>
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={3}
            className="w-full px-4 py-2.5 rounded-xl border border-white/10 bg-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-none placeholder:text-slate-500" />
        </div>
        {error && <p className="text-sm text-red-300 bg-red-500/20 border border-red-500/30 rounded-xl p-3">{error}</p>}
        <div className="flex gap-3 pt-2">
          <button onClick={handleSchedule} disabled={saving}
            className="btn-glass-dark flex-1 px-4 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-50" style={{ color: '#fff' }}>
            {saving ? "Scheduling…" : "Schedule & notify"}
          </button>
          <button onClick={onClose} className="px-4 py-2.5 rounded-xl border border-slate-200 text-sm font-semibold text-slate-600 hover:bg-slate-50">Cancel</button>
        </div>
      </div>
    </div>
  );
}

function SkillsCell({ skills }: { skills: string[] }) {
  const [expanded, setExpanded] = useState(false);
  const visible = expanded ? skills : skills.slice(0, 3);
  const extra = skills.length - 3;
  const pillStyle = { background: '#f1f5f9', boxShadow: 'inset 0 0 12px rgba(0,0,0,0.09), 0px 0px 1px rgba(0,0,0,0.2)' };
  return (
    <div className="flex flex-wrap items-center gap-1">
      {visible.map((s) => (
        <span key={s} className="px-2.5 py-1 rounded-full text-xs font-medium text-slate-600" style={pillStyle}>{s}</span>
      ))}
      {!expanded && extra > 0 && (
        <button onClick={() => setExpanded(true)} className="px-2 py-0.5 rounded-full text-xs font-medium text-slate-400 hover:text-slate-600 transition-colors cursor-pointer">+{extra}</button>
      )}
      {expanded && extra > 0 && (
        <button onClick={() => setExpanded(false)} className="px-2 py-0.5 rounded-full text-xs font-medium text-slate-400 hover:text-slate-600 transition-colors cursor-pointer">less</button>
      )}
    </div>
  );
}

function CandidateCard({
  app,
  selected,
  onSelect,
  onAction,
}: {
  app: ApplicationRecord;
  selected: boolean;
  onSelect: (id: string) => void;
  onAction: (action: "shortlist" | "test" | "testscore" | "interview" | "reject" | "offer" | "delete", app: ApplicationRecord) => void;
}) {
  const score = app.final_score ?? app.resume_score;

  return (
    <tr className={`border-b border-white/5 hover:bg-white/5 transition-colors ${
      selected ? "bg-emerald-500/5" : ""
    }`}>
      {/* Checkbox */}
      <td className="pl-4 pr-2 py-3 w-8">
        <input type="checkbox" checked={selected} onChange={() => onSelect(app.id)}
          className="h-3.5 w-3.5 rounded border-white/20 bg-white/10 text-emerald-500 cursor-pointer"
          onClick={(e) => e.stopPropagation()} />
      </td>

      {/* Name + email */}
      <td className="px-3 py-3 min-w-[160px]">
        <Link to={`/candidates/${app.candidate_id}`}
          className="text-sm font-semibold text-emerald-400 hover:underline block leading-tight">
          {app.candidate_name}
        </Link>
        <p className="text-xs text-slate-500 mt-0.5">{app.candidate_email}</p>
      </td>

      {/* Score */}
      <td className="px-3 py-3 w-16 text-center">
        {score !== null ? (
          <span className="text-xs font-bold px-2.5 py-1 rounded-full text-slate-700" style={{ background: '#f1f5f9', boxShadow: 'inset 0 0 12px rgba(0,0,0,0.09), 0px 0px 1px rgba(0,0,0,0.2)' }}>
            {score.toFixed(0)}%
          </span>
        ) : <span className="text-slate-600 text-xs">—</span>}
      </td>

      {/* Skills */}
      <td className="px-3 py-3 min-w-[140px] align-middle">
        <SkillsCell skills={app.matched_skills} />
      </td>

      {/* Actions */}
      <td className="px-3 py-3 pr-4">
        <div className="flex flex-wrap gap-1.5">
          {app.stage === "applied" && (
            <button onClick={() => onAction("shortlist", app)}
              className="px-2.5 py-1 rounded-full text-xs font-semibold" style={{ background: '#131313', color: '#fff', boxShadow: 'inset 0 0 12px rgba(255,255,255,1), 0px 0px 2px rgba(0,0,0,0.1)' }}>
              Shortlist
            </button>
          )}
          {(app.stage === "applied" || app.stage === "shortlisted") && (
            <button onClick={() => onAction("test", app)}
              className="px-2.5 py-1 rounded-full text-xs font-semibold" style={{ background: '#131313', color: '#fff', boxShadow: 'inset 0 0 12px rgba(255,255,255,1), 0px 0px 2px rgba(0,0,0,0.1)' }}>
              Send Test
            </button>
          )}
          {app.stage === "test_sent" && (
            <button onClick={() => onAction("testscore", app)}
              className="px-2.5 py-1 rounded-full text-xs font-semibold" style={{ background: '#f1f5f9', boxShadow: 'inset 0 0 12px rgba(0,0,0,0.09), 0px 0px 1px rgba(0,0,0,0.2)', color: '#475569' }}>
              Enter Score
            </button>
          )}
          {(app.stage === "shortlisted" || app.stage === "test_sent" || app.stage === "tested") && (
            <button onClick={() => onAction("interview", app)}
              className="px-2.5 py-1 rounded-full text-xs font-semibold" style={{ background: '#131313', color: '#fff', boxShadow: 'inset 0 0 12px rgba(255,255,255,1), 0px 0px 2px rgba(0,0,0,0.1)' }}>
              Interview
            </button>
          )}
          {(app.stage === "interview_1" || app.stage === "interview_2") && (
            <button onClick={() => onAction("offer", app)}
              className="px-2.5 py-1 rounded-full text-xs font-semibold" style={{ background: '#131313', color: '#fff', boxShadow: 'inset 0 0 12px rgba(255,255,255,1), 0px 0px 2px rgba(0,0,0,0.1)' }}>
              Offer
            </button>
          )}
          {app.stage !== "rejected" && app.stage !== "offered" && (
            <button onClick={() => onAction("reject", app)}
              className="px-2.5 py-1 rounded-full text-xs font-semibold" style={{ background: '#f1f5f9', boxShadow: 'inset 0 0 12px rgba(0,0,0,0.09), 0px 0px 1px rgba(0,0,0,0.2)', color: '#dc2626' }}>
              Reject
            </button>
          )}
          <button onClick={() => onAction("delete", app)}
            className="px-2.5 py-1 rounded-full text-xs font-semibold" style={{ background: '#f1f5f9', boxShadow: 'inset 0 0 12px rgba(0,0,0,0.09), 0px 0px 1px rgba(0,0,0,0.2)', color: '#94a3b8' }}>
            Delete
          </button>
        </div>
      </td>
    </tr>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function Pipeline() {
  const { activeJob } = useJobs();
  const [applications, setApplications] = useState<ApplicationRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [bulkLoading, setBulkLoading] = useState(false);

  const [testModal, setTestModal] = useState<ApplicationRecord | null>(null);
  const [testScoreModal, setTestScoreModal] = useState<ApplicationRecord | null>(null);
  const [scheduleModal, setScheduleModal] = useState<ApplicationRecord | null>(null);
  const [offerModal, setOfferModal] = useState<ApplicationRecord | null>(null);
  const [rejectModal, setRejectModal] = useState<ApplicationRecord | null>(null);
  const [rejectLoading, setRejectLoading] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = (message: string, type: Toast["type"]) => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
  };

  const dismissToast = (id: number) => setToasts((prev) => prev.filter((t) => t.id !== id));

  const showEmailToast = (data: ApplicationRecord, actionLabel: string) => {
    if (data.email_status === "sent") addToast(`✓ ${actionLabel} email sent to ${data.candidate_email}`, "success");
    else if (data.email_status === "disabled") addToast(`${actionLabel} saved. Email not sent — SMTP is disabled in .env`, "info");
    else if (data.email_status === "failed") addToast(`${actionLabel} saved but email failed to send`, "error");
  };

const isRealDbRecord = (app: ApplicationRecord) =>
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(app.id);

  const load = useCallback(async () => {
    if (!activeJob) return;
    setLoading(true);
    setError(null);
    try {
      const { data } = await applicationService.list(activeJob.id);
      setApplications(data);
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to load applications"));
    } finally {
      setLoading(false);
    }
  }, [activeJob]);

  useEffect(() => { load(); }, [load]);

  const handleAction = async (
    action: "shortlist" | "test" | "testscore" | "interview" | "reject" | "offer" | "delete",
    app: ApplicationRecord,
  ) => {
    if (action === "shortlist") {
      if (!isRealDbRecord(app)) { setError("Cannot shortlist — re-run pipeline to persist candidates."); return; }
      try {
        const { data } = await applicationService.shortlist(app.id);
        setApplications((prev) => prev.map((a) => a.id === data.id ? data : a));
        addToast(`${app.candidate_name} moved to Shortlisted`, "success");
      } catch (e) { setError(getApiErrorMessage(e, "Action failed")); }
      return;
    }
    if (action === "test") { setTestModal(app); return; }
    if (action === "testscore") { setTestScoreModal(app); return; }
    if (action === "interview") { setScheduleModal(app); return; }
    if (action === "offer") { setOfferModal(app); return; }
    if (action === "reject") { setRejectModal(app); return; }
    if (action === "delete") {
      if (!window.confirm(`Remove ${app.candidate_name} from this pipeline? This cannot be undone.`)) return;
      try {
        await applicationService.delete(app.id);
        setApplications((prev) => prev.filter((a) => a.id !== app.id));
        addToast(`${app.candidate_name} removed from pipeline`, "info");
      } catch (e) { setError(getApiErrorMessage(e, "Delete failed")); }
      return;
    }
  };

  const confirmReject = async () => {
    if (!rejectModal) return;
    if (!isRealDbRecord(rejectModal)) {
      setError("This candidate was not saved to the database. Re-run the pipeline to persist candidates.");
      setRejectModal(null);
      return;
    }
    setRejectLoading(true);
    setApplications((prev) => prev.map((a) => a.id === rejectModal.id ? { ...a, stage: "rejected" } : a));
    try {
      const { data } = await applicationService.reject(rejectModal.id);
      setApplications((prev) => prev.map((a) => a.id === data.id ? data : a));
      showEmailToast(data, "Rejection");
    } catch (e) {
      setError(getApiErrorMessage(e, "Action failed"));
      setApplications((prev) => prev.map((a) => a.id === rejectModal.id ? { ...a, stage: rejectModal.stage } : a));
    } finally {
      setRejectLoading(false);
      setRejectModal(null);
    }
  };

  const toggleSelect = (id: string) =>
    setSelected((prev) => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n; });

  const selectedApps = applications.filter((a) => selected.has(a.id));

  const bulkShortlist = async () => {
    setBulkLoading(true);
    await Promise.allSettled(
      selectedApps.filter(isRealDbRecord).map((a) =>
        applicationService.shortlist(a.id).then(({ data }) =>
          setApplications((prev) => prev.map((x) => x.id === data.id ? data : x))
        )
      )
    );
    setSelected(new Set());
    setBulkLoading(false);
  };

  const bulkReject = async () => {
    if (!window.confirm(`Reject ${selectedApps.length} candidate(s)? Rejection emails will be sent.`)) return;
    setBulkLoading(true);
    await Promise.allSettled(
      selectedApps.filter(isRealDbRecord).map((a) =>
        applicationService.reject(a.id).then(({ data }) =>
          setApplications((prev) => prev.map((x) => x.id === data.id ? data : x))
        )
      )
    );
    setSelected(new Set());
    setBulkLoading(false);
  };

  const bulkDelete = async () => {
    if (!window.confirm(`Permanently remove ${selectedApps.length} candidate(s) from this pipeline?`)) return;
    setBulkLoading(true);
    await Promise.allSettled(
      selectedApps.filter(isRealDbRecord).map((a) =>
        applicationService.delete(a.id).then(() =>
          setApplications((prev) => prev.filter((x) => x.id !== a.id))
        )
      )
    );
    setSelected(new Set());
    setBulkLoading(false);
    addToast(`${selectedApps.length} application(s) removed`, "info");
  };

  const byStage = (stage: Stage) =>
    applications
      .filter((a) => a.stage === stage)
      .sort((a, b) => (b.final_score ?? b.resume_score ?? 0) - (a.final_score ?? a.resume_score ?? 0));

  if (!activeJob) {
    return (
      <Layout>
        <div className="max-w-md mx-auto text-center py-16">
          <Users className="h-12 w-12 text-slate-500 mx-auto mb-4" />
          <h1 className="text-xl font-bold text-slate-900">No active job</h1>
          <p className="mt-2 text-slate-500">Select a job from the navbar to view its pipeline.</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="glass rounded-2xl shadow-card p-6">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <h1 className="text-2xl font-bold text-white">Pipeline</h1>
              <p className="mt-1 text-sm text-slate-400">{activeJob.title} · {applications.length} applicants</p>
            </div>
            <button onClick={load} disabled={loading}
              className="btn-glass px-4 py-2 rounded-xl text-sm font-semibold disabled:opacity-50">
              {loading ? <Loader2 className="h-4 w-4 animate-spin inline" /> : "Refresh"}
            </button>
          </div>
        </div>

        {error && <div className="p-4 rounded-xl bg-red-500/20 border border-red-500/30 text-sm text-red-300">{error}</div>}

        {/* Bulk action bar */}
        {selected.size > 0 && (
          <div className="glass rounded-2xl shadow-card px-5 py-3 flex items-center gap-4 flex-wrap">
            <span className="text-sm font-semibold text-emerald-300">{selected.size} selected</span>
            <button onClick={bulkShortlist} disabled={bulkLoading}
              className="btn-glass-dark px-3 py-1.5 rounded-lg text-xs font-semibold disabled:opacity-50" style={{ color: '#fff' }}>
              {bulkLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin inline" /> : "Shortlist all"}
            </button>
            <button onClick={bulkReject} disabled={bulkLoading}
              className="btn-glass px-3 py-1.5 rounded-lg text-xs font-semibold border border-red-200 text-red-600 disabled:opacity-50">
              {bulkLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin inline" /> : "Reject all"}
            </button>
            <button onClick={bulkDelete} disabled={bulkLoading}
              className="btn-glass px-3 py-1.5 rounded-lg text-xs font-semibold disabled:opacity-50">
              {bulkLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin inline" /> : "Delete all"}
            </button>
            <button onClick={() => setSelected(new Set())}
              className="ml-auto text-xs text-emerald-400 hover:underline font-medium">Clear</button>
          </div>
        )}

        {loading && applications.length === 0 ? (
          <div className="flex justify-center py-16"><Loader2 className="h-8 w-8 text-emerald-400 animate-spin" /></div>
        ) : !loading && applications.length === 0 ? (
          <div className="glass rounded-2xl shadow-card p-10 text-center">
            <p className="text-slate-500 mb-4">No applications yet for <strong className="text-slate-900">{activeJob.title}</strong>.</p>
            <Link to="/process-resumes" className="btn-glass-dark inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold" style={{ color: '#fff' }}>
              Process Resumes <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {STAGES.map(({ key, label, color }) => {
              const cards = byStage(key);
              if (cards.length === 0) return null;
              return (
                <div key={key} className="glass rounded-2xl shadow-card overflow-hidden">
                  {/* Stage header */}
                  <div className="px-5 py-3 flex items-center gap-3" style={{ background: '#131313' }}>
                    <span className="text-sm font-bold" style={{ color: '#fff' }}>{label}</span>
                    <span className="text-xs font-bold px-2 py-0.5 rounded-full" style={{ background: 'rgba(255,255,255,0.15)', color: '#fff' }}>{cards.length}</span>
                  </div>
                  {/* Table */}
                  <div className="overflow-x-auto" data-lenis-prevent>
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-white/10" style={{background:"rgba(255,255,255,0.03)"}}>
                          <th className="pl-4 pr-2 py-2 w-8"></th>
                          <th className="px-3 py-2 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">Candidate</th>
                          <th className="px-3 py-2 text-center text-xs font-semibold text-slate-400 uppercase tracking-wide w-20">Score</th>
                          <th className="px-3 py-2 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">Skills</th>
                          <th className="px-3 py-2 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {cards.map((app) => (
                          <CandidateCard key={app.id} app={app} selected={selected.has(app.id)} onSelect={toggleSelect} onAction={handleAction} />
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              );
            })}
            {/* Show empty stages summary */}
            <div className="glass rounded-2xl shadow-card p-4">
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">All Stages</p>
              <div className="flex flex-wrap gap-2">
                {STAGES.map(({ key, label, color }) => {
                  const count = byStage(key).length;
                  return (
                    <div key={key} className="flex items-center gap-2 px-3 py-1.5 rounded-full" style={{ background: '#131313', boxShadow: 'inset 0 0 12px rgba(255,255,255,1), 0px 0px 2px rgba(0,0,0,0.1)' }}>
                      <span className="text-xs" style={{ color: '#fff' }}>{label}</span>
                      <span className={`text-xs font-bold ${count > 0 ? "" : "opacity-40"}`} style={{ color: '#fff' }}>{count}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>

      {testScoreModal && (
        <TestScoreModal
          app={testScoreModal}
          onClose={() => setTestScoreModal(null)}
          onSaved={(updated) => {
            setApplications((prev) => prev.map((a) => a.id === updated.id ? updated : a));
            setTestScoreModal(null);
          }}
        />
      )}

      {testModal && (
        <TestLinkModal
          app={testModal}
          onClose={() => setTestModal(null)}
          onSent={(updated) => {
            setApplications((prev) => prev.map((a) => a.id === updated.id ? updated : a));
            showEmailToast(updated, "Test link");
            setTestModal(null);
          }}
        />
      )}

      {scheduleModal && (
        <ScheduleModal
          app={scheduleModal}
          roundNumber={1}
          onClose={() => setScheduleModal(null)}
          onScheduled={(updatedApp) => {
            setApplications((prev) => prev.map((a) => a.id === updatedApp.id ? updatedApp : a));
            setScheduleModal(null);
          }}
        />
      )}

      {offerModal && (
        <OfferDraftModal
          app={offerModal}
          onClose={() => setOfferModal(null)}
          onSent={(updatedApp) => {
            setApplications((prev) => prev.map((a) => a.id === updatedApp.id ? updatedApp : a));
            showEmailToast(updatedApp, "Offer letter");
            setOfferModal(null);
          }}
        />
      )}

      {rejectModal && (
        <RejectConfirmModal
          name={rejectModal.candidate_name}
          loading={rejectLoading}
          onConfirm={confirmReject}
          onClose={() => setRejectModal(null)}
        />
      )}

      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </Layout>
  );
}
