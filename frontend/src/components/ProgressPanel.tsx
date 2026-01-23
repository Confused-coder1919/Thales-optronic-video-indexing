import { formatStage } from "../lib/format";

interface ProgressPanelProps {
  progress: number;
  currentStage?: string | null;
  statusText?: string | null;
}

export default function ProgressPanel({ progress, currentStage, statusText }: ProgressPanelProps) {
  return (
    <div className="ei-card">
      <div className="ei-card-header">Processing Progress</div>
      <div className="ei-card-body">
        <div className="ei-card border border-ei-border rounded-lg">
          <div className="px-4 py-3 border-b border-ei-border flex items-center gap-2 text-sm font-semibold">
            <span className="w-2 h-2 rounded-full bg-ei-pill-processing" />
            Processing Video
          </div>
          <div className="px-4 py-3 text-sm">
            <div className="flex items-center justify-between text-ei-muted">
              <span>Progress</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div className="mt-2 h-2 rounded-full bg-ei-tab">
              <div
                className="h-2 rounded-full bg-ei-pill-processing"
                style={{ width: `${Math.min(progress, 100)}%` }}
              />
            </div>
            <div className="mt-4 text-ei-muted">
              <div className="text-xs uppercase tracking-wide">Current Stage</div>
              <div className="text-sm text-ei-text mt-1">{formatStage(currentStage)}</div>
            </div>
            <div className="mt-4 text-ei-muted">
              <div className="text-xs uppercase tracking-wide">Status</div>
              <div className="text-sm text-ei-text mt-1">{statusText || "Processing"}</div>
            </div>
            <div className="mt-4 text-xs text-ei-muted">
              Automatically refreshing every 1.5 seconds...
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
