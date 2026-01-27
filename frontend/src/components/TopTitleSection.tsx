import { ReactNode } from "react";

interface TopTitleSectionProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  icon?: ReactNode;
}

export default function TopTitleSection({ title, subtitle, actions, icon }: TopTitleSectionProps) {
  return (
    <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-6">
      <div>
        <h1 className="ei-section-title flex items-center gap-2">
          {icon && <span className="text-ei-accent">{icon}</span>}
          {title}
        </h1>
        {subtitle && <p className="ei-section-subtitle mt-1 max-w-2xl">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-3">{actions}</div>}
    </div>
  );
}
