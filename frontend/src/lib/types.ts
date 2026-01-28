export interface VideoSummary {
  video_id: string;
  filename: string;
  created_at?: string | null;
  status: string;
  duration_sec?: number | null;
  frames_analyzed?: number | null;
  entities_found?: number | null;
  interval_sec: number;
}

export interface VideoListResponse {
  items: VideoSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface VideoEntity {
  label: string;
  count: number;
  presence: number;
}

export interface VideoDetail {
  video_id: string;
  filename: string;
  created_at?: string | null;
  status: string;
  duration_sec?: number | null;
  interval_sec: number;
  frames_analyzed?: number | null;
  voice_file_included: boolean;
  unique_entities?: number | null;
  entities: VideoEntity[];
  report_ready: boolean;
}

export interface VideoStatus {
  status: string;
  progress: number;
  current_stage?: string | null;
  status_text?: string | null;
}

export interface ReportTimeRange {
  start_sec: number;
  end_sec: number;
  start_label: string;
  end_label: string;
}

export interface ReportEntity {
  count: number;
  presence: number;
  appearances: number;
  time_ranges: ReportTimeRange[];
  confidence_score?: number;
  sources?: string[];
  raw_count?: number;
}

export interface VideoReport {
  video_id: string;
  filename: string;
  duration_sec: number;
  interval_sec: number;
  frames_analyzed: number;
  unique_entities: number;
  entities: Record<string, ReportEntity>;
  transcript?: Transcript;
}

export interface ShareLinkResponse {
  token: string;
}

export interface SharedReportResponse {
  token: string;
  video_id: string;
  filename: string;
  created_at?: string | null;
  report: VideoReport;
}

export interface TranscriptSegment {
  segment_id: number;
  start: number;
  end: number;
  text: string;
}

export interface Transcript {
  language: string;
  text: string;
  segments: TranscriptSegment[];
  error?: string;
  audio_analysis?: {
    speech_ratio?: number | null;
    speech_seconds?: number | null;
    music_detected?: boolean | null;
    vad_available?: boolean | null;
  };
}

export interface FrameItem {
  frame_index: number;
  timestamp_sec: number;
  image_url: string;
}

export interface FramesPage {
  page: number;
  page_size: number;
  total_frames: number;
  total_pages: number;
  items: FrameItem[];
}

export interface SearchMatch {
  label: string;
  presence: number;
  frames: number;
}

export interface SearchResult {
  video_id: string;
  filename: string;
  status: string;
  duration_sec?: number | null;
  created_at?: string | null;
  matched_entities: SearchMatch[];
}

export interface SimilarEntity {
  label: string;
  similarity: number;
}

export interface SearchResponse {
  exact_matches_count: number;
  ai_enhancements_count: number;
  total_unique_videos: number;
  similar_entities: SimilarEntity[];
  results: SearchResult[];
}
