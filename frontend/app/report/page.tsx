import { DownloadSimpleIcon } from "@phosphor-icons/react/dist/ssr";

import { PageHeader } from "@/components/PageHeader";
import { Placeholder } from "@/components/Placeholder";
import { API_BASE, fetchEngagement, fetchRuns } from "@/lib/api";
import { getRole } from "@/lib/role-server";

export const dynamic = "force-dynamic";

/**
 * Report preview and export. [UX_BRIEF 4.8]
 *
 * The paper metaphor, and the only place it is allowed: a white page on the
 * inset field, page-width column, visible print margins. Export is a plain
 * link to the API's own file response (Content-Disposition: attachment) --
 * no client JavaScript needed to save a file. [PRD 7.1, 7.2, M9, S5]
 *
 * Consultant exports the full workpaper; client exports the one-page
 * executive summary. Not both buttons for both roles: the export a reader
 * can produce is itself part of what the role changes. [PRD 4.4]
 */
export default async function ReportPage() {
  const [engagement, role] = await Promise.all([fetchEngagement(), getRole()]);

  if (engagement === null) {
    return (
      <PageHeader
        title="Workpaper and export"
        lede="The API is unreachable, so nothing can be exported right now. The page renders regardless; content never waits on a cold backend."
      />
    );
  }

  const runs = await fetchRuns(engagement.id);
  const latestRun = runs !== null && runs.length > 0 ? runs[0]! : null;

  return (
    <div className="flex flex-col gap-7">
      <PageHeader
        title="Workpaper and export"
        lede="An audit-format DOCX workpaper: control, procedure, population and sample, evidence, result with its confidence interval and, where a control was gated, the gate reason printed in full. The same run, opened in Word, reads exactly as it does on screen."
      />

      {latestRun === null ? (
        <Placeholder
          title="Nothing to export yet"
          summary="No test run has completed for this engagement. Start one from Test Runs, then come back here to export it."
          buildsOn="Day 9"
        />
      ) : (
        <div className="bg-inset px-4 py-8 md:px-8 md:py-7">
          <article className="mx-auto max-w-[54rem] border border-rule-strong bg-surface px-8 py-10 md:px-8 md:py-8">
            <p className="label m-0">
              {role === "consultant" ? "Workpaper preview" : "Executive summary preview"}
            </p>
            <h2 className="mt-2 text-2xl font-medium tracking-title text-ink">
              {engagement.name}
            </h2>
            <p className="m-0 mt-1 font-medium text-ink-2">{engagement.organization}</p>

            <div className="mt-6 flex flex-wrap gap-x-6 gap-y-1 font-mono text-sm text-ink-3">
              <span>Run {latestRun.id}</span>
              <span>Seed {latestRun.seed}</span>
              <span>Suites: {latestRun.suites.join(", ")}</span>
              <span>{latestRun.result_count} results</span>
            </div>

            <hr className="my-6 border-rule" />

            <p className="m-0 max-w-prose text-sm leading-prose text-ink-2">
              {role === "consultant"
                ? "One section per control tested: procedure performed, population and sample, evidence obtained, result, exception and recommendation. Front matter states scope, methodology and limitations. Appendices list the full control library and every threshold override."
                : "One page, drawn from the same live data as the overview: where the engagement stands by domain, the five things to fix first, what could not be concluded and why, and what changes before obligations commence."}
            </p>

            <div className="mt-8 flex flex-wrap gap-3 border-t border-rule pt-6">
              {role === "consultant" ? (
                <a
                  href={`${API_BASE}/api/runs/${latestRun.id}/workpaper`}
                  className="btn btn-primary no-underline"
                >
                  <DownloadSimpleIcon size={18} weight="bold" aria-hidden />
                  Download workpaper (DOCX)
                </a>
              ) : (
                <a
                  href={`${API_BASE}/api/engagements/${engagement.id}/summary`}
                  className="btn btn-primary no-underline"
                >
                  <DownloadSimpleIcon size={18} weight="bold" aria-hidden />
                  Download executive summary (DOCX)
                </a>
              )}
            </div>
          </article>
        </div>
      )}
    </div>
  );
}
