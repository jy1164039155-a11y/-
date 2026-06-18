#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const target = process.argv[2];
if (!target) {
  console.error('Usage: node check-vue-form-contract.mjs <App.vue>');
  process.exit(2);
}

const file = path.resolve(target);
const source = fs.readFileSync(file, 'utf8');
const marker = 'const form = reactive({';
const start = source.indexOf(marker);
const end = source.indexOf('\n});', start);

if (start === -1 || end === -1) {
  console.error('Could not locate "const form = reactive({...})" in the target file.');
  process.exit(2);
}

const formBlock = source.slice(start, end);
const defined = new Set(
  [...formBlock.matchAll(/^\s{2}([A-Za-z_$][\w$]*):\s*\{/gm)].map((match) => match[1]),
);
const referenced = new Set(
  [...source.matchAll(/\bform\.([A-Za-z_$][\w$]*)\.value\b/g)].map((match) => match[1]),
);
const missing = [...referenced].filter((key) => !defined.has(key)).sort();

process.stdout.write(`${JSON.stringify({
  file: path.relative(process.cwd(), file) || file,
  referencedCount: referenced.size,
  definedCount: defined.size,
  missing,
}, null, 2)}\n`);
process.exitCode = missing.length ? 1 : 0;

