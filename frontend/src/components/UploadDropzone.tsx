import { useId } from "react";

interface UploadDropzoneProps {
  label: string;
  description: string;
  helper: string;
  accept: string;
  file: File | null;
  onFileChange: (file: File | null) => void;
  disabled?: boolean;
}

export default function UploadDropzone({
  label,
  description,
  helper,
  accept,
  file,
  onFileChange,
  disabled = false,
}: UploadDropzoneProps) {
  const id = useId();

  return (
    <div className="space-y-2">
      <div className="text-sm font-semibold text-ei-text">{label}</div>
      <label
        htmlFor={id}
        className={`flex flex-col items-center justify-center gap-2 border-2 border-dashed border-ei-border rounded-lg px-4 py-8 text-center text-sm text-ei-muted bg-white ${
          disabled ? "opacity-60 cursor-not-allowed" : "cursor-pointer"
        }`}
      >
        <div className="w-10 h-10 rounded-full border border-ei-border flex items-center justify-center text-ei-muted">
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
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        </div>
        <div className="text-ei-text font-medium">{description}</div>
        <div className="text-xs text-ei-muted">{helper}</div>
        {file && <div className="text-xs text-ei-text mt-2">{file.name}</div>}
      </label>
      <input
        id={id}
        type="file"
        accept={accept}
        className="hidden"
        disabled={disabled}
        onChange={(event) => {
          if (disabled) return;
          const next = event.target.files?.[0] || null;
          onFileChange(next);
        }}
      />
    </div>
  );
}
