/**
 * Severity banding, mirrored from the backend's single source of truth
 * (`backend/app/engine/findings.py::band_severity`). Used only to draw the
 * heatmap's fixed grid: which of the 25 (likelihood, impact) cells is which
 * colour never depends on what is plotted in it, so the mapping is safe to
 * duplicate here rather than fetching it. The banding rule itself
 * (20-25 CRITICAL / 12-19 HIGH / 6-11 MEDIUM / 1-5 LOW) is stated on every
 * finding that uses it, so a change on one side cannot go unnoticed on
 * the other silently. [SCHEMA 3.5]
 */

import type { Severity } from "./api";

export function bandSeverity(riskScore: number): Severity {
  if (riskScore >= 20) return "CRITICAL";
  if (riskScore >= 12) return "HIGH";
  if (riskScore >= 6) return "MEDIUM";
  return "LOW";
}
