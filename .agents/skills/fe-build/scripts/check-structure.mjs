// FE 구조 검사 — 규칙은 ../references/structure.md. 의존성 없이 Node만 쓴다.
// 사용: node .agents/skills/fe-build/scripts/check-structure.mjs <앱 src 경로>
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";

const RULES_DOC = ".agents/skills/fe-build/references/structure.md";
const FLAT_FILE_LIMIT = 15;
const CODE_FILE = /\.(tsx?|jsx?)$/;
const SKIP_FILE = /\.d\.ts$|\.(test|spec)\.[jt]sx?$/;
const SKIP_DIRS = new Set(["node_modules", "assets", "styles", "test", "tests", "__tests__", "__mocks__"]);
const LAYER_DIRS = new Set(["components", "hooks", "lib", "api", "types"]);
const ALLOWED = {
  components: ["components", "hooks", "lib", "types"],
  hooks: ["hooks", "api", "lib", "types"],
  api: ["api", "lib", "types"],
  lib: ["lib", "types"],
  types: ["types"],
};
const NO_REACT = new Set(["api", "lib"]);
const PASCAL = /^[A-Z][A-Za-z0-9]*$/;
const HOOK = /^use[A-Z][A-Za-z0-9]*$/;

const srcArg = process.argv[2];
if (!srcArg || !existsSync(srcArg) || !statSync(srcArg).isDirectory()) {
  console.error("사용: node .agents/skills/fe-build/scripts/check-structure.mjs <앱 src 경로>");
  process.exit(2);
}
const srcAbs = path.resolve(srcArg);
const errors = [];
const warnings = [];

const toPosix = (p) => p.split(path.sep).join("/");
const display = (abs) => toPosix(path.relative(process.cwd(), abs));
const report = (list, abs, line, message) => list.push({ where: `${display(abs)}:${line}`, file: display(abs), line, message });
const byLocation = (a, b) => a.file.localeCompare(b.file) || a.line - b.line;

function walk(dir) {
  const files = [];
  for (const name of readdirSync(dir)) {
    if (name.startsWith(".")) continue;
    const abs = path.join(dir, name);
    if (statSync(abs).isDirectory()) {
      if (!SKIP_DIRS.has(name)) files.push(...walk(abs));
    } else if (CODE_FILE.test(name) && !SKIP_FILE.test(name)) {
      files.push(abs);
    }
  }
  return files;
}

// src 기준 상대 경로(확장자 없음)를 { scope: "shared" | feature 이름, layer } 로 분류한다.
function classify(rel) {
  const parts = rel.split("/");
  if (parts[0] === "features") {
    if (parts.length <= 2) return { scope: parts[1] ?? "", layer: "page" };
    const inner = parts.slice(2);
    if (LAYER_DIRS.has(inner[0])) return { scope: parts[1], layer: inner[0] };
    return { scope: parts[1], layer: inner.length === 1 ? "page" : "unknown" };
  }
  if (LAYER_DIRS.has(parts[0])) return { scope: "shared", layer: parts[0] };
  return { scope: "shared", layer: parts.length === 1 ? "app" : "unknown" };
}

