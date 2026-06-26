import type { AnswerValue, AttemptResults, ModuleId, Question } from "../types";

function uniqSorted(xs: string[]): string[] {
  return Array.from(new Set(xs)).sort();
}

function sameSet(a: string[], b: string[]): boolean {
  const aa = uniqSorted(a);
  const bb = uniqSorted(b);
  if (aa.length !== bb.length) return false;
  for (let i = 0; i < aa.length; i++) {
    if (aa[i] !== bb[i]) return false;
  }
  return true;
}

export function scoreQuestion(
  question: Question,
  answer: AnswerValue | undefined,
): { score: number; max: number; isCorrect: boolean } {
  const max = 1;

  if (question.type === "free_text") {
    const required = question.rubric?.required_points ?? [];
    if (!required.length) return { score: 0, max, isCorrect: false };
    const achieved =
      answer?.type === "free_text"
        ? new Set(answer.achievedPoints.filter((p) => required.includes(p)))
        : new Set<string>();
    const score = achieved.size / required.length;
    return { score, max, isCorrect: score === 1 };
  }

  const correct = question.correct ?? [];
  const selected =
    answer?.type === "mcq" ? answer.selected : [];
  const isCorrect = sameSet(selected, correct);
  return { score: isCorrect ? 1 : 0, max, isCorrect };
}

export function scoreAttempt(
  questions: Question[],
  questionIds: number[],
  answers: Record<number, AnswerValue>,
): AttemptResults {
  const byId = new Map<number, Question>(questions.map((q) => [q.id, q]));

  const perQuestion: AttemptResults["perQuestion"] = {};
  let totalScore = 0;
  const maxScore = questionIds.length;

  const byModule: AttemptResults["byModule"] = {
    1: { score: 0, maxScore: 0, accuracy: 0 },
    2: { score: 0, maxScore: 0, accuracy: 0 },
    3: { score: 0, maxScore: 0, accuracy: 0 },
    4: { score: 0, maxScore: 0, accuracy: 0 },
  };

  const byTag: AttemptResults["byTag"] = {};
  const missedQuestionIds: number[] = [];

  for (const id of questionIds) {
    const q = byId.get(id);
    if (!q) continue;
    const r = scoreQuestion(q, answers[id]);
    perQuestion[id] = r;
    totalScore += r.score;

    const mod = q.module as ModuleId;
    byModule[mod].score += r.score;
    byModule[mod].maxScore += r.max;

    for (const tag of q.tags) {
      if (!byTag[tag]) byTag[tag] = { score: 0, maxScore: 0, accuracy: 0, count: 0 };
      byTag[tag].score += r.score;
      byTag[tag].maxScore += r.max;
      byTag[tag].count += 1;
    }

    if (!r.isCorrect) missedQuestionIds.push(id);
  }

  for (const mod of [1, 2, 3, 4] as const) {
    const m = byModule[mod];
    m.accuracy = m.maxScore ? m.score / m.maxScore : 0;
  }
  for (const tag of Object.keys(byTag)) {
    const t = byTag[tag];
    t.accuracy = t.maxScore ? t.score / t.maxScore : 0;
  }

  return { perQuestion, totalScore, maxScore, byModule, byTag, missedQuestionIds };
}

