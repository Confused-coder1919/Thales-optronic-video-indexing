import type { VideoReport } from "../lib/types";

const COLOR_MAP: Record<string, string> = {
  aircraft: "#f59e0b",
  helicopter: "#6366f1",
  "military personnel": "#8b5cf6",
  weapon: "#f97316",
  equipment: "#fb7185",
  "armored vehicle": "#ef4444",
  "military vehicle": "#14b8a6",
  turret: "#f97316",
};

const fallbackColors = ["#0ea5e9", "#22c55e", "#f97316", "#a855f7", "#f43f5e"];

function pickColor(label: string, index: number) {
  return COLOR_MAP[label] || fallbackColors[index % fallbackColors.length];
}

interface TimelineViewProps {
  report: VideoReport;
}

export default function TimelineView({ report }: TimelineViewProps) {
  const entries = Object.entries(report.entities);
  const duration = report.duration_sec || 1;

  return (
    <div className="ei-card">
      <div className="ei-card-header">Consolidated Timeline View</div>
      <div className="px-5 py-3 text-xs text-ei-muted border-b border-ei-border">
        Visual representation of when each entity appears in the video
      </div>
      <div className="ei-card-body space-y-4">
        {entries.map(([label, data], idx) => {
          const color = pickColor(label, idx);
          return (
            <div key={label} className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
                  <span className="font-semibold text-ei-text">{label}</span>
                  <span className="text-xs text-ei-muted">({data.appearances} appearances)</span>
                </div>
                <span className="text-xs text-ei-muted">
                  {(data.presence * 100).toFixed(1)}% of video
                </span>
              </div>
              <div className="relative h-10 rounded-md bg-ei-tab border border-ei-border overflow-hidden">
                {data.time_ranges.map((range, ridx) => {
                  const length = Math.max(report.interval_sec, range.end_sec - range.start_sec + report.interval_sec);
                  const left = (range.start_sec / duration) * 100;
                  const width = (length / duration) * 100;
                  return (
                    <div
                      key={`${label}-${ridx}`}
                      className="absolute top-2 bottom-2 rounded-md"
                      style={{
                        left: `${left}%`,
                        width: `${width}%`,
                        backgroundColor: color,
                      }}
                    />
                  );
                })}
              </div>
            </div>
          );
        })}
        {entries.length === 0 && (
          <div className="text-sm text-ei-muted">No entities detected.</div>
        )}
      </div>
    </div>
  );
}
