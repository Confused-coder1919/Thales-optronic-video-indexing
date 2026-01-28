import { useState } from "react";
import { useNavigate } from "react-router-dom";
import TopTitleSection from "../components/TopTitleSection";
import UploadDropzone from "../components/UploadDropzone";
import {
  checkVideoUrl,
  uploadVideo,
  uploadVideoFromUrl,
  uploadVideoFromUrlWithCookies,
} from "../lib/api";

export default function Upload() {
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [voiceFile, setVoiceFile] = useState<File | null>(null);
  const [videoUrl, setVideoUrl] = useState("");
  const [cookiesFile, setCookiesFile] = useState<File | null>(null);
  const [urlCheckMessage, setUrlCheckMessage] = useState<string | null>(null);
  const [urlChecking, setUrlChecking] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleSubmit = async () => {
    const useUrl = videoUrl.trim().length > 0;
    if (!videoFile && !useUrl) {
      setError("Please select a video file or paste a video URL.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const response = useUrl
        ? cookiesFile
          ? await uploadVideoFromUrlWithCookies(videoUrl.trim(), 5, cookiesFile)
          : await uploadVideoFromUrl(videoUrl.trim(), 5)
        : await uploadVideo(videoFile as File, voiceFile, 5);
      navigate(`/videos/${response.video_id}`);
    } catch (err) {
      if (err instanceof Error && err.message) {
        setError(err.message);
      } else {
        setError("Upload failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCheckUrl = async () => {
    const url = videoUrl.trim();
    if (!url) {
      setUrlCheckMessage("Paste a URL to test.");
      return;
    }
    setUrlChecking(true);
    setUrlCheckMessage(null);
    try {
      const result = await checkVideoUrl(url, cookiesFile);
      const duration =
        result.duration_sec !== undefined && result.duration_sec !== null
          ? ` (${Math.round(result.duration_sec)}s)`
          : "";
      setUrlCheckMessage(`URL looks good: ${result.title || "Video"}${duration}`);
    } catch (err) {
      if (err instanceof Error && err.message) {
        setUrlCheckMessage(err.message);
      } else {
        setUrlCheckMessage("URL check failed.");
      }
    } finally {
      setUrlChecking(false);
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
              <div className="space-y-2">
                <label className="text-sm font-semibold text-ei-text">Video URL (Optional)</label>
                <input
                  className="ei-input"
                  placeholder="https://www.youtube.com/watch?v=..."
                  value={videoUrl}
                  onChange={(event) => setVideoUrl(event.target.value)}
                />
                <p className="text-xs text-ei-muted">
                  Paste a public URL to download and process (YouTube, etc.). Voice file upload is
                  supported only when uploading a local video file.
                </p>
                <div className="flex items-center gap-3">
                  <button
                    className="ei-button"
                    type="button"
                    onClick={handleCheckUrl}
                    disabled={urlChecking}
                  >
                    {urlChecking ? "Checking..." : "Test URL"}
                  </button>
                  {urlCheckMessage && (
                    <span className="text-xs text-ei-muted">{urlCheckMessage}</span>
                  )}
                </div>
              </div>
              <UploadDropzone
                label="Cookies File (Optional)"
                description="Drop cookies file or click to browse"
                helper="TXT (Netscape cookies export)"
                accept=".txt"
                file={cookiesFile}
                onFileChange={setCookiesFile}
                disabled={videoUrl.trim().length === 0}
              />
              <div className="text-xs text-ei-muted uppercase tracking-wide">Or upload a file</div>
              <UploadDropzone
                label="Video File"
                description="Click to upload or drag and drop"
                helper="MP4, MKV, AVI, MOV (max 2GB)"
                accept="video/*"
                file={videoFile}
                onFileChange={setVideoFile}
                disabled={videoUrl.trim().length > 0}
              />
              <UploadDropzone
                label="Voice Description File (Optional)"
                description="Drop voice description file or click to browse"
                helper="TXT (max 10MB)"
                accept=".txt"
                file={voiceFile}
                onFileChange={setVoiceFile}
                disabled={videoUrl.trim().length > 0}
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
