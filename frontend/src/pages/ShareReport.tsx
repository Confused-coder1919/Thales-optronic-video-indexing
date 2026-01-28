import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import ChipsRow from "../components/ChipsRow";
import FrameGallery from "../components/FrameGallery";
import SummaryStats from "../components/SummaryStats";
import TimelineView from "../components/TimelineView";
import { getFrames, getNearestFrame, getSharedReport } from "../lib/api";
import { formatDateTime } from "../lib/format";
import type { FramesPage, SharedReportResponse } from "../lib/types";

export default function ShareReport() {
  const { token } = useParams();
  const [data, setData] = useState<SharedReportResponse | null>(null);
  const [frames, setFrames] = useState<FramesPage | null>(null);
  const [page, setPage] = useState(1);
  const [showDetections, setShowDetections] = useState(true);
  const [selectedEntity, setSelectedEntity] = useState("all");
  const [highlightFrameIndex, setHighlightFrameIndex] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    getSharedReport(token)
      .then(setData)
      .catch((err) => {
        if (err instanceof Error && err.message) {
          setError(err.message);
        } else {
          setError("Share link not found.");
        }
      });
  }, [token]);

  useEffect(() => {
    if (!data?.video_id) return;
    getFrames(data.video_id, page, 12, showDetections, selectedEntity)
      .then(setFrames)
      .catch(() => setFrames(null));
  }, [data?.video_id, page, showDetections, selectedEntity]);

  useEffect(() => {
    setHighlightFrameIndex(null);
  }, [page, selectedEntity, showDetections]);

  const report = data?.report;
  const entityRanges = useMemo(() => {
    if (!report) return [];
    return Object.entries(report.entities).map(([label, entity]) => ({
      label,
      appearances: entity.appearances,
      timeRanges: entity.time_ranges,
      confidence: entity.confidence_score,
      sources: entity.sources,
    }));
  }, [report]);

  const handleTimelineClick = async (label: string, timestampSec: number) => {
    if (!data?.video_id) return;
    setSelectedEntity(label);
    try {
      const nearest = await getNearestFrame(data.video_id, timestampSec, 12, label);
      setPage(nearest.page);
      setHighlightFrameIndex(nearest.frame_index);
    } catch {
      setPage(1);
    }
  };

  if (!token) {
    return <div className="text-sm text-ei-muted">Invalid share link.</div>;
  }

  if (error) {
    return <div className="text-sm text-red-500">{error}</div>;
  }

  if (!data || !report) {
    return <div className="text-sm text-ei-muted">Loading shared report...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="ei-card">
        <div className="px-5 py-4 border-b border-ei-border">
          <div className="text-lg font-semibold text-ei-text">{data.filename}</div>
          <div className="text-xs text-ei-muted">Shared report</div>
        </div>
        <div className="px-5 py-4 grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-ei-muted">Uploaded</div>
            <div className="mt-1 text-ei-text">{formatDateTime(data.created_at)}</div>
          </div>
          <div>
            <div className="text-ei-muted">Interval</div>
            <div className="mt-1 text-ei-text">{report.interval_sec} seconds</div>
          </div>
        </div>
      </div>

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
              confidence: data.confidence_score,
              sources: data.sources,
            }))}
          />

          <TimelineView report={report} onRangeClick={handleTimelineClick} />

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
                  {(entity.confidence !== undefined ||
                    (entity.sources && entity.sources.length > 0)) && (
                    <div className="px-4 py-2 border-b border-ei-border text-xs text-ei-muted flex flex-wrap gap-3">
                      {entity.confidence !== undefined && (
                        <span>
                          Confidence:{" "}
                          <span className="text-ei-text">
                            {Math.round(entity.confidence * 100)}%
                          </span>
                        </span>
                      )}
                      {entity.sources && entity.sources.length > 0 && (
                        <span>
                          Sources: <span className="text-ei-text">{entity.sources.join(", ")}</span>
                        </span>
                      )}
                    </div>
                  )}
                  <div className="px-4 py-3">
                    {entity.timeRanges.length === 0 ? (
                      <div className="text-xs text-ei-muted">No time ranges detected.</div>
                    ) : (
                      <ol className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-ei-text">
                        {entity.timeRanges.map((range, idx) => (
                          <li key={`${entity.label}-${idx}`} className="ei-chip px-2 py-1">
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

          <div className="flex flex-wrap items-center gap-3 text-xs text-ei-muted">
            <label htmlFor="entity-filter" className="text-xs text-ei-muted">
              Frames for entity:
            </label>
            <select
              id="entity-filter"
              className="ei-input text-xs"
              value={selectedEntity}
              onChange={(event) => {
                setPage(1);
                setSelectedEntity(event.target.value);
              }}
            >
              <option value="all">All entities</option>
              {Object.keys(report.entities).map((label) => (
                <option key={label} value={label}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          {frames ? (
            <FrameGallery
              frames={frames}
              page={page}
              onPageChange={setPage}
              highlightFrameIndex={highlightFrameIndex}
            />
          ) : (
            <div className="ei-card">
              <div className="ei-card-header">Frame Gallery</div>
              <div className="ei-card-body text-sm text-ei-muted">
                Frames are not available yet.
              </div>
            </div>
          )}
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
              {report.transcript?.error && (
                <div className="text-xs text-red-500 mb-2">
                  Transcript error: {report.transcript.error}
                </div>
              )}
              {report.transcript?.audio_analysis && (
                <div className="text-xs text-ei-muted mb-2">
                  {report.transcript.audio_analysis.vad_available === false ? (
                    <span>Audio analysis unavailable (speech detector not installed).</span>
                  ) : (
                    <span>
                      Audio analysis: Speech{" "}
                      {report.transcript.audio_analysis.speech_ratio !== undefined &&
                      report.transcript.audio_analysis.speech_ratio !== null
                        ? `${Math.round(report.transcript.audio_analysis.speech_ratio * 100)}%`
                        : "N/A"}
                      {report.transcript.audio_analysis.speech_seconds !== undefined &&
                      report.transcript.audio_analysis.speech_seconds !== null
                        ? ` (${report.transcript.audio_analysis.speech_seconds}s)`
                        : ""}
                      . Music likely: {report.transcript.audio_analysis.music_detected ? "Yes" : "No"}
                    </span>
                  )}
                </div>
              )}
              {report.transcript?.text ? (
                <div className="text-sm text-ei-text whitespace-pre-wrap leading-6">
                  {report.transcript.text}
                </div>
              ) : (
                <div className="text-sm text-ei-muted">Transcript not available.</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
