import { describe, expect, it } from "vitest";
import { scoreQuestion } from "./scoring";
import type { AnswerValue, Question } from "../types";

describe("scoreQuestion", () => {
  it("scores MCQ as 1 only when fully correct (set-equality)", () => {
    const q: Question = {
      id: 1,
      module: 1,
      prompt_en: "Pick two",
      type: "mcq_multi",
      choices: [
        { key: "a", text_en: "A" },
        { key: "b", text_en: "B" },
        { key: "c", text_en: "C" },
      ],
      correct: ["a", "c"],
      explanation_en: "x",
      tags: ["t"],
      source_ref: "src",
    };

    const a1: AnswerValue = { type: "mcq", selected: ["c", "a"] };
    expect(scoreQuestion(q, a1).score).toBe(1);

    const a2: AnswerValue = { type: "mcq", selected: ["a"] };
    expect(scoreQuestion(q, a2).score).toBe(0);

    const a3: AnswerValue = { type: "mcq", selected: ["a", "b", "c"] };
    expect(scoreQuestion(q, a3).score).toBe(0);
  });

  it("scores free-text from rubric completion", () => {
    const q: Question = {
      id: 2,
      module: 1,
      prompt_en: "Explain",
      type: "free_text",
      rubric: { required_points: ["p1", "p2"], sample_answer_en: "x" },
      explanation_en: "x",
      tags: ["t"],
      source_ref: "src",
    };

    const a1: AnswerValue = { type: "free_text", notes: "", achievedPoints: ["p1"] };
    expect(scoreQuestion(q, a1).score).toBe(0.5);

    const a2: AnswerValue = { type: "free_text", notes: "", achievedPoints: ["p1", "p2"] };
    expect(scoreQuestion(q, a2).score).toBe(1);
  });
});

