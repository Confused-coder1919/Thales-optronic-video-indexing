import { useState } from "react";
import { useNavigate } from "react-router-dom";
import TopTitleSection from "../components/TopTitleSection";
import UploadDropzone from "../components/UploadDropzone";
import { uploadVideo } from "../lib/api";

export default function Upload() {
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [voiceFile, setVoiceFile] = useState<File | null>(null);
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
      const response = await uploadVideo(videoFile, voiceFile, 5);
      navigate(`/videos/${response.video_id}`);
    } catch (err) {
      setError("Upload failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <TopTitleSection
        title="Upload Video"
        subtitle="Upload a video file to begin automated entity detection and analysis"
      />

      <div className="ei-card">
        <div className="ei-card-header">Video Upload</div>
        <div className="px-5 py-3 text-sm text-ei-muted border-b border-ei-border">
          Drag and drop your video file or click to browse
        </div>
        <div className="ei-card-body">
          <div className="ei-card border border-ei-border">
            <div className="ei-card-header">Upload Video</div>
            <div className="px-5 py-3 text-sm text-ei-muted border-b border-ei-border">
              Upload a video file for processing. Optionally include a voice description file.
            </div>
            <div className="ei-card-body space-y-6">
              <UploadDropzone
                label="Video File *"
                description="Click to upload or drag and drop"
                helper="MP4, MKV, AVI, MOV (max 2GB)"
                accept="video/*"
                file={videoFile}
                onFileChange={setVideoFile}
              />
              <UploadDropzone
                label="Voice Description File (Optional)"
                description="Drop voice description file or click to browse"
                helper="TXT (max 10MB)"
                accept=".txt"
                file={voiceFile}
                onFileChange={setVoiceFile}
              />
              {error && <div className="text-sm text-red-500">{error}</div>}
              <button className="ei-button-primary" onClick={handleSubmit} disabled={loading}>
                {loading ? "Uploading..." : "Upload Video"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
