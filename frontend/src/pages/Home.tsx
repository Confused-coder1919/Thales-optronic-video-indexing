import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import StatCard from "../components/StatCard";
import TopTitleSection from "../components/TopTitleSection";
import { getVideos } from "../lib/api";

export default function Home() {
  const [total, setTotal] = useState(0);
  const [processing, setProcessing] = useState(0);
  const [completed, setCompleted] = useState(0);

  useEffect(() => {
    Promise.all([
      getVideos(undefined, 1, 1),
      getVideos("processing", 1, 1),
      getVideos("completed", 1, 1),
    ])
      .then(([allRes, processingRes, completedRes]) => {
        setTotal(allRes.total);
        setProcessing(processingRes.total);
        setCompleted(completedRes.total);
      })
      .catch(() => {
        setTotal(0);
        setProcessing(0);
        setCompleted(0);
      });
  }, []);

  return (
    <div className="space-y-6">
      <TopTitleSection
        title="Video Indexing"
        subtitle="Advanced video processing platform with AI-powered entity detection and comprehensive analytics."
      />

      <div className="ei-card px-5 py-4 space-y-3">
        <div className="flex items-center gap-2">
          <span className="text-ei-muted">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          </span>
          <input
            className="ei-input"
            placeholder="Search for entities, objects, or scenes..."
          />
        </div>
        <div className="text-xs text-ei-muted">
          Try: <span className="text-ei-text">“aircraft”</span>,{" "}
          <span className="text-ei-text">“military personnel”</span>,{" "}
          <span className="text-ei-text">“drones”</span>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link className="ei-button-primary" to="/upload">
            Upload Video
          </Link>
          <Link className="ei-button" to="/videos">
            View Library
          </Link>
          <Link className="ei-button" to="/search">
            Advanced Search
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard label="TOTAL VIDEOS" value={total} />
        <StatCard label="PROCESSING" value={processing} />
        <StatCard label="COMPLETED" value={completed} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="ei-card px-5 py-4">
          <div className="text-sm font-semibold">AI-Powered Search</div>
          <div className="text-sm text-ei-muted mt-2">
            Discover videos by entity names or natural language using semantic
            expansion.
          </div>
        </div>
        <div className="ei-card px-5 py-4">
          <div className="text-sm font-semibold">Easy Upload</div>
          <div className="text-sm text-ei-muted mt-2">
            Drag-and-drop uploads with optional voice descriptions for richer
            context.
          </div>
        </div>
        <div className="ei-card px-5 py-4">
          <div className="text-sm font-semibold">Entity Detection</div>
          <div className="text-sm text-ei-muted mt-2">
            Automated frame-by-frame detection with consolidated timelines and
            analytics.
          </div>
        </div>
      </div>
    </div>
  );
}
