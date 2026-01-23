const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return res.json();
}

export async function uploadVideo(
  videoFile: File,
  voiceFile: File | null,
  intervalSec: number
): Promise<{ video_id: string }> {
  const form = new FormData();
  form.append("video_file", videoFile);
  if (voiceFile) {
    form.append("voice_file", voiceFile);
  }
  form.append("interval_sec", intervalSec.toString());
  const res = await fetch(`${API_BASE}/api/videos`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return res.json();
}

export { API_BASE };
