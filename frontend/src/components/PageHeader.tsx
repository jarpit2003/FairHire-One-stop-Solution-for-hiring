import type { ReactNode } from "react";

interface PageHeaderProps {
  icon: ReactNode;
  title: string;
  subtitle?: string;
  action?: ReactNode;
  badge?: ReactNode;
}

export default function PageHeader({ icon, title, subtitle, action, badge }: PageHeaderProps) {
  return (
    <div className="glass rounded-2xl shadow-card p-5 flex items-center justify-between gap-4 flex-wrap mb-6">
      <div className="flex items-center gap-4 min-w-0">
        <div className="bg-emerald-500/20 rounded-xl p-3 flex-shrink-0">
          {icon}
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-xl font-bold text-white">{title}</h1>
            {badge}
          </div>
          {subtitle && <p className="text-sm text-slate-400 mt-0.5">{subtitle}</p>}
        </div>
      </div>
      {action && <div className="flex-shrink-0">{action}</div>}
    </div>
  );
}
