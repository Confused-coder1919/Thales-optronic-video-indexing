import type { FramesPage } from "../lib/types";
import { API_BASE } from "../lib/api";

interface FrameGalleryProps {
  frames: FramesPage | null;
  page: number;
  onPageChange: (page: number) => void;
}

export default function FrameGallery({ frames, page, onPageChange }: FrameGalleryProps) {
  if (!frames) {
    return null;
  }

  return (
    <div className="ei-card">
      <div className="ei-card-header">Frame Gallery</div>
      <div className="ei-card-body">
        <div className="ei-card border border-ei-border">
          <div className="px-5 py-3 border-b border-ei-border flex items-center justify-between text-sm">
            <span>Extracted Frames ({frames.total_frames} total)</span>
            <div className="flex items-center gap-3 text-xs text-ei-muted">
              <button
                className="ei-button"
                disabled={page <= 1}
                onClick={() => onPageChange(page - 1)}
                type="button"
              >
                ◀
              </button>
              <span>
                Page {page} of {frames.total_pages || 1}
              </span>
              <button
                className="ei-button"
                disabled={page >= frames.total_pages}
                onClick={() => onPageChange(page + 1)}
                type="button"
              >
                ▶
              </button>
            </div>
          </div>
          <div className="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {frames.items.map((frame) => (
              <div key={frame.frame_index} className="border border-ei-border rounded-lg overflow-hidden">
                <img
                  src={`${API_BASE}${frame.image_url}`}
                  alt={`Frame ${frame.frame_index}`}
                  className="w-full h-28 object-cover"
                />
                <div className="px-3 py-2 text-xs text-ei-muted">Frame {frame.frame_index}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
