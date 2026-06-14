import { useEffect, useRef, useState } from "react";

import { getLLMStatus, setLLMMode } from "../lib/api";
import type { LLMMode, LLMStatus } from "../lib/types";

const modeOptions: Array<{ value: LLMMode; label: string; hint: string }> = [
  {
    value: "env",
    label: "Environment default",
    hint: "Use server env variables as configured.",
  },
  { value: "auto", label: "Auto", hint: "Cloud first, then local fallback." },
  { value: "mistral", label: "Cloud (Mistral)", hint: "Force cloud inference." },
  { value: "ollama", label: "Local (Ollama)", hint: "Force local runtime." },
  { value: "off", label: "Off", hint: "Disable LLM extraction." },
];

function statusClass(active: boolean): string {
  return active ? "bg-green-500" : "bg-slate-300";
}

function prettyMode(mode: LLMMode | LLMStatus["effective_mode"] | undefined): string {
  if (!mode) {
    return "-";
  }
  switch (mode) {
    case "env":
      return "Environment";
    case "auto":
      return "Auto";
    case "mistral":
      return "Cloud (Mistral)";
    case "ollama":
      return "Local (Ollama)";
    case "off":
      return "Off";
    default:
      return mode;
  }
}

export default function TopBar() {
  const [status, setStatus] = useState<LLMStatus | null>(null);
  const [mode, setMode] = useState<LLMMode>("env");
  const [saving, setSaving] = useState(false);
  const [warning, setWarning] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const panelRef = useRef<HTMLDivElement | null>(null);

  const loadStatus = async () => {
    const payload = await getLLMStatus();
    setStatus(payload);
    setMode(payload.mode);
    setWarning(null);
  };

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      try {
        const payload = await getLLMStatus();
        if (!mounted) {
          return;
        }
        setStatus(payload);
        setMode(payload.mode);
        setWarning(null);
      } catch {
        if (!mounted) {
          return;
        }
        setWarning("LLM status unavailable");
      }
    };

    load();
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    const onDocumentClick = (event: MouseEvent) => {
      if (!panelRef.current) {
        return;
      }
      if (!panelRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    if (open) {
      document.addEventListener("mousedown", onDocumentClick);
    }
    return () => {
      document.removeEventListener("mousedown", onDocumentClick);
    };
  }, [open]);

  const onModeChange = async (nextMode: LLMMode) => {
    setMode(nextMode);
    setSaving(true);
    try {
      const payload = await setLLMMode(nextMode);
      setStatus(payload);
      setWarning(null);
    } catch (error) {
      const message =
        error instanceof Error && error.message
          ? error.message
          : "Unable to update LLM mode";
      setWarning(message);
      try {
        const payload = await getLLMStatus();
        setStatus(payload);
        setMode(payload.mode);
      } catch {
        // keep local state and warning; do not block the UI
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <header className="h-14 bg-ei-surface border-b border-ei-border flex items-center justify-between px-6">
      <div className="flex items-center gap-3">
        <img src="/thales-logo.svg" alt="Thales" className="h-6 w-auto" />
        <div className="text-ei-accent font-semibold">Entity Indexing</div>
      </div>
      <div className="flex items-center gap-3" ref={panelRef}>
        <button
          type="button"
          className="ei-button h-9 px-3"
          onClick={() => setOpen((current) => !current)}
          aria-expanded={open}
          aria-controls="llm-control-panel"
        >
          <span className="text-xs font-semibold">LLM</span>
          <span
            className={`inline-block h-2 w-2 rounded-full ${statusClass(
              Boolean(status?.mistral_available || status?.ollama_reachable)
            )}`}
          />
          <span className="text-xs text-ei-muted">{prettyMode(mode)}</span>
        </button>
        <div className="hidden lg:flex items-center gap-2 text-xs text-ei-muted">
          <span>Effective:</span>
          <span className="ei-chip-accent">{prettyMode(status?.effective_mode)}</span>
        </div>
        {open ? (
          <div
            id="llm-control-panel"
            className="absolute right-6 top-12 z-30 w-[min(92vw,520px)] rounded-xl border border-ei-border bg-ei-surface p-4 shadow-2xl"
          >
            <div className="flex items-center justify-between mb-3">
              <div>
                <p className="text-sm font-semibold text-ei-text">LLM Mode Control</p>
                <p className="text-xs text-ei-muted">Choose runtime policy for indexing.</p>
              </div>
              <button
                type="button"
                className="text-xs text-ei-muted hover:text-ei-text"
                onClick={() => setOpen(false)}
              >
                Close
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-3">
              {modeOptions.map((option) => {
                const active = option.value === mode;
                return (
                  <button
                    key={option.value}
                    type="button"
                    disabled={saving}
                    onClick={() => onModeChange(option.value)}
                    className={`text-left rounded-lg border px-3 py-2 transition-colors ${
                      active
                        ? "border-ei-accent bg-ei-accent-soft"
                        : "border-ei-border bg-white hover:bg-ei-tab"
                    } ${saving ? "opacity-70 cursor-not-allowed" : ""}`}
                  >
                    <p className="text-xs font-semibold text-ei-text">{option.label}</p>
                    <p className="text-[11px] text-ei-muted mt-0.5">{option.hint}</p>
                  </button>
                );
              })}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mb-3">
              <div className="rounded-lg border border-ei-border bg-white px-3 py-2">
                <p className="text-[11px] uppercase tracking-wide text-ei-muted">Cloud</p>
                <p className="text-xs font-semibold text-ei-text mt-1">
                  {status?.mistral_available ? "Available" : "Unavailable"}
                </p>
              </div>
              <div className="rounded-lg border border-ei-border bg-white px-3 py-2">
                <p className="text-[11px] uppercase tracking-wide text-ei-muted">Offline</p>
                <p className="text-xs font-semibold text-ei-text mt-1">
                  {status?.ollama_reachable ? "Reachable" : "Not running"}
                </p>
              </div>
              <div className="rounded-lg border border-ei-border bg-white px-3 py-2">
                <p className="text-[11px] uppercase tracking-wide text-ei-muted">Effective</p>
                <p className="text-xs font-semibold text-ei-text mt-1">
                  {prettyMode(status?.effective_mode)}
                </p>
              </div>
            </div>

            {(status?.note || warning) && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 mb-3">
                <p className="text-xs text-amber-800">
                  {warning ?? status?.note}
                  {mode === "ollama" && status && !status.ollama_reachable
                    ? " Start Ollama (docker-compose.ollama.yml)."
                    : ""}
                </p>
              </div>
            )}

            <div className="flex items-center justify-between">
              <p className="text-[11px] text-ei-muted">
                Base URL: {status?.ollama_base_url ?? "-"} | Model: {status?.ollama_model ?? "-"}
              </p>
              <button
                type="button"
                className="ei-button text-xs px-2.5 py-1.5 h-auto"
                disabled={saving}
                onClick={async () => {
                  try {
                    setSaving(true);
                    await loadStatus();
                  } catch {
                    setWarning("LLM status unavailable");
                  } finally {
                    setSaving(false);
                  }
                }}
              >
                Refresh
              </button>
            </div>
          </div>
        ) : null}
        <div className="hidden md:block max-w-[260px] text-[11px] text-ei-muted">
          {saving ? "Updating mode..." : ""}
        </div>
      </div>
    </header>
  );
}
