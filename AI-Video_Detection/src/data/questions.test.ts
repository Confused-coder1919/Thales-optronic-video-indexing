import { describe, expect, it } from "vitest";
import { questions } from "./questions";

describe("questions dataset", () => {
  it("contains exactly 94 questions with IDs 1..94 (unique)", () => {
    expect(questions).toHaveLength(94);
    const ids = questions.map((q) => q.id).sort((a, b) => a - b);
    expect(ids[0]).toBe(1);
    expect(ids[ids.length - 1]).toBe(94);
    for (let i = 1; i <= 94; i++) expect(ids[i - 1]).toBe(i);
  });

  it("has coherent shapes for MCQ vs free-text questions", () => {
    for (const q of questions) {
      expect([1, 2, 3, 4]).toContain(q.module);
      expect(q.prompt_en.length).toBeGreaterThan(0);
      expect(q.source_ref.length).toBeGreaterThan(0);
      expect(q.tags.length).toBeGreaterThan(0);

      if (q.type === "free_text") {
        expect(q.rubric).toBeTruthy();
        expect(q.rubric?.required_points.length).toBeGreaterThan(0);
        expect(q.rubric?.sample_answer_en.length).toBeGreaterThan(0);
        expect(q.correct).toBeUndefined();
      } else {
        expect(q.choices?.length).toBeGreaterThan(1);
        expect(q.correct?.length).toBeGreaterThan(0);
        expect(q.rubric).toBeUndefined();
      }
    }
  });
});

