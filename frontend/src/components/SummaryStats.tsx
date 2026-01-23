import { formatDuration } from "../lib/format";

interface SummaryStatsProps {
  durationSec: number;
  framesAnalyzed: number;
  intervalSec: number;
  uniqueEntities: number;
}

export default function SummaryStats({
  durationSec,
  framesAnalyzed,
  intervalSec,
  uniqueEntities,
}: SummaryStatsProps) {
  return (
    <div className="ei-card">
      <div className="ei-card-header">Summary Statistics</div>
      <div className="ei-card-body grid grid-cols-2 md:grid-cols-4 gap-6 text-sm">
        <div>
          <div className="text-ei-muted">Duration</div>
          <div className="text-lg font-semibold mt-1">{formatDuration(durationSec)}</div>
        </div>
        <div>
          <div className="text-ei-muted">Frames Analyzed</div>
          <div className="text-lg font-semibold mt-1">{framesAnalyzed}</div>
        </div>
        <div>
          <div className="text-ei-muted">Interval</div>
          <div className="text-lg font-semibold mt-1">{intervalSec}s</div>
        </div>
        <div>
          <div className="text-ei-muted">Unique Entities</div>
          <div className="text-lg font-semibold mt-1">{uniqueEntities}</div>
        </div>
      </div>
    </div>
  );
}
