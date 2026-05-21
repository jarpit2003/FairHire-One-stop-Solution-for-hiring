import { useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, LogOut, Menu, X, Loader2 } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useJobs } from "../context/JobContext";

const NAV_ITEMS = [
  { path: "/dashboard",       label: "DASHBOARD"  },
  { path: "/jobs",            label: "JOBS"       },
  { path: "/process-resumes", label: "UPLOAD"     },
  { path: "/pipeline",        label: "PIPELINE"   },
  { path: "/candidates",      label: "CANDIDATES" },
  { path: "/interviews",      label: "INTERVIEWS" },
];

function JobSwitcher() {
  const { jobs, activeJob, setActiveJobId, loading } = useJobs();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  if (loading && jobs.length === 0) {
    return (
      <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-black/5 text-xs text-slate-500">
        <Loader2 className="h-3 w-3 animate-spin" /> Loading…
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <Link to="/jobs" className="px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-xs font-semibold text-emerald-700 hover:bg-emerald-100 transition-colors">
        + Create job
      </Link>
    );
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium text-slate-700 max-w-[180px]" style={{ background: '#f1f5f9', boxShadow: 'inset 0 0 12px rgba(0,0,0,0.09), 0px 0px 1px rgba(0,0,0,0.2)' }}
      >
        <span className="truncate">{activeJob?.title ?? "Select job"}</span>
        <ChevronDown className={`h-3 w-3 text-slate-400 flex-shrink-0 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.97 }}
            transition={{ duration: 0.15 }}
            className="absolute top-full mt-2 right-0 min-w-[200px] bg-white rounded-2xl shadow-lg border border-black/8 z-50 py-1.5 overflow-hidden"
          >
            <p className="px-3 py-1 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Switch job</p>
            {jobs.map(job => (
              <button
                key={job.id}
                onClick={() => { setActiveJobId(job.id); setOpen(false); }}
                className={`w-full text-left px-3 py-2 text-xs font-medium flex items-center gap-2 transition-colors ${
                  job.id === activeJob?.id ? "text-emerald-700 bg-emerald-50" : "text-slate-700 hover:bg-slate-50"
                }`}
              >
                <div className={`h-1.5 w-1.5 rounded-full flex-shrink-0 ${job.id === activeJob?.id ? "bg-emerald-500" : "bg-slate-300"}`} />
                <span className="truncate">{job.title}</span>
              </button>
            ))}
            <div className="border-t border-slate-100 mt-1 pt-1">
              <Link to="/jobs" onClick={() => setOpen(false)} className="flex items-center gap-2 px-3 py-2 text-xs font-semibold text-emerald-600 hover:bg-slate-50 transition-colors">
                + New job
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function Navbar() {
  const location = useLocation();
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  const initials = user?.full_name
    ? user.full_name.split(" ").map(n => n[0]).join("").slice(0, 2).toUpperCase()
    : "HR";

  return (
    <>
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: "easeOut" }}
        className="fixed top-0 inset-x-6 z-50 mt-2"
      >
        <div className="glass-navbar rounded-full shadow-card border border-white/12 px-8 py-5 flex items-center">

          {/* Logo — extreme left */}
          <Link to="/dashboard" className="flex items-center flex-shrink-0">
            <span className="text-base font-bold text-slate-900 tracking-tight">QuantumLogic Labs</span>
          </Link>

          {/* Nav — absolute center */}
          <nav className="hidden lg:flex items-center gap-0.5 absolute left-1/2 -translate-x-1/2">
            {NAV_ITEMS.map(({ path, label }) => {
              const active = location.pathname === path || (path !== "/dashboard" && location.pathname.startsWith(path));
              return (
                <Link
                  key={path}
                  to={path}
                  className={`px-3.5 py-1.5 rounded-full text-xs font-semibold tracking-widest transition-all duration-200 ${
                    active
                      ? "text-slate-900 bg-slate-900/8 shadow-sm"
                      : "text-slate-400 hover:text-slate-700 hover:bg-slate-900/5"
                  }`}
                >
                  {label}
                </Link>
              );
            })}
          </nav>

          {/* Right — extreme right */}
          <div className="flex items-center gap-2.5 ml-auto flex-shrink-0">
            <div className="hidden sm:block">
              <JobSwitcher />
            </div>
            <div className="hidden sm:flex items-center gap-2">
              <div className="h-7 w-7 rounded-full bg-gradient-to-br from-slate-700 to-slate-900 flex items-center justify-center ring-2 ring-slate-200">
                <span className="text-[10px] font-bold text-white">{initials}</span>
              </div>
              <span className="text-xs font-semibold text-slate-600">{user?.full_name ?? "HR User"}</span>
            </div>
            <button onClick={() => setShowLogoutConfirm(true)} title="Sign out" className="p-1.5 rounded-full text-slate-400 hover:text-red-500 hover:bg-red-50 transition-colors">
              <LogOut className="h-3.5 w-3.5" />
            </button>
            <button onClick={() => setMobileOpen(o => !o)} className="lg:hidden p-1.5 rounded-full text-slate-500 hover:bg-black/5 transition-colors">
              {mobileOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
            </button>
          </div>
        </div>

        {/* Mobile dropdown */}
        <AnimatePresence>
          {mobileOpen && (
            <motion.div
              initial={{ opacity: 0, y: -8, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8, scale: 0.97 }}
              transition={{ duration: 0.18 }}
              className="mt-2 bg-white rounded-2xl shadow-lg border border-black/8 p-3 space-y-0.5"
            >
              <div className="pb-2 mb-2 border-b border-slate-100">
                <JobSwitcher />
              </div>
              {NAV_ITEMS.map(({ path, label }) => {
                const active = location.pathname === path || (path !== "/dashboard" && location.pathname.startsWith(path));
                return (
                  <Link
                    key={path}
                    to={path}
                    onClick={() => setMobileOpen(false)}
                    className={`block px-3 py-2.5 rounded-xl text-sm font-semibold tracking-widest transition-colors ${
                      active ? "text-slate-900 bg-slate-100" : "text-slate-500 hover:text-slate-900 hover:bg-slate-50"
                    }`}
                  >
                    {label}
                  </Link>
                );
              })}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.header>
      {showLogoutConfirm && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center" style={{ background: 'rgba(0,0,0,0.3)', backdropFilter: 'blur(4px)' }}>
          <div className="glass rounded-2xl shadow-card p-8 w-full max-w-sm mx-4 text-center space-y-4">
            <h2 className="text-lg font-bold text-slate-900">Sign out?</h2>
            <p className="text-sm text-slate-500">You'll need to sign in again to access your workspace.</p>
            <div className="flex gap-3 pt-2">
              <button onClick={() => { setShowLogoutConfirm(false); logout(); }} className="btn-glass-dark flex-1 px-4 py-2.5 rounded-full text-sm font-semibold">Sign out</button>
              <button onClick={() => setShowLogoutConfirm(false)} className="btn-glass flex-1 px-4 py-2.5 rounded-full text-sm font-semibold">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
