// -*- coding: utf-8 -*-
// Script quét chuỗi tiếng Việt KHÔNG DẤU trong mã nguồn.
import { readFileSync, readdirSync } from 'fs';
import { join, relative, extname } from 'path';
// Chạy: node scripts/check_vietnamese.mjs (từ thư mục gốc dự án, không cần cài thêm)
// Thoát mã khác 0 nếu phát hiện chuỗi vi phạm.
//
// Nghiêm túc: chỉ quét các CHUỖI NGUYÊN TỪ (string literal) trong:
//   frontend/src  (*.vue, *.js)
//   backend/app   (*.py)
// Bỏ qua: tên biến/hàm/class/import/route/key JSON (chúng không nằm trong string literal),
//         URL, comment, file tạm/node_modules/.git/dist/__pycache__/.pytest_cache.
//
// Cách kiểm tra: xóa comment, trích toàn bộ chuỗi trong nháy đơn/nháy kép/template literal,
// rồi quét mẫu tiếng Việt không dấu với ranh giới từ (\b).
//
// ALLOWLIST: các chuỗi được phép pese (ví dụ mã lỗi/backend key cố định). Thêm vào mảng
// dưới đây kèm chú thích tại sao được phép. Mỗi phần tử là một RegExp hoặc chuỗi con.
const ALLOWLIST = [
  // Ví dụ (để trống nếu không cần):
  // /legacy\-message\-without\-dau/, // lý do: ...
];

const EXTENSIONS = { '.vue': true, '.js': true, '.py': true };

const SKIP_DIRS = new Set([
  'node_modules', '.git', 'dist', 'build', '.pytest_cache', '__pycache__',
  'instance', 'migrations', 'tests', 'scripts', 'uploads',
]);

// Mẫu tiếng Việt không dấu, ranh giới từ. Dùng /i để bắt cả hoa/thường.
// Từng mẫu là một cụm (có thể nhiều từ) để giảm dương tính giả.
const PATTERNS = [
  { re: /\bco\s+loi\b/i, label: '"Co loi"' },
  { re: /\bthu\s+lai\b/i, label: '"Thu lai"' },
  { re: /\bkhong\b/i, label: 'khong' },
  { re: /\bdang\s+nhap\b/i, label: 'Dang nhap' },
  { re: /\bdang\s+ky\b/i, label: 'Dang ky' },
  { re: /\bmat\s+khau\b/i, label: 'Mat khau' },
  { re: /\btai\s+khoan\b/i, label: 'Tai khoan' },
  { re: /\bda\s+ton\s+tai\b/i, label: 'da ton tai' },
  { re: /\bchinh\s+xac\b/i, label: 'chinh xac' },
  { re: /\bten\s+dang\b/i, label: 'Ten dang' },
  { re: /\bbo\s+de\b/i, label: 'Bo de' },
  { re: /\bgiao\s+vien\b/i, label: 'Giao vien' },
  { re: /\btrang\s+chu\b/i, label: 'Trang chu' },
  { re: /\bhoac\b/i, label: 'hoac' },
];

const ROOT = process.cwd();

// Xóa comment trước khi trích chuỗi (giúp giảm dương tính giả).
function stripComments(code, isPy) {
  let out = code;
  // HTML comment
  out = out.replace(/<!--[\s\S]*?-->/g, '');
  if (isPy) {
    // Python docstring """...""" va '''...'''
    out = out.replace(/"""[\s\S]*?"""/g, '');
    out = out.replace(/'''[\s\S]*?'''/g, '');
    // Python comment # den cuoi hang (khong xoa trong chuoi - da xoa docstring o tren)
    out = out.replace(/#[^\n]*/g, '');
  } else {
    // JS /* ... */
    out = out.replace(/\/\*[\s\S]*?\*\//g, '');
    // JS // den cuoi hang
    out = out.replace(/\/\/[^\n]*/g, '');
  }
  return out;
}

// Trích các string literal (nháy đơn, nháy kép, template literal).
const STRING_RE = /'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"|`(?:[^`\\]|\$\{[^}]*\}|\\.)*`/g;

function isUrlLike(s) {
  // Bo qua duong dan / URL
  return /^[\w+\-]+:\/\//.test(s) || s.startsWith('/') || s.endsWith('.vue') || s.endsWith('.js') || s.endsWith('.py');
}

function allowed(s) {
  return ALLOWLIST.some((a) => (a instanceof RegExp ? a.test(s) : s.includes(a)));
}

function scanFile(absPath, relPath, isPy) {
  const code = readFileSync(absPath, 'utf8');
  const cleaned = stripComments(code, isPy);
  const findings = [];
  let match;
  STRING_RE.lastIndex = 0;
  while ((match = STRING_RE.exec(cleaned)) !== null) {
    const raw = match[0];
    // Lấy nội dung trong ngoài (bỏ đi dấu ngoai bao quanh) để kiểm tra.
    let inner = raw;
    if (raw.startsWith('`') && raw.endsWith('`')) inner = raw.slice(1, -1);
    else if ((raw.startsWith("'") && raw.endsWith("'")) || (raw.startsWith('"') && raw.endsWith('"'))) inner = raw.slice(1, -1);
    if (isUrlLike(inner)) continue;
    if (allowed(inner)) continue;
    const line = cleaned.slice(0, match.index).split('\n').length;
    for (const p of PATTERNS) {
      if (p.re.test(inner)) {
        findings.push({ line, label: p.label, snippet: inner.slice(0, 80) });
        break; // một chuỗi chỉ báo 1 lần
      }
    }
  }
  return findings;
}

function walk(dir, results) {
  let entries;
  try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch (_) { return; }
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (SKIP_DIRS.has(entry.name)) continue;
      walk(full, results);
    } else {
      const ext = path.extname(entry.name).toLowerCase();
      if (!EXTENSIONS[ext]) continue;
      // Chỉ quét frontend/src và backend/app
      const rel = path.relative(ROOT, full);
      if (!rel.startsWith('frontend/src') && !rel.startsWith('backend/app')) continue;
      const isPy = ext === '.py';
      const findings = scanFile(full, rel, isPy);
      for (const f of findings) {
        results.push(`${rel}:${f.line}: [${f.label}] ${f.snippet}`);
      }
    }
  }
}

const results = [];
walk(ROOT, results);

if (results.length > 0) {
  console.error('PHAT HIEN CHUOI TIENG VIET KHONG DAU:');
  results.forEach((r) => console.error('  ' + r));
  console.error(`\nTong so vi pham: ${results.length}`);
  process.exit(1);
} else {
  console.log('SA CHU: khong tim thay chuoi tieng Viet khong dau trong frontend/src va backend/app.');
  process.exit(0);
}
