import axios from "axios";

const api = axios.create({ baseURL: "/api/v1" });

// Inject JWT on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("quantumlogic_token");
  if (token) {
    config.headers = config.headers ?? {};
    (config.headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }
  return config;
});

// Auto-clear token and redirect to login on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (axios.isAxiosError(err) && err.response?.status === 401) {
      localStorage.removeItem("quantumlogic_token");
      localStorage.removeItem("quantumlogic_user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export const candidateService = {
  list: () => api.get<CandidateRecord[]>("/candidates/"),
  get: (id: string) => api.get<CandidateRecord>(`/candidates/${id}`),
  create: (data: unknown) => api.post<CandidateRecord>("/candidates/", data),
};

export const jobService = {
  list: () => api.get<JobRecord[]>("/jobs/"),
  get: (id: string) => api.get<JobRecord>(`/jobs/${id}`),
  create: (data: unknown) => api.post<JobRecord>("/jobs/", data),
};

export const applicationService = {
  list: (jobId: string) => api.get<ApplicationRecord[]>(`/applications/?job_id=${jobId}`),
  listByCandidate: (candidateId: string) => api.get<ApplicationRecord[]>(`/applications/by-candidate/${candidateId}`),
  get: (id: string) => api.get<ApplicationRecord>(`/applications/${id}`),
  create: (data: unknown) => api.post<ApplicationRecord>("/applications/", data),
  advanceStage: (id: string, stage: string) =>
    api.patch<ApplicationRecord>(`/applications/${id}/stage`, { stage }),
  shortlist: (id: string) =>
    api.patch<ApplicationRecord>(`/applications/${id}/stage`, { stage: "shortlisted" }),
  recordTestScore: (id: string, test_score: number) =>
    api.post<ApplicationRecord>(`/applications/${id}/test-score`, { test_score }),
  sendTestLink: (id: string, test_link: string, deadline?: string) =>
    api.post<ApplicationRecord>(`/applications/${id}/send-test-link`, { test_link, deadline }),
  updateWeights: (id: string, resume_weight: number, test_weight: number) =>
    api.patch<ApplicationRecord>(`/applications/${id}/weights`, { resume_weight, test_weight }),
  getOfferDraft: (id: string) =>
    api.get<{ draft: string; candidate_name: string; job_title: string }>(`/applications/${id}/offer-draft`),
  reject: (id: string) => api.post<ApplicationRecord>(`/applications/${id}/reject`),
  offer: (id: string, draft: string) => api.post<ApplicationRecord>(`/applications/${id}/offer`, { draft }),
  delete: (id: string) => api.delete(`/applications/${id}`),
};

export const interviewService = {
  list: (jobId?: string) => api.get<InterviewRecord[]>(jobId ? `/interviews/?job_id=${jobId}` : "/interviews/"),
  schedule: (data: unknown) => api.post<InterviewRecord>("/interviews/", data),
  submitScore: (id: string, score: number, feedback?: string) =>
    api.patch<InterviewRecord>(`/interviews/${id}/score`, { score, feedback }),
  updateStatus: (id: string, status: string) =>
    api.patch<InterviewRecord>(`/interviews/${id}/status`, { status }),
};

export const analyticsService = {
  summary: (data: AnalyticsRequest) => api.post<AnalyticsResponse>("/analytics/summary", data),
};

/** POST /api/v1/upload/resume — multipart field name must be `file`. */
export const uploadService = {
  resume: (file: File) => {
    const body = new FormData();
    body.append("file", file);
    return api.post<UploadResponse>("/upload/resume", body);
  },
};

/** POST /api/v1/match/jd — per-candidate shortlist / fit scoring. */
export const matchService = {
  matchJd: (data: MatchRequest) => api.post<MatchResponse>("/match/jd", data),
};

export const chatService = {
  send: (message: string, history: {role:string;content:string}[], job_id?: string) =>
    api.post<{reply: string}>("/chat/", { message, history, job_id }),
};

// --- DB Records (persistent) ---
export interface CandidateRecord {
  id: string;
  full_name: string;
  email: string;
  phone: string | null;
  resume_text: string | null;
}

export interface JobRecord {
  id: string;
  title: string;
  description: string | null;
  status: string;
  deadline: string | null;
  form_url: string | null;
  published_platforms: string[];
}

export interface ApplicationRecord {
  id: string;
  job_id: string;
  candidate_id: string;
  candidate_name: string;
  candidate_email: string;
  candidate_phone: string | null;
  resume_score: number | null;
  test_score: number | null;
  interview_score: number | null;
  hr_interview_score: number | null;
  final_score: number | null;
  stage: string;
  status: string;
  matched_skills: string[];
  missing_skills: string[];
  applied_at: string;
  resume_weight: number;
  test_weight: number;
  email_sent?: boolean;
  email_status?: string;
}

export interface InterviewRecord {
  id: string;
  candidate_id: string;
  job_id: string;
  application_id: string | null;
  round_number: number;
  interviewer_name: string | null;
  status: string;
  scheduled_at: string | null;
  meet_link: string | null;
  notes: string | null;
  score: number | null;
  feedback: string | null;
}

// --- Upload ---
export interface ProfileSummary {
  skills: string[];
  education: string[];
  certifications: string[];
  experience_years: number | null;
  full_name: string | null;
  email: string | null;
  phone: string | null;
}

export interface VerifiedLink {
  url: string;
  reachable: boolean;
  platform: string;
  detail: string;
  commit_activity: boolean;
}

export interface UploadResponse {
  filename: string;
  size_bytes: number;
  detected_type: string;
  full_text: string;
  extracted_text_preview: string;
  profile_summary: ProfileSummary | null;
  verified_links: VerifiedLink[];
  used_gemini_fallback: boolean;
  message: string;
}

// --- Match (shortlist) ---
export interface CandidateProfilePayload {
  skills: string[];
  education: string[];
  certifications: string[];
  experience_years?: number | null;
  resume_text?: string | null;
}

export interface MatchRequest {
  candidate_profile: CandidateProfilePayload;
  job_description: string;
}

export interface MatchResponse {
  fit_score: number;
  matched_skills: string[];
  missing_skills: string[];
  skill_overlap_score: number;
  education_relevance_score: number;
  experience_relevance_score: number;
  semantic_similarity_score: number;
  impact_score: number;
  impact_highlights: string[];
  explanation: Record<string, string>;
}

// --- Analytics ---
export interface CandidateProfile {
  candidate_id: string;
  skills: string[];
  education: string[];
  certifications: string[];
  experience_years?: number;
}

export interface AnalyticsRequest {
  job_description: string;
  candidates: CandidateProfile[];
}

export interface ScoreDistribution {
  excellent: number;
  good: number;
  moderate: number;
  poor: number;
}

export interface AnalyticsResponse {
  total_candidates: number;
  average_fit_score: number;
  top_candidate_score: number;
  shortlisted_count: number;
  recommended_for_interview_count: number;
  common_missing_skills: string[];
  score_distribution: ScoreDistribution;
  recommendation_breakdown: Record<string, number>;
  insights: Record<string, string>;
}

/** Row shape for `TopCandidates` leaderboard. */
export interface LeaderboardCandidate {
  id: string;
  name: string;
  fitScore: number;
  matchedSkills: string[];
  recommendation: string;
}
