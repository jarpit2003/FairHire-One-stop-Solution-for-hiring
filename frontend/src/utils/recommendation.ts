/** Aligns with backend `services.analytics._determine_recommendation` thresholds. */
export function recommendationFromFitScore(fitScore: number): string {
  if (fitScore >= 80) return 'interview';
  if (fitScore >= 60) return 'shortlisted';
  if (fitScore >= 40) return 'consider';
  return 'reject';
}
