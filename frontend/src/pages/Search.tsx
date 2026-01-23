import { useState } from "react";
import Header from "../components/Header";
import { fetchJSON } from "../lib/api";

interface SearchResponse {
  exact_matches_count: number;
  ai_enhancements_count: number;
  total_unique_videos: number;
  similar_entities: { label: string; similarity: number }[];
  results: {
    video_id: string;
    filename: string;
    status: string;
    matched_entities: { label: string; presence: number; frames: number }[];
  }[];
}

export default function Search() {
  const [query, setQuery] = useState("");
  const [similarity, setSimilarity] = useState(0.7);
  const [minPresence, setMinPresence] = useState(0);
  const [minFrames, setMinFrames] = useState(0);
  const [results, setResults] = useState<SearchResponse | null>(null);

  const runSearch = async () => {
    if (!query) return;
    const params = new URLSearchParams({
      q: query,
      similarity: similarity.toString(),
      min_presence: minPresence.toString(),
      min_frames: minFrames.toString(),
    });
    const data = await fetchJSON<SearchResponse>(`/api/search?${params}`);
    setResults(data);
  };

  return (
    <div>
      <Header title="Unified Entity Search" subtitle="Exact + AI semantic expansion." />
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <input
            className="bg-ei-panel border border-ei-border rounded-lg px-3 py-2"
            placeholder="e.g. aircraft, turret"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <input
            type="number"
            step="0.05"
            min="0"
            max="1"
            className="bg-ei-panel border border-ei-border rounded-lg px-3 py-2"
            value={similarity}
            onChange={(e) => setSimilarity(Number(e.target.value))}
          />
          <input
            type="number"
            step="0.05"
            min="0"
            max="1"
            className="bg-ei-panel border border-ei-border rounded-lg px-3 py-2"
            value={minPresence}
            onChange={(e) => setMinPresence(Number(e.target.value))}
          />
          <input
            type="number"
            min="0"
            className="bg-ei-panel border border-ei-border rounded-lg px-3 py-2"
            value={minFrames}
            onChange={(e) => setMinFrames(Number(e.target.value))}
          />
        </div>
        <button className="button-primary mt-4" onClick={runSearch}>
          Search
        </button>
      </div>

      {results && (
        <div className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="card">
              <div className="text-xs text-ei-muted">Exact matches</div>
              <div className="text-2xl font-semibold mt-2">
                {results.exact_matches_count}
              </div>
            </div>
            <div className="card">
              <div className="text-xs text-ei-muted">AI expansions</div>
              <div className="text-2xl font-semibold mt-2">
                {results.ai_enhancements_count}
              </div>
            </div>
            <div className="card">
              <div className="text-xs text-ei-muted">Videos matched</div>
              <div className="text-2xl font-semibold mt-2">
                {results.total_unique_videos}
              </div>
            </div>
          </div>

          <div className="card mt-6">
            <div className="text-sm text-ei-muted mb-3">Similar entities</div>
            <div className="flex flex-wrap gap-2">
              {results.similar_entities.map((item) => (
                <span key={item.label} className="badge">
                  {item.label} · {Math.round(item.similarity * 100)}%
                </span>
              ))}
              {results.similar_entities.length === 0 && (
                <span className="text-sm text-ei-muted">None</span>
              )}
            </div>
          </div>

          <div className="card mt-6">
            <div className="grid grid-cols-4 text-xs uppercase text-ei-muted pb-3 border-b border-ei-border">
              <div>Video</div>
              <div>Status</div>
              <div>Entities</div>
              <div>Presence</div>
            </div>
            <div className="divide-y divide-ei-border">
              {results.results.map((item) => (
                <div key={item.video_id} className="grid grid-cols-4 py-3 text-sm">
                  <div>{item.filename}</div>
                  <div>{item.status}</div>
                  <div>
                    {item.matched_entities.map((ent) => (
                      <div key={ent.label}>{ent.label}</div>
                    ))}
                  </div>
                  <div>
                    {item.matched_entities.map((ent) => (
                      <div key={ent.label}>{Math.round(ent.presence * 100)}%</div>
                    ))}
                  </div>
                </div>
              ))}
              {results.results.length === 0 && (
                <div className="py-6 text-sm text-ei-muted">No matches.</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
