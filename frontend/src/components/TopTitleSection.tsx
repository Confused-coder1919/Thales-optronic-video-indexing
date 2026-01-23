import { ReactNode } from "react";

interface TopTitleSectionProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}

export default function TopTitleSection({ title, subtitle, actions }: TopTitleSectionProps) {
  return (
    <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-6">
      <div>
        <h1 className="ei-section-title">{title}</h1>
        {subtitle && <p className="ei-section-subtitle mt-1 max-w-2xl">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-3">{actions}</div>}
    </div>
  );
}
