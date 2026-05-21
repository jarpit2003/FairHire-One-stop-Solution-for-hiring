import { PieChart as PieChartIcon } from 'lucide-react';

interface RecommendationFunnelProps {
  breakdown: Record<string, number>;
}

const ROWS: {
  key: string;
  label: string;
  color: string;
  track: string;
  description: string;
}[] = [
  {
    key: 'interview',
    label: 'Interview Ready',
    color: '#10B981',
    track: 'bg-green-100',
    description: 'Ready for immediate interviews',
  },
  {
    key: 'shortlisted',
    label: 'Shortlisted',
    color: '#F59E0B',
    track: 'bg-amber-100',
    description: 'Strong contenders',
  },
  {
    key: 'consider',
    label: 'Consider',
    color: '#fbbf24',
    track: 'bg-amber-50',
    description: 'May need additional screening',
  },
  {
    key: 'reject',
    label: 'Reject',
    color: '#EF4444',
    track: 'bg-red-50',
    description: 'Not suitable for this role',
  },
];

export default function RecommendationFunnel({ breakdown }: RecommendationFunnelProps) {
  const enriched = ROWS.map((row) => ({
    ...row,
    value: breakdown[row.key] ?? 0,
  })).filter((row) => row.value > 0);

  const total = enriched.reduce((sum, row) => sum + row.value, 0);

  return (
    <div className="bg-white rounded-2xl shadow-card border border-gray-100 p-6">
      <div className="flex items-start gap-3 mb-6">
        <div className="bg-blue-50 rounded-xl p-2.5 flex-shrink-0">
          <PieChartIcon className="h-5 w-5 text-blue-600" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900 tracking-tight">Recommendation Breakdown</h3>
          <p className="mt-1 text-sm text-gray-500">Share of candidates by AI recommendation tier</p>
        </div>
      </div>

      {enriched.length === 0 ? (
        <div className="text-center py-10 text-sm text-gray-500">No recommendation data for this pool</div>
      ) : (
        <div className="space-y-5">
          {enriched.map((row) => {
            const pct = total > 0 ? Math.round((row.value / total) * 1000) / 10 : 0;
            return (
              <div key={row.key}>
                <div className="flex items-center justify-between gap-3 mb-2">
                  <div>
                    <span className="text-sm font-semibold text-gray-900">{row.label}</span>
                    <p className="text-xs text-gray-500 mt-0.5">{row.description}</p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <span className="text-sm font-bold text-gray-900">{row.value}</span>
                    <span className="text-xs text-gray-500 ml-2">{pct}%</span>
                  </div>
                </div>
                <div className={`h-2.5 w-full rounded-full overflow-hidden ${row.track}`}>
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${pct}%`,
                      backgroundColor: row.color,
                      minWidth: pct > 0 ? '4px' : undefined,
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
