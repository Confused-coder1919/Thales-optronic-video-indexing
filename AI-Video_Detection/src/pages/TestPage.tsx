import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import QuestionView from "../components/QuestionView";
import { questions, questionsById } from "../data/questions";
import { useNow } from "../lib/useNow";
import { actions, useAppStore } from "../store/appStore";
import type { ModuleId } from "../types";

function fmtDuration(ms: number): string {
  const s = Math.max(0, Math.floor(ms / 1000));
  const mm = Math.floor(s / 60);
  const ss = s % 60;
  return `${mm}:${String(ss).padStart(2, "0")}`;
}

function moduleLabel(m: ModuleId): string {
  if (m === 1) return "Module 1";
  if (m === 2) return "Module 2";
  if (m === 3) return "Module 3";
  return "Module 4";
}

export default function TestPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const now = useNow({ intervalMs: 1000 });

  const attemptId = params.get("attempt");
  const attempts = useAppStore((s) => s.attempts);
  const inProgress = useAppStore((s) => s.inProgressTest);

  const attempt = useMemo(() => {
    if (!attemptId) return null;
    return attempts.find((a) => a.id === attemptId) ?? null;
  }, [attemptId, attempts]);

  // Setup state
  const [scopeKind, setScopeKind] = useState<"all" | "module">("all");
  const [module, setModule] = useState<ModuleId>(1);
  const [timerEnabled, setTimerEnabled] = useState(false);
  const [durationMin, setDurationMin] = useState(60);

  // In-test navigation state (not persisted; answers are).
  const [idx, setIdx] = useState(0);

  useEffect(() => {
    if (!inProgress) return;
    const total = inProgress.questionIds.length;
    if (total === 0) return;

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.altKey || e.ctrlKey || e.metaKey) return;
      if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;

      const el = document.activeElement;
      if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement || el instanceof HTMLSelectElement) {
        return;
      }

      if (e.key === "ArrowLeft") {
        e.preventDefault();
        setIdx((v) => Math.max(0, v - 1));
      }
      if (e.key === "ArrowRight") {
        e.preventDefault();
        setIdx((v) => Math.min(total - 1, v + 1));
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [inProgress]);

  if (attempt) {
    const { results } = attempt;
    const percent = results.maxScore ? Math.round((results.totalScore / results.maxScore) * 100) : 0;
    const missed = results.missedQuestionIds;

    const tagRows = Object.entries(results.byTag)
      .map(([tag, v]) => ({ tag, ...v }))
      .sort((a, b) => a.accuracy - b.accuracy);

    return (
      <div className="stack">
        <div className="card">
          <div className="card-body stack">
            <h1 className="h1">Test Results</h1>
            <p className="lead">
              Score: <strong>{results.totalScore.toFixed(1)}</strong> / {results.maxScore} ({percent}
              %)
            </p>
            <div className="row">
              <button className="btn primary" type="button" onClick={() => actions.exportResults()}>
                Export results (JSON)
              </button>
              <Link className="btn" to="/test">
                New test
              </Link>
              <Link className="btn" to="/review">
                Go to Review Queue
              </Link>
            </div>
          </div>
        </div>

        <div className="grid cols-2">
          <div className="card">
            <div className="card-body stack">
              <div style={{ fontWeight: 900 }}>Breakdown by module</div>
              <div className="stack" style={{ gap: 8 }}>
                {([1, 2, 3, 4] as const).map((m) => (
                  <div key={m} className="row" style={{ justifyContent: "space-between" }}>
                    <span className="muted">{moduleLabel(m)}</span>
                    <span style={{ fontWeight: 800 }}>
                      {results.byModule[m].score.toFixed(1)} / {results.byModule[m].maxScore} (
                      {Math.round(results.byModule[m].accuracy * 100)}%)
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-body stack">
              <div style={{ fontWeight: 900 }}>Breakdown by tag (lowest first)</div>
              <div className="stack" style={{ gap: 8 }}>
                {tagRows.slice(0, 10).map((t) => (
                  <div key={t.tag} className="row" style={{ justifyContent: "space-between" }}>
                    <span className="muted">{t.tag}</span>
                    <span style={{ fontWeight: 800 }}>
                      {Math.round(t.accuracy * 100)}% ({t.count})
                    </span>
                  </div>
                ))}
                {tagRows.length > 10 ? (
                  <div className="muted">…and {tagRows.length - 10} more tags</div>
                ) : null}
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-body stack">
            <div style={{ fontWeight: 900 }}>Missed questions ({missed.length})</div>
            {missed.length === 0 ? (
              <p className="lead">Perfect score. Nothing to review.</p>
            ) : (
              <div className="stack" style={{ gap: 14 }}>
                {missed.map((qid) => {
                  const q = questionsById.get(qid);
                  if (!q) return null;
                  return (
                    <div key={qid} className="card" style={{ boxShadow: "none" }}>
                      <div className="card-body stack">
                        <QuestionView
                          question={q}
                          answer={attempt.answers[qid]}
                          onAnswer={() => {}}
                          disabled
                          reveal
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (inProgress) {
    const qids = inProgress.questionIds;
    const total = qids.length;
    const qid = qids[Math.min(idx, total - 1)];
    const q = questionsById.get(qid)!;

    const endAt = inProgress.timerEnabled && inProgress.durationMs ? inProgress.startedAt + inProgress.durationMs : null;
    const remainingMs = endAt && now ? endAt - now : null;
    const canPrev = idx > 0;
    const canNext = idx < total - 1;

    const scrollToQuestion = () => {
      document.getElementById("test-question-anchor")?.scrollIntoView({ behavior: "smooth", block: "start" });
    };

    const goPrev = () => {
      setIdx((v) => Math.max(0, v - 1));
      scrollToQuestion();
    };

    const goNext = () => {
      setIdx((v) => Math.min(total - 1, v + 1));
      scrollToQuestion();
    };

    const jumpToQuestion = (nextId: number) => {
      const nextIdx = qids.indexOf(nextId);
      if (nextIdx >= 0) {
        setIdx(nextIdx);
        scrollToQuestion();
      }
    };

    const abandonTest = () => {
      actions.abandonTest();
      setIdx(0);
    };

    const submitTest = () => {
      const id = actions.submitTest();
      if (id) navigate(`/test?attempt=${encodeURIComponent(id)}`);
    };

    return (
      <div className="stack">
        <div className="card">
          <div className="card-body stack">
            <h1 className="h1">Test In Progress</h1>
            <div className="row">
              <span className="pill">
                Scope:{" "}
                {inProgress.scope === "all" ? "Full exam (94)" : `Module ${inProgress.scope.module}`}
              </span>
              <span className="pill">
                Progress: {idx + 1} / {total}
              </span>
              {endAt ? (
                <span className="pill">
                  Timer: {remainingMs !== null ? fmtDuration(remainingMs) : "—"}
                </span>
              ) : (
                <span className="pill">Timer: off</span>
              )}
            </div>

            <div className="grid cols-2">
              <div className="field">
                <label htmlFor="jump">Jump to question</label>
                <select
                  id="jump"
                  value={qid}
                  onChange={(e) => {
                    const nextId = Number.parseInt(e.target.value, 10);
                    jumpToQuestion(nextId);
                  }}
                >
                  {qids.map((id) => (
                    <option key={id} value={id}>
                      Q{id}
                    </option>
                  ))}
                </select>
              </div>

              <div className="field">
                <label>Keyboard</label>
                <div className="muted">Use ← / → to move quickly between questions.</div>
              </div>
            </div>
          </div>
        </div>

        <div id="test-question-anchor">
          <QuestionView
            question={q}
            answer={inProgress.answers[qid]}
            onAnswer={(next) => actions.setTestAnswer(qid, next)}
          />
        </div>

        <div className="card" style={{ boxShadow: "none" }}>
          <div className="card-body stack">
            <div className="row">
              <span className="pill">
                Question {idx + 1} / {total}
              </span>
              <span className="pill">Actions are below the question for faster flow</span>
            </div>
            <div className="row">
              <button className="btn" type="button" onClick={goPrev} disabled={!canPrev}>
                Previous
              </button>
              <button className="btn" type="button" onClick={goNext} disabled={!canNext}>
                Next
              </button>
              <button className="btn primary" type="button" onClick={submitTest}>
                Submit test
              </button>
              <button className="btn danger" type="button" onClick={abandonTest}>
                Abandon
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Setup view
  const scope =
    scopeKind === "all"
      ? ("all" as const)
      : ({ module } as const);

  const suggestedMin =
    scopeKind === "all"
      ? 75
      : 25;

  return (
    <div className="stack">
      <div className="card">
        <div className="card-body stack">
          <h1 className="h1">Test Mode</h1>
          <p className="lead">
            Choose full exam (94) or a module. MCQs are auto-scored; free-text questions use a self-check rubric.
          </p>

          <div className="field">
            <label>Scope</label>
            <div className="row">
              <label className="pill" style={{ cursor: "pointer" }}>
                <input
                  type="radio"
                  name="scope"
                  checked={scopeKind === "all"}
                  onChange={() => setScopeKind("all")}
                />
                Full exam (94)
              </label>
              <label className="pill" style={{ cursor: "pointer" }}>
                <input
                  type="radio"
                  name="scope"
                  checked={scopeKind === "module"}
                  onChange={() => setScopeKind("module")}
                />
                Per module
              </label>
              {scopeKind === "module" ? (
                <select value={module} onChange={(e) => setModule(Number.parseInt(e.target.value, 10) as ModuleId)}>
                  <option value={1}>Module 1 (Q1–20)</option>
                  <option value={2}>Module 2 (Q21–47)</option>
                  <option value={3}>Module 3 (Q48–74)</option>
                  <option value={4}>Module 4 (Q75–94)</option>
                </select>
              ) : null}
            </div>
          </div>

          <div className="field">
            <label>Timer (optional)</label>
            <div className="row">
              <label className="pill" style={{ cursor: "pointer" }}>
                <input
                  type="checkbox"
                  checked={timerEnabled}
                  onChange={(e) => setTimerEnabled(e.target.checked)}
                />
                Enable timer
              </label>
              {timerEnabled ? (
                <>
                  <span className="muted">Minutes:</span>
                  <input
                    type="number"
                    min={5}
                    max={240}
                    value={durationMin}
                    onChange={(e) => setDurationMin(Number.parseInt(e.target.value || "0", 10))}
                    style={{ maxWidth: 120 }}
                  />
                  <button className="btn" type="button" onClick={() => setDurationMin(suggestedMin)}>
                    Suggest ({suggestedMin})
                  </button>
                </>
              ) : null}
            </div>
          </div>

          <div className="row">
            <button
              className="btn primary"
              type="button"
              onClick={() => {
                const durationMs = timerEnabled ? Math.max(5, durationMin) * 60 * 1000 : undefined;
                setIdx(0);
                actions.startTest(scope, { timerEnabled, durationMs });
              }}
            >
              Start test
            </button>
            <button className="btn" type="button" onClick={() => actions.exportResults()}>
              Export results (JSON)
            </button>
          </div>

          <p className="lead">
            Tip: after submitting, missed questions are automatically added to the Review Queue.
          </p>
        </div>
      </div>

      <div className="card">
        <div className="card-body stack">
          <div style={{ fontWeight: 900 }}>Question counts</div>
          <div className="row">
            <span className="pill">Module 1: {questions.filter((q) => q.module === 1).length}</span>
            <span className="pill">Module 2: {questions.filter((q) => q.module === 2).length}</span>
            <span className="pill">Module 3: {questions.filter((q) => q.module === 3).length}</span>
            <span className="pill">Module 4: {questions.filter((q) => q.module === 4).length}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
