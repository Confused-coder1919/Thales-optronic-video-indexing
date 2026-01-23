import { useEffect, useState } from "react";
import Header from "../components/Header";
import StatCard from "../components/StatCard";
import { fetchJSON } from "../lib/api";

interface VideoSummary {
  video_id: string;
  filename: string;
  status: string;
}

export default function Home() {
  const [videos, setVideos] = useState<VideoSummary[]>([]);

  useEffect(() => {
    fetchJSON<VideoSummary[]>("/api/videos")
      .then(setVideos)
      .catch(() => setVideos([]));
  }, []);

  const completed = videos.filter((v) => v.status === "completed").length;
  const processing = videos.filter((v) => v.status === "processing").length;

  return (
    <div>
      <Header
        title="Entity Indexing"
        subtitle="Unified intelligence layer across your video archive."
      />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard label="Total Videos" value={videos.length} />
        <StatCard label="Processing" value={processing} />
        <StatCard label="Completed" value={completed} />
      </div>
      <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="text-sm text-ei-muted">Quick start</div>
          <h2 className="text-lg font-semibold mt-2">Upload a new video</h2>
          <p className="text-sm text-ei-muted mt-2">
            Run entity extraction with configurable frame intervals and generate
            structured reports.
          </p>
        </div>
        <div className="card">
          <div className="text-sm text-ei-muted">Unified Search</div>
          <h2 className="text-lg font-semibold mt-2">Search across entities</h2>
          <p className="text-sm text-ei-muted mt-2">
            Combine exact matching and AI semantic expansion to find related
            entities across your library.
          </p>
        </div>
      </div>
    </div>
  );
}
