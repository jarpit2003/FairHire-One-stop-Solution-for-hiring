import {
  analyticsService,
  matchService,
  uploadService,
  CandidateProfile,
  AnalyticsResponse,
  LeaderboardCandidate,
  ProfileSummary,
} from "./api";
import { recommendationFromFitScore } from "../utils/recommendation";
import { displayNameFromFilename, makeCandidateId } from "../utils/resumeFilename";

export type PipelinePhase = "idle" | "upload" | "shortlist" | "analytics" | "done" | "error";

export interface PipelineProgress {
  phase: PipelinePhase;
  message: string;
  current?: number;
  total?: number;
}

function profileToCandidatePayload(profile: ProfileSummary): {
  skills: string[];
  education: string[];
  certifications: string[];
  experience_years: number | undefined;
} {
  return {
    skills: profile.skills ?? [],
    education: profile.education ?? [],
    certifications: profile.certifications ?? [],
    experience_years: profile.experience_years ?? undefined,
  };
}

export interface RecruiterPipelineResult {
  jobDescription: string;
  candidates: CandidateProfile[];
  analytics: AnalyticsResponse;
  leaderboard: LeaderboardCandidate[];
}

const JD_MIN = 10;

/**
 * Orchestrates upload → match/jd (shortlist per candidate) → analytics/summary.
 * Backend has no batch shortlist route; `/match/jd` is the scoring step before aggregate analytics.
 */
export async function runRecruiterPipeline(
  files: File[],
  jobDescription: string,
  onProgress: (p: PipelineProgress) => void
): Promise<RecruiterPipelineResult> {
  const trimmed = jobDescription.trim();
  if (trimmed.length < JD_MIN) {
    throw new Error(`Job description must be at least ${JD_MIN} characters.`);
  }
  if (files.length === 0) {
    throw new Error("Add at least one resume (PDF or Word).");
  }

  const uploaded: { file: File; candidateId: string; displayName: string; profile: ProfileSummary }[] = [];

  onProgress({ phase: "upload", message: "Uploading resumes…", current: 0, total: files.length });

  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    onProgress({
      phase: "upload",
      message: `Uploading ${file.name}…`,
      current: i + 1,
      total: files.length,
    });

    const { data } = await uploadService.resume(file);
    if (!data.profile_summary) {
      throw new Error(
        `Could not extract a profile from "${data.filename}". Try another file or a clearer resume.`
      );
    }

    const candidateId = makeCandidateId(file.name, i);
    uploaded.push({
      file,
      candidateId,
      displayName: displayNameFromFilename(data.filename || file.name),
      profile: data.profile_summary,
    });
  }

  const candidates: CandidateProfile[] = uploaded.map((u) => ({
    candidate_id: u.candidateId,
    ...profileToCandidatePayload(u.profile),
  }));

  const leaderboard: LeaderboardCandidate[] = [];

  onProgress({
    phase: "shortlist",
    message: "Scoring candidates against the job description…",
    current: 0,
    total: candidates.length,
  });

  for (let i = 0; i < candidates.length; i++) {
    const u = uploaded[i];
    const c = candidates[i];
    onProgress({
      phase: "shortlist",
      message: `Shortlisting ${u.displayName}…`,
      current: i + 1,
      total: candidates.length,
    });

    const { data: match } = await matchService.matchJd({
      job_description: trimmed,
      candidate_profile: {
        skills: c.skills,
        education: c.education,
        certifications: c.certifications,
        experience_years: c.experience_years ?? null,
      },
    });

    leaderboard.push({
      id: c.candidate_id,
      name: u.displayName,
      fitScore: match.fit_score,
      matchedSkills: match.matched_skills,
      recommendation: recommendationFromFitScore(match.fit_score),
    });
  }

  leaderboard.sort((a, b) => b.fitScore - a.fitScore);

  onProgress({ phase: "analytics", message: "Computing dashboard analytics…" });

  const { data: analytics } = await analyticsService.summary({
    job_description: trimmed,
    candidates,
  });

  onProgress({ phase: "done", message: "Done" });

  return {
    jobDescription: trimmed,
    candidates,
    analytics,
    leaderboard,
  };
}
