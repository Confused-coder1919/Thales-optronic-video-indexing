import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import QuestionView from "../components/QuestionView";
import { conceptCards } from "../data/concepts";
import { questions, questionsById } from "../data/questions";
import { scoreQuestion } from "../lib/scoring";
import { actions, useAppStore } from "../store/appStore";
import type { AnswerValue, ModuleId, Question } from "../types";

const moduleMeta: Record<ModuleId, { title: string; blurb: string }> = {
  1: {
    title: "Cybersecurity: core notions",
    blurb:
      "Understand core security ideas (CIA triad, common threats, and impacts).",
  },
  2: {
    title: "Cyber hygiene rules",
    blurb:
      "Build safe daily habits: passwords, updates, antivirus, web hygiene, incident reflexes.",
  },
  3: {
    title: "Network and application aspects",
    blurb:
      "Learn where network/app security works: segmentation, TLS, certificates, web risks.",
  },
  4: {
    title: "Managing cybersecurity in an organization",
    blurb:
      "Connect risk, defense-in-depth, cloud choices, and governance decisions.",
  },
};

function hintForQuestion(q: Question): string {
  const tagHints: Record<string, string> = {
    cia: "Ask yourself which of confidentiality, integrity, or availability is involved.",
    phishing: "Look for social manipulation: urgency, authority, or requests for secrets.",
    passwords: "Think: long, unique, and stored safely (password manager).",
    wifi: "Treat the network as untrusted; encryption and authentication matter.",
    https: "HTTPS helps, but certificate warnings are a big deal.",
    sql_injection: "If input becomes part of a query, injection is possible.",
    risk_analysis: "Risk is impact x likelihood, and treatment is a decision.",
    defense_in_depth: "One control will fail. Think layers.",
  };

  for (const t of q.tags) {
    if (tagHints[t]) return tagHints[t];
  }
  return "Focus on the key idea and eliminate options that confuse goals (what you want) with means (how you do it).";
}

function guideForQuestion(q: Question): { ask: string; remember: string; doNext: string } {
  const guideByTag: Record<string, { ask: string; remember: string; doNext: string }> = {
    cia: {
      ask: "Which CIA property is mainly affected in this scenario?",
      remember: "Confidentiality = secrecy, Integrity = correctness, Availability = uptime.",
      doNext: "Map each option to one CIA property, then remove mismatches.",
    },
    phishing: {
      ask: "Is this social manipulation (urgency, authority, fear, reward)?",
      remember: "Phishing targets human trust before technical controls.",
      doNext: "Look for verification steps and safe reporting behavior.",
    },
    passwords: {
      ask: "Which choice creates strong, unique credentials in real life?",
      remember: "Length and uniqueness matter more than complexity tricks.",
      doNext: "Prioritize passphrases and password manager use.",
    },
    wifi: {
      ask: "Is the network trusted or potentially hostile?",
      remember: "Public Wi-Fi should be treated as untrusted by default.",
      doNext: "Choose options with encryption, caution, and safe behavior.",
    },
    https: {
      ask: "Does the answer include certificate trust checks, not just 'HTTPS is on'?",
      remember: "HTTPS without trusted certificates can still be unsafe.",
      doNext: "Reject options that ignore warnings or certificate validation.",
    },
    sql_injection: {
      ask: "Can user input reach SQL commands directly?",
      remember: "Concatenated input into queries creates injection risk.",
      doNext: "Prefer parameterized queries and validation-focused options.",
    },
    risk_analysis: {
      ask: "Is the answer evaluating both impact and likelihood?",
      remember: "Risk treatment is a management decision after analysis.",
      doNext: "Choose options that align controls with risk level and context.",
    },
    defense_in_depth: {
      ask: "Does the option rely on a single control or layered controls?",
      remember: "One control can fail; layers reduce blast radius.",
      doNext: "Prefer combinations: identity + network + endpoint + monitoring.",
    },
  };

  for (const t of q.tags) {
    if (guideByTag[t]) return guideByTag[t];
  }

  return {
    ask: "What exact decision is this question asking you to make?",
    remember: "Good answers align with security principles and practical behavior.",
    doNext: "Eliminate options that are extreme, vague, or unrealistic.",
  };
}

