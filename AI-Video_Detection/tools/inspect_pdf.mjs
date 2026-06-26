import fs from "node:fs";
import path from "node:path";
import { PDFParse } from "pdf-parse";

const pdfPath = process.argv[2] ?? "source.pdf";

const absPath = path.resolve(pdfPath);
if (!fs.existsSync(absPath)) {
  console.error(`PDF not found: ${absPath}`);
  console.error(`Usage: node tools/inspect_pdf.mjs /path/to/source.pdf`);
  process.exit(1);
}
const buf = fs.readFileSync(absPath);

const parser = new PDFParse({ data: buf });
const data = await parser.getText();
await parser.destroy();

console.log(`File: ${absPath}`);
console.log(`Pages: ${data.total}`);
console.log("---- TEXT (first 4000 chars) ----");
console.log(data.text.slice(0, 4000));
