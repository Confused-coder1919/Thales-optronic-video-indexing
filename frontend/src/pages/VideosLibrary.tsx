import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import TopTitleSection from "../components/TopTitleSection";
import Tabs from "../components/Tabs";
import VideoCard from "../components/VideoCard";
import { deleteVideo, getVideos } from "../lib/api";
import type { VideoSummary } from "../lib/types";

const TAB_ITEMS = [
  { id: "all", label: "All Videos" },
  { id: "processing", label: "Processing" },
  { id: "completed", label: "Completed" },
  { id: "failed", label: "Failed" },
];

export default function VideosLibrary() {
  const [activeTab, setActiveTab] = useState("all");
  const [videos, setVideos] = useState<VideoSummary[]>([]);
  const [loading, setLoading] = useState(true);

  const statusFilter = useMemo(() => (activeTab === "all" ? undefined : activeTab), [activeTab]);

  const fetchVideos = () => {
    setLoading(true);
    getVideos(statusFilter, 1, 24)
      .then((res) => setVideos(res.items))
      .catch(() => setVideos([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchVideos();
  }, [statusFilter]);

  const handleDelete = async (id: string) => {
    await deleteVideo(id);
    fetchVideos();
  };

  return (
    <div className="space-y-6">
      <TopTitleSection
        title="Video Library"
        subtitle="Manage and view all your uploaded videos"
        actions={
          <Link className="ei-button" to="/upload">
            Upload New Video
          </Link>
        }
      />

      <Tabs tabs={TAB_ITEMS} active={activeTab} onChange={setActiveTab} />

      {loading && <div className="text-sm text-ei-muted">Loading videos...</div>}
      {!loading && videos.length === 0 && (
        <div className="text-sm text-ei-muted">No videos found.</div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {videos.map((video) => (
          <VideoCard key={video.video_id} video={video} onDelete={handleDelete} />
        ))}
      </div>
    </div>
  );
}
