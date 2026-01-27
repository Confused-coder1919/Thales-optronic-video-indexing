import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import ProgressPanel from "../components/ProgressPanel";
import SummaryStats from "../components/SummaryStats";
import ChipsRow from "../components/ChipsRow";
import TimelineView from "../components/TimelineView";
import FrameGallery from "../components/FrameGallery";
import {
  API_BASE,
  getFrames,
  getTranscript,
  getVideo,
  getVideoReport,
  getVideoStatus,
} from "../lib/api";
import { formatDateTime, formatDuration } from "../lib/format";
import type {
  FramesPage,
  Transcript,
  VideoDetail,
  VideoReport,
  VideoStatus,
} from "../lib/types";

const statusClass = (status: string) => {
  if (status === "completed") return "ei-pill completed";
  if (status === "failed") return "ei-pill failed";
  return "ei-pill processing";
};

const formatStatus = (status: string) =>
  status ? status.charAt(0).toUpperCase() + status.slice(1) : status;

export default function VideoDetails() {
  const { id } = useParams();
  const [detail, setDetail] = useState<VideoDetail | null>(null);
  const [status, setStatus] = useState<VideoStatus | null>(null);
  const [report, setReport] = useState<VideoReport | null>(null);
  const [transcript, setTranscript] = useState<Transcript | null>(null);
  const [frames, setFrames] = useState<FramesPage | null>(null);
  const [page, setPage] = useState(1);
  const [showDetections, setShowDetections] = useState(true);

  useEffect(() => {
    if (!id) return;
    getVideo(id).then(setDetail).catch(() => setDetail(null));
  }, [id]);

  useEffect(() => {
    if (!id) return;
    if (status?.status === "completed" || status?.status === "failed") {
      getVideo(id).then(setDetail).catch(() => setDetail(null));
    }
  }, [id, status?.status]);

  useEffect(() => {
    if (!id) return;
    let timer: number | undefined;
    const poll = async () => {
      try {
        const data = await getVideoStatus(id);
        setStatus(data);
        if (data.status === "processing") {
          timer = window.setTimeout(poll, 1500);
        }
      } catch {
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
    if (detail?.report_ready) {
      getVideoReport(id).then(setReport).catch(() => setReport(null));
    }
  }, [id, detail?.report_ready]);

  useEffect(() => {
    if (!id) return;
    if (!detail?.report_ready) return;
    getTranscript(id)
      .then(setTranscript)
      .catch(() =>
        setTranscript({
          language: "unknown",
          text: "",
          segments: [],
          error:
            "Transcript not generated for this video. Re-upload after starting the worker, or ensure the video has an audio track.",
        })
      );
  }, [id, detail?.report_ready]);

  useEffect(() => {
    if (!id) return;
    if (!detail?.report_ready) return;
    getFrames(id, page, 12, showDetections).then(setFrames).catch(() => setFrames(null));
  }, [id, detail?.report_ready, page, showDetections]);

  const entityRanges = useMemo(() => {
    if (!report) return [];
    return Object.entries(report.entities).map(([label, data]) => ({
      label,
      appearances: data.appearances,
      timeRanges: data.time_ranges,
    }));
  }, [report]);

  if (!detail) {
    return <div className="text-sm text-ei-muted">Loading...</div>;
  }

  const currentStatus = status?.status || detail.status;
  const progressValue = status?.progress ?? (detail.status === "completed" ? 100 : 0);

  return (
    <div className="space-y-6">
      <div className="text-sm text-ei-muted">
        <Link to="/videos" className="hover:text-ei-text">
          ← Back to Videos
        </Link>
      </div>

      <div className="ei-card">
        <div className="px-5 py-4 border-b border-ei-border flex items-start justify-between gap-4">
          <div>
            <div className="text-lg font-semibold text-ei-text">{detail.filename}</div>
            <div className="text-xs text-ei-muted">ID: {detail.video_id}</div>
          </div>
          <span className={statusClass(currentStatus)}>{formatStatus(currentStatus)}</span>
        </div>
        <div className="px-5 py-4 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-ei-muted">Uploaded</div>
              <div className="mt-1 text-ei-text">{formatDateTime(detail.created_at)}</div>
            </div>
            <div>
              <div className="text-ei-muted">Interval</div>
              <div className="mt-1 text-ei-text">{detail.interval_sec} seconds</div>
            </div>
            {detail.duration_sec !== null && detail.duration_sec !== undefined && (
              <div>
                <div className="text-ei-muted">Duration</div>
                <div className="mt-1 text-ei-text">{formatDuration(detail.duration_sec)}</div>
              </div>
            )}
            {detail.frames_analyzed !== null && detail.frames_analyzed !== undefined && (
              <div>
                <div className="text-ei-muted">Frames Analyzed</div>
                <div className="mt-1 text-ei-text">{detail.frames_analyzed}</div>
              </div>
            )}
            {detail.unique_entities !== null && detail.unique_entities !== undefined && (
              <div>
                <div className="text-ei-muted"># Unique Entities</div>
                <div className="mt-1 text-ei-text">{detail.unique_entities}</div>
              </div>
            )}
            <div>
              <div className="text-ei-muted">Voice File</div>
              <div className="mt-1 text-ei-text">
                {detail.voice_file_included ? "Included" : "Not included"}
              </div>
            </div>
          </div>
          <div className="relative border border-ei-border rounded-lg bg-ei-tab min-h-[160px] flex items-center justify-center">
            <div className="w-14 h-14 rounded-full border border-ei-border bg-white flex items-center justify-center">
              <div className="w-0 h-0 border-t-8 border-b-8 border-l-12 border-transparent border-l-ei-muted ml-1" />
            </div>
          </div>
        </div>
        <div className="px-5 pb-4 flex items-center gap-3">
          <a
            className="ei-button"
            href={`${API_BASE}/api/videos/${detail.video_id}/download`}
          >
            Download Video
          </a>
          {detail.report_ready && (
            <a
              className="ei-button-outline"
              href={`${API_BASE}/api/videos/${detail.video_id}/report/download`}
            >
              Download Report
            </a>
          )}
          {detail.report_ready && (
            <a
              className="ei-button-outline"
              href={`${API_BASE}/api/videos/${detail.video_id}/report/csv/download`}
            >
              Download CSV
            </a>
          )}
        </div>
      </div>

      {currentStatus === "processing" && (
        <ProgressPanel
          progress={progressValue}
          currentStage={status?.current_stage}
          statusText={status?.status_text}
        />
      )}

      {currentStatus === "completed" && report && (
        <div className="space-y-6">
          <div className="ei-card">
            <div className="ei-card-header">Analysis Report</div>
            <div className="ei-card-body space-y-6">
              <SummaryStats
                durationSec={report.duration_sec}
                framesAnalyzed={report.frames_analyzed}
                intervalSec={report.interval_sec}
                uniqueEntities={report.unique_entities}
              />

              <ChipsRow
                title="Detected Entities"
                items={Object.entries(report.entities).map(([label, data]) => ({
                  label,
                  count: data.count,
                }))}
              />

              <TimelineView report={report} />

              <div className="ei-card">
                <div className="ei-card-header">Entity Time Ranges</div>
                <div className="ei-card-body space-y-4">
                  {entityRanges.map((entity) => (
                    <div key={entity.label} className="border border-ei-border rounded-lg">
                      <div className="px-4 py-3 border-b border-ei-border flex items-center justify-between">
                        <div className="text-sm font-semibold text-ei-text">{entity.label}</div>
                        <div className="text-xs text-ei-muted">
                          Appearances: <span className="text-ei-text">{entity.appearances}</span>
                        </div>
                      </div>
                      <div className="px-4 py-3">
                        {entity.timeRanges.length === 0 ? (
                          <div className="text-xs text-ei-muted">No time ranges detected.</div>
                        ) : (
                          <ol className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-ei-text">
                            {entity.timeRanges.map((range, idx) => (
                              <li
                                key={`${entity.label}-${idx}`}
                                className="ei-chip px-2 py-1"
                              >
                                {idx + 1}. {range.start_label} ({range.start_sec.toFixed(1)}s) -{" "}
                                {range.end_label} ({range.end_sec.toFixed(1)}s) (
                                {Math.max(
                                  1,
                                  Math.round(range.end_sec - range.start_sec + report.interval_sec)
                                )}
                                s)
                              </li>
                            ))}
                          </ol>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <FrameGallery frames={frames} page={page} onPageChange={setPage} />
              <div className="flex items-center gap-2 text-xs text-ei-muted">
                <input
                  id="show-detections"
                  type="checkbox"
                  checked={showDetections}
                  onChange={(event) => setShowDetections(event.target.checked)}
                />
                <label htmlFor="show-detections">Show detection overlays</label>
              </div>

              <div className="ei-card">
                <div className="ei-card-header">Transcript</div>
                <div className="ei-card-body">
                  {transcript?.error && (
                    <div className="text-xs text-red-500 mb-2">
                      Transcript error: {transcript.error}
                    </div>
                  )}
                  {transcript?.text ? (
                    <div className="text-sm text-ei-text whitespace-pre-wrap leading-6">
                      {transcript.text}
                    </div>
                  ) : (
                    <div className="text-sm text-ei-muted">
                      Transcript not available yet.
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
