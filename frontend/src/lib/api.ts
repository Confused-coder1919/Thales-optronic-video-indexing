import type {
  FramesPage,
  SearchResponse,
  ShareLinkResponse,
  SharedReportResponse,
  VideoDetail,
  VideoListResponse,
  VideoReport,
  VideoStatus,
  Transcript,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

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

export async function uploadVideoFromUrl(
  url: string,
  intervalSec: number
): Promise<{ video_id: string; status: string }> {
  return fetchJSON(`/api/videos/from-url`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, interval_sec: intervalSec }),
  });
}

export async function uploadVideoFromUrlWithCookies(
  url: string,
  intervalSec: number,
  cookiesFile: File
): Promise<{ video_id: string; status: string }> {
  const form = new FormData();
  form.append("url", url);
  form.append("interval_sec", intervalSec.toString());
  form.append("cookies_file", cookiesFile);
  return fetchJSON(`/api/videos/from-url-upload`, { method: "POST", body: form });
}

export async function checkVideoUrl(
  url: string,
  cookiesFile?: File | null
): Promise<{ ok: boolean; title?: string; duration_sec?: number }> {
  const form = new FormData();
  form.append("url", url);
  if (cookiesFile) {
    form.append("cookies_file", cookiesFile);
  }
  return fetchJSON(`/api/videos/from-url/check`, { method: "POST", body: form });
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

export function createShareLink(videoId: string) {
  return fetchJSON<ShareLinkResponse>(`/api/videos/${videoId}/share`, {
    method: "POST",
  });
}

export function getSharedReport(token: string) {
  return fetchJSON<SharedReportResponse>(`/api/share/${token}`);
}

export function getTranscript(videoId: string) {
  return fetchJSON<Transcript>(`/api/videos/${videoId}/transcript`);
}

export function getFrames(
  videoId: string,
  page = 1,
  pageSize = 12,
  annotated = false,
  entity?: string
) {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  if (annotated) {
    params.set("annotated", "true");
  }
  if (entity && entity !== "all") {
    params.set("entity", entity);
  }
  return fetchJSON<FramesPage>(`/api/videos/${videoId}/frames?${params.toString()}`);
}

export function getNearestFrame(
  videoId: string,
  timestampSec: number,
  pageSize = 12,
  entity?: string
) {
  const params = new URLSearchParams({
    timestamp_sec: timestampSec.toString(),
    page_size: pageSize.toString(),
  });
  if (entity && entity !== "all") {
    params.set("entity", entity);
  }
  return fetchJSON<{
    page: number;
    page_size: number;
    total_frames: number;
    total_pages: number;
    frame_index: number;
    timestamp_sec: number;
    image_url: string;
  }>(`/api/videos/${videoId}/frames/nearest?${params.toString()}`);
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
