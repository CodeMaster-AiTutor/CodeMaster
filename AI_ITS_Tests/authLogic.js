/**
 * authLogic.js — Pure auth business logic (no Express/MongoDB deps)
 * These functions are extracted from authController.js for testability.
 */

// ── Password Validation ────────────────────────────────────────────────────
function validatePassword(password) {
  if (!password || password.length < 8)
    return { valid: false, reason: "Password must be at least 8 characters" };
  if (!/[A-Z]/.test(password))
    return { valid: false, reason: "Password must contain an uppercase letter" };
  if (!/[0-9]/.test(password))
    return { valid: false, reason: "Password must contain a number" };
  if (!/[!@#$%^&*]/.test(password))
    return { valid: false, reason: "Password must contain a special character (!@#$%^&*)" };
  return { valid: true, reason: null };
}

// ── Email Validation ───────────────────────────────────────────────────────
function validateEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}

// ── JWT simulation (base64 encode/decode — mirrors jsonwebtoken structure) ──
function createToken(payload, secret, expiresInDays = 7) {
  const header  = Buffer.from(JSON.stringify({ alg: "HS256", typ: "JWT" })).toString("base64url");
  const exp     = Math.floor(Date.now() / 1000) + expiresInDays * 86400;
  const body    = Buffer.from(JSON.stringify({ ...payload, exp, iat: Math.floor(Date.now() / 1000) })).toString("base64url");
  // Simple HMAC-like signature using crypto
  const crypto  = require("crypto");
  const sig     = crypto.createHmac("sha256", secret).update(`${header}.${body}`).digest("base64url");
  return `${header}.${body}.${sig}`;
}

function verifyToken(token, secret) {
  if (!token || typeof token !== "string") throw new Error("No token provided");
  const parts = token.split(".");
  if (parts.length !== 3) throw new Error("Malformed token");
  const [header, body, sig] = parts;
  const crypto  = require("crypto");
  const expected = crypto.createHmac("sha256", secret).update(`${header}.${body}`).digest("base64url");
  if (sig !== expected) throw new Error("Invalid token signature");
  const payload = JSON.parse(Buffer.from(body, "base64url").toString());
  if (payload.exp < Math.floor(Date.now() / 1000)) throw new Error("Token expired");
  return payload;
}

// ── Registration logic (without DB) ───────────────────────────────────────
function validateRegistration(body) {
  const errors = [];
  if (!body.name || body.name.trim().length < 2)
    errors.push("Name must be at least 2 characters");
  if (!validateEmail(body.email))
    errors.push("Invalid email format");
  const pwCheck = validatePassword(body.password);
  if (!pwCheck.valid)
    errors.push(pwCheck.reason);
  return errors;
}

// ── Bearer token extraction ────────────────────────────────────────────────
function extractBearerToken(authHeader) {
  if (!authHeader || !authHeader.startsWith("Bearer "))
    return null;
  return authHeader.slice(7);
}

module.exports = {
  validatePassword,
  validateEmail,
  createToken,
  verifyToken,
  validateRegistration,
  extractBearerToken,
};
