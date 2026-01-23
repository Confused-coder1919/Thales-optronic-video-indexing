import { useState } from "react";
import TopTitleSection from "../components/TopTitleSection";
import { searchEntities } from "../lib/api";
import { formatDateOnly, formatDuration, formatPercent } from "../lib/format";
import type { SearchResponse } from "../lib/types";
import { Link } from "react-router-dom";

const statusClass = (status: string) => {
  if (status === "completed") return "ei-pill completed";
  if (status === "failed") return "ei-pill failed";
  return "ei-pill processing";
};

const formatStatus = (status: string) =>
  status ? status.charAt(0).toUpperCase() + status.slice(1) : status;

export default function Search() {
  const [query, setQuery] = useState("");
  const [similarity, setSimilarity] = useState(0.7);
  const [minPresence, setMinPresence] = useState(0);
  const [minFrames, setMinFrames] = useState(0);
  const [results, setResults] = useState<SearchResponse | null>(null);

  const handleSearch = async () => {
    if (!query.trim()) return;
    const data = await searchEntities(query, similarity, minPresence, minFrames);
    setResults(data);
  };

  const resetFilters = () => {
    setSimilarity(0.7);
    setMinPresence(0);
    setMinFrames(0);
  };

  return (
    <div className="space-y-6">
      <TopTitleSection
        title="Unified Entity Search"
        subtitle="Search for videos using entity names or natural language. The system automatically combines exact matches with AI-powered semantic search for comprehensive results."
      />

      <div className="space-y-2">
        <input
          className="ei-input"
          placeholder="e.g., aircraft, tanks in the sky, military personnel with drones..."
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <div className="text-xs text-ei-muted">
          Enter entity names (comma-separated) or natural language queries. Short queries will search for exact entity matches, while longer queries will use AI-powered semantic search for enhanced results.
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-6">
        <div className="ei-card px-4 py-4 space-y-4">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold">Filters</div>
            <button className="text-xs text-ei-accent" type="button" onClick={resetFilters}>
              Reset
            </button>
          </div>

          <div className="space-y-2">
            <div className="text-xs text-ei-muted">Similarity: {Math.round(similarity * 100)}%</div>
            <input
              className="ei-slider"
              type="range"
              min={0.5}
              max={1}
              step={0.01}
              value={similarity}
              onChange={(event) => setSimilarity(Number(event.target.value))}
            />
            <div className="flex justify-between text-[11px] text-ei-muted">
              <span>Broader (50%)</span>
              <span>Stricter (100%)</span>
            </div>
            <div className="text-[11px] text-ei-muted">Higher values find more exact semantic matches</div>
          </div>

          <div className="space-y-2">
            <div className="text-xs text-ei-muted">Min Presence: {Math.round(minPresence * 100)}%</div>
            <input
              className="ei-slider"
              type="range"
              min={0}
              max={1}
              step={0.01}
              value={minPresence}
              onChange={(event) => setMinPresence(Number(event.target.value))}
            />
            <div className="flex justify-between text-[11px] text-ei-muted">
              <span>0%</span>
              <span>50%</span>
              <span>100%</span>
            </div>
          </div>

          <div className="space-y-2">
            <div className="text-xs text-ei-muted">Min Frames</div>
            <input
              className="ei-input"
              type="number"
              min={0}
              value={minFrames}
              onChange={(event) => setMinFrames(Number(event.target.value))}
            />
            <div className="text-[11px] text-ei-muted">
              Only show videos where the entity appears in at least this many frames
            </div>
          </div>

          <button className="ei-button-primary w-full" onClick={handleSearch}>
            Search
          </button>
        </div>

        <div className="space-y-6">
          {!results && (
            <div className="ei-card flex flex-col items-center justify-center py-20 text-center text-ei-muted">
              <div className="w-12 h-12 rounded-full border border-ei-border flex items-center justify-center">
                <svg
                  width="22"
                  height="22"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="11" cy="11" r="8" />
                  <line x1="21" y1="21" x2="16.65" y2="16.65" />
                </svg>
              </div>
              <div className="text-sm font-semibold mt-4">Start searching</div>
              <div className="text-xs mt-1">Enter one or more entity names above to search for videos</div>
            </div>
          )}

          {results && (
            <>
              <div className="ei-card bg-ei-blue-soft border border-ei-border">
                <div className="px-5 py-4">
                  <div className="text-sm font-semibold flex items-center gap-2">
                    <span className="text-ei-accent">
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <circle cx="11" cy="11" r="8" />
                        <line x1="21" y1="21" x2="16.65" y2="16.65" />
                      </svg>
                    </span>
                    Unified Search Results
                  </div>
                  <div className="grid grid-cols-3 text-center text-xs text-ei-muted mt-4">
                    <div>
                      <div className="uppercase">Exact Matches</div>
                      <div className="text-lg font-semibold text-ei-text mt-1">
                        {results.exact_matches_count}
                      </div>
                    </div>
                    <div>
                      <div className="uppercase">AI Enhancements</div>
                      <div className="text-lg font-semibold text-ei-text mt-1">
                        {results.ai_enhancements_count}
                      </div>
                    </div>
                    <div>
                      <div className="uppercase">Total Unique Videos</div>
                      <div className="text-lg font-semibold text-ei-text mt-1">
                        {results.total_unique_videos}
                      </div>
                    </div>
                  </div>
                  <div className="mt-4 text-xs text-ei-muted">Found similar entities:</div>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {results.similar_entities.map((entity) => (
                      <span key={entity.label} className="ei-chip-muted">
                        {entity.label} {Math.round(entity.similarity * 100)}%
                      </span>
                    ))}
                    {results.similar_entities.length === 0 && (
                      <span className="text-xs text-ei-muted">None</span>
                    )}
                  </div>
                  <div className="text-[11px] text-ei-muted mt-2">
                    These entities were found via semantic similarity and used to enhance your search results
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs text-ei-muted">
                <span>Found {results.total_unique_videos} unique videos</span>
                <span>Page 1 of 1</span>
              </div>

              <div className="space-y-4">
                {results.results.map((item) => (
                  <Link
                    key={item.video_id}
                    to={`/videos/${item.video_id}`}
                    className="ei-card block hover:bg-ei-tab"
                  >
                    <div className="px-5 py-4 flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 rounded-md bg-ei-blue-soft flex items-center justify-center text-ei-accent">
                          <svg
                            width="16"
                            height="16"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          >
                            <rect x="3" y="4" width="18" height="14" rx="2" ry="2" />
                            <polygon points="10 9 15 12 10 15 10 9" />
                          </svg>
                        </div>
                        <div>
                          <div className="text-sm font-semibold">{item.filename}</div>
                          <div className="text-xs text-ei-muted mt-1">{formatDateOnly(item.created_at)}</div>
                          <div className="flex items-center gap-4 text-xs text-ei-muted mt-2">
                            <div className="flex items-center gap-1">
                              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <circle cx="12" cy="12" r="10" />
                                <polyline points="12 6 12 12 16 14" />
                              </svg>
                              {formatDuration(item.duration_sec ?? undefined)}
                            </div>
                            <div className="flex items-center gap-1">
                              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <rect x="3" y="4" width="18" height="14" rx="2" ry="2" />
                                <line x1="7" y1="8" x2="7" y2="16" />
                                <line x1="12" y1="8" x2="12" y2="16" />
                                <line x1="17" y1="8" x2="17" y2="16" />
                              </svg>
                              {item.matched_entities.reduce((sum, ent) => sum + ent.frames, 0)} frames
                            </div>
                          </div>
                          <div className="text-xs text-ei-muted mt-3">Matched Entities:</div>
                          <div className="flex flex-wrap gap-2 mt-2">
                            {item.matched_entities.map((entity) => (
                              <span key={entity.label} className="ei-chip">
                                {entity.label} {formatPercent(entity.presence, 1)} ({entity.frames} frames)
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                      <span className={statusClass(item.status)}>{formatStatus(item.status)}</span>
                    </div>
                    <div className="px-5 pb-4 text-[11px] text-ei-muted">
                      Click to view full video details and timeline
                    </div>
                  </Link>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
