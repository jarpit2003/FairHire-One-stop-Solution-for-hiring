import { Link } from "react-router-dom";
import { ArrowRight, CheckCircle2, ScanText, KanbanSquare, Scale, BellRing, Send, MessageSquare, FilePlus, FileUp, UserCheck } from "lucide-react";

const FEATURES = [
  { icon: ScanText,      title: "AI Resume Scoring",       desc: "Scores every candidate on skills, experience, impact, and semantic fit in seconds." },
  { icon: KanbanSquare,  title: "Visual Hiring Pipeline",  desc: "Kanban board tracks every candidate from Applied to Offered. Bulk shortlist, test, and interview in one click." },
  { icon: Scale,         title: "Bias-Free Shortlisting",  desc: "Structured scoring criteria ensure every candidate is evaluated on merit. No gut-feel, no unconscious bias." },
  { icon: BellRing,      title: "Automated Notifications", desc: "Candidates get instant emails at every stage: application received, interview scheduled, offer letter." },
  { icon: Send,          title: "One-Click Job Publishing", desc: "Post to LinkedIn, Naukri, and X/Twitter simultaneously. Auto-create Google Forms for candidate intake." },
  { icon: MessageSquare, title: "Recruiter AI Chatbot",    desc: "Ask anything about your pipeline. Top candidates, skill gaps, hiring decisions, interview questions — all answered instantly." },
];

const STEPS = [
  { num: "01", icon: FilePlus,  title: "Create & Publish Job", desc: "Write your JD, publish to LinkedIn, Naukri, and X, and get a Google Form for applications in under 2 minutes." },
  { num: "02", icon: FileUp,    title: "Upload Resumes",       desc: "Drop PDF/DOCX resumes. AI parses, scores, and ranks every candidate against your JD automatically." },
  { num: "03", icon: UserCheck, title: "Hire the Best",        desc: "Review ranked candidates, shortlist, send assessments, schedule interviews, and send offers from one dashboard." },
];

const STATS = [
  { value: "10x",  label: "Faster screening" },
  { value: "90%",  label: "Less manual work"  },
  { value: "100%", label: "Bias-free"          },
];

