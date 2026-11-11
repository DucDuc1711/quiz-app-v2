// -*- coding: utf-8 -*-
// Script quy ước mã nguồn cho Quiz App v2 (không cần cài thêm).
// Chạy: node scripts/check_conventions.mjs (từ thư mục gốc dự án)
// FAIL nếu trong frontend/src (*.vue, *.js, kể cả test):
//   - Có "{ toast }" (destructure sai useToast)
//   - Có destructure từ useToast() (mẫu "= useToast()" đi sau dấu "}")
//   - Có "const { success" hoặc "const { error" từ useToast (trừ ToastHost.vue)
// Thoát mã khác 0 nếu phát hiện vi phạm.
import { readFileSync, readdirSync } from 'fs';
import { join, relative, extname } from 'path';

const ROOT = process.cwd();
const EXTENSIONS = { '.vue': true, '.js': true };
const SKIP_DIRS = new Set([
  'node_modules', '.git', 'dist', 'build', '.pytest_cache', '__pycache__',
  'instance', 'migrations', 'tests', 'scripts', 'uploads', '.vite',
]);

// ToastHost.vue ĐƯỢC PHÉP dùng { toasts, remove } (không trùng tên biến khác).
const ALLOWED_FILES = new Set(['frontend/src/components/ToastHost.vue']);

function scanFile(absPath, relPath) {
  const code = readFileSync(absPath, 'utf8');
  const findings = [];
  const lines = code.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // Bỏ qua comment dòng
    if (trimmed.startsWith('//')) continue;

    // 1. "{ toast }" (không có dấu phẩy sau toast, tức destructure đơn isolate)
    if (/\{\s*toast\s*\}/.test(trimmed)) {
      findings.push({ line: i + 1, label: '{ toast }', snippet: trimmed });
      continue;
    }

    // 2. Destructure từ useToast(): mẫu "... = useToast()" đi sau dấu "}"
    // Bất kỳ destructure nào từ useToast() ngoài ToastHost đều vi phạm.
    if (/\}\s*=\s*useToast\(\)/.test(trimmed)) {
      if (!ALLOWED_FILES.has(relPath)) {
        findings.push({ line: i + 1, label: 'destructure useToast()', snippet: trimmed });
      }
      continue;
    }

    // 3. const { success, ... } hoặc const { error, ... } (từ useToast)
    // Kiểm tra nếu dòng chứa "const {" và "success" hoặc "error" trước "useToast"
    if (/const\s*\{\s*(success|error)\s*[},]/.test(trimmed)) {
      findings.push({ line: i + 1, label: 'destructure success/error', snippet: trimmed });
    }
  }
  return findings;
}

function walk(dir, results) {
  let entries;
  try { entries = readdirSync(dir, { withFileTypes: true }); } catch (_) { return; }
  for (const entry of entries) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) {
      if (SKIP_DIRS.has(entry.name)) continue;
      walk(full, results);
    } else {
      const ext = extname(entry.name).toLowerCase();
      if (!EXTENSIONS[ext]) continue;
      const rel = relative(ROOT, full);
      if (!rel.startsWith('frontend/src')) continue;
      const findings = scanFile(full, rel);
      for (const f of findings) {
        results.push(`${rel}:${f.line}: [${f.label}] ${f.snippet}`);
      }
    }
  }
}

const results = [];
walk(ROOT, results);

if (results.length > 0) {
  console.error('PHẠM QUY ƯỚC MÃ NGUỒN (check_conventions.mjs):');
  results.forEach((r) => console.error('  ' + r));
  console.error(`\nTổng số vi phạm: ${results.length}`);
  process.exit(1);
} else {
  console.log('SẠCH: không vi phạm quy ước toast trong frontend/src.');
  process.exit(0);
}