export default function LearnPage() {
  const [params, setParams] = useSearchParams();
  const learn = useAppStore((s) => s.learn);

  const moduleId = useMemo(() => {
    const raw = Number.parseInt(params.get("module") ?? "", 10);
    if (raw === 1 || raw === 2 || raw === 3 || raw === 4) return raw as ModuleId;
    return learn.module ?? 1;
  }, [params, learn.module]);

  const moduleQuestions = useMemo(
    () => questions.filter((q) => q.module === moduleId),
    [moduleId],
  );

  const moduleStats = useMemo(() => {
    const total = moduleQuestions.length;
    const freeText = moduleQuestions.filter((q) => q.type === "free_text").length;
    const mcq = total - freeText;
    const tagCounts = new Map<string, number>();
    for (const q of moduleQuestions) {
      for (const t of q.tags) tagCounts.set(t, (tagCounts.get(t) ?? 0) + 1);
    }
    const topTags = Array.from(tagCounts.entries())
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .slice(0, 10);
    return { total, mcq, freeText, topTags };
  }, [moduleQuestions]);

  const questionId = useMemo(() => {
    const raw = Number.parseInt(params.get("q") ?? "", 10);
    if (moduleQuestions.some((q) => q.id === raw)) return raw;
    const fallback = learn.questionId;
    if (fallback && moduleQuestions.some((q) => q.id === fallback)) return fallback;
    return moduleQuestions[0]?.id ?? 1;
  }, [params, moduleQuestions, learn.questionId]);

  const question = useMemo(
    () => moduleQuestions.find((q) => q.id === questionId)!,
    [moduleQuestions, questionId],
  );

  const [showHint, setShowHint] = useState(false);
  const [showTheory, setShowTheory] = useState(false);
  const [showAllConcepts, setShowAllConcepts] = useState(false);

  useEffect(() => {
    actions.setLearnLocation(moduleId, questionId);
  }, [moduleId, questionId]);

  const relatedCards = useMemo(() => {
    const qTags = new Set(question.tags);
    return conceptCards
      .filter((c) => c.questionIds.includes(question.id) || c.tags.some((t) => qTags.has(t)))
      .slice(0, 6);
  }, [question]);
  const guide = useMemo(() => guideForQuestion(question), [question]);

  const nav = useMemo(() => {
    const idx = moduleQuestions.findIndex((q) => q.id === questionId);
    const total = moduleQuestions.length;

    const prevInModule = idx > 0 ? moduleQuestions[idx - 1] : null;
    const nextInModule = idx >= 0 && idx < total - 1 ? moduleQuestions[idx + 1] : null;

    if (prevInModule && nextInModule) {
      return { idx, total, prev: prevInModule, next: nextInModule };
    }

    const prevModule = moduleId > 1 ? ((moduleId - 1) as ModuleId) : null;
    const nextModule = moduleId < 4 ? ((moduleId + 1) as ModuleId) : null;
    const prevModuleQuestions = prevModule ? questions.filter((q) => q.module === prevModule) : [];
    const nextModuleQuestions = nextModule ? questions.filter((q) => q.module === nextModule) : [];

    const prev =
      prevInModule ??
      (prevModule ? prevModuleQuestions[prevModuleQuestions.length - 1] ?? null : null);
    const next = nextInModule ?? (nextModule ? nextModuleQuestions[0] ?? null : null);

    return { idx, total, prev, next };
  }, [moduleQuestions, questionId, moduleId]);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.altKey || e.ctrlKey || e.metaKey) return;
      if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;

      // Avoid hijacking keystrokes while typing.
      const el = document.activeElement;
      if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement || el instanceof HTMLSelectElement) {
        return;
      }

      if (e.key === "ArrowLeft" && nav.prev) {
        e.preventDefault();
        setParams({ module: String(nav.prev.module), q: String(nav.prev.id) });
      }
      if (e.key === "ArrowRight" && nav.next) {
        e.preventDefault();
        setParams({ module: String(nav.next.module), q: String(nav.next.id) });
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [nav.prev, nav.next, setParams]);

  const cardsByPrimaryTag = useMemo(() => {
    const cardsForModule = conceptCards.filter((c) =>
      c.questionIds.some((qid) => questionsById.get(qid)?.module === moduleId),
    );
    const groups = new Map<string, typeof cardsForModule>();
    for (const c of cardsForModule) {
      const tag = c.tags[0] ?? "other";
      if (!groups.has(tag)) groups.set(tag, []);
      groups.get(tag)!.push(c);
    }
    return Array.from(groups.entries()).sort((a, b) => a[0].localeCompare(b[0]));
  }, [moduleId]);

  return (
    <div className="stack">
      <div className="card">
        <div className="card-body stack">
          <h1 className="h1">Learn Mode</h1>
          <p className="lead">
            Start with the question. Open extra help only when needed.
          </p>

          <div className="row">
            {[1, 2, 3, 4].map((m) => (
              <button
                key={m}
                type="button"
                className={`btn ${m === moduleId ? "primary" : ""}`}
                onClick={() => setParams({ module: String(m), q: String(questions.find((q) => q.module === m)?.id ?? 1) })}
              >
                Module {m}
              </button>
            ))}
          </div>

          <div className="card" style={{ boxShadow: "none" }}>
            <div className="card-body stack">
              <div style={{ fontWeight: 900 }}>
                Module {moduleId}: {moduleMeta[moduleId].title}
              </div>
              <div className="muted">{moduleMeta[moduleId].blurb}</div>
              <div className="row">
                <span className="pill">Questions: {moduleStats.total}</span>
                <span className="pill">MCQ: {moduleStats.mcq}</span>
                <span className="pill">Free-text: {moduleStats.freeText}</span>
                <span className="pill">Tip: use ← / → to navigate</span>
              </div>
              <div className="row">
                {moduleStats.topTags.map(([t, n]) => (
                  <span key={t} className="pill">
                    {t} <span className="badge">{n}</span>
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="card" style={{ boxShadow: "none" }}>
            <div className="card-body stack">
              <div style={{ fontWeight: 900 }}>How to use Learn Mode</div>
              <ol className="learn-steps">
                <li>Read and answer the question first.</li>
                <li>If unsure, open Hint (one short clue).</li>
                <li>If still unsure, open Theory (short explanation cards).</li>
              </ol>
              <div className="muted">This keeps your screen clean and reduces overload.</div>
            </div>
          </div>

          <div className="grid cols-2">
            <div className="field">
              <label htmlFor="question">Question</label>
              <select
                id="question"
                value={questionId}
                onChange={(e) => setParams({ module: String(moduleId), q: e.target.value })}
              >
                {moduleQuestions.map((q) => (
                  <option key={q.id} value={q.id}>
                    {q.id}. {q.prompt_en.slice(0, 70)}
                    {q.prompt_en.length > 70 ? "…" : ""}
                  </option>
                ))}
              </select>
              <div className="muted" style={{ marginTop: 6 }}>
                Position: {nav.idx >= 0 ? nav.idx + 1 : "—"} / {nav.total}
              </div>
            </div>

            <div className="field">
              <label>Navigation</label>
              <div className="row">
                <button
                  className="btn"
                  type="button"
                  onClick={() => nav.prev && setParams({ module: String(nav.prev.module), q: String(nav.prev.id) })}
                  disabled={!nav.prev}
                >
                  Previous
                </button>
                <button
                  className="btn"
                  type="button"
                  onClick={() => nav.next && setParams({ module: String(nav.next.module), q: String(nav.next.id) })}
                  disabled={!nav.next}
                >
                  Next
                </button>
              </div>
            </div>

            <div className="field">
              <label>Support (optional)</label>
              <div className="row">
                <button className="btn" type="button" onClick={() => setShowHint((v) => !v)}>
                  {showHint ? "Hide Hint" : "Show Hint"}
                </button>
                <button className="btn" type="button" onClick={() => setShowTheory((v) => !v)}>
                  {showTheory ? "Hide Theory" : "Show Theory"}
                </button>
                <button className="btn" type="button" onClick={() => setShowAllConcepts((v) => !v)}>
                  {showAllConcepts ? "Hide Module Library" : "Module Library"}
                </button>
              </div>
              <div className="muted">Theory is now closed by default.</div>
            </div>
          </div>

          <div className="card" style={{ boxShadow: "none" }}>
            <div className="card-body stack">
              <div style={{ fontWeight: 900 }}>Quick context for this question</div>
              <div className="learn-guide-grid">
                <div className="learn-guide-item">
                  <strong>What this asks</strong>
                  <span className="muted">{guide.ask}</span>
                </div>
                <div className="learn-guide-item">
                  <strong>Remember</strong>
                  <span className="muted">{guide.remember}</span>
                </div>
                <div className="learn-guide-item">
                  <strong>Do next</strong>
                  <span className="muted">{guide.doNext}</span>
                </div>
              </div>
              <div className="row">
                {relatedCards.length ? (
                  relatedCards.map((c) => (
                    <span key={c.id} className="pill">
                      {c.title_en}
                    </span>
                  ))
                ) : (
                  <span className="muted">No related concept cards for this question.</span>
                )}
              </div>
            </div>
          </div>

          {showHint ? (
            <div className="card" style={{ boxShadow: "none" }}>
              <div className="card-body stack">
                <div style={{ fontWeight: 800 }}>Hint (1-line)</div>
                <div className="muted">{hintForQuestion(question)}</div>
              </div>
            </div>
          ) : null}

          {showTheory ? (
            <div className="card" style={{ boxShadow: "none" }}>
              <div className="card-body stack">
                <div style={{ fontWeight: 900 }}>Theory for this question</div>
                <div className="muted">Short cards only. Read 1 card, then answer again.</div>
                {relatedCards.length ? (
                  relatedCards.slice(0, 3).map((c) => (
                    <div key={c.id} className="card" style={{ boxShadow: "none" }}>
                      <div className="card-body stack">
                        <div style={{ fontWeight: 900 }}>{c.title_en}</div>
                        <div className="muted" style={{ whiteSpace: "pre-line" }}>
                          {c.body_en}
                        </div>
                        <div className="row">
                          {c.questionIds.map((qid) => (
                            <button
                              key={qid}
                              type="button"
                              className="btn"
                              onClick={() => {
                                const q = questionsById.get(qid);
                                const m = q?.module ?? moduleId;
                                setParams({ module: String(m), q: String(qid) });
                              }}
                            >
                              Go to Q{qid}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="lead">No theory cards linked to this question yet.</p>
                )}
              </div>
            </div>
          ) : null}

          {showAllConcepts ? (
            <div className="card" style={{ boxShadow: "none" }}>
              <div className="card-body stack">
                <div style={{ fontWeight: 900 }}>Module concept library (grouped by tag)</div>
                {cardsByPrimaryTag.length ? (
                  <div className="stack" style={{ gap: 14 }}>
                    {cardsByPrimaryTag.map(([tag, cards]) => (
                      <div key={tag} className="card" style={{ boxShadow: "none" }}>
                        <div className="card-body stack">
                          <div className="pill">Tag: {tag}</div>
                          <div className="stack" style={{ gap: 10 }}>
                            {cards.map((c) => (
                              <div key={c.id} className="card" style={{ boxShadow: "none" }}>
                                <div className="card-body stack">
                                  <div style={{ fontWeight: 900 }}>{c.title_en}</div>
                                  <div className="muted" style={{ whiteSpace: "pre-line" }}>
                                    {c.body_en}
                                  </div>
                                  <div className="row">
                                    {c.questionIds.map((qid) => (
                                      <button
                                        key={qid}
                                        type="button"
                                        className="btn"
                                        onClick={() => {
                                          const q = questionsById.get(qid);
                                          const m = q?.module ?? moduleId;
                                          setParams({ module: String(m), q: String(qid) });
                                        }}
                                      >
                                        Go to Q{qid}
                                      </button>
                                    ))}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="lead">No concept cards for this module yet.</p>
                )}
              </div>
            </div>
          ) : null}
        </div>
      </div>

      <PracticePanel key={question.id} question={question} />

      <div className="row" style={{ justifyContent: "space-between" }}>
        <button
          className="btn"
          type="button"
          onClick={() => nav.prev && setParams({ module: String(nav.prev.module), q: String(nav.prev.id) })}
          disabled={!nav.prev}
        >
          Previous
        </button>
        <button
          className="btn primary"
          type="button"
          onClick={() => nav.next && setParams({ module: String(nav.next.module), q: String(nav.next.id) })}
          disabled={!nav.next}
        >
          Next
        </button>
      </div>
    </div>
  );
}

function PracticePanel({ question }: { question: Question }) {
  const [answer, setAnswer] = useState<AnswerValue | undefined>(undefined);
  const [revealWhy, setRevealWhy] = useState(false);
  const [lastCheck, setLastCheck] = useState<{ score: number; isCorrect: boolean } | null>(null);

  return (
    <>
      <QuestionView question={question} answer={answer} onAnswer={setAnswer} reveal={revealWhy} />

      <div className="row">
        <button
          className="btn primary"
          type="button"
          onClick={() => {
            const r = scoreQuestion(question, answer);
            setLastCheck({ score: r.score, isCorrect: r.isCorrect });
            setRevealWhy(true);
            if (!r.isCorrect) actions.scheduleReviewFromIncorrect(question.id);
          }}
        >
          Check answer
        </button>
        <button className="btn" type="button" onClick={() => setRevealWhy((v) => !v)}>
          {revealWhy ? "Hide Why" : "Why"}
        </button>
        <button
          className="btn"
          type="button"
          onClick={() => {
            setAnswer(undefined);
            setLastCheck(null);
            setRevealWhy(false);
          }}
        >
          Reset answer
        </button>
      </div>

      {lastCheck ? (
        <div className="card" style={{ boxShadow: "none" }}>
          <div className="card-body stack">
            <div style={{ fontWeight: 900 }}>
              {lastCheck.isCorrect ? "Correct" : "Not fully correct"} · Score{" "}
              {lastCheck.score.toFixed(2)} / 1.00
            </div>
            {!lastCheck.isCorrect ? (
              <div className="muted">
                Added to Review Queue (spaced repetition): +10 minutes, +1 day, +3 days.
              </div>
            ) : (
              <div className="muted">Great. Move on or try the next question.</div>
            )}
          </div>
        </div>
      ) : null}
    </>
  );
}
