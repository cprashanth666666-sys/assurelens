/**
 * API client.
 *
 * Server Components call these directly during render, so reads happen on the
 * server and the dense tables arrive as HTML rather than as a client-side
 * fetch waterfall. [TRD ADR-002]
 */

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type ControlSummary = {
  ref: string;
  title: string;
  domain: Domain;
  inference_mode: "POPULATION" | "CENSUS";
  is_executable: boolean;
  suite: string | null;
  primary_clause: string | null;
  primary_framework: string | null;
  framework_refs: string[];
  in_scope: boolean;
  na_reason: string | null;
  evidence_owner: string | null;
  primary_source_unverified: boolean;
};

export type ClauseRef = {
  framework_code: string;
  framework_name: string;
  ref: string;
  title: string;
  verbatim_text: string | null;
  in_force_from: string | null;
  source_status: "VERIFIED" | "UNVERIFIED";
  source_note: string | null;
  is_primary: boolean;
  rationale: string | null;
};

export type ControlDetail = ControlSummary & {
  objective: string;
  procedure_text: string;
  auto_raise: boolean;
  threshold_overrides: Record<string, unknown>;
  yaml_source: string;
  plugin_key: string | null;
  evidence_contract: Record<string, unknown> | null;
  clauses: ClauseRef[];
};

export type Engagement = {
  id: number;
  name: string;
  scope_note: string | null;
  compliance_deadline: string | null;
  organization: string;
  city: string | null;
  sector: string | null;
  headcount: number | null;
  is_significant_data_fiduciary: boolean;
  is_synthetic: boolean;
  control_count: number;
  executable_count: number;
  out_of_scope_count: number;
};

export const DOMAINS = [
  "NOTICE_CONSENT",
  "SECURITY_SAFEGUARDS",
  "RETENTION_ERASURE",
  "PRINCIPAL_RIGHTS",
  "BREACH_RESPONSE",
  "THIRD_PARTY_TRANSFER",
  "AI_GOVERNANCE",
  "GOVERNANCE_ACCOUNTABILITY",
] as const;

export type Domain = (typeof DOMAINS)[number];

export const DOMAIN_LABEL: Record<Domain, string> = {
  NOTICE_CONSENT: "Notice & consent",
  SECURITY_SAFEGUARDS: "Security safeguards",
  RETENTION_ERASURE: "Retention & erasure",
  PRINCIPAL_RIGHTS: "Principal rights",
  BREACH_RESPONSE: "Breach response",
  THIRD_PARTY_TRANSFER: "Third party & transfer",
  AI_GOVERNANCE: "AI governance",
  GOVERNANCE_ACCOUNTABILITY: "Governance & accountability",
};

export const FRAMEWORK_LABEL: Record<string, string> = {
  DPDP: "DPDP",
  ISO27001: "ISO 27001",
  NIST_AI_RMF: "NIST AI RMF",
};

/**
 * A cold free-tier backend takes ~30s to wake, and the page must render
 * regardless. Callers receive null and show a reachability notice rather than
 * a spinner or a crash. [TRD 1.4]
 */
async function get<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
    if (!response.ok) return null;
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export const fetchControls = (query = "") =>
  get<ControlSummary[]>(`/api/controls${query}`);

export const fetchControl = (ref: string) =>
  get<ControlDetail>(`/api/controls/${encodeURIComponent(ref)}`);

export const fetchEngagement = () => get<Engagement>("/api/engagement");
