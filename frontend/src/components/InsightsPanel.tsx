import { Lightbulb, CheckCircle, AlertCircle, Info } from 'lucide-react';

interface InsightsPanelProps {
  insights: Record<string, string>;
}

export default function InsightsPanel({ insights }: InsightsPanelProps) {
  const getInsightIcon = (key: string) => {
    switch (key) {
      case 'quality':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'readiness':
        return <Info className="h-5 w-5 text-blue-600" />;
      case 'skill_gaps':
        return <AlertCircle className="h-5 w-5 text-amber-600" />;
      case 'recommendation':
        return <Lightbulb className="h-5 w-5 text-blue-600" />;
      default:
        return <Info className="h-5 w-5 text-gray-500" />;
    }
  };

  const getInsightTitle = (key: string) => {
    switch (key) {
      case 'quality':
        return 'Candidate Pool Quality';
      case 'readiness':
        return 'Interview Readiness';
      case 'skill_gaps':
        return 'Skill Gap Analysis';
      case 'recommendation':
        return 'Recommended Action';
      default:
        return key.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase());
    }
  };

  const getInsightColor = (key: string) => {
    switch (key) {
      case 'quality':
        return 'border-green-200 bg-green-50';
      case 'readiness':
        return 'border-blue-200 bg-blue-50';
      case 'skill_gaps':
        return 'border-amber-200 bg-amber-50';
      case 'recommendation':
        return 'border-blue-200 bg-blue-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-card border border-gray-100 p-6">
      <div className="flex items-start gap-3 mb-6">
        <div className="bg-blue-50 rounded-xl p-2.5 flex-shrink-0">
          <Lightbulb className="h-5 w-5 text-blue-600" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900 tracking-tight">AI Insights</h3>
          <p className="mt-1 text-sm text-gray-500">Narrative summary across your pipeline</p>
        </div>
      </div>

      <div className="space-y-4">
        {Object.entries(insights).map(([key, value]) => (
          <div key={key} className={`p-4 rounded-xl border ${getInsightColor(key)}`}>
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 mt-0.5">{getInsightIcon(key)}</div>
              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-semibold text-gray-900 mb-1">{getInsightTitle(key)}</h4>
                <p className="text-sm text-gray-700 leading-relaxed">{value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
