---
name: encoding-mojibake-guard
description: 检测并修复源码/文档中的 mojibake（乱码），并在编辑中文内容时强制 UTF-8 工作流。当用户提到乱码、garbled text、mojibake、编码错误、UTF-8/GBK，或在 Windows 下编辑含中文的 Vue/JS/md 文件时使用。
user-invocable: true
---

# 防乱码守护（Mojibake Guard）

本技能沉淀自 `frontend/src/App.vue` 的 19 处乱码修复事件，目标是**预防乱码回归**并提供**标准化的检测/修复流程**。

## 何时使用

- 用户报告界面或文档出现乱码 / garbled text / `�`；
- 在 Windows/PowerShell 环境编辑含中文的源码、Vue 模板、md 文档；
- 提交前需要确认改动文件没有引入乱码。

## 工作流

### 1. 准备：强制 UTF-8 终端

```powershell
chcp 65001
$OutputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

### 2. 检测：扫描乱码

优先用项目内脚本：

```bash
node tmp/scan_pollution3.js frontend/src/App.vue
```

需广覆盖时，扫描以下区段（任一命中即为可疑）：
- `U+FFFD`（替换符 `�`）
- C1 控制符 `U+0080–U+009F`
- PUA `U+E000–U+F8FF`
- 常见 GBK 误解码引导字 `鍥鍖鐜鈥鉂鎴鍙鐢鏄鐨` 等

目标：可疑行数 = 0。

### 3. 分类：区分功能性 vs 文案

- **功能性乱码**（高危）：模板插值 `图${...}`、正则 `/^图\d+.../`、toast/提示前缀、key/标识符。修复后必须运行时复测。
- **可见文案乱码**（低危）：纯展示文字，修复后构建通过即可。
- **良性项**（不动）：UTF-8 BOM、合法正则量词 `?`。

### 4. 修复

- 用编辑器工具按 UTF-8 写回正确中文，**不要**用 `echo`/重定向/heredoc。
- 逐处对照上下文恢复语义，避免“看起来像”的错字替换。

### 5. 验证（缺一不可）

1. 重跑扫描 → `TOTAL: 0`；
2. `npm run build` 通过、SFC 0 错误；
3. 功能性改动：浏览器实际复测（caption 重排、toast 显示等）。

## 反模式（禁止）

- 用 `echo "中文" > file` 写中文文件（会按终端编码污染）。
- 只看构建通过就认定修复完成（功能性乱码可能潜伏）。
- 把合法 BOM / 正则量词误判为乱码并“修复”。

## 相关文档

- `02_Process/App.vue乱码修复记录与编码规范.md`
- `.cursor/rules/encoding-utf8.mdc`
