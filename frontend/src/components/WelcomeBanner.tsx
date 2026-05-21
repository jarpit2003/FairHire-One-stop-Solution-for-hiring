import { Link } from "react-router-dom";
import { Briefcase, FileStack, GitBranch, Calendar, ArrowRight, X } from "lucide-react";
import { useState } from "react";

const STEPS = [
  {
    step: "1",
    icon: Briefcase,
    title: "Create a Job",
    desc: "Add a job title and paste the job description.",
    to: "/jobs",
    color: "text-emerald-400",
    bg: "bg-emerald-500/15",
  },
  {
    step: "2",
    icon: FileStack,
    title: "Upload Resumes",
    desc: "Upload PDFs — AI scores and ranks candidates instantly.",
    to: "/process-resumes",
    color: "text-cyan-400",
    bg: "bg-cyan-500/15",
  },
  {
    step: "3",
    icon: GitBranch,
    title: "Manage Pipeline",
    desc: "Shortlist, send tests, and schedule interviews.",
    to: "/pipeline",
    color: "text-amber-400",
    bg: "bg-amber-500/15",
  },
  {
    step: "4",
    icon: Calendar,
    title: "Conduct Interviews",
    desc: "Track rounds, score candidates, and send offers.",
    to: "/interviews",
    color: "text-purple-400",
    bg: "bg-purple-500/15",
  },
];

export default function WelcomeBanner() {
  const [dismissed, setDismissed] = useState(
    () => localStorage.getItem("fh_welcome_dismissed") === "1"
  );

  if (dismissed) return null;

  const dismiss = () => {
    localStorage.setItem("fh_welcome_dismissed", "1");
    setDismissed(true);
  };

  return (
    <div className="glass rounded-2xl shadow-card p-6 mb-6 relative"
      style={{ borderColor: "rgba(16,185,129,0.25)" }}>

      {/* Dismiss */}
      <button
        onClick={dismiss}
        className="absolute top-4 right-4 text-slate-500 hover:text-white transition-colors"
        title="Dismiss"
      >
        <X className="h-4 w-4" />
      </button>

      <div className="mb-4">
        <h2 className="text-base font-bold text-white">👋 Welcome to QuantumLogic Labs</h2>
        <p className="text-sm text-slate-400 mt-0.5">
          Follow these 4 steps to start hiring smarter.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
        {STEPS.map(({ step, icon: Icon, title, desc, to, color, bg }) => (
          <Link
            key={step}
            to={to}
            className="group flex items-start gap-3 p-4 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all"
          >
            <div className={`${bg} rounded-lg p-2 flex-shrink-0`}>
              <Icon className={`h-4 w-4 ${color}`} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-bold text-slate-500">Step {step}</span>
              </div>
              <p className="text-sm font-semibold text-white mt-0.5">{title}</p>
              <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">{desc}</p>
            </div>
            <ArrowRight className="h-3.5 w-3.5 text-slate-600 group-hover:text-emerald-400 flex-shrink-0 mt-1 transition-colors" />
          </Link>
        ))}
      </div>
    </div>
  );
}
