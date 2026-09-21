/**
 * Demo engagement identity.
 *
 * Day 1 holds this locally so the shell can render before the API exists.
 * Day 2 replaces it with a fetch from `GET /api/engagements/{id}`.
 */

export const ENGAGEMENT = {
  organisation: "Meridian Financial Services India GCC",
  city: "Bengaluru",
  engagementName: "DPDP + AI Controls Readiness Assessment",
  /**
   * Eighteen months after G.S.R. 846(E) of 13 November 2025, per Rule 1(4).
   * Verified against the MeitY gazette, not a secondary source.
   * [SOURCES.md A1.1]
   */
  complianceDeadline: "2027-05-13",
  isSynthetic: true,
} as const;

export type Role = "consultant" | "client";

export const ROLE_LABEL: Record<Role, string> = {
  consultant: "Consultant",
  client: "Client (CISO / DPO)",
};
