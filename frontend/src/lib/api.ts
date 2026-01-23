import type {
  FramesPage,
  SearchResponse,
  VideoDetail,
  VideoListResponse,
  VideoReport,
  VideoStatus,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8010";

export async function fetchJSON<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return res.json();
}

export async function uploadVideo(
  videoFile: File,
  voiceFile: File | null,
  intervalSec: number
): Promise<{ video_id: string; status: string }> {
  const form = new FormData();
  form.append("video_file", videoFile);
  if (voiceFile) {
    form.append("voice_file", voiceFile);
  }
  form.append("interval_sec", intervalSec.toString());
  return fetchJSON(`/api/videos`, { method: "POST", body: form });
}

export function getVideos(status?: string, page = 1, pageSize = 20) {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  if (status && status !== "all") {
    params.set("status", status);
  }
  return fetchJSON<VideoListResponse>(`/api/videos?${params.toString()}`);
}

export function getVideo(videoId: string) {
  return fetchJSON<VideoDetail>(`/api/videos/${videoId}`);
}

export function getVideoStatus(videoId: string) {
  return fetchJSON<VideoStatus>(`/api/videos/${videoId}/status`);
}

export function getVideoReport(videoId: string) {
  return fetchJSON<VideoReport>(`/api/videos/${videoId}/report`);
}

export function getFrames(videoId: string, page = 1, pageSize = 12) {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  return fetchJSON<FramesPage>(`/api/videos/${videoId}/frames?${params.toString()}`);
}

export function deleteVideo(videoId: string) {
  return fetchJSON(`/api/videos/${videoId}`, { method: "DELETE" });
}

export function searchEntities(
  query: string,
  similarity: number,
  minPresence: number,
  minFrames: number
) {
  const params = new URLSearchParams({
    q: query,
    similarity: similarity.toString(),
    min_presence: minPresence.toString(),
    min_frames: minFrames.toString(),
  });
  return fetchJSON<SearchResponse>(`/api/search?${params.toString()}`);
}

export { API_BASE };
