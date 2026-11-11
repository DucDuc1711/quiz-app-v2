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

// Các file view có tham số route (router khai báo :id nhưng view đọc tên prop khác -> vi phạm).
const VIEW_DIRS = ['frontend/src/views/teacher', 'frontend/src/views/student'];

function scanFile(absPath, relPath) {
  const code = readFileSync(absPath, 'utf8');
  const findings = [];
  const lines = code.split('\n');
  const isView = VIEW_DIRS.some((d) => relPath.startsWith(d));

  // Trích tên prop khai báo qua defineProps(['...', '...']) hoặc defineProps({ ... })
  const propNames = new Set();
  const mProps = code.match(/defineProps\s*\(\s*\[([^\]]*)\]/);
  if (mProps) {
    for (const p of mProps[1].split(',')) {
      const name = p.trim().replace(/['"]/g, '');
      if (name) propNames.add(name);
    }
  }
  const mPropsObj = code.match(/defineProps\s*\(\s*\{([^}]*)\}/);
  if (mPropsObj) {
    for (const part of mPropsObj[1].split(',')) {
      const name = part.trim().split(':')[0].replace(/['"]/g, '');
      if (name) propNames.add(name);
    }
  }

  // Trích tên tham số route được ĐỌC: route.params.<tên> hoặc params.<tên>
  const readParams = new Set();
  for (const rm of code.matchAll(/route\.params\.([a-zA-Z_]\w*)/g)) readParams.add(rm[1]);
  for (const rm of code.matchAll(/\bparams\.([a-zA-Z_]\w*)/g)) readParams.add(rm[1]);

  if (isView && readParams.size > 0) {
    // Nếu đọc params.<tên> mà tên đó không có trong prop khai báo -> ngắt khớp
    for (const p of readParams) {
      if (!propNames.has(p)) {
        findings.push({
          line: 1,
          label: 'route-param-mismatch',
          snippet: `đọc params.${p} nhưng props khai báo: ${[...propNames].join(', ') || '(không có)'}`,
        });
        break; // một file chỉ báo 1 lần
      }
    }
  }

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
  console.log('SẠCH: không vi phạm quy ước toast và route-param trong frontend/src.');
  process.exit(0);
}