function stripComments(text) {
  const blank = (m) => m.replace(/[^\n]/g, " ");
  return text.replace(/\/\*[\s\S]*?\*\//g, blank).replace(/(^|[^:"'`])\/\/[^\n]*/g, (m, p) => p + blank(m.slice(p.length)));
}

function lineAt(text, index) {
  return text.slice(0, index).split("\n").length;
}

function findImports(text) {
  const patterns = [
    /(?:^|[;\s])(?:import|export)\s[^;]*?\bfrom\s*(["'])([^"']+)\1/g,
    /(?:^|[;\s])import\s*(["'])([^"']+)\1/g,
    /\bimport\(\s*(["'])([^"']+)\1\s*\)/g,
  ];
  const found = new Map();
  for (const pattern of patterns) {
    for (const match of text.matchAll(pattern)) {
      const index = match.index + match[0].lastIndexOf(match[2]);
      found.set(index, { spec: match[2], line: lineAt(text, index) });
    }
  }
  return [...found.values()];
}

// import 대상: 패키지면 { external }, src 밖이면 { outside }, 코드가 아닌 파일이면 null.
function resolveImport(spec, fromAbs) {
  let target;
  if (spec.startsWith("@/")) target = path.join(srcAbs, spec.slice(2));
  else if (spec.startsWith(".")) target = path.resolve(path.dirname(fromAbs), spec);
  else return { external: spec };
  const ext = path.extname(spec);
  if (ext && !CODE_FILE.test(spec)) return null;
  const rel = toPosix(path.relative(srcAbs, target));
  if (rel.startsWith("..")) return { outside: true };
  return { target: classify(ext ? rel.slice(0, -ext.length) : rel) };
}

function importError(from, to) {
  if (from.layer === "unknown" || to.layer === "unknown") return null; // 위치 오류로 이미 보고됨
  if (to.layer === "app") return from.layer === "app" && from.scope === "shared" ? null : "App·main은 다른 파일이 import하지 않는다";
  if (to.scope !== "shared") {
    if (from.scope === "shared") {
      if (from.layer !== "app") return "공용 코드는 feature를 import하지 않는다";
      return to.layer === "page" ? null : `App은 feature의 루트 화면만 import한다 (features/${to.scope}/${to.layer})`;
    }
    if (from.scope !== to.scope) return `feature끼리 import하지 않는다 (${from.scope} → ${to.scope}), 함께 쓰면 공용으로 올린다`;
  }
  if (from.layer === "app" || from.layer === "page") return null;
  if (to.layer === "page") return "feature 화면은 App만 import한다";
  if (!ALLOWED[from.layer].includes(to.layer)) return `${from.layer}는 ${to.layer}를 import하지 않는다`;
  return null;
}

function checkPlacement(abs, rel, where, text) {
  const parts = rel.split("/");
  const base = parts[parts.length - 1];
  const stem = base.replace(/\.[^.]+$/, "");
  const isTsx = /\.[jt]sx$/.test(base);
  const exportsName = (name) => new RegExp(`\\bexport\\s+(?:async\\s+)?(?:function|const|class)\\s+${name}\\b`).test(text);

  if (stem === "index") report(errors, abs, 1, "index 재수출 파일(barrel)을 만들지 않는다, 진입은 main.tsx");
  if (where.layer === "unknown") {
    const dir = parts.slice(0, -1).join("/");
    report(errors, abs, 1, `구조에 없는 폴더(${dir}) — 위치 표를 따른다 (components·hooks·lib·api·types)`);
  }
  if (where.layer === "app" && !["App", "main", "index"].includes(stem)) {
    report(errors, abs, 1, "src 바로 아래 코드 파일은 main·App·api·types만 둔다");
  }
  if (where.layer === "page" && !isTsx) {
    report(errors, abs, 1, "feature 루트에는 화면 .tsx와 api·types만 둔다");
  }
  if (where.layer === "components" && !isTsx) {
    report(errors, abs, 1, "components에는 컴포넌트(.tsx)만 둔다, 계산·상수는 lib/");
  }
  if ((where.layer === "components" || where.layer === "page") && isTsx && stem !== "index") {
    if (!PASCAL.test(stem)) report(errors, abs, 1, `컴포넌트 파일 이름은 PascalCase (${base})`);
    else if (!exportsName(stem)) report(errors, abs, 1, `파일 이름과 같은 이름(${stem})으로 named export한다`);
  }
  if (where.layer === "hooks") {
    if (!HOOK.test(stem)) report(errors, abs, 1, `훅 파일 이름은 useX (${base})`);
    else if (!exportsName(stem)) report(errors, abs, 1, `파일 이름과 같은 이름(${stem})으로 named export한다`);
  }
}

const files = walk(srcAbs);
for (const abs of files) {
  const rel = toPosix(path.relative(srcAbs, abs));
  const where = classify(rel.replace(/\.[^.]+$/, ""));
  const text = stripComments(readFileSync(abs, "utf8"));

  checkPlacement(abs, rel, where, text);

  const defaultExport = text.search(/\bexport\s+default\b|\bas\s+default\b/);
  if (defaultExport >= 0) report(errors, abs, lineAt(text, defaultExport), "export default 대신 named export");

  for (const { spec, line } of findImports(text)) {
    const resolved = resolveImport(spec, abs);
    if (resolved === null) continue;
    if (resolved.outside) {
      report(errors, abs, line, `src 밖을 import하지 않는다 (${spec})`);
    } else if (resolved.external) {
      const isReact = /^react(-dom)?(\/|$)/.test(resolved.external);
      if (isReact && NO_REACT.has(where.layer)) report(errors, abs, line, `${where.layer}는 ${resolved.external}를 import하지 않는다`);
    } else {
      const message = importError(where, resolved.target);
      if (message) report(errors, abs, line, `${message} (${spec})`);
    }
  }
}

const featuresDir = path.join(srcAbs, "features");
const features = existsSync(featuresDir)
  ? readdirSync(featuresDir).filter((name) => statSync(path.join(featuresDir, name)).isDirectory())
  : [];
const layout = features.length > 0 ? `features(${features.join(", ")})` : "flat";
if (features.length === 0 && files.length > FLAT_FILE_LIMIT) {
  report(warnings, srcAbs, 0, `코드 파일 ${files.length}개 > ${FLAT_FILE_LIMIT} — features 전환 여부를 D-n으로 정한다 (structure.md 4절)`);
}

console.log(`[구조 검사] src=${display(srcAbs)}  구조=${layout}  코드 파일=${files.length}`);
for (const item of errors.sort(byLocation)) console.log(`ERROR ${item.where}  ${item.message}`);
for (const item of warnings) console.log(`WARN  ${item.file}  ${item.message}`);
const verdict = errors.length === 0 ? "PASS" : "FAIL";
console.log(`결과: ${verdict} (오류 ${errors.length}, 경고 ${warnings.length}) — 규칙: ${RULES_DOC}`);
process.exit(errors.length === 0 ? 0 : 1);
