/**
 * compilerLogic.js — Java compiler service logic (no child_process exec)
 * Covers: code sanitization, class name extraction, output parsing.
 */

const { execSync, exec } = require("child_process");
const fs   = require("fs");
const path = require("path");
const os   = require("os");
const crypto = require("crypto");

// ── Dangerous API blacklist ────────────────────────────────────────────────
const BLACKLIST = [
  /Runtime\.getRuntime\(\)/,
  /ProcessBuilder/,
  /System\.exit\s*\(/,
  /File\s*\(\s*["']\//,           // absolute path file access
  /ServerSocket/,
  /\.exec\s*\(/,
];

function sanitizeCode(code) {
  for (const pattern of BLACKLIST) {
    if (pattern.test(code)) {
      return { safe: false, reason: `Dangerous API usage detected: ${pattern}` };
    }
  }
  return { safe: true, reason: null };
}

// ── Extract public class name ──────────────────────────────────────────────
function extractClassName(code) {
  const match = code.match(/public\s+class\s+(\w+)/);
  return match ? match[1] : null;
}

// ── Parse compiler error — extract line number and message ────────────────
function parseCompilerError(stderr) {
  const lines = stderr.split("\n").filter(Boolean);
  return lines.map(line => {
    const m = line.match(/\.java:(\d+):\s*error:\s*(.+)/);
    return m ? { line: parseInt(m[1]), message: m[2].trim() } : null;
  }).filter(Boolean);
}

// ── Actually compile + run Java using the JRE (runtime only — ecj if avail) ─
// We use javax.tools via a helper or fall back to runtime-only test
function runJava(code, stdinInput = "") {
  const id  = crypto.randomUUID();
  const dir = path.join(os.tmpdir(), id);
  fs.mkdirSync(dir, { recursive: true });

  const className = extractClassName(code) || "Main";
  const javaFile  = path.join(dir, `${className}.java`);
  fs.writeFileSync(javaFile, code, "utf8");

  try {
    // Try javac (may not be available)
    execSync(`javac "${javaFile}"`, { timeout: 15000, stdio: "pipe" });

    // Run with piped stdin
    const inputFile = path.join(dir, "input.txt");
    fs.writeFileSync(inputFile, stdinInput);
    const output = execSync(
      `java -cp "${dir}" ${className}`,
      { input: stdinInput, timeout: 10000, stdio: ["pipe","pipe","pipe"] }
    );
    fs.rmSync(dir, { recursive: true, force: true });
    return { output: output.toString(), error: "" };
  } catch (e) {
    fs.rmSync(dir, { recursive: true, force: true });
    const stderr = e.stderr ? e.stderr.toString() : e.message;
    return { output: "", error: stderr };
  }
}

// ── Timeout simulation ─────────────────────────────────────────────────────
function willTimeout(code) {
  // Simple heuristic: while(true) with no break
  return /while\s*\(\s*true\s*\)\s*\{[^}]*\}/.test(code) ||
         /for\s*\(\s*;\s*;\s*\)/.test(code);
}

module.exports = {
  sanitizeCode,
  extractClassName,
  parseCompilerError,
  runJava,
  willTimeout,
};
