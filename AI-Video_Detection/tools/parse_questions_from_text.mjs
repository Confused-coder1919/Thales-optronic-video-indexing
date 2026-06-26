import fs from "node:fs";

const inPath = process.argv[2] ?? "tools/cyberedu_quiz.txt";
const outPath = process.argv[3] ?? "tools/questions_fr.json";

const raw = fs.readFileSync(inPath, "utf8");
const lines = raw.split(/\r?\n/);

function isNoise(line) {
  const t = line.trim();
  if (!t) return true;
  if (/^-- \d+ of \d+ --$/.test(t)) return true;
  if (/^CyberEdu version\b/.test(t)) return true;
  if (/^Quizz de sensibilisation\b/.test(t)) return true;
  if (/^Ce document pédagogique\b/.test(t)) return true;
  if (/^professionnels du secteur de la cybersécurité/i.test(t)) return true;
  if (/^Il est mis à disposition\b/.test(t)) return true;
  if (/^Version 1\.1\b/.test(t)) return true;
  return false;
}

function pushJoined(arr, line) {
  const t = line.trim();
  if (!t) return;
  // Join simple end-of-line hyphenation artifacts (e.g. "trans-" + "mis").
  if (
    arr.length > 0 &&
    /[\p{L}]-$/u.test(arr[arr.length - 1]) &&
    /^[\p{Ll}]/u.test(t)
  ) {
    arr[arr.length - 1] = arr[arr.length - 1].slice(0, -1) + t;
    return;
  }
  arr.push(t);
}

function cleanText(parts) {
  return parts
    .join(" ")
    .replace(/\s+/g, " ")
    .replace(/\s+([;:?!.,)\]])/g, "$1")
    .replace(/\(\s+/g, "(")
    .trim();
}

let currentModule = 0;
let current = null;
let mode = "none"; // prompt | choices
let currentChoice = null;
const questions = [];

function flushChoice() {
  if (!currentChoice) return;
  current.choices.push({
    key: currentChoice.key,
    text_fr: cleanText(currentChoice.textParts),
  });
  currentChoice = null;
}

function flushQuestion() {
  if (!current) return;
  flushChoice();
  const prompt_fr = cleanText(current.promptParts);
  questions.push({
    id: current.id,
    module: current.module,
    prompt_fr,
    choices: current.choices.length ? current.choices : undefined,
  });
  current = null;
  mode = "none";
}

for (let idx = 0; idx < lines.length; idx++) {
  const line = lines[idx];
  const t = line.trim();

  const mMod = /^\d+\s+Quizz pour le module\s+(\d+)/.exec(t);
  if (mMod) {
    // Module headings appear between questions; make sure we don't
    // accidentally append the heading continuation line to the last choice.
    flushQuestion();
    currentModule = Number.parseInt(mMod[1], 10);
    continue;
  }

  const mQ = /^(\d+)\.\s*(.*)$/.exec(t);
  if (mQ) {
    flushQuestion();
    current = {
      id: Number.parseInt(mQ[1], 10),
      module: currentModule,
      promptParts: [],
      choices: [],
    };
    mode = "prompt";
    const rest = mQ[2].trim();
    if (rest) pushJoined(current.promptParts, rest);
    continue;
  }

  if (!current) continue;
  if (isNoise(line)) continue;

  if (/^Réponses possibles\s*:/.test(t)) {
    mode = "choices";
    continue;
  }

  if (mode === "prompt") {
    pushJoined(current.promptParts, t);
    continue;
  }

  if (mode === "choices") {
    const mC = /^([a-z])\.\s*(.*)$/.exec(t);
    if (mC) {
      flushChoice();
      currentChoice = { key: mC[1], textParts: [] };
      const rest = mC[2].trim();
      if (rest) pushJoined(currentChoice.textParts, rest);
      continue;
    }
    if (currentChoice) {
      pushJoined(currentChoice.textParts, t);
    } else {
      // Unexpected line in choices block; treat as prompt continuation.
      pushJoined(current.promptParts, t);
    }
  }
}

flushQuestion();

fs.writeFileSync(outPath, JSON.stringify({ questions }, null, 2), "utf8");
console.log(`Parsed ${questions.length} questions -> ${outPath}`);
const ids = questions.map((q) => q.id).sort((a, b) => a - b);
console.log(`ID range: ${ids[0]}..${ids[ids.length - 1]}`);
