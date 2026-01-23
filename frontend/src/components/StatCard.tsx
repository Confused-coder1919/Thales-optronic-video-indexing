interface StatCardProps {
  label: string;
  value: string | number;
}

export default function StatCard({ label, value }: StatCardProps) {
  return (
    <div className="ei-card px-4 py-3">
      <div className="text-[11px] uppercase tracking-wide text-ei-muted">{label}</div>
      <div className="text-2xl font-semibold mt-1 text-ei-text">{value}</div>
    </div>
  );
}
