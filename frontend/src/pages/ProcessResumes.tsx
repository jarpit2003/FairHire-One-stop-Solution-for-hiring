import { useCallback, useEffect, useId, useRef, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { ArrowRight, FileText, Loader2, UploadCloud, X, Briefcase, CheckCircle2, AlertCircle, RefreshCw, FileUp, PenLine } from "lucide-react";
import mammoth from "mammoth";
import Layout from "../components/Layout";
import { useJobs } from "../context/JobContext";
import { uploadService, matchService, applicationService, candidateService } from "../services/api";
import { getApiErrorMessage } from "../utils/apiError";
import { displayNameFromFilename } from "../utils/resumeFilename";

const ACCEPT_EXT = /\.(pdf|docx?)$/i;
const ACCEPT_MIME = new Set(["application/pdf","application/msword","application/vnd.openxmlformats-officedocument.wordprocessingml.document"]);

function isAllowedFile(f: File) { return ACCEPT_EXT.test(f.name) || (f.type && ACCEPT_MIME.has(f.type)); }

interface ProcessedResult {
  name: string; email: string; phone: string | null;
  fitScore: number; matchedSkills: string[]; missingSkills: string[];
  links: { url: string; platform: string; reachable: boolean; detail: string }[];
  status: "saved" | "duplicate" | "error"; error?: string;
}

export default function ProcessResumes() {
  const navigate = useNavigate();
  const { activeJob, jobs } = useJobs();
  const inputId = useId();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const jdFileInputRef = useRef<HTMLInputElement>(null);

  const [jobDescription, setJobDescription] = useState("");
  const [jdMode, setJdMode] = useState<"type" | "upload">("type");
  const [jdSource, setJdSource] = useState<"auto" | "manual" | "file">("auto");
  const [jdFileName, setJdFileName] = useState<string | null>(null);
  const [isDraggingJd, setIsDraggingJd] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [currentStep, setCurrentStep] = useState("");
  const [currentFile, setCurrentFile] = useState(0);
  const [results, setResults] = useState<ProcessedResult[]>([]);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Auto-fill JD from active job — always sync when job changes or on first mount
  useEffect(() => {
    if (activeJob?.description) {
      setJobDescription(activeJob.description);
      setJdSource("auto");
      setJdMode("type");
      setJdFileName(null);
    } else {
      setJobDescription("");
      setJdSource("manual");
    }
  }, [activeJob?.id]); // eslint-disable-line

  // Read JD file content entirely in the browser — no backend call needed
  const readJdFile = useCallback(async (file: File) => {
    setJdFileName(file.name);
    setJdSource("file");
    setError(null);

    const isDocx = file.name.toLowerCase().endsWith(".docx") ||
      file.type === "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
    const isPdf = file.name.toLowerCase().endsWith(".pdf") || file.type === "application/pdf";

    if (isDocx) {
      // mammoth extracts clean text from DOCX binary in the browser
      try {
        const arrayBuffer = await file.arrayBuffer();
        const result = await mammoth.extractRawText({ arrayBuffer });
        setJobDescription(result.value.slice(0, 8000));
      } catch {
        setError("Could not read DOCX. Try copy-pasting the text instead.");
        setJdSource("manual"); setJdFileName(null);
      }
      return;
    }

    if (isPdf) {
      // PDF — send to backend parser
      try {
        const { data: upload } = await uploadService.resume(file);
        setJobDescription((upload.full_text || upload.extracted_text_preview || "").slice(0, 8000));
      } catch {
        setError("Could not parse JD PDF. Try copy-pasting the text instead.");
        setJdSource("manual"); setJdFileName(null);
      }
      return;
    }

    // TXT / plain text — read directly
    const reader = new FileReader();
    reader.onload = (e) => setJobDescription(((e.target?.result as string) ?? "").slice(0, 8000));
    reader.onerror = () => { setError("Could not read file."); setJdSource("manual"); setJdFileName(null); };
    reader.readAsText(file);
  }, []);

  const resetJdToJob = () => {
    if (activeJob?.description) {
      setJobDescription(activeJob.description);
      setJdSource("auto");
      setJdFileName(null);
    }
  };

  const onFilesPicked = useCallback((list: FileList | null) => {
    if (!list?.length) return;
    const next: File[] = []; const rejected: string[] = [];
    for (let i = 0; i < list.length; i++) {
      if (isAllowedFile(list[i])) next.push(list[i]); else rejected.push(list[i].name);
    }
    setFiles((prev) => {
      const seen = new Set(prev.map((p) => `${p.name}-${p.size}`));
      const merged = [...prev];
      for (const f of next) { const k = `${f.name}-${f.size}`; if (!seen.has(k)) { seen.add(k); merged.push(f); } }
      return merged;
    });
    if (rejected.length) setError(`Skipped (PDF/DOCX only): ${rejected.join(", ")}`); else setError(null);
  }, []);

  const onDrop = useCallback((e: React.DragEvent) => { e.preventDefault(); setIsDragging(false); onFilesPicked(e.dataTransfer.files); }, [onFilesPicked]);

  const runPipeline = async () => {
    if (!activeJob) return;
    setIsRunning(true); setDone(false); setResults([]); setError(null);
    const processed: ProcessedResult[] = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      setCurrentFile(i + 1); setCurrentStep(`Parsing resume: ${file.name}`);
      try {
        const { data: upload } = await uploadService.resume(file);
        if (!upload.profile_summary) {
          processed.push({ name: file.name, email: "", phone: null, fitScore: 0, matchedSkills: [], missingSkills: [], links: [], status: "error", error: "Could not extract profile" });
          continue;
        }
        const profile = upload.profile_summary;
        const displayName = profile.full_name || displayNameFromFilename(upload.filename || file.name);
        // Build a stable fallback email — deterministic from filename+size so same file always maps to same candidate
        const fallbackEmail = profile.phone
          ? `${profile.phone.replace(/\D/g, "")}@quantumlogic.local`
          : `${file.name.toLowerCase().replace(/[^a-z0-9]/g, "").slice(0, 30)}${file.size}@quantumlogic.local`;
        const email = profile.email || fallbackEmail;
        setCurrentStep(`Scoring ${displayName}…`);
        const { data: match } = await matchService.matchJd({ job_description: jobDescription.trim(), candidate_profile: { skills: profile.skills ?? [], education: profile.education ?? [], certifications: profile.certifications ?? [], experience_years: profile.experience_years ?? null, resume_text: upload.extracted_text_preview } });
        setCurrentStep(`Saving ${displayName}…`);
        let candidateId: string;
        // Backend upserts by email — same resume always maps to same candidate
        const { data: c } = await candidateService.create({ full_name: displayName, email, phone: profile.phone ?? null, resume_text: upload.full_text || upload.extracted_text_preview || null });
        candidateId = c.id;
        // application_service also upserts — re-uploading updates score, never duplicates
        await applicationService.create({ job_id: activeJob.id, candidate_id: candidateId, resume_score: match.fit_score, matched_skills: match.matched_skills, missing_skills: match.missing_skills });
        processed.push({ name: displayName, email, phone: profile.phone ?? null, fitScore: match.fit_score, matchedSkills: match.matched_skills, missingSkills: match.missing_skills, links: upload.verified_links ?? [], status: "saved" });
      } catch (e) {
        processed.push({ name: file.name, email: "", phone: null, fitScore: 0, matchedSkills: [], missingSkills: [], links: [], status: "error", error: getApiErrorMessage(e, "Processing failed") });
      }
      setResults([...processed]);
    }
    setIsRunning(false); setDone(true); setCurrentStep("");
  };

  if (jobs.length === 0) {
    return (
      <Layout>
        <div className="max-w-lg mx-auto mt-16 text-center">
          <div className="glass rounded-2xl shadow-card p-10">
            <div className="bg-emerald-500/20 rounded-2xl p-4 inline-flex mb-5"><Briefcase className="h-10 w-10 text-emerald-400" /></div>
            <h1 className="text-xl font-bold text-white">No job created yet</h1>
            <p className="mt-2 text-sm text-slate-400">Create a job first, then come back to upload resumes.</p>
            <Link to="/jobs" className="btn-glass-dark mt-6 inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold" style={{ color: '#fff' }}>
              Create a job <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">

        {/* Header */}
        <div className="glass rounded-2xl shadow-card p-6">
          <div className="flex items-start gap-4">
            <div className="bg-emerald-500/20 rounded-xl p-3 flex-shrink-0">
              <UploadCloud className="h-7 w-7 text-emerald-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Process Resumes</h1>
              <p className="mt-1 text-sm text-slate-400">Upload resumes → AI parses & scores each one → saved directly to Pipeline</p>
              {activeJob && (
                <span className="mt-2 inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold" style={{ background: '#f1f5f9', boxShadow: 'inset 0 0 12px rgba(0,0,0,0.09), 0px 0px 1px rgba(0,0,0,0.2)', color: '#475569' }}>
                  <Briefcase className="h-3 w-3" /> {activeJob.title}
                </span>
              )}
            </div>
          </div>
        </div>

        {!activeJob && (
          <div className="p-4 rounded-xl bg-amber-500/15 border border-amber-500/30 text-sm text-amber-300 flex items-center gap-3">
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
            No active job selected. <Link to="/jobs" className="font-semibold underline ml-1">Select a job →</Link>
          </div>
        )}

        {/* Step 1: Job Description */}
        <div className="glass rounded-2xl shadow-card p-6 space-y-4">
          {/* Header row */}
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <div className="flex items-center gap-2">
              <span className="h-6 w-6 rounded-full text-xs font-bold flex items-center justify-center flex-shrink-0" style={{ background: '#131313', color: '#fff', boxShadow: 'inset 0 0 12px rgba(255,255,255,1), 0px 0px 2px rgba(0,0,0,0.1)' }}>1</span>
              <span className="text-sm font-semibold text-white">Job Description</span>
              {jdSource === "auto" && <span className="text-xs text-emerald-400 font-medium">✓ Auto-filled from job</span>}
              {jdSource === "file" && <span className="text-xs text-sky-400 font-medium">✓ Loaded from {jdFileName}</span>}
              {jdSource === "manual" && jobDescription.length > 0 && <span className="text-xs text-amber-400 font-medium">✎ Edited manually</span>}
            </div>
            <div className="flex items-center gap-1.5">
              {/* Mode toggle */}
              <div className="flex rounded-lg border border-white/10 overflow-hidden">
                <button type="button"
                  onClick={() => setJdMode("type")}
                  className={`btn-glass inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold ${
                    jdMode === "type" ? "btn-glass-dark" : ""
                  }`}
                  style={jdMode === "type" ? { color: '#fff' } : undefined}>
                  <PenLine className="h-3 w-3" /> Type
                </button>
                <button type="button"
                  onClick={() => setJdMode("upload")}
                  className={`btn-glass inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold ${
                    jdMode === "upload" ? "btn-glass-dark" : ""
                  }`}
                  style={jdMode === "upload" ? { color: '#fff' } : undefined}>
                  <FileUp className="h-3 w-3" /> Upload
                </button>
              </div>
              {/* Reset button */}
              {activeJob?.description && jdSource !== "auto" && (
                <button type="button" onClick={resetJdToJob} disabled={isRunning}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-emerald-500/30 text-xs font-semibold text-emerald-400 hover:bg-emerald-500/10 disabled:opacity-40">
                  <RefreshCw className="h-3 w-3" /> Reset
                </button>
              )}
            </div>
          </div>

          {/* Type mode */}
          {jdMode === "type" && (
            <textarea
              data-lenis-prevent
              id={inputId} value={jobDescription}
              onChange={(e) => { setJobDescription(e.target.value); setJdSource("manual"); setJdFileName(null); }}
              rows={6} placeholder="Paste the full job description here…" disabled={isRunning}
              className="w-full px-4 py-3 rounded-xl border border-white/10 bg-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-y min-h-[120px] disabled:opacity-60 placeholder:text-slate-500"
            />
          )}

          {/* Upload mode */}
          {jdMode === "upload" && (
            <>
              <input ref={jdFileInputRef} type="file" accept=".pdf,.txt,.doc,.docx" className="hidden"
                onChange={(e) => { const f = e.target.files?.[0]; if (f) readJdFile(f); e.target.value = ""; }}
                disabled={isRunning} />
              {!jdFileName ? (
                <div
                  onDragOver={(e) => { e.preventDefault(); setIsDraggingJd(true); }}
                  onDragLeave={() => setIsDraggingJd(false)}
                  onDrop={(e) => { e.preventDefault(); setIsDraggingJd(false); const f = e.dataTransfer.files?.[0]; if (f) readJdFile(f); }}
                  onClick={() => jdFileInputRef.current?.click()}
                  className={`flex flex-col items-center justify-center gap-3 p-8 rounded-xl border-2 border-dashed cursor-pointer transition-all ${
                    isDraggingJd ? "border-sky-400 bg-sky-500/10" : "border-white/10 hover:border-sky-500/50 hover:bg-white/5"
                  }`}
                >
                  <FileUp className={`h-8 w-8 ${isDraggingJd ? "text-sky-400" : "text-slate-500"}`} />
                  <div className="text-center">
                    <p className="text-sm font-semibold text-slate-300">Drop JD file here or click to browse</p>
                    <p className="text-xs text-slate-500 mt-1">PDF, TXT, DOC, DOCX supported</p>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-between gap-3 px-4 py-3 rounded-xl bg-sky-500/10 border border-sky-500/30">
                  <div className="flex items-center gap-3">
                    <FileText className="h-4 w-4 text-sky-400 flex-shrink-0" />
                    <span className="text-sm font-medium text-sky-300">{jdFileName}</span>
                    {jobDescription && <span className="text-xs text-slate-500">{jobDescription.length} chars loaded</span>}
                  </div>
                  <button type="button" onClick={() => { setJdFileName(null); setJobDescription(""); setJdSource("manual"); }}
                    className="p-1 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-500/20">
                    <X className="h-4 w-4" />
                  </button>
                </div>
              )}
              {/* Preview loaded text */}
              {jdFileName && jobDescription && (
                <textarea
                  data-lenis-prevent
                  value={jobDescription}
                  onChange={(e) => { setJobDescription(e.target.value); setJdSource("manual"); }}
                  rows={5} disabled={isRunning}
                  className="w-full px-4 py-3 rounded-xl border border-white/10 bg-white/5 text-slate-300 text-xs focus:outline-none focus:ring-2 focus:ring-sky-500 resize-y disabled:opacity-60"
                />
              )}
            </>
          )}
        </div>

        {/* Step 2: Upload Resumes */}
        <div className="glass rounded-2xl shadow-card p-6 space-y-4">
          <div className="flex items-center gap-2 mb-1">
            <span className="h-6 w-6 rounded-full text-xs font-bold flex items-center justify-center flex-shrink-0" style={{ background: '#131313', color: '#fff', boxShadow: 'inset 0 0 12px rgba(255,255,255,1), 0px 0px 2px rgba(0,0,0,0.1)' }}>2</span>
            <span className="text-sm font-semibold text-white">Upload Resumes</span>
            <span className="text-xs text-slate-500">PDF, DOC, DOCX</span>
          </div>

          <input ref={fileInputRef} type="file" multiple accept=".pdf,.doc,.docx" className="hidden"
            onChange={(e) => { onFilesPicked(e.target.files); e.target.value = ""; }} disabled={isRunning} />

          <div
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={onDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`flex flex-col items-center justify-center gap-3 p-8 rounded-xl border-2 border-dashed cursor-pointer transition-all ${
              isDragging ? "border-emerald-400 bg-emerald-500/10" : "border-white/10 hover:border-emerald-500/50 hover:bg-white/5"
            }`}
          >
            <UploadCloud className={`h-8 w-8 ${isDragging ? "text-emerald-400" : "text-slate-500"}`} />
            <div className="text-center">
              <p className="text-sm font-semibold text-slate-300">Drop resumes here or click to browse</p>
              <p className="text-xs text-slate-500 mt-1">PDF, DOC, DOCX — multiple files supported</p>
            </div>
          </div>

          {files.length > 0 && (
            <ul className="space-y-2">
              {files.map((file, i) => (
                <li key={`${file.name}-${i}`} className="flex items-center justify-between gap-3 px-4 py-3 rounded-xl bg-white/5 border border-white/10">
                  <div className="flex items-center gap-3 min-w-0">
                    <FileText className="h-4 w-4 text-emerald-400 flex-shrink-0" />
                    <span className="text-sm font-medium text-slate-200 truncate">{file.name}</span>
                    <span className="text-xs text-slate-500 flex-shrink-0">{(file.size / 1024).toFixed(0)} KB</span>
                  </div>
                  <button type="button" onClick={() => setFiles((prev) => prev.filter((_, idx) => idx !== i))}
                    disabled={isRunning} className="p-1 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-500/20 disabled:opacity-40">
                    <X className="h-4 w-4" />
                  </button>
                </li>
              ))}
            </ul>
          )}

          {error && <p className="text-sm text-red-300 bg-red-500/20 border border-red-500/30 rounded-xl p-3">{error}</p>}
        </div>

        {/* Progress */}
        {isRunning && (
          <div className="glass rounded-2xl shadow-card p-5" style={{ borderColor: "rgba(16,185,129,0.3)" }}>
            <div className="flex items-center gap-3 mb-3">
              <Loader2 className="h-5 w-5 text-emerald-400 animate-spin flex-shrink-0" />
              <p className="text-sm font-semibold text-white">{currentStep}</p>
            </div>
            <div className="h-2 bg-white/10 rounded-full overflow-hidden">
              <div className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                style={{ width: `${files.length > 0 ? (currentFile / files.length) * 100 : 0}%` }} />
            </div>
            <p className="text-xs text-slate-400 mt-2">{currentFile} of {files.length} resumes</p>
          </div>
        )}

        {/* Results */}
        {results.length > 0 && (
          <div className="glass rounded-2xl shadow-card overflow-hidden">
            <div className="px-6 py-4 border-b border-white/10" style={{ background: "rgba(255,255,255,0.04)" }}>
              <p className="text-sm font-semibold text-white">Processing Results</p>
            </div>
            <ul className="divide-y divide-white/5">
              {results.map((r, i) => (
                <li key={i} className="px-6 py-4 flex items-start gap-4">
                  <div className="flex-shrink-0 mt-0.5">
                    {r.status === "saved" && <CheckCircle2 className="h-5 w-5 text-emerald-400" />}
                    {r.status === "duplicate" && <CheckCircle2 className="h-5 w-5 text-amber-400" />}
                    {r.status === "error" && <AlertCircle className="h-5 w-5 text-red-400" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 flex-wrap">
                      <p className="text-sm font-semibold text-white">{r.name}</p>
                      {r.status === "saved" && <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Score: {r.fitScore.toFixed(0)}%</span>}
                      {r.status === "duplicate" && <span className="text-xs font-medium text-amber-400">Already applied</span>}
                      {r.status === "error" && <span className="text-xs text-red-400">{r.error}</span>}
                    </div>
                    <div className="flex flex-wrap gap-3 mt-1.5 text-xs text-slate-400">
                      {r.email && r.email.includes("@") && !r.email.includes("quantumlogic.local") && <span>📧 {r.email}</span>}
                      {r.phone && <span>📞 {r.phone}</span>}
                    </div>
                    {r.links.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-1.5">
                        {r.links.map((l) => (
                          <a key={l.url} href={l.url} target="_blank" rel="noopener noreferrer"
                            className={`text-xs px-2 py-0.5 rounded-full border font-medium ${l.reachable ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/30 hover:bg-emerald-500/25" : "bg-white/5 text-slate-500 border-white/10 line-through"}`}>
                            {l.platform === "github_repo" ? "⭐ GitHub Repo" : l.platform === "github_profile" ? "🐙 GitHub" : l.platform === "linkedin" ? "💼 LinkedIn" : "🔗 Link"}
                          </a>
                        ))}
                      </div>
                    )}
                    {r.matchedSkills.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {r.matchedSkills.slice(0, 5).map((s) => <span key={s} className="px-1.5 py-0.5 rounded text-xs bg-emerald-500/15 text-emerald-300 border border-emerald-500/20">{s}</span>)}
                        {r.matchedSkills.length > 5 && <span className="text-xs text-slate-500">+{r.matchedSkills.length - 5} more</span>}
                      </div>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3 pb-8 justify-center">
          {!done ? (
            <button type="button" onClick={runPipeline}
              disabled={isRunning || files.length === 0 || jobDescription.trim().length < 10 || !activeJob}
              className="btn-glass-dark inline-flex items-center justify-center gap-2 px-8 py-3 rounded-full text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed">
              {isRunning ? <><Loader2 className="h-4 w-4 animate-spin" /> Processing…</> : <><UploadCloud className="h-4 w-4" /> Run Pipeline</>}
            </button>
          ) : (
            <button type="button" onClick={() => navigate("/pipeline")}
              className="btn-glass-dark inline-flex items-center justify-center gap-2 px-8 py-3 rounded-full text-sm font-semibold">
              <ArrowRight className="h-4 w-4" /> View Pipeline →
            </button>
          )}
          {done && (
            <button type="button" onClick={() => { setFiles([]); setResults([]); setDone(false); }}
              className="btn-glass inline-flex items-center justify-center gap-2 px-8 py-3 rounded-full text-sm font-semibold">
              Process More Resumes
            </button>
          )}
        </div>
      </div>
    </Layout>
  );
}
