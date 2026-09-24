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


// --- Runs ------------------------------------------------------------------

export type ResultSummary = {
  id: number;
  control_ref: string;
  control_title: string;
  verdict: Verdict;
  raw_outcome: Verdict | null;
  gate_fired: boolean;
  gate_reasons: string[];
  gate_explanations: string[];
  gate_remedies: string[];
  sample_size: number | null;
  population_size: number | null;
  successes: number | null;
  coverage_pct: number | null;
  point_estimate: number | null;
  ci_lower: number | null;
  ci_upper: number | null;
  ci_method: string | null;
  thresholds_applied: Record<string, unknown>;
  threshold_overrides: Record<string, unknown>;
  duration_ms: number | null;
};

export type Verdict =
  | "PASS"
  | "FAIL"
  | "INSUFFICIENT_EVIDENCE"
  | "NOT_APPLICABLE";

export type RunSummary = {
  id: number;
  engagement_id: number;
  seed: number;
  suites: string[];
  status: string;
  started_at: string;
  completed_at: string | null;
  engine_version: string;
  error: string | null;
  result_count: number;
};

export type RunDetail = RunSummary & { results: ResultSummary[] };

export type SuiteCatalogue = {
  suites: string[];
  registered_procedures: string[];
};

export const VERDICT_LABEL: Record<Verdict, string> = {
  PASS: "Pass",
  FAIL: "Fail",
  // Never "Unknown", "Error" or "Incomplete". It is a peer verdict, and the
  // wording is what makes that legible. [UX 6.1]
  INSUFFICIENT_EVIDENCE: "Insufficient evidence",
  NOT_APPLICABLE: "Not applicable",
};

/**
 * v5: every verdict is a SOLID chip of equal weight and size. Insufficient
 * evidence is the ink chip, the most assertive fill in the set: it is a
 * conclusion the product stands behind, not a grey absence of one. It is
 * still never red, amber or yellow. [DESIGN.md 2, UX_BRIEF 14.4]
 */
export const VERDICT_CLASS: Record<Verdict, string> = {
  PASS: "bg-pass text-on-verdict",
  FAIL: "bg-fail text-on-verdict",
  INSUFFICIENT_EVIDENCE: "bg-insufficient text-on-verdict",
  NOT_APPLICABLE: "border border-dashed border-control text-na",
};

export const fetchSuites = () => get<SuiteCatalogue>("/api/suites");

export const fetchRun = (id: number) => get<RunDetail>(`/api/runs/${id}`);

export const fetchRuns = (engagementId: number) =>
  get<RunSummary[]>(`/api/engagements/${engagementId}/runs`);

export async function startRun(
  engagementId: number,
  suiteIds: string[],
  seed: number,
): Promise<RunSummary | null> {
  try {
    const response = await fetch(
      `${API_BASE}/api/engagements/${engagementId}/runs`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ suite_ids: suiteIds, seed }),
      },
    );
    if (!response.ok) return null;
    return (await response.json()) as RunSummary;
  } catch {
    return null;
  }
}

// --- Latest result per control (evidence viewer) ---------------------------

export type EvidenceOut = {
  label: string;
  kind: string;
  source_ref: string | null;
  content_hash: string;
  collected_at: string;
  summary: unknown;
};

export type ControlResult = ResultSummary & {
  run_id: number;
  seed: number;
  completed_at: string | null;
  detail: Record<string, unknown>;
  evidence: EvidenceOut[];
};

/**
 * Three states, kept distinct on purpose.
 *
 * The endpoint returns JSON `null` for a control that has never run, and the
 * shared `get()` also returns null when the API is unreachable. Folding both
 * into null would render "not tested yet" when the truth is "could not ask",
 * which is the same category of error the gate exists to prevent: reporting
 * an absence of evidence as if it were a finding.
 */
export type LatestResult =
  | { kind: "result"; result: ControlResult }
  | { kind: "never-run" }
  | { kind: "unreachable" };

export async function fetchLatestResult(ref: string): Promise<LatestResult> {
  try {
    const response = await fetch(
      `${API_BASE}/api/controls/${encodeURIComponent(ref)}/latest-result`,
      { cache: "no-store" },
    );
    if (!response.ok) return { kind: "unreachable" };
    const body = (await response.json()) as ControlResult | null;
    return body === null ? { kind: "never-run" } : { kind: "result", result: body };
  } catch {
    return { kind: "unreachable" };
  }
}
