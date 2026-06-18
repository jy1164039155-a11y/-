---
name: encoding-mojibake-guard
description: Prevents, diagnoses, and safely recovers UTF-8/GBK mojibake and encoding-corrupted source files without overwriting good code. Use when Chinese text appears garbled, U+FFFD or literal question marks appear, PowerShell Set-Content/Out-File touched a source file, a large Unicode file needs rewriting, a mixed pre/post-incident patch must be analyzed, or a recovered Vue/JS/Markdown file builds but may still fail at runtime.
---

# Encoding Mojibake Guard

Protect Unicode source files with a byte-first, candidate-only workflow. Never auto-repair the only copy of a damaged file.

## Core Rules

1. Treat terminal rendering as evidence, not byte truth.
2. Stop writing as soon as corruption is suspected.
3. Preserve the current file, Git state, patches, logs, and timestamps.
4. Never apply a mixed pre-incident/post-incident patch as one unit.
5. Never infer lost `?` or U+FFFD characters from mojibake mapping alone.
6. Recover into a temporary candidate and promote only after the full validation ladder passes.
7. Build success is insufficient; verify runtime rendering and console errors.

## Workflow

### 1. Freeze And Preserve

- Stop feature work and automated rewrites.
- Copy the affected file to a timestamped backup.
- Record `git status`, `git diff`, the current commit, file size, and hash.
- Keep patches immutable as recovery evidence.

Do not use `Set-Content`, `Out-File`, redirection, `echo`, or heredocs to rewrite the formal Unicode source.

### 2. Establish Byte Truth

Run the read-only scanner:

```powershell
node .cursor/skills/encoding-mojibake-guard/scripts/check-text-integrity.mjs frontend/src/App.vue
```

Distinguish:

- invalid UTF-8 bytes;
- reversible UTF-8-as-GBK mojibake;
- U+FFFD replacement characters;
- literal `?` loss;
- syntax delimiters or whole definitions that disappeared;
- console-only display corruption.

If a terminal view and the strict decoder disagree, trust the bytes and decoder.

### 3. Split The Incident Timeline

Classify every source or patch hunk:

- known good before the incident;
- produced by the damaging write;
- manual repair after the incident;
- later valid business changes.

Only pre-incident clean material is an authoritative recovery source. Post-incident edits may contain useful clues but must not be replayed blindly.

### 4. Rank Recovery Sources

Use this order:

1. clean same-version source or checkpoint;
2. pre-incident patch hunks for new code;
3. clean source maps or built bundles;
4. stable code skeleton in the damaged file;
5. manual semantic reconstruction as a last resort.

When current code contains newer business logic, match by variable names, tags, attributes, indentation, and neighboring statements. Replace damaged text or delimiters without rolling back unrelated logic.

### 5. Build A Candidate

- Work only on a temporary candidate.
- Use `apply_patch` for small deterministic edits.
- For bulk recovery, write an explicitly UTF-8 temporary file and compare its diff before promotion.
- Keep an unresolved list instead of guessing.
- Repair compiler-reported syntax failures one confirmed location at a time.

Never perform automatic global character replacement on the formal file.

### 6. Run The Validation Ladder

Run every applicable level in order:

1. strict UTF-8 decode and mojibake scan;
2. parser/SFC/compiler check;
3. structural contract checks;
4. production build;
5. focused regression tests;
6. real browser smoke test;
7. browser console must have zero errors;
8. final Git diff and file-size review.

For this project:

```powershell
node .cursor/skills/encoding-mojibake-guard/scripts/check-text-integrity.mjs frontend/src/App.vue
node .cursor/skills/encoding-mojibake-guard/scripts/check-vue-form-contract.mjs frontend/src/App.vue
node tmp/check_vue_candidate.js frontend/src/App.vue
npm --prefix frontend run build
```

If the affected code participates in first render, open a fresh browser session. A nonblank snapshot and zero console errors are required.

### 7. Promote Safely

- Back up the formal file immediately before replacement.
- Replace it only after the candidate passes all checks.
- Re-run the checks against the formal path.
- Keep recovery artifacts until the Git commit is verified.
- Document root cause, failed approaches, sources used, and prevention controls.

## Common Rationalizations

| Rationalization | Reality |
| --- | --- |
| "Only emoji and punctuation look wrong." | Full Chinese blocks, quotes, tags, or state definitions may also be damaged. Scan and compile the whole file. |
| "The patch has everything, so apply it." | A patch spanning the incident boundary mixes valid work and contaminated repairs. Split it first. |
| "A token map fixed most lines." | Token maps cannot restore literal `?`, U+FFFD, deleted syntax, or missing definitions. |
| "The build passed." | Vue can still crash on first render because a referenced state field is undefined. |
| "PowerShell shows mojibake, so the file is corrupt." | The console may be decoding incorrectly. Verify bytes with a strict decoder. |
| "I will test on the formal file because it is faster." | A second overwrite can destroy the last recoverable evidence. Use a candidate. |

## Red Flags

- A whole-file Unicode rewrite without an explicit encoding and candidate file;
- hundreds of unrelated changed lines after a small edit;
- file size changes unexpectedly;
- `Set-Content`, `Out-File`, `>` or heredoc appears in the write path;
- U+FFFD or CJK-adjacent `?`;
- a mixed patch is described as directly reversible;
- verification stops after a build;
- the page is not opened after recovering first-render Vue state.

## Verification

- [ ] Evidence and timestamped backup preserved
- [ ] Incident boundary identified
- [ ] Recovery sources ranked
- [ ] Formal file not modified during exploration
- [ ] Strict UTF-8 scan passes
- [ ] Suspicious markers are explained or removed
- [ ] Parser/compiler passes
- [ ] Structural reference checks pass
- [ ] Build and focused tests pass
- [ ] Browser renders and console has zero errors
- [ ] Final diff contains only intended changes

Read `02_Process/App.vue乱码修复记录与编码规范.md` for the full project incident record.
