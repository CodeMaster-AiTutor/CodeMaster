/**
 * aiLogic.js — AI service logic (prompt building, response validation)
 * No Ollama/network calls needed — tests pure logic.
 */

const SYSTEM_PROMPT = `You are CodeMaster AI, an expert Java programming tutor.
You help students understand programming concepts clearly and patiently.
When a student shows code, analyze it carefully. Always provide examples in Java.
Keep explanations concise and beginner-friendly.
Never write complete assignments for students — guide them with hints instead.`;

// ── Build error explanation prompt ────────────────────────────────────────
function buildErrorPrompt(code, errorMessage) {
  if (!code || typeof code !== "string") throw new Error("code is required");
  if (!errorMessage || typeof errorMessage !== "string" || !errorMessage.trim())
    throw new Error("Error message is required");

  return `You are a helpful Java programming tutor.
A student wrote the following Java code:

${code}

The compiler returned this error:
${errorMessage}

Please explain what this error means in simple terms,
identify exactly where in the code the problem is,
and provide a corrected version of the relevant line(s).
Be concise and use beginner-friendly language.`;
}

// ── Build multi-turn chat messages array ──────────────────────────────────
function buildChatMessages(history, newMessage) {
  if (!newMessage || !newMessage.trim()) throw new Error("Message cannot be empty");
  const messages = [
    { role: "system", content: SYSTEM_PROMPT },
    ...history.slice(-10),   // keep last 10 turns for context window
    { role: "user", content: newMessage.trim() },
  ];
  return messages;
}

// ── Validate AI response isn't empty ─────────────────────────────────────
function validateAIResponse(response) {
  if (!response || typeof response !== "string") return false;
  if (response.trim().length < 10) return false;
  return true;
}

// ── Check if a message asks for complete assignment solution ──────────────
function isAssignmentRequest(message) {
  const lower = message.toLowerCase();
  const triggers = [
    "write complete code",
    "do my assignment",
    "complete solution",
    "full code for assignment",
    "write full program for",
    "solve my homework",
  ];
  return triggers.some(t => lower.includes(t));
}

// ── Input sanitisation — strip code injection from chat ──────────────────
function sanitizeChatInput(message) {
  if (!message || typeof message !== "string") return "";
  // Remove any attempt to override system prompt
  return message
    .replace(/ignore\s+previous\s+instructions/gi, "[removed]")
    .replace(/system\s*:/gi, "[removed]")
    .trim()
    .slice(0, 2000);    // max 2000 chars
}

// ── Alias for backward compatibility ─────────────────────────────────────
const isAssignmentQuestion = isAssignmentRequest;

// ── Estimate token count (approx 4 chars per token) ──────────────────────
function estimateTokens(text) {
  if (!text || typeof text !== "string") return 0;
  return Math.ceil(text.length / 4);
}

module.exports = {
  buildErrorPrompt,
  buildChatMessages,
  validateAIResponse,
  isAssignmentRequest,
  isAssignmentQuestion,
  sanitizeChatInput,
  estimateTokens,
  SYSTEM_PROMPT,
};
