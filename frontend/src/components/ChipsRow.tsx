interface ChipItem {
  label: string;
  count?: number;
  confidence?: number;
  sources?: string[];
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
          <span
            key={item.label}
            className="ei-chip"
            title={
              item.sources && item.sources.length > 0
                ? `Sources: ${item.sources.join(", ")}`
                : undefined
            }
          >
            {item.label}
            {item.count !== undefined ? ` (${item.count})` : ""}
            {item.confidence !== undefined
              ? ` · ${Math.round(item.confidence * 100)}%`
              : ""}
          </span>
        ))}
      </div>
    </div>
  );
}
