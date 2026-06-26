import { Link } from "react-router-dom";
import { actions, useAppStore } from "../store/appStore";
import { questions } from "../data/questions";
import { useNow } from "../lib/useNow";

export default function HomePage() {
  const attempts = useAppStore((s) => s.attempts);
  const inProgress = useAppStore((s) => s.inProgressTest);
  const reviewQueue = useAppStore((s) => s.reviewQueue);

  const now = useNow({ intervalMs: 30_000 });
  const dueCount = Object.values(reviewQueue).filter((it) => it.nextDue <= now).length;
  const lastAttempt = attempts[0];

  const lastScore = lastAttempt
    ? `${lastAttempt.results.totalScore.toFixed(1)} / ${lastAttempt.results.maxScore}`
    : "—";

  return (
    <div className="stack">
      <div className="card hero-card">
        <div className="card-body stack">
          <h1 className="h1">Student-Friendly CyberEdu Quiz (Modules 1–4)</h1>
          <p className="lead">
            This app contains all 94 questions from CyberEdu v1.1 (Feb 2017), translated to English,
            with added explanations. Your progress is stored locally in your browser (no backend).
          </p>
          <p className="lead">
            Note: the original PDF states some answers can be debatable depending on interpretation.
            This app provides recommended answers for learning and self-testing.
          </p>
          <div className="row hero-pills">
            <span className="pill">94 questions (1..94)</span>
            <span className="pill">Modules 1–4</span>
            <span className="pill">Spaced review built-in</span>
            <span className="pill">Local-first (private)</span>
          </div>
          <div className="row cta-row">
            <Link className="btn primary" to="/learn">
              Start Learn Mode
            </Link>
            <Link className="btn primary" to="/test">
              {inProgress ? "Resume Test" : "Start Test Mode"}
            </Link>
            <Link className="btn" to="/review">
              Review Queue {dueCount ? `(${dueCount} due)` : ""}
            </Link>
            <button className="btn" type="button" onClick={() => actions.exportResults()}>
              Export results (JSON)
            </button>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-body stack">
          <h2 style={{ margin: 0 }}>Recommended study flow</h2>
          <div className="grid cols-2 path-grid">
            <div className="path-step">
              <div className="path-step-title">1) Learn the concept</div>
              <p className="lead">
                Open Learn Mode, pick a module, and use theory cards and hints before answering.
              </p>
              <Link className="btn" to="/learn">
                Open Learn
              </Link>
            </div>
            <div className="path-step">
              <div className="path-step-title">2) Run a focused test</div>
              <p className="lead">
                Start with a single module, then move to full exam mode once your basics are stable.
              </p>
              <Link className="btn" to="/test">
                Open Test
              </Link>
            </div>
            <div className="path-step">
              <div className="path-step-title">3) Review weak areas</div>
              <p className="lead">
                Incorrect answers are auto-scheduled with spaced repetition for long-term memory.
              </p>
              <Link className="btn" to="/review">
                Open Review
              </Link>
            </div>
            <div className="path-step">
              <div className="path-step-title">4) Track and export</div>
              <p className="lead">
                Export attempts and scores as JSON for study logs or teacher follow-up.
              </p>
              <button className="btn" type="button" onClick={() => actions.exportResults()}>
                Export results
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="grid cols-2">
        <div className="kpi">
          <div className="value">{questions.length}</div>
          <div className="label">Questions</div>
        </div>
        <div className="kpi">
          <div className="value">{attempts.length}</div>
          <div className="label">Attempts saved</div>
        </div>
        <div className="kpi">
          <div className="value">{lastScore}</div>
          <div className="label">Latest score</div>
        </div>
        <div className="kpi">
          <div className="value">{dueCount}</div>
          <div className="label">Due for review</div>
        </div>
      </div>

      <div className="card">
        <div className="card-body stack">
          <h2 style={{ margin: 0 }}>What you can do</h2>
          <ul className="feature-list">
            <li>
              <strong>Learn</strong>: browse modules, read theory cards by tag, and practice each
              question with hints and explanations.
            </li>
            <li>
              <strong>Test</strong>: run the full 94-question exam or a per-module test, with an
              optional timer and a score breakdown by module and tag.
            </li>
            <li>
              <strong>Review</strong>: incorrect answers are scheduled for spaced repetition (+10
              min, +1 day, +3 days).
            </li>
          </ul>
          <div className="row">
            <Link className="btn ghost" to="/attribution">
              License and attribution
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
