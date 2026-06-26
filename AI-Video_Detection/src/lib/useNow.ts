import { useEffect, useState } from "react";

// Keeps render-pure by updating time from an effect (eslint react-hooks/purity).
export function useNow(opts?: { intervalMs?: number }): number {
  const intervalMs = opts?.intervalMs ?? 30_000;
  const [now, setNow] = useState(0);

  useEffect(() => {
    const tick = () => setNow(Date.now());
    // Keep setState inside callbacks to satisfy react-hooks/set-state-in-effect.
    const raf = window.requestAnimationFrame(tick);
    const id = window.setInterval(tick, intervalMs);
    return () => {
      window.cancelAnimationFrame(raf);
      window.clearInterval(id);
    };
  }, [intervalMs]);

  return now;
}
