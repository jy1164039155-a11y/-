import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const [pdfPath, outputDir, modulesRoot] = process.argv.slice(2);
if (!pdfPath || !outputDir || !modulesRoot) {
  throw new Error("Usage: render_pdf_pages.mjs <pdf> <output_dir> <node_modules>");
}

globalThis.DOMMatrix = class DOMMatrix {
  constructor() {
    this.a = 1;
    this.b = 0;
    this.c = 0;
    this.d = 1;
    this.e = 0;
    this.f = 0;
  }
};
globalThis.ImageData = class ImageData {};
globalThis.Path2D = class Path2D {};

const pdfjs = await import(pathToFileURL(path.join(modulesRoot, "pdfjs-dist", "legacy", "build", "pdf.mjs")));
const document = await pdfjs.getDocument({
  data: new Uint8Array(fs.readFileSync(pdfPath)),
  disableWorker: true,
}).promise;

const matches = [];
for (let pageNumber = 1; pageNumber <= document.numPages; pageNumber += 1) {
  const page = await document.getPage(pageNumber);
  const text = (await page.getTextContent()).items.map((item) => item.str || "").join("");
  if (["成本逼近法", "土地取得费", "675.3"].some((needle) => text.includes(needle))) {
    matches.push(pageNumber);
  }
}

const selected = [...new Set(matches.flatMap((pageNumber) => [
  Math.max(1, pageNumber - 1),
  pageNumber,
  Math.min(document.numPages, pageNumber + 1),
]))].sort((a, b) => a - b);

fs.mkdirSync(outputDir, { recursive: true });
console.log(JSON.stringify({ pages: document.numPages, matches, rendered: selected }));
