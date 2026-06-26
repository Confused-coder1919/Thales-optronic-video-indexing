import type { AnswerValue, Question } from "../types";

function toggleInArray(xs: string[], x: string): string[] {
  return xs.includes(x) ? xs.filter((v) => v !== x) : [...xs, x];
}

function formatChoiceKeyList(keys: string[]): string {
  return keys.length ? keys.join(", ") : "—";
}

export default function QuestionView(props: {
  question: Question;
  answer: AnswerValue | undefined;
  onAnswer: (next: AnswerValue) => void;
  disabled?: boolean;
  reveal?: boolean;
}) {
  const { question, answer, onAnswer, disabled, reveal } = props;

  return (
    <div className="stack">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div className="pill">
          Q{question.id} · Module {question.module} · <span className="muted">{question.type}</span>
        </div>
        <div className="row">
          {question.tags.slice(0, 4).map((t) => (
            <span key={t} className="pill">
              {t}
            </span>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="card-body stack">
          <div style={{ fontWeight: 800, fontSize: "1.05rem" }}>{question.prompt_en}</div>

          {question.type !== "free_text" && question.choices ? (
            <fieldset style={{ border: "0", padding: 0, margin: 0 }} disabled={disabled}>
              <legend className="muted" style={{ fontWeight: 700 }}>
                Choose {question.type === "mcq_single" ? "one" : "one or more"} option(s).
              </legend>
              <div className="stack" style={{ gap: 8 }}>
                {question.choices.map((c) => {
                  const selected =
                    answer?.type === "mcq" ? answer.selected.includes(c.key) : false;
                  const inputType = question.type === "mcq_single" ? "radio" : "checkbox";
                  const name = `q-${question.id}`;
                  const correctKeys = new Set(question.correct ?? []);
                  const showCorrect = reveal && correctKeys.has(c.key);

                  return (
                    <label
                      key={c.key}
                      style={{
                        display: "flex",
                        gap: 10,
                        alignItems: "flex-start",
                        padding: "10px 12px",
                        borderRadius: 12,
                        border: "1px solid var(--border)",
                        background: showCorrect ? "var(--accent-soft)" : "rgba(255,255,255,0.7)",
                      }}
                    >
                      <input
                        type={inputType}
                        name={name}
                        value={c.key}
                        checked={selected}
                        onChange={() => {
                          const prev = answer?.type === "mcq" ? answer.selected : [];
                          const nextSelected =
                            question.type === "mcq_single" ? [c.key] : toggleInArray(prev, c.key);
                          onAnswer({ type: "mcq", selected: nextSelected });
                        }}
                      />
                      <div>
                        <div style={{ fontWeight: 800 }}>
                          {c.key.toUpperCase()}{" "}
                          {reveal && correctKeys.has(c.key) ? (
                            <span className="badge" style={{ marginLeft: 6 }}>
                              correct
                            </span>
                          ) : null}
                        </div>
                        <div className="muted">{c.text_en}</div>
                      </div>
                    </label>
                  );
                })}
              </div>
            </fieldset>
          ) : null}

          {question.type === "free_text" ? (
            <div className="stack">
              <div className="field">
                <label htmlFor={`notes-${question.id}`}>Your notes / draft answer (optional)</label>
                <textarea
                  id={`notes-${question.id}`}
                  value={answer?.type === "free_text" ? answer.notes : ""}
                  disabled={disabled}
                  onChange={(e) => {
                    const prev = answer?.type === "free_text" ? answer.achievedPoints : [];
                    onAnswer({ type: "free_text", notes: e.target.value, achievedPoints: prev });
                  }}
                />
              </div>

              {question.rubric ? (
                <fieldset style={{ border: "0", padding: 0, margin: 0 }} disabled={disabled}>
                  <legend style={{ fontWeight: 800 }}>Self-check rubric</legend>
                  <div className="stack" style={{ gap: 8 }}>
                    {question.rubric.required_points.map((p) => {
                      const checked =
                        answer?.type === "free_text" ? answer.achievedPoints.includes(p) : false;
                      return (
                        <label
                          key={p}
                          style={{
                            display: "flex",
                            gap: 10,
                            alignItems: "flex-start",
                            padding: "10px 12px",
                            borderRadius: 12,
                            border: "1px solid var(--border)",
                            background: checked ? "rgba(15,118,110,0.08)" : "rgba(255,255,255,0.7)",
                          }}
                        >
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={() => {
                              const prev = answer?.type === "free_text" ? answer.achievedPoints : [];
                              const next = toggleInArray(prev, p);
                              const notes = answer?.type === "free_text" ? answer.notes : "";
                              onAnswer({ type: "free_text", notes, achievedPoints: next });
                            }}
                          />
                          <span className="muted">{p}</span>
                        </label>
                      );
                    })}
                  </div>

                  {reveal ? (
                    <div className="card" style={{ boxShadow: "none" }}>
                      <div className="card-body stack">
                        <div style={{ fontWeight: 800 }}>Sample answer</div>
                        <div className="muted">{question.rubric.sample_answer_en}</div>
                      </div>
                    </div>
                  ) : null}
                </fieldset>
              ) : null}
            </div>
          ) : null}

          {reveal && question.type !== "free_text" ? (
            <div className="card" style={{ boxShadow: "none" }}>
              <div className="card-body stack">
                <div style={{ fontWeight: 800 }}>Correct answer</div>
                <div className="muted">{formatChoiceKeyList(question.correct ?? [])}</div>
              </div>
            </div>
          ) : null}

          {reveal ? (
            <div className="card" style={{ boxShadow: "none" }}>
              <div className="card-body stack">
                <div style={{ fontWeight: 800 }}>Why</div>
                <div className="muted">{question.explanation_en}</div>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

