import { DeadlineCount } from "@/components/DeadlineCount";
import { HealthProbe } from "@/components/HealthProbe";
import { Figure, Plate } from "@/components/Plate";
import { Placeholder } from "@/components/Placeholder";
import { Reveal } from "@/components/Reveal";
import { ENGAGEMENT } from "@/lib/engagement";
import { PLATES } from "@/lib/imagery";

/**
 * The overview is the engagement's COVER SHEET: whose engagement, against what
 * law, standing on what evidence. There is no headline compliance percentage
 * anywhere, by product decision. [PRD 7.3]
 *
 * v5 builds it as one ruled grid of colour blocks rather than a stack of
 * floating tiles: a display-size statement on white, a cobalt fact block, the
 * photograph at full colour, and the three commitments as a numbered list.
 * [DESIGN.md 5]
 */
export default function OverviewPage() {
  return (
    <div className="flex flex-col gap-8">
      <CoverSheet />

      <Reveal as="section" className="flex flex-col gap-5" >
        <h2 className="section-rule">The estate under test</h2>
        <div className="ruled md:grid-cols-2">
          <Figure plate={PLATES.estate} sizes="(max-width: 768px) 100vw, 46vw" />
          <Figure plate={PLATES.evidence} sizes="(max-width: 768px) 100vw, 46vw" />
        </div>
      </Reveal>

      <Reveal delay={40}>
        <Placeholder
          title="Engagement overview"
          summary={
            "Readiness by domain, a 5×5 risk heatmap, and the evidence quality " +
            "meter: what proportion of the estate has been graded, and what " +
            "has not. Deliberately no headline compliance percentage. A domain " +
            "at 40% coverage and one at 95% cannot be averaged into an honest " +
            "number."
          }
          buildsOn="Day 8"
        />
      </Reveal>

      <Reveal delay={80}>
        <HealthProbe />
      </Reveal>
    </div>
  );
}

function CoverSheet() {
  return (
    <section aria-label="Engagement cover" className="ruled lg:grid-cols-12">
      {/* The statement. It carries a sentence, never a number: this product's
          argument is that the single number is the wrong object. */}
      <div className="flex flex-col justify-between gap-7 p-5 md:p-7 lg:col-span-8 lg:p-8">
        <p className="m-0 text-sm font-medium text-ink-3">
          Engagement cover <span aria-hidden="true">/</span> synthetic data
        </p>
        <div>
          <p className="m-0 max-w-[15ch] text-display font-medium tracking-display text-ink">
            It refuses to state a result its evidence cannot support.
          </p>
          <p className="m-0 mt-6 max-w-[58ch] text-base text-ink-2 md:text-lg md:leading-prose">
            AssureLens turns the Digital Personal Data Protection Act 2023 and
            the Rules of 13 November 2025 into controls that actually execute,
            against a real target service, over HTTP, on a recorded seed. Where
            the evidence cannot carry a conclusion, the result says{" "}
            <mark className="font-semibold">insufficient evidence</mark> and
            names what would resolve it.
          </p>
        </div>
      </div>

      {/* The facts, as a flat cobalt block. The day count is the one large
          figure on the page, and it is a date, not a score. */}
      <div className="flex flex-col justify-between gap-7 bg-cobalt p-5 text-on-cobalt md:p-7 lg:col-span-4">
        <div>
          <p className="m-0 text-sm font-medium text-on-cobalt-2">Obligations commence in</p>
          <p className="m-0 mt-2 font-mono text-num font-medium tracking-head">
            <DeadlineCount />
            <span className="ml-3 font-sans text-xl font-medium">days</span>
          </p>
          <p className="m-0 mt-2 font-mono text-sm text-on-cobalt-2">
            {ENGAGEMENT.complianceDeadline}, per Rule 1(4)
          </p>
        </div>

        <dl className="m-0 grid gap-4 border-t border-on-cobalt-2 pt-5 text-base">
          <Fact label="Client" value={ENGAGEMENT.organisation} />
          <Fact label="Location" value={ENGAGEMENT.city} />
          <Fact label="Frameworks" value="DPDP, ISO 27001, NIST AI RMF" />
        </dl>
      </div>

      <figure className="m-0 flex flex-col lg:col-span-5">
        <Plate
          plate={PLATES.statute}
          sizes="(max-width: 1023px) 100vw, 40vw"
          priority
          className="aspect-[4/3] lg:aspect-auto lg:min-h-[360px] lg:flex-1"
          fill
        />
        <figcaption className="px-4 py-3 text-meta text-ink-2">
          {PLATES.statute.caption} Photograph{" "}
          <a
            href={PLATES.statute.credit.href}
            target="_blank"
            rel="noopener noreferrer"
            className="link font-mono text-xs"
          >
            {PLATES.statute.credit.name}
          </a>{" "}
          on Unsplash.
        </figcaption>
      </figure>

      <Principles />
    </section>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-sm font-medium text-on-cobalt-2">{label}</dt>
      <dd className="m-0 mt-1 font-semibold">{value}</dd>
    </div>
  );
}

/**
 * Three commitments the engine actually keeps, as one numbered list rather
 * than three equal cards. The numbers are list order, set in mono cobalt.
 */
function Principles() {
  const items = [
    {
      title: "One clause, quoted",
      body: "Every control names a single statutory basis and shows its verbatim text. A paraphrase is where an assurance conclusion quietly becomes an opinion.",
    },
    {
      title: "A gate before a verdict",
      body: "Eight rules stand between a measurement and a published result: structural failures first, then sample size, coverage and interval width.",
    },
    {
      title: "A seed on every run",
      body: "Each run records the seed it was generated from. A result nobody can regenerate is an assertion, not a finding.",
    },
  ];

  return (
    <div className="p-5 md:p-7 lg:col-span-7">
      <h2>How the instrument works</h2>
      <ol className="m-0 mt-5 list-none divide-y divide-rule p-0">
        {items.map((item, i) => (
          <li key={item.title} className="grid grid-cols-[3rem_1fr] gap-4 py-5 first:pt-0 last:pb-0">
            <span className="font-mono text-xl font-medium text-link">0{i + 1}</span>
            <div>
              <h3>{item.title}</h3>
              <p className="m-0 mt-2 max-w-prose text-base text-ink-2">{item.body}</p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
