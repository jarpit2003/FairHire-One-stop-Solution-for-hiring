import { TrendingUp, Users, Award, Target } from "lucide-react";

interface MetricsCardsProps {
  totalCandidates: number;
  averageFitScore: number;
  topCandidateScore: number;
  interviewReadyCount: number;
}

export default function MetricsCards({
  totalCandidates,
  averageFitScore,
  topCandidateScore,
  interviewReadyCount,
}: MetricsCardsProps) {
  const metrics = [
    {
      label: "Total Applicants",
      value: totalCandidates.toString(),
      sub: "in this pipeline run",
      icon: Users,
      accent: "border-blue-500",
      iconBg: "bg-blue-50",
      iconColor: "text-blue-600",
      valueColor: "text-slate-900",
    },
    {
      label: "Avg. Fit Score",
      value: `${averageFitScore.toFixed(1)}%`,
      sub: "across all profiles",
      icon: TrendingUp,
      accent: averageFitScore >= 60 ? "border-emerald-500" : "border-amber-400",
      iconBg: averageFitScore >= 60 ? "bg-emerald-50" : "bg-amber-50",
      iconColor: averageFitScore >= 60 ? "text-emerald-600" : "text-amber-600",
      valueColor: averageFitScore >= 60 ? "text-emerald-700" : "text-amber-700",
    },
    {
      label: "Top Match Score",
      value: `${topCandidateScore}%`,
      sub: "best candidate strength",
      icon: Award,
      accent: topCandidateScore >= 80 ? "border-emerald-500" : "border-blue-400",
      iconBg: "bg-amber-50",
      iconColor: "text-amber-500",
      valueColor: "text-slate-900",
    },
    {
      label: "Interview Ready",
      value: interviewReadyCount.toString(),
      sub: `of ${totalCandidates} candidates`,
      icon: Target,
      accent: "border-emerald-500",
      iconBg: "bg-emerald-50",
      iconColor: "text-emerald-600",
      valueColor: "text-emerald-700",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
      {metrics.map((m) => (
        <div
          key={m.label}
          className={`glass glass-hover rounded-2xl shadow-card p-5 border-l-4 ${m.accent} flex items-center gap-4 transition-all`}
        >
          <div className={`${m.iconBg} rounded-xl p-3 flex-shrink-0`}>
            <m.icon className={`h-5 w-5 ${m.iconColor}`} />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide truncate">{m.label}</p>
            <p className={`text-2xl font-bold tracking-tight mt-0.5 ${m.valueColor}`}>{m.value}</p>
            <p className="text-xs text-slate-500 mt-0.5 truncate">{m.sub}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
