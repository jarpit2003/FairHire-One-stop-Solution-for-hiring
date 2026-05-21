import { AlertTriangle, Sparkles } from 'lucide-react';

interface MissingSkillsProps {
  skills: string[];
  insights: Record<string, string>;
}

export default function MissingSkills({ skills, insights }: MissingSkillsProps) {
  return (
    <div className="bg-white rounded-2xl shadow-card border border-gray-100 p-6">
      <div className="flex items-start gap-3 mb-5">
        <div className="bg-amber-50 rounded-xl p-2.5 flex-shrink-0">
          <AlertTriangle className="h-5 w-5 text-amber-600" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900 tracking-tight">Common Missing Skills</h3>
          <p className="mt-1 text-sm text-gray-500">Gaps most often seen vs. this job description</p>
        </div>
      </div>

      {skills.length > 0 ? (
        <div className="space-y-5">
          <div className="flex flex-wrap gap-2">
            {skills.map((skill) => (
              <span
                key={skill}
                className="inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium bg-amber-50 text-amber-800 border border-amber-200"
              >
                {skill}
              </span>
            ))}
          </div>

          {insights.skill_gaps && (
            <div className="mt-2 p-4 bg-blue-50 border border-blue-200 rounded-xl">
              <div className="flex items-start gap-2">
                <Sparkles className="h-4 w-4 text-blue-600 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-blue-800">
                  <strong>Insight:</strong> {insights.skill_gaps}
                </p>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-10">
          <div className="text-gray-300 mb-3">
            <AlertTriangle className="h-12 w-12 mx-auto" />
          </div>
          <p className="text-sm font-medium text-gray-600">No significant skill gaps identified</p>
          <p className="text-xs text-gray-500 mt-1">All candidates meet the core requirements</p>
        </div>
      )}
    </div>
  );
}
