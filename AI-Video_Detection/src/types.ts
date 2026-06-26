export type ModuleId = 1 | 2 | 3 | 4;

export type QuestionType = "mcq_single" | "mcq_multi" | "free_text";

export type QuestionChoice = {
  key: string;
  text_en: string;
};

export type FreeTextRubric = {
  required_points: string[];
  sample_answer_en: string;
};

export type Question = {
  id: number; // 1..94 (original numbering)
  module: ModuleId;
  prompt_en: string;
  type: QuestionType;
  choices?: QuestionChoice[];
  correct?: string[]; // choice keys for MCQ
  rubric?: FreeTextRubric; // required for free_text
  explanation_en: string;
  tags: string[];
  source_ref: string;
};

export type AnswerValue =
  | { type: "mcq"; selected: string[] }
  | { type: "free_text"; notes: string; achievedPoints: string[] };

export type InProgressTest = {
  id: string;
  scope: "all" | { module: ModuleId };
  startedAt: number;
  timerEnabled: boolean;
  durationMs?: number;
  questionIds: number[];
  answers: Record<number, AnswerValue>;
};

export type ReviewItem = {
  id: number;
  stage: 0 | 1 | 2;
  nextDue: number; // epoch ms
  updatedAt: number; // epoch ms
};

export type AttemptResults = {
  perQuestion: Record<
    number,
    {
      score: number; // 0..1
      max: number; // always 1 for this quiz
      isCorrect: boolean; // score === 1
    }
  >;
  totalScore: number;
  maxScore: number;
  byModule: Record<
    ModuleId,
    {
      score: number;
      maxScore: number;
      accuracy: number; // 0..1
    }
  >;
  byTag: Record<
    string,
    {
      score: number;
      maxScore: number;
      accuracy: number; // 0..1
      count: number;
    }
  >;
  missedQuestionIds: number[];
};

export type Attempt = {
  id: string;
  mode: "test";
  scope: "all" | { module: ModuleId };
  startedAt: number;
  finishedAt: number;
  timerEnabled: boolean;
  durationMs?: number;
  answers: Record<number, AnswerValue>;
  results: AttemptResults;
};

export type ConceptCard = {
  id: string;
  title_en: string;
  body_en: string;
  tags: string[];
  questionIds: number[]; // 1..3 links
};

