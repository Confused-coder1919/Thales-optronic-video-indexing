import { Link } from "react-router-dom";
import { formatDateTime, formatDuration } from "../lib/format";
import type { VideoSummary } from "../lib/types";

interface VideoCardProps {
  video: VideoSummary;
  onDelete?: (id: string) => void;
}

const statusClass = (status: string) => {
  if (status === "completed") return "ei-pill completed";
  if (status === "failed") return "ei-pill failed";
  return "ei-pill processing";
};

const formatStatus = (status: string) =>
  status ? status.charAt(0).toUpperCase() + status.slice(1) : status;

export default function VideoCard({ video, onDelete }: VideoCardProps) {
  return (
    <div className="ei-card">
      <div className="px-4 py-3 border-b border-ei-border flex items-center justify-between text-xs text-ei-muted">
        <span>{formatDateTime(video.created_at)}</span>
        <span className={statusClass(video.status)}>
          {formatStatus(video.status)}
        </span>
      </div>
      <div className="px-4 py-3 border-b border-ei-border text-sm text-ei-text flex items-center gap-4">
        <div className="flex items-center gap-2">
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          <span>{formatDuration(video.duration_sec ?? undefined)}</span>
        </div>
        <div className="flex items-center gap-2">
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <rect x="3" y="4" width="18" height="14" rx="2" ry="2" />
            <line x1="7" y1="8" x2="7" y2="16" />
            <line x1="12" y1="8" x2="12" y2="16" />
            <line x1="17" y1="8" x2="17" y2="16" />
          </svg>
          <span>{video.frames_analyzed ?? "-"} frames</span>
        </div>
      </div>
      <div className="px-4 py-3 text-sm text-ei-muted">
        Entities found: {video.entities_found ?? "-"}
      </div>
      <div className="px-4 py-3 border-t border-ei-border flex items-center justify-end gap-3">
        <button
          type="button"
          className="ei-button-danger"
          onClick={() => onDelete?.(video.video_id)}
        >
          Delete
        </button>
        <Link className="ei-button-outline" to={`/videos/${video.video_id}`}>
          View Details
        </Link>
      </div>
    </div>
  );
}
