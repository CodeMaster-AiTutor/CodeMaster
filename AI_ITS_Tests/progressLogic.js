/**
 * progressLogic.js — Dashboard & progress tracking pure logic
 */

// ── Streak calculation ────────────────────────────────────────────────────
function computeStreak(submissionDates) {
  if (!submissionDates || submissionDates.length === 0) return 0;

  // Deduplicate by calendar day, sort newest first
  const uniqueDays = [...new Set(
    submissionDates.map(d => {
      const date = new Date(d);
      return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;
    })
  )].sort().reverse();

  let streak = 0;
  let prev   = new Date();
  prev.setHours(0, 0, 0, 0);

  for (const dayStr of uniqueDays) {
    const curr = new Date(dayStr);
    const diffMs   = prev.getTime() - curr.getTime();
    const diffDays = Math.round(diffMs / 86400000);
    if (diffDays <= 1) {
      streak++;
      prev = curr;
    } else {
      break;
    }
  }
  return streak;
}

// ── Topic accuracy aggregation ────────────────────────────────────────────
function aggregateTopicStats(attempts) {
  const map = {};
  for (const a of attempts) {
    if (!map[a.topic]) map[a.topic] = { total: 0, correct: 0 };
    map[a.topic].total++;
    if (a.isCorrect) map[a.topic].correct++;
  }
  return Object.entries(map).map(([topic, s]) => ({
    topic,
    total:    s.total,
    correct:  s.correct,
    accuracy: parseFloat(((s.correct / s.total) * 100).toFixed(1)),
  }));
}

// ── Overall summary ───────────────────────────────────────────────────────
function computeSummary(attempts) {
  const total   = attempts.length;
  const correct = attempts.filter(a => a.isCorrect).length;
  return {
    totalAttempted: total,
    totalSolved:    correct,
    accuracy:       total > 0 ? parseFloat(((correct / total) * 100).toFixed(1)) : 0,
  };
}

// ── Leaderboard sort ──────────────────────────────────────────────────────
function buildLeaderboard(users, limit = 10) {
  return [...users]
    .sort((a, b) => b.totalSolved - a.totalSolved || a.name.localeCompare(b.name))
    .slice(0, limit)
    .map((u, i) => ({ rank: i + 1, name: u.name, totalSolved: u.totalSolved }));
}

// ── XP calculation ────────────────────────────────────────────────────────
function calculateXP(attempts) {
  return attempts.reduce((xp, a) => {
    if (!a.isCorrect) return xp;
    const base = { easy: 10, medium: 25, hard: 50 }[a.difficulty] || 10;
    return xp + base;
  }, 0);
}

// ── Simple accuracy helper (solved / total * 100) ────────────────────────
function calculateAccuracy(solved, total) {
  if (!total || total === 0) return 0;
  return parseFloat(((solved / total) * 100).toFixed(1));
}

module.exports = {
  computeStreak,
  aggregateTopicStats,
  computeSummary,
  buildLeaderboard,
  calculateXP,
  calculateAccuracy,
};
