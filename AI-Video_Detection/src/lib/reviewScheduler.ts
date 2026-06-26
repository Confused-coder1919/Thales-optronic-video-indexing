import type { ReviewItem } from "../types";

export const REVIEW_INTERVALS_MS = [
  10 * 60 * 1000, // 10 minutes
  24 * 60 * 60 * 1000, // 1 day
  3 * 24 * 60 * 60 * 1000, // 3 days
] as const;

export function scheduleAfterWrong(questionId: number, now: number): ReviewItem {
  return {
    id: questionId,
    stage: 0,
    nextDue: now + REVIEW_INTERVALS_MS[0],
    updatedAt: now,
  };
}

export function advanceAfterCorrect(item: ReviewItem, now: number): ReviewItem | null {
  if (item.stage === 0) {
    return { ...item, stage: 1, nextDue: now + REVIEW_INTERVALS_MS[1], updatedAt: now };
  }
  if (item.stage === 1) {
    return { ...item, stage: 2, nextDue: now + REVIEW_INTERVALS_MS[2], updatedAt: now };
  }
  return null; // stage 2 answered correctly => mastered (remove from queue)
}

export function resetAfterWrong(item: ReviewItem, now: number): ReviewItem {
  return { ...item, stage: 0, nextDue: now + REVIEW_INTERVALS_MS[0], updatedAt: now };
}

export function isDue(item: ReviewItem, now: number): boolean {
  return item.nextDue <= now;
}

