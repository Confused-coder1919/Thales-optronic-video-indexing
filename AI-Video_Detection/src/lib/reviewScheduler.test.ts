import { describe, expect, it } from "vitest";
import { REVIEW_INTERVALS_MS, advanceAfterCorrect, resetAfterWrong, scheduleAfterWrong } from "./reviewScheduler";

describe("reviewScheduler", () => {
  it("schedules +10 minutes after a wrong answer", () => {
    const now = 1_700_000_000_000;
    const it0 = scheduleAfterWrong(42, now);
    expect(it0.id).toBe(42);
    expect(it0.stage).toBe(0);
    expect(it0.nextDue).toBe(now + REVIEW_INTERVALS_MS[0]);
  });

  it("advances stages on correct answers and removes after stage 2", () => {
    const now = 1_700_000_000_000;
    const it0 = scheduleAfterWrong(1, now);

    const it1 = advanceAfterCorrect(it0, now + 1000);
    expect(it1?.stage).toBe(1);
    expect(it1?.nextDue).toBe(now + 1000 + REVIEW_INTERVALS_MS[1]);

    const it2 = advanceAfterCorrect(it1!, now + 2000);
    expect(it2?.stage).toBe(2);
    expect(it2?.nextDue).toBe(now + 2000 + REVIEW_INTERVALS_MS[2]);

    const it3 = advanceAfterCorrect(it2!, now + 3000);
    expect(it3).toBeNull();
  });

  it("resets to stage 0 after a wrong answer", () => {
    const now = 1_700_000_000_000;
    const base = { id: 5, stage: 2 as const, nextDue: now - 1, updatedAt: now - 1 };
    const reset = resetAfterWrong(base, now);
    expect(reset.stage).toBe(0);
    expect(reset.nextDue).toBe(now + REVIEW_INTERVALS_MS[0]);
  });
});

