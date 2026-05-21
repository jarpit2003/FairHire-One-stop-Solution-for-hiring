import type { LeaderboardCandidate } from "../services/api";

/** Recruiter-driven ATS stage (separate from AI recommendation tier). */
export type PipelineWorkflowStatus = "matched" | "shortlisted" | "interview_scheduled";

export interface InterviewBooking {
  scheduledDate: string;
  scheduledTime: string;
  format: "video" | "phone" | "onsite";
  notes: string;
}

/** Passed via `navigate('/interviews', { state })` from the dashboard leaderboard. */
export interface InterviewScheduleLocationState {
  candidate: LeaderboardCandidate;
}
