import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";
import { uploadVideo } from "../lib/api";

export default function Upload() {
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [voiceFile, setVoiceFile] = useState<File | null>(null);
  const [intervalSec, setIntervalSec] = useState<number>(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleSubmit = async () => {
    if (!videoFile) {
      setError("Please select a video file.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = await uploadVideo(videoFile, voiceFile, intervalSec);
      navigate(`/videos/${res.video_id}`);
    } catch (err) {
      setError("Upload failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Header title="Upload" subtitle="Create a new entity indexing job." />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="text-sm text-ei-muted">Video</div>
          <input
            type="file"
            accept="video/*"
            className="mt-3 text-sm"
            onChange={(e) => setVideoFile(e.target.files?.[0] || null)}
          />
          <div className="text-sm text-ei-muted mt-6">Optional Voice Notes (.txt)</div>
          <input
            type="file"
            accept=".txt"
            className="mt-3 text-sm"
            onChange={(e) => setVoiceFile(e.target.files?.[0] || null)}
          />
          <div className="text-sm text-ei-muted mt-6">Frame Interval (sec)</div>
          <input
            type="number"
            min={1}
            value={intervalSec}
            onChange={(e) => setIntervalSec(Number(e.target.value))}
            className="mt-3 bg-ei-panel border border-ei-border rounded-lg px-3 py-2 w-32"
          />
          {error && <div className="text-red-400 text-sm mt-4">{error}</div>}
          <button
            className="button-primary mt-6"
            disabled={loading}
            onClick={handleSubmit}
          >
            {loading ? "Uploading..." : "Start Processing"}
          </button>
        </div>
        <div className="card">
          <h3 className="text-lg font-semibold">What happens next</h3>
          <ul className="mt-4 space-y-3 text-sm text-ei-muted">
            <li>1. Frames extracted at your chosen interval.</li>
            <li>2. Object detection runs per frame.</li>
            <li>3. Entities aggregated into timeline report.</li>
            <li>4. Results indexed for unified search.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
