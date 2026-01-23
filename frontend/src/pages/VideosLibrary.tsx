import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Header from "../components/Header";
import { fetchJSON } from "../lib/api";

interface VideoSummary {
  video_id: string;
  filename: string;
  status: string;
  duration_sec?: number;
  frames_analyzed?: number;
  unique_entities?: number;
}

export default function VideosLibrary() {
  const [videos, setVideos] = useState<VideoSummary[]>([]);

  useEffect(() => {
    fetchJSON<VideoSummary[]>("/api/videos")
      .then(setVideos)
      .catch(() => setVideos([]));
  }, []);

  return (
    <div>
      <Header title="Videos Library" subtitle="Browse indexed videos and reports." />
      <div className="card">
        <div className="grid grid-cols-6 text-xs uppercase text-ei-muted pb-3 border-b border-ei-border">
          <div className="col-span-2">Video</div>
          <div>Status</div>
          <div>Duration</div>
          <div>Frames</div>
          <div>Entities</div>
        </div>
        <div className="divide-y divide-ei-border">
          {videos.map((video) => (
            <div key={video.video_id} className="grid grid-cols-6 py-3 text-sm">
              <div className="col-span-2">
                <Link to={`/videos/${video.video_id}`} className="text-ei-accent">
                  {video.filename}
                </Link>
              </div>
              <div>{video.status}</div>
              <div>{video.duration_sec ? `${video.duration_sec}s` : "-"}</div>
              <div>{video.frames_analyzed ?? "-"}</div>
              <div>{video.unique_entities ?? "-"}</div>
            </div>
          ))}
          {videos.length === 0 && (
            <div className="py-6 text-sm text-ei-muted">No videos yet.</div>
          )}
        </div>
      </div>
    </div>
  );
}
