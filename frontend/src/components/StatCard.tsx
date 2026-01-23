interface StatCardProps {
  label: string;
  value: string | number;
  helper?: string;
}

export default function StatCard({ label, value, helper }: StatCardProps) {
  return (
    <div className="card">
      <div className="text-xs uppercase tracking-widest text-ei-muted">{label}</div>
      <div className="text-2xl font-semibold mt-2">{value}</div>
      {helper && <div className="text-xs text-ei-muted mt-1">{helper}</div>}
    </div>
  );
}
