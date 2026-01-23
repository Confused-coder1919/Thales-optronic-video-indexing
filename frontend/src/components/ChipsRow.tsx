interface ChipItem {
  label: string;
  count?: number;
}

interface ChipsRowProps {
  title: string;
  items: ChipItem[];
}

export default function ChipsRow({ title, items }: ChipsRowProps) {
  return (
    <div className="ei-card">
      <div className="ei-card-header">{title}</div>
      <div className="ei-card-body flex flex-wrap gap-2">
        {items.length === 0 && <div className="text-sm text-ei-muted">None</div>}
        {items.map((item) => (
          <span key={item.label} className="ei-chip">
            {item.label}
            {item.count !== undefined ? ` (${item.count})` : ""}
          </span>
        ))}
      </div>
    </div>
  );
}
