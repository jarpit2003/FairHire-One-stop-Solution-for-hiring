import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { BarChart3 } from 'lucide-react';
import { ScoreDistribution } from '../services/api';

interface ScoreDistributionChartProps {
  distribution: ScoreDistribution;
}

export default function ScoreDistributionChart({ distribution }: ScoreDistributionChartProps) {
  const data = [
    {
      category: 'Excellent',
      range: '80-100%',
      count: distribution.excellent,
      color: '#10B981',
    },
    {
      category: 'Good',
      range: '60-79%',
      count: distribution.good,
      color: '#2563EB',
    },
    {
      category: 'Moderate',
      range: '40-59%',
      count: distribution.moderate,
      color: '#F59E0B',
    },
    {
      category: 'Poor',
      range: '0-39%',
      count: distribution.poor,
      color: '#EF4444',
    },
  ];

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const row = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-100 rounded-xl shadow-card">
          <p className="font-semibold text-gray-900">{`${label} (${row.range})`}</p>
          <p className="text-sm text-gray-600 mt-1">{`Candidates: ${row.count}`}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-2xl shadow-card border border-gray-100 p-6">
      <div className="flex items-start gap-3 mb-6">
        <div className="bg-blue-50 rounded-xl p-2.5 flex-shrink-0">
          <BarChart3 className="h-5 w-5 text-blue-600" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900 tracking-tight">Score Distribution</h3>
          <p className="mt-1 text-sm text-gray-500">How candidates cluster across fit score bands</p>
        </div>
      </div>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 12, right: 24, left: 8, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
            <XAxis dataKey="category" tick={{ fontSize: 12, fill: '#6b7280' }} tickLine={false} axisLine={false} />
            <YAxis tick={{ fontSize: 12, fill: '#6b7280' }} tickLine={false} axisLine={false} />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(37, 99, 235, 0.06)' }} />
            <Bar dataKey="count" radius={[8, 8, 0, 0]} maxBarSize={56}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
