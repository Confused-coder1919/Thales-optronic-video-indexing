import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import Header from "../components/Header";
import StatCard from "../components/StatCard";
import TimelineBar from "../components/TimelineBar";
import { fetchJSON, API_BASE } from "../lib/api";

interface VideoDetail {
  video_id: string;
  filename: string;
  status: string;
  duration_sec?: number;
  interval_sec: number;
  frames_analyzed?: number;
  unique_entities?: number;
  report_available: boolean;
  report?: Report;
}

interface Report {
  duration_sec: number;
  interval_sec: number;
  frames_analyzed: number;
  unique_entities: number;
  entities: Record<
    string,
    { count: number; presence: number; time_ranges: { start_sec: number; end_sec: number }[] }
  >;
}

interface Status {
  status: string;
  progress: number;
  current_stage?: string;
}

interface FramesResponse {
  page: number;
  page_size: number;
  total: number;
  frames: { url: string; timestamp_sec: number; detections: any[]; filename: string }[];
}

export default function VideoDetails() {
  const { id } = useParams();
  const [detail, setDetail] = useState<VideoDetail | null>(null);
  const [status, setStatus] = useState<Status | null>(null);
  const [frames, setFrames] = useState<FramesResponse | null>(null);
  const [page, setPage] = useState(1);

  useEffect(() => {
    if (!id) return;
    fetchJSON<VideoDetail>(`/api/videos/${id}`).then(setDetail);
  }, [id]);

  useEffect(() => {
    if (!id) return;
    let timer: number | undefined;
    const poll = async () => {
      const data = await fetchJSON<Status>(`/api/videos/${id}/status`);
      setStatus(data);
      if (data.status !== "completed" && data.status !== "failed") {
        timer = window.setTimeout(poll, 1500);
      }
    };
    poll();
    return () => {
      if (timer) window.clearTimeout(timer);
    };
  }, [id]);

  useEffect(() => {
    if (!id) return;
    if (detail?.status !== "completed") return;
    fetchJSON<FramesResponse>(`/api/videos/${id}/frames?page=${page}&page_size=12`).then(
      setFrames
    );
  }, [id, detail?.status, page]);

  if (!detail) {
    return <div className="text-ei-muted">Loading...</div>;
  }

  const report = detail.report;
  const entities = report ? Object.entries(report.entities) : [];

  return (
    <div>
      <Header
        title={detail.filename}
        subtitle={`Video ID: ${detail.video_id}`}
        actions={
          <>
            <a
              className="button-secondary"
              href={`${API_BASE}/api/videos/${detail.video_id}/download`}
            >
              Download Video
            </a>
            {detail.report_available && (
              <a
                className="button-secondary"
                href={`${API_BASE}/api/videos/${detail.video_id}/report/download?format=json`}
              >
                Download Report
              </a>
            )}
          </>
        }
      />
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard label="Status" value={status?.status || detail.status} />
        <StatCard label="Progress" value={`${Math.round((status?.progress || 0) * 100)}%`} />
        <StatCard label="Frames" value={detail.frames_analyzed ?? "-"} />
        <StatCard label="Entities" value={detail.unique_entities ?? "-"} />
      </div>

      <div className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card lg:col-span-2">
          <h3 className="text-lg font-semibold">Timeline Summary</h3>
          <div className="mt-4 space-y-4">
            {entities.map(([label, data]) => (
              <div key={label}>
                <div className="flex justify-between text-sm mb-1">
                  <span>{label}</span>
                  <span className="text-ei-muted">{Math.round(data.presence * 100)}%</span>
                </div>
                <TimelineBar ranges={data.time_ranges} duration={report?.duration_sec || 1} />
              </div>
            ))}
            {entities.length === 0 && (
              <div className="text-sm text-ei-muted">No entities detected yet.</div>
            )}
          </div>
        </div>
        <div className="card">
          <h3 className="text-lg font-semibold">Processing Stage</h3>
          <div className="text-sm text-ei-muted mt-3">
            {status?.current_stage || "-"}
          </div>
          <div className="mt-4 h-2 bg-ei-border rounded-full">
            <div
              className="h-2 bg-ei-accent rounded-full"
              style={{ width: `${Math.round((status?.progress || 0) * 100)}%` }}
            />
          </div>
        </div>
      </div>

      <div className="mt-8">
        <Header title="Frame Gallery" subtitle="Sampled frames with detections." />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {frames?.frames.map((frame) => (
            <div key={frame.filename} className="card">
              <img
                src={`${API_BASE}${frame.url}`}
                alt={frame.filename}
                className="rounded-lg mb-3"
              />
              <div className="text-xs text-ei-muted">
                Timestamp: {frame.timestamp_sec}s
              </div>
              <div className="flex flex-wrap gap-2 mt-2">
                {frame.detections.map((det, idx) => (
                  <span key={idx} className="badge">
                    {det.label}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
        {frames && (
          <div className="flex gap-3 mt-6">
            <button
              className="button-secondary"
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
            >
              Previous
            </button>
            <button
              className="button-secondary"
              disabled={frames.page * frames.page_size >= frames.total}
              onClick={() => setPage(page + 1)}
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
