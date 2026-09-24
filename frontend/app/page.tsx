import { ArrowDownIcon, ArrowRightIcon } from "@phosphor-icons/react/dist/ssr";
import Link from "next/link";

import { DeadlineCount } from "@/components/DeadlineCount";
import { EvidenceQualityMeter } from "@/components/EvidenceQualityMeter";
import { GateExplorer } from "@/components/GateExplorer";
import { HealthProbe } from "@/components/HealthProbe";
import { MediaClip } from "@/components/MediaClip";
import { Plate } from "@/components/Plate";
import { Placeholder } from "@/components/Placeholder";
import { ReadinessByDomain } from "@/components/ReadinessBar";
import { Reveal } from "@/components/Reveal";
import { RiskHeatmap } from "@/components/RiskHeatmap";
import { OPEN_FINDING_STATUSES, fetchEngagement, fetchFindings, fetchReadiness } from "@/lib/api";
import { ENGAGEMENT } from "@/lib/engagement";
import { CLIPS, type Clip } from "@/lib/media";
import { PLATES } from "@/lib/imagery";

export const dynamic = "force-dynamic";

/**
 * The overview: the engagement's cover sheet, then the product's argument
 * made interactive. No headline compliance percentage anywhere, by product
 * decision. [PRD 7.3]
 *
 * v6 layout (Figma: "AssureLens v6 Revamp" / Overview / Desktop 1440):
 *   1. Split hero: statement + actions on white, the estate on live video
 *      with the statutory clock in a cobalt block over it.
 *   2. The evidence gate, as something the reader can move.
 *   3. How the instrument works: an asymmetric media bento.
 */
export default async function OverviewPage() {
  const engagement = await fetchEngagement();
  const [readiness, findings] = engagement
    ? await Promise.all([
        fetchReadiness(engagement.id),
        fetchFindings(engagement.id),
      ])
    : [null, null];

  return (
    <div className="flex flex-col gap-9">
      <Hero />

      <Reveal as="section" className="flex flex-col gap-5">
        <div id="gate" className="flex max-w-prose scroll-mt-[140px] flex-col gap-3">
          <h2 className="text-2xl font-medium tracking-title">Try the evidence gate</h2>
          <p className="m-0 text-base text-ink-2 md:text-lg md:leading-prose">
            Move the sliders. A verdict is only published when the sample, the
            coverage and the interval all clear the gate. Otherwise the result
            says insufficient evidence, and says why.
          </p>
        </div>
        <GateExplorer />
      </Reveal>

      <Reveal as="section" className="flex flex-col gap-5">
        <h2 className="text-2xl font-medium tracking-title">How the instrument works</h2>
        <HowItWorks />
      </Reveal>

      <Reveal delay={40} as="section" className="flex flex-col gap-7">
        <div className="flex max-w-prose flex-col gap-3">
          <h2 className="text-2xl font-medium tracking-title">Engagement overview</h2>
          <p className="m-0 text-base text-ink-2 md:text-lg md:leading-prose">
            Readiness by domain, a 5×5 risk heatmap, and the evidence quality
            meter: what proportion of the estate has been graded, and what has
            not. Deliberately no headline compliance percentage — a domain at
            40% coverage and one at 95% cannot be averaged into an honest
            number.
          </p>
        </div>

        {readiness === null || findings === null ? (
          <Placeholder
            title="Engagement overview"
            summary="The API is unreachable, so readiness cannot be graded right now. This section renders once the backend responds; content never waits on a cold backend."
            buildsOn="Day 8"
          />
        ) : (
          <div className="ruled lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)]">
            <div className="flex flex-col gap-6 bg-surface p-5 md:p-7">
              <h3 className="m-0 text-lg font-medium">Readiness by domain</h3>
              <ReadinessByDomain rows={readiness.by_domain} />
            </div>
            <div className="grid gap-px bg-rule-strong">
              <div className="flex flex-col gap-4 bg-surface p-5 md:p-6">
                <h3 className="m-0 text-lg font-medium">Risk heatmap</h3>
                <RiskHeatmap
                  findings={findings.filter((f) => OPEN_FINDING_STATUSES.includes(f.status))}
                />
              </div>
              <div className="flex flex-col gap-4 bg-surface p-5 md:p-6">
                <h3 className="m-0 text-lg font-medium">Evidence quality</h3>
                <EvidenceQualityMeter quality={readiness.evidence_quality} />
              </div>
            </div>
          </div>
        )}
      </Reveal>

      <Reveal delay={80}>
        <HealthProbe />
      </Reveal>
    </div>
  );
}

