interface Range {
  start_sec: number;
  end_sec: number;
}

interface TimelineBarProps {
  ranges: Range[];
  duration: number;
}

export default function TimelineBar({ ranges, duration }: TimelineBarProps) {
  if (!duration || ranges.length === 0) {
    return <div className="h-2 bg-ei-border rounded-full" />;
  }
  return (
    <div className="relative h-3 bg-ei-border rounded-full overflow-hidden">
      {ranges.map((range, idx) => {
        const left = (range.start_sec / duration) * 100;
        const width = ((range.end_sec - range.start_sec) / duration) * 100;
        return (
          <div
            key={idx}
            className="absolute top-0 h-full bg-ei-accent"
            style={{ left: `${left}%`, width: `${Math.max(width, 2)}%` }}
          />
        );
      })}
    </div>
  );
}
