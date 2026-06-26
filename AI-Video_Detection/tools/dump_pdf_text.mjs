import fs from "node:fs";
import path from "node:path";
import { PDFParse } from "pdf-parse";

const pdfPath = process.argv[2] ?? "source.pdf";
const outPath = process.argv[3] ?? "tools/cyberedu_quiz.txt";

const absPdfPath = path.resolve(pdfPath);
const absOutPath = path.resolve(outPath);
if (!fs.existsSync(absPdfPath)) {
  console.error(`PDF not found: ${absPdfPath}`);
  console.error(`Usage: node tools/dump_pdf_text.mjs /path/to/source.pdf tools/cyberedu_quiz.txt`);
  process.exit(1);
}

const buf = fs.readFileSync(absPdfPath);
const parser = new PDFParse({ data: buf });
const data = await parser.getText();
await parser.destroy();

fs.writeFileSync(absOutPath, data.text, "utf8");
console.log(`Wrote ${data.text.length} chars to ${absOutPath}`);
