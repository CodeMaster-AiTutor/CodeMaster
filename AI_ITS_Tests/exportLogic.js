/**
 * exportLogic.js — Export service logic (DOCX generation testable without DB)
 */

const path = require("path");

// ── Validate export options ───────────────────────────────────────────────
function validateExportOptions(options) {
  const errors = [];
  if (!options) return ["Options object is required"];
  if (!["pdf", "docx"].includes(options.format))
    errors.push("format must be 'pdf' or 'docx'");
  if (options.dateFrom && options.dateTo) {
    if (new Date(options.dateFrom) > new Date(options.dateTo))
      errors.push("dateFrom must be before dateTo");
  }
  return errors;
}

// ── Build filename ────────────────────────────────────────────────────────
function buildFileName(studentName, format) {
  const safe = studentName.replace(/[^a-zA-Z0-9]/g, "_");
  const ts   = new Date().toISOString().slice(0, 10);
  return `${safe}_Progress_Report_${ts}.${format}`;
}

// ── Content type resolver ──────────────────────────────────────────────────
function getContentType(format) {
  if (format === "pdf")  return "application/pdf";
  if (format === "docx") return "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
  return "application/octet-stream";
}

// ── Render HTML report (template data injection) ──────────────────────────
function renderReportData(studentData, summary) {
  return {
    title:        `Progress Report — ${studentData.name}`,
    generated:    new Date().toLocaleDateString("en-IN"),
    student:      studentData.name,
    email:        studentData.email,
    totalSolved:  summary.totalSolved,
    totalAttempted: summary.totalAttempted,
    accuracy:     `${summary.accuracy}%`,
    streak:       summary.streak,
    topics:       summary.topicBreakdown || [],
  };
}

// ── Minimal DOCX generation test (uses docx library) ─────────────────────
async function generateMinimalDOCX(reportData) {
  const { Document, Packer, Paragraph, TextRun, HeadingLevel } = require("docx");
  const doc = new Document({
    sections: [{
      children: [
        new Paragraph({
          heading: HeadingLevel.HEADING_1,
          children: [new TextRun({ text: reportData.title, bold: true })]
        }),
        new Paragraph({
          children: [new TextRun(`Student: ${reportData.student}`)]
        }),
        new Paragraph({
          children: [new TextRun(`Problems Solved: ${reportData.totalSolved} / ${reportData.totalAttempted}`)]
        }),
        new Paragraph({
          children: [new TextRun(`Accuracy: ${reportData.accuracy}`)]
        }),
        new Paragraph({
          children: [new TextRun(`Current Streak: ${reportData.streak} days`)]
        }),
        new Paragraph({
          children: [new TextRun(`Generated: ${reportData.generated}`)]
        }),
      ]
    }]
  });
  const buffer = await Packer.toBuffer(doc);
  return buffer;
}

module.exports = {
  validateExportOptions,
  buildFileName,
  getContentType,
  renderReportData,
  generateMinimalDOCX,
};
