import { useSyncExternalStore } from "react";
import { questions } from "../data/questions";
import { downloadJson } from "../lib/download";
import { scheduleAfterWrong, advanceAfterCorrect, resetAfterWrong } from "../lib/reviewScheduler";
import { scoreAttempt } from "../lib/scoring";
import type {
  AnswerValue,
  Attempt,
  InProgressTest,
  ModuleId,
  ReviewItem,
} from "../types";

type LearnProgress = {
  module?: ModuleId;
  questionId?: number;
};

export type AppState = {
  attempts: Attempt[];
  reviewQueue: Record<number, ReviewItem>;
  inProgressTest?: InProgressTest;
  learn: LearnProgress;
};

const STORAGE_KEY = "cyberedu-quiz:v1";

const defaultState: AppState = {
  attempts: [],
  reviewQueue: {},
  inProgressTest: undefined,
  learn: {},
};

function safeParse(json: string): unknown {
  try {
    return JSON.parse(json);
  } catch {
    return null;
  }
}

function loadState(): AppState {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return defaultState;
  const parsed = safeParse(raw);
  if (!parsed || typeof parsed !== "object") return defaultState;
  const p = parsed as Partial<AppState>;
  return {
    attempts: Array.isArray(p.attempts) ? (p.attempts as Attempt[]) : [],
    reviewQueue: p.reviewQueue && typeof p.reviewQueue === "object" ? (p.reviewQueue as Record<number, ReviewItem>) : {},
    inProgressTest: p.inProgressTest as InProgressTest | undefined,
    learn: p.learn && typeof p.learn === "object" ? (p.learn as LearnProgress) : {},
  };
}

function saveState(state: AppState): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

let state: AppState = defaultState;
let initialized = false;
const listeners = new Set<() => void>();

function ensureInit(): void {
  if (initialized) return;
  initialized = true;
  state = loadState();
}

function emit(): void {
  for (const l of listeners) l();
}

function setState(next: AppState): void {
  state = next;
  saveState(state);
  emit();
}

export function getAppState(): AppState {
  ensureInit();
  return state;
}

export function useAppStore<T>(selector: (s: AppState) => T): T {
  ensureInit();
  return useSyncExternalStore(
    (cb) => {
      listeners.add(cb);
      return () => listeners.delete(cb);
    },
    () => selector(state),
    () => selector(state),
  );
}

function questionIdsForScope(scope: "all" | { module: ModuleId }): number[] {
  if (scope === "all") return questions.map((q) => q.id);
  return questions.filter((q) => q.module === scope.module).map((q) => q.id);
}

export const actions = {
  startTest(scope: "all" | { module: ModuleId }, opts: { timerEnabled: boolean; durationMs?: number }): string {
    ensureInit();
    const id = crypto.randomUUID();
    const startedAt = Date.now();
    const questionIds = questionIdsForScope(scope);
    const inProgressTest: InProgressTest = {
      id,
      scope,
      startedAt,
      timerEnabled: opts.timerEnabled,
      durationMs: opts.durationMs,
      questionIds,
      answers: {},
    };
    setState({ ...state, inProgressTest });
    return id;
  },

  abandonTest(): void {
    ensureInit();
    if (!state.inProgressTest) return;
    setState({ ...state, inProgressTest: undefined });
  },

  setTestAnswer(questionId: number, value: AnswerValue): void {
    ensureInit();
    const s = state.inProgressTest;
    if (!s) return;
    setState({
      ...state,
      inProgressTest: {
        ...s,
        answers: { ...s.answers, [questionId]: value },
      },
    });
  },

  submitTest(): string | null {
    ensureInit();
    const s = state.inProgressTest;
    if (!s) return null;
    const finishedAt = Date.now();
    const results = scoreAttempt(questions, s.questionIds, s.answers);

    // Schedule review for any missed question: +10m, +1d, +3d.
    const now = finishedAt;
    const nextQueue: Record<number, ReviewItem> = { ...state.reviewQueue };
    for (const qid of results.missedQuestionIds) {
      const existing = nextQueue[qid];
      nextQueue[qid] = existing ? resetAfterWrong(existing, now) : scheduleAfterWrong(qid, now);
    }

    const attempt: Attempt = {
      id: s.id,
      mode: "test",
      scope: s.scope,
      startedAt: s.startedAt,
      finishedAt,
      timerEnabled: s.timerEnabled,
      durationMs: s.durationMs,
      answers: s.answers,
      results,
    };

    setState({
      ...state,
      attempts: [attempt, ...state.attempts],
      reviewQueue: nextQueue,
      inProgressTest: undefined,
    });

    return attempt.id;
  },

  scheduleReviewFromIncorrect(questionId: number): void {
    ensureInit();
    const now = Date.now();
    const existing = state.reviewQueue[questionId];
    const item = existing ? resetAfterWrong(existing, now) : scheduleAfterWrong(questionId, now);
    setState({
      ...state,
      reviewQueue: { ...state.reviewQueue, [questionId]: item },
    });
  },

  recordReviewResult(questionId: number, isCorrect: boolean): void {
    ensureInit();
    const now = Date.now();
    const existing = state.reviewQueue[questionId];
    if (!existing) {
      // Defensive: if user reviews a question not in the queue, treat it as newly wrong.
      if (!isCorrect) {
        setState({
          ...state,
          reviewQueue: { ...state.reviewQueue, [questionId]: scheduleAfterWrong(questionId, now) },
        });
      }
      return;
    }

    if (!isCorrect) {
      setState({
        ...state,
        reviewQueue: { ...state.reviewQueue, [questionId]: resetAfterWrong(existing, now) },
      });
      return;
    }

    const advanced = advanceAfterCorrect(existing, now);
    if (!advanced) {
      const rest = { ...state.reviewQueue };
      delete rest[questionId];
      setState({ ...state, reviewQueue: rest });
      return;
    }

    setState({
      ...state,
      reviewQueue: { ...state.reviewQueue, [questionId]: advanced },
    });
  },

  setLearnLocation(module: ModuleId, questionId?: number): void {
    ensureInit();
    setState({ ...state, learn: { module, questionId } });
  },

  exportResults(): void {
    ensureInit();
    const exportedAt = new Date().toISOString();
    const safeStamp = exportedAt.replace(/[:.]/g, "-");
    downloadJson(`cyberedu-quiz-results-${safeStamp}.json`, {
      exportedAt,
      attempts: state.attempts,
    });
  },
};

export function getDueReviewIds(now: number): number[] {
  ensureInit();
  return Object.values(state.reviewQueue)
    .filter((it) => it.nextDue <= now)
    .sort((a, b) => a.nextDue - b.nextDue)
    .map((it) => it.id);
}