function Hero() {
  return (
    <section aria-label="Engagement cover" className="ruled lg:grid-cols-[minmax(0,1.05fr)_minmax(0,1fr)]">
      <div className="flex flex-col justify-between gap-7 p-5 md:p-7 lg:p-8">
        <p className="m-0 text-sm font-medium text-ink-3">
          Engagement cover <span aria-hidden="true">/</span> synthetic data
        </p>
        <div>
          <h2 className="m-0 max-w-[17ch] text-[clamp(2.5rem,3.4vw+1rem,4.5rem)] font-medium leading-[1.02] tracking-display text-ink">
            It refuses to state a result its evidence cannot support.
          </h2>
          <p className="m-0 mt-6 max-w-[54ch] text-base text-ink-2 md:text-lg md:leading-prose">
            AssureLens turns the DPDP Act 2023 and the Rules of 13 November 2025
            into controls that execute against a real service, on a recorded
            seed. Where the evidence cannot carry a conclusion, the result says{" "}
            <mark className="font-semibold">insufficient evidence</mark> and names
            what would resolve it.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <a href="#gate" className="btn btn-primary no-underline">
            Try the evidence gate
            <ArrowDownIcon size={18} weight="bold" aria-hidden className="btn-arrow" />
          </a>
          <Link href="/controls" className="btn btn-secondary no-underline">
            Open the control library
            <ArrowRightIcon size={18} weight="bold" aria-hidden className="btn-arrow" />
          </Link>
        </div>
      </div>

      {/* The estate on live video. Text never sits on the footage: the facts
          are in a solid cobalt block, the credit is on the white strip below. */}
      <figure className="m-0 flex min-h-[360px] flex-col lg:min-h-[620px]">
        <div className="relative flex-1">
          <div className="absolute inset-0">
            <MediaClip clip={CLIPS.estate} priority className="h-full" />
          </div>
          <div className="absolute bottom-0 left-0 z-[1] bg-cobalt px-5 py-4 text-on-cobalt md:px-6 md:py-5">
            <p className="m-0 text-sm font-medium text-on-cobalt-2">Obligations commence in</p>
            <p className="m-0 mt-1 font-mono text-num font-medium tracking-head">
              <DeadlineCount />
              <span className="ml-3 font-sans text-xl font-medium">days</span>
            </p>
            <p className="m-0 mt-1 font-mono text-sm text-on-cobalt-2">
              {ENGAGEMENT.complianceDeadline}, per Rule 1(4)
            </p>
          </div>
        </div>
        <Credit as="figcaption" clip={CLIPS.estate} caption={`${ENGAGEMENT.city}: the estate under test is real; every record in it is synthetic.`} />
      </figure>
    </section>
  );
}

/**
 * Three commitments, as an asymmetric bento: one large clip and two stacked
 * cells. Each cell carries real media and plays on hover or focus (or when
 * in view on a touch screen). Not three equal cards.
 */
function HowItWorks() {
  return (
    <div className="ruled lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)]">
      <article data-clip-card className="flex flex-col">
        <MediaClip clip={CLIPS.network} mode="hover" className="aspect-[16/10] lg:aspect-auto lg:flex-1" />
        <CellText
          n="01"
          title="Tests run against a live service"
          body="Every executable control probes a real target over HTTP, on a recorded seed, and keeps what came back as evidence."
          href="/runs"
          cta="Open the run console"
        />
        <Credit clip={CLIPS.network} />
      </article>

      <div className="grid gap-px bg-rule-strong">
        <article data-clip-card className="flex flex-col bg-surface">
          <MediaClip clip={CLIPS.evidence} mode="hover" className="aspect-[16/8]" />
          <CellText
            n="02"
            title="Every item of evidence is hashed"
            body="A SHA-256 pins exactly the bytes a verdict stood on, so the finding can be re-checked later."
          />
          <Credit clip={CLIPS.evidence} />
        </article>
        <article data-clip-card className="flex flex-col bg-surface">
          <Plate plate={PLATES.statute} sizes="(max-width: 1023px) 100vw, 40vw" className="aspect-[16/8]" fill />
          <CellText
            n="03"
            title="One clause, quoted verbatim"
            body="Each control names a single statutory basis and shows its text. A paraphrase is where a conclusion becomes an opinion."
            href="/controls"
            cta="Browse the controls"
          />
          <p className="m-0 px-5 pb-4 text-xs text-ink-3">
            Vidhana Soudha, Bengaluru. Photograph{" "}
            <a href={PLATES.statute.credit.href} target="_blank" rel="noopener noreferrer" className="link">
              {PLATES.statute.credit.name}
            </a>{" "}
            on Unsplash.
          </p>
        </article>
      </div>
    </div>
  );
}

function CellText({
  n, title, body, href, cta,
}: {
  n: string; title: string; body: string; href?: string; cta?: string;
}) {
  return (
    <div className="flex flex-col gap-2 px-5 pb-3 pt-5 md:px-6">
      <h3 className="flex items-baseline gap-3">
        <span className="font-mono text-lg font-medium text-link">{n}</span>
        {title}
      </h3>
      <p className="m-0 max-w-prose text-base text-ink-2">{body}</p>
      {href && cta && (
        <Link href={href} className="link mt-1 inline-flex w-fit items-center gap-1 text-sm font-semibold">
          {cta}
          <ArrowRightIcon size={14} weight="bold" aria-hidden />
        </Link>
      )}
    </div>
  );
}

function Credit({
  clip, caption, as: Tag = "p",
}: {
  clip: Clip; caption?: string; as?: "p" | "figcaption";
}) {
  return (
    <Tag className="m-0 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 bg-surface px-5 py-3 text-xs text-ink-3 md:px-6">
      {caption && <span className="text-meta text-ink-2">{caption}</span>}
      <span>
        Video{" "}
        <a href={clip.credit.href} target="_blank" rel="noopener noreferrer" className="link">
          {clip.credit.name}
        </a>{" "}
        on {clip.credit.source}
      </span>
    </Tag>
  );
}
