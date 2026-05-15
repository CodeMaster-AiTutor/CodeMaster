/**
 * smoke_tests.js — Smoke Testing
 * Quick sanity checks to verify all core functions are alive and responsive.
 * Each test must complete in < 200ms.
 */

const { describe, it, before } = require("node:test");
const assert = require("node:assert/strict");

const { validatePassword, createToken, verifyToken, validateEmail } = require("./authLogic");
const { sanitizeCode, extractClassName, parseCompilerError, willTimeout } = require("./compilerLogic");
const { buildChatMessages, sanitizeChatInput, isAssignmentQuestion, estimateTokens } = require("./aiLogic");
const { computeStreak, aggregateTopicStats, calculateAccuracy } = require("./progressLogic");
const { validateExportOptions, buildFileName, getContentType, renderReportData } = require("./exportLogic");

// ─────────────────────────────────────────────
// SMOKE SUITE 1 — Auth Module
// ─────────────────────────────────────────────
describe("SMOKE-01 Auth Module", () => {
  it("SM-A01: validatePassword returns valid for strong password", () => {
    const r = validatePassword("Hello@123");
    assert.equal(r.valid, true);
  });

  it("SM-A02: validatePassword rejects short password", () => {
    const r = validatePassword("Hi@1");
    assert.equal(r.valid, false);
  });

  it("SM-A03: createToken returns a JWT string", () => {
    const tok = createToken({ userId: "u1", role: "student" }, "testsecret");
    assert.equal(typeof tok, "string");
    assert.equal(tok.split(".").length, 3);
  });

  it("SM-A04: verifyToken round-trips successfully", () => {
    const tok = createToken({ userId: "u2" }, "smokekey");
    const payload = verifyToken(tok, "smokekey");
    assert.equal(payload.userId, "u2");
  });

  it("SM-A05: validateEmail accepts valid email", () => {
    assert.equal(validateEmail("student@college.edu"), true);
  });
});

// ─────────────────────────────────────────────
// SMOKE SUITE 2 — Compiler Module
// ─────────────────────────────────────────────
describe("SMOKE-02 Compiler Module", () => {
  it("SM-C01: sanitizeCode allows safe Java code", () => {
    const r = sanitizeCode('public class Hello { public static void main(String[] a){System.out.println("Hi");}}');
    assert.equal(r.safe, true);
  });

  it("SM-C02: sanitizeCode blocks Runtime.getRuntime()", () => {
    const r = sanitizeCode("Runtime.getRuntime().exec(\"ls\");");
    assert.equal(r.safe, false);
  });

  it("SM-C03: extractClassName returns correct name", () => {
    assert.equal(extractClassName("public class Fibonacci {"), "Fibonacci");
  });

  it("SM-C04: willTimeout detects infinite loop", () => {
    assert.equal(willTimeout("while(true){ }"), true);
  });

  it("SM-C05: parseCompilerError returns empty for no errors", () => {
    assert.deepEqual(parseCompilerError(""), []);
  });
});

// ─────────────────────────────────────────────
// SMOKE SUITE 3 — AI Module
// ─────────────────────────────────────────────
describe("SMOKE-03 AI Module", () => {
  it("SM-I01: buildChatMessages returns array with system + user", () => {
    const msgs = buildChatMessages([], "What is recursion?");
    assert.ok(Array.isArray(msgs));
    assert.equal(msgs[0].role, "system");
    assert.equal(msgs[msgs.length - 1].role, "user");
  });

  it("SM-I02: sanitizeChatInput trims whitespace", () => {
    assert.equal(sanitizeChatInput("  hello  "), "hello");
  });

  it("SM-I03: isAssignmentQuestion detects homework", () => {
    assert.equal(isAssignmentQuestion("solve my homework: sort array"), true);
  });

  it("SM-I04: estimateTokens returns positive integer", () => {
    const t = estimateTokens("Hello world");
    assert.ok(t > 0);
  });
});

// ─────────────────────────────────────────────
// SMOKE SUITE 4 — Progress Module
// ─────────────────────────────────────────────
describe("SMOKE-04 Progress Module", () => {
  it("SM-P01: computeStreak returns 0 for empty array", () => {
    assert.equal(computeStreak([]), 0);
  });

  it("SM-P02: computeStreak returns positive for recent dates", () => {
    const today = new Date().toISOString();
    const s = computeStreak([today]);
    assert.ok(s >= 1);
  });

  it("SM-P03: aggregateTopicStats returns array with topic entry", () => {
    const r = aggregateTopicStats([{ topic: "Arrays", isCorrect: true }]);
    assert.ok(Array.isArray(r));
    assert.ok(r.some(x => x.topic === "Arrays"));
  });

  it("SM-P04: calculateAccuracy returns correct percentage", () => {
    assert.equal(calculateAccuracy(7, 10), 70);
  });
});

// ─────────────────────────────────────────────
// SMOKE SUITE 5 — Export Module
// ─────────────────────────────────────────────
describe("SMOKE-05 Export Module", () => {
  it("SM-E01: validateExportOptions passes for valid options", () => {
    const errs = validateExportOptions({ format: "docx" });
    assert.equal(errs.length, 0);
  });

  it("SM-E02: buildFileName returns string with student name", () => {
    const fn = buildFileName("Alice", "docx");
    assert.ok(fn.includes("Alice"));
  });

  it("SM-E03: getContentType returns correct MIME for docx", () => {
    assert.ok(getContentType("docx").includes("wordprocessingml"));
  });

  it("SM-E04: renderReportData returns title field", () => {
    const data = renderReportData(
      { name: "Bob", email: "bob@test.com" },
      { totalSolved: 10, totalAttempted: 12, accuracy: 83, streak: 5, topicBreakdown: [] }
    );
    assert.ok(data.title.includes("Bob"));
  });
});
