#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { TextDecoder } from 'node:util';

const TEXT_EXTENSIONS = new Set([
  '.cjs', '.css', '.html', '.js', '.json', '.jsx', '.md', '.mdc', '.mjs',
  '.ps1', '.py', '.ts', '.tsx', '.txt', '.vue', '.yaml', '.yml',
]);
const IGNORED_DIRS = new Set([
  '.git', '.pytest_cache', '.playwright-cli', 'dist', 'node_modules', 'output',
  'scratch', 'tmp', 'venv',
]);
const MOJIBAKE_MARKERS = [
  '\u951b', '\u9286', '\u9225', '\u99a3',
  '\u9242', '\u923d', '\u8133', '\u95bf',
];
const MAX_REPORTED_FINDINGS = 100;

const targets = process.argv.slice(2);
if (!targets.length) {
  console.error('Usage: node check-text-integrity.mjs <file-or-directory> [...]');
  process.exit(2);
}

function collectFiles(target, files) {
  const resolved = path.resolve(target);
  if (!fs.existsSync(resolved)) {
    throw new Error(`Path does not exist: ${target}`);
  }
  const stat = fs.statSync(resolved);
  if (stat.isFile()) {
    files.push(resolved);
    return;
  }
  for (const entry of fs.readdirSync(resolved, { withFileTypes: true })) {
    if (entry.isDirectory() && IGNORED_DIRS.has(entry.name)) continue;
    const child = path.join(resolved, entry.name);
    if (entry.isDirectory()) {
      collectFiles(child, files);
    } else if (entry.isFile() && TEXT_EXTENSIONS.has(path.extname(entry.name).toLowerCase())) {
      files.push(child);
    }
  }
}

function lineNumber(text, index) {
  return text.slice(0, index).split('\n').length;
}

function maskMarkdownCode(text, extension) {
  if (extension !== '.md' && extension !== '.mdc') return text;
  const preserveLines = (value) => value.replace(/[^\n]/g, ' ');
  return text
    .replace(/```[\s\S]*?```/g, preserveLines)
    .replace(/`[^`\n]*`/g, preserveLines);
}

function inspectFile(file) {
  const bytes = fs.readFileSync(file);
  const findings = [];

  if (
    (bytes[0] === 0xff && bytes[1] === 0xfe)
    || (bytes[0] === 0xfe && bytes[1] === 0xff)
  ) {
    findings.push({ severity: 'error', kind: 'utf16-bom', line: 1 });
    return findings;
  }

  let text;
  try {
    text = new TextDecoder('utf-8', { fatal: true }).decode(bytes);
  } catch (error) {
    findings.push({
      severity: 'error',
      kind: 'invalid-utf8',
      line: null,
      detail: error.message,
    });
    return findings;
  }

  if (bytes[0] === 0xef && bytes[1] === 0xbb && bytes[2] === 0xbf) {
    findings.push({ severity: 'warning', kind: 'utf8-bom', line: 1 });
  }

  const patterns = [
    { kind: 'replacement-character', severity: 'error', regex: /\uFFFD/g },
    { kind: 'c1-control', severity: 'error', regex: /[\u0080-\u009F]/g },
    { kind: 'private-use-character', severity: 'warning', regex: /[\uE000-\uF8FF]/g },
    {
      kind: 'cjk-adjacent-question-mark',
      severity: 'warning',
      regex: /(?:[\u3400-\u9FFF]\?[\u3400-\u9FFF]|[\u3400-\u9FFF]\?(?=[，。；：、）】』」]))/g,
    },
  ];

  for (const pattern of patterns) {
    for (const match of text.matchAll(pattern.regex)) {
      findings.push({
        severity: pattern.severity,
        kind: pattern.kind,
        line: lineNumber(text, match.index),
        sample: match[0],
      });
    }
  }

  const markerText = maskMarkdownCode(text, path.extname(file).toLowerCase());
  for (const marker of MOJIBAKE_MARKERS) {
    let index = markerText.indexOf(marker);
    while (index !== -1) {
      findings.push({
        severity: 'error',
        kind: 'mojibake-marker',
        line: lineNumber(text, index),
        sample: marker,
      });
      index = markerText.indexOf(marker, index + marker.length);
    }
  }

  return findings;
}

const files = [];
try {
  for (const target of targets) collectFiles(target, files);
} catch (error) {
  console.error(error.message);
  process.exit(2);
}

const results = files.map((file) => {
  const findings = inspectFile(file);
  return {
    file: path.relative(process.cwd(), file) || file,
    errorCount: findings.filter((item) => item.severity === 'error').length,
    warningCount: findings.filter((item) => item.severity === 'warning').length,
    findings: findings.slice(0, MAX_REPORTED_FINDINGS),
    omittedFindings: Math.max(0, findings.length - MAX_REPORTED_FINDINGS),
  };
});
const errorCount = results.reduce(
  (count, result) => count + result.errorCount,
  0,
);
const warningCount = results.reduce(
  (count, result) => count + result.warningCount,
  0,
);

process.stdout.write(`${JSON.stringify({
  filesScanned: files.length,
  errorCount,
  warningCount,
  results: results.filter((result) => result.errorCount || result.warningCount),
}, null, 2)}\n`);
process.exitCode = errorCount ? 1 : 0;
