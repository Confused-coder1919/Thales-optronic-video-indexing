import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import QuestionView from "../components/QuestionView";
import { questionsById } from "../data/questions";
import { scoreQuestion } from "../lib/scoring";
import { useNow } from "../lib/useNow";
import { actions, useAppStore } from "../store/appStore";
import type { AnswerValue } from "../types";

export default function ReviewPage() {
  const reviewQueue = useAppStore((s) => s.reviewQueue);
  const now = useNow({ intervalMs: 30_000 });

  const dueIds = useMemo(() => {
    return Object.values(reviewQueue)
      .filter((it) => it.nextDue <= now)
      .sort((a, b) => a.nextDue - b.nextDue)
      .map((it) => it.id);
  }, [reviewQueue, now]);

  const totalQueued = Object.keys(reviewQueue).length;

  const [sessionIds, setSessionIds] = useState<number[] | null>(null);
  const [idx, setIdx] = useState(0);
  const [answer, setAnswer] = useState<AnswerValue | undefined>(undefined);
  const [reveal, setReveal] = useState(false);
  const [lastCheck, setLastCheck] = useState<{ score: number; isCorrect: boolean } | null>(null);

  const activeIds = sessionIds ?? dueIds;
  const activeId = activeIds[idx];
  const question = activeId ? questionsById.get(activeId) : undefined;

  if (!question) {
    return (
      <div className="stack">
        <div className="card">
          <div className="card-body stack">
            <h1 className="h1">Review Queue</h1>
            <p className="lead">
              Due now: <strong>{dueIds.length}</strong> · In queue: <strong>{totalQueued}</strong>
            </p>
            {dueIds.length === 0 ? (
              <p className="lead">No due questions right now. Come back later.</p>
            ) : (
              <p className="lead">Start a review session to practice due questions.</p>
            )}
            <div className="row">
              {dueIds.length ? (
                <button
                  className="btn primary"
                  type="button"
                  onClick={() => {
                    setSessionIds(dueIds);
                    setIdx(0);
                    setAnswer(undefined);
                    setReveal(false);
                    setLastCheck(null);
                  }}
                >
                  Start review ({dueIds.length})
                </button>
              ) : null}
              <Link className="btn" to="/learn">
                Learn mode
              </Link>
              <Link className="btn" to="/test">
                Test mode
              </Link>
            </div>
          </div>
        </div>

        {totalQueued ? (
          <div className="card">
            <div className="card-body stack">
              <div style={{ fontWeight: 900 }}>Scheduled (not yet due)</div>
              <div className="muted">
                {totalQueued - dueIds.length} question(s) are scheduled for later.
              </div>
            </div>
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <div className="stack">
      <div className="card">
        <div className="card-body stack">
          <h1 className="h1">Review Session</h1>
          <p className="lead">
            Due now: <strong>{dueIds.length}</strong> · Session: <strong>{idx + 1}</strong> /{" "}
            {activeIds.length}
          </p>
          <div className="row">
            <button
              className="btn"
              type="button"
              onClick={() => {
                setSessionIds(null);
                setIdx(0);
                setAnswer(undefined);
                setReveal(false);
                setLastCheck(null);
              }}
            >
              Exit session
            </button>
          </div>
        </div>
      </div>

      <QuestionView question={question} answer={answer} onAnswer={setAnswer} reveal={reveal} />

      <div className="row">
        <button
          className="btn primary"
          type="button"
          onClick={() => {
            const r = scoreQuestion(question, answer);
            setLastCheck({ score: r.score, isCorrect: r.isCorrect });
            setReveal(true);
            actions.recordReviewResult(question.id, r.isCorrect);
          }}
        >
          Check answer
        </button>
        <button
          className="btn"
          type="button"
          onClick={() => {
            setAnswer(undefined);
            setReveal(false);
            setLastCheck(null);
          }}
        >
          Reset answer
        </button>
        <button
          className="btn"
          type="button"
          onClick={() => {
            const prev = Math.max(0, idx - 1);
            setIdx(prev);
            setAnswer(undefined);
            setReveal(false);
            setLastCheck(null);
          }}
          disabled={idx === 0}
        >
          Previous
        </button>
        <button
          className="btn"
          type="button"
          onClick={() => {
            const next = Math.min(activeIds.length - 1, idx + 1);
            setIdx(next);
            setAnswer(undefined);
            setReveal(false);
            setLastCheck(null);
          }}
          disabled={idx >= activeIds.length - 1}
        >
          Next
        </button>
      </div>

      {lastCheck ? (
        <div className="card" style={{ boxShadow: "none" }}>
          <div className="card-body stack">
            <div style={{ fontWeight: 900 }}>
              {lastCheck.isCorrect ? "Correct" : "Incorrect"} · Score {lastCheck.score.toFixed(2)} /
              1.00
            </div>
            <div className="muted">
              {lastCheck.isCorrect
                ? "Scheduled to the next interval (or removed if mastered)."
                : "Reset: scheduled again at +10 minutes."}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