export default function Landing() {
  return (
    <div className="min-h-screen">

      {/* ── Navbar ─────────────────────────────────────────────────────── */}
      <nav className="sticky top-0 z-50 glass-navbar px-6 h-16 flex items-center">
        <div className="max-w-6xl mx-auto w-full flex items-center justify-between">
          <span className="text-base font-bold text-slate-900 tracking-tight">QuantumLogic Labs</span>
          <div className="flex items-center gap-3">
            <Link
              to="/login"
              className="px-4 py-2 text-sm font-semibold text-slate-500 hover:text-slate-900 transition-colors duration-200"
            >
              Sign in
            </Link>
            <Link
              to="/login"
              className="btn-glass-dark inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold"
              style={{ color: "#fff" }}
            >
              Get started <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </nav>

      {/* ── Hero ───────────────────────────────────────────────────────── */}
      <section className="relative pt-24 pb-28 px-6 text-center">
        <div className="max-w-4xl mx-auto">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-slate-100 border border-slate-200 text-xs font-semibold text-slate-600 mb-8 tracking-wide uppercase">
            AI-Powered Hiring Platform
          </div>

          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold text-slate-900 leading-[1.08] tracking-tight">
            Hire smarter,<br />
            <span className="text-slate-400">not harder.</span>
          </h1>

          <p className="mt-7 text-lg sm:text-xl text-slate-500 leading-relaxed max-w-2xl mx-auto">
            QuantumLogic Labs automates resume screening, AI-powered candidate scoring, pipeline management,
            and interview scheduling — so your HR team focuses on people, not paperwork.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              to="/login"
              className="btn-glass-dark inline-flex items-center gap-2 px-8 py-3.5 rounded-2xl text-base font-semibold w-full sm:w-auto justify-center"
              style={{ color: "#fff" }}
            >
              Start hiring free <ArrowRight className="h-4 w-4" />
            </Link>
            <a
              href="#how-it-works"
              className="btn-glass inline-flex items-center gap-2 px-8 py-3.5 rounded-2xl text-base font-semibold w-full sm:w-auto justify-center"
            >
              See how it works
            </a>
          </div>

          <div className="mt-10 flex items-center justify-center gap-6 flex-wrap">
            {["No credit card required", "Setup in 2 minutes", "Free to use"].map((t) => (
              <div key={t} className="flex items-center gap-1.5 text-sm text-slate-400">
                <CheckCircle2 className="h-4 w-4 text-slate-300 flex-shrink-0" />
                {t}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Stats ──────────────────────────────────────────────────────── */}
      <section className="py-12 px-6">
        <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-4">
          {STATS.map(({ value, label }) => (
            <div
              key={label}
              className="glass rounded-2xl p-8 text-center hover:scale-[1.02] transition-transform duration-200"
            >
              <p className="text-4xl font-extrabold text-slate-900 tracking-tight">{value}</p>
              <p className="mt-2 text-sm font-medium text-slate-500">{label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Features ───────────────────────────────────────────────────── */}
      <section className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight">
              Everything your HR team needs
            </h2>
            <p className="mt-3 text-base text-slate-500 max-w-xl mx-auto">
              From job posting to offer letter — one platform, zero spreadsheets.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map(({ icon: Icon, title, desc }) => (
              <div
                key={title}
                className="glass rounded-2xl p-6 hover:scale-[1.02] hover:shadow-lg transition-all duration-200 cursor-default group"
              >
                <div className="inline-flex p-2.5 rounded-xl mb-4 bg-slate-100 group-hover:bg-slate-200 transition-colors duration-200">
                  <Icon className="h-5 w-5 text-slate-700" />
                </div>
                <h3 className="text-sm font-bold text-slate-900 mb-2">{title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it works ───────────────────────────────────────────────── */}
      <section id="how-it-works" className="py-20 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight">
              Up and running in minutes
            </h2>
            <p className="mt-3 text-base text-slate-500">Three steps to your next great hire.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {STEPS.map(({ num, icon: Icon, title, desc }, i) => (
              <div key={num} className="glass rounded-2xl p-8 text-center relative group hover:scale-[1.02] transition-transform duration-200">
                {/* Step number */}
                <span className="absolute top-4 right-5 text-xs font-bold text-slate-200 tabular-nums">{num}</span>
                {/* Connector line between steps */}
                {i < STEPS.length - 1 && (
                  <div className="hidden md:block absolute top-1/2 -right-3 w-6 h-px bg-slate-200 z-10" />
                )}
                <div className="inline-flex p-4 rounded-2xl mb-5 bg-slate-100 group-hover:bg-slate-200 transition-colors duration-200">
                  <Icon className="h-7 w-7 text-slate-700" />
                </div>
                <h3 className="text-sm font-bold text-slate-900 mb-2">{title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ────────────────────────────────────────────────────────── */}
      <section className="py-20 px-6">
        <div className="max-w-3xl mx-auto">
          <div className="glass rounded-3xl p-12 sm:p-16 text-center relative overflow-hidden">
            {/* Subtle background accent */}
            <div className="absolute inset-0 bg-gradient-to-br from-slate-50 to-white opacity-60 rounded-3xl pointer-events-none" />
            <div className="relative">
              <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4 tracking-tight">
                Ready to transform your hiring?
              </h2>
              <p className="text-slate-500 text-base mb-10 max-w-lg mx-auto leading-relaxed">
                Join HR teams using QuantumLogic Labs to hire faster, fairer, and smarter.
              </p>
              <Link
                to="/login"
                className="btn-glass-dark inline-flex items-center gap-2 px-8 py-4 rounded-2xl text-base font-bold"
                style={{ color: "#fff" }}
              >
                Get started free <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────────────────── */}
      <footer className="py-10 px-6 border-t border-slate-100">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <span className="text-sm font-bold text-slate-900">QuantumLogic Labs</span>
          <p className="text-xs text-slate-400">
            © {new Date().getFullYear()} QuantumLogic Labs. Built for modern HR teams.
          </p>
          <div className="flex items-center gap-4">
            <Link to="/login" className="text-xs text-slate-400 hover:text-slate-700 transition-colors duration-200">Sign in</Link>
            <Link to="/login" className="text-xs text-slate-400 hover:text-slate-700 transition-colors duration-200">Register</Link>
          </div>
        </div>
      </footer>

    </div>
  );
}
