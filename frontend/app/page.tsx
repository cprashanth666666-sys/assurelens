import { HealthProbe } from "@/components/HealthProbe";
import { Figure, Plate } from "@/components/Plate";
import { Placeholder } from "@/components/Placeholder";
import { Reveal } from "@/components/Reveal";
import { Spotlight } from "@/components/Spotlight";
import { ENGAGEMENT } from "@/lib/engagement";
import { PLATES } from "@/lib/imagery";

/**
 * The overview is a COVER SHEET, not a landing page.
 *
 * UX 1.1 still rejects the full-width marketing hero, and this is not one:
 * there is no call to action, no product pitch and no headline compliance
 * percentage. What a workpaper file does have is a cover — whose engagement,
 * against what law, standing on what evidence — and that is what this is.
 * The distinction is worth holding, because the fix for "the page looks
 * plain" is very easily a hero section, and a hero section here would be the
 * single most damaging thing in the product. [UX 1.3]
 */
export default function OverviewPage() {
  return (
    <div className="flex flex-col gap-7">
      <CoverSheet />
      <Principles />

      <Reveal as="section" className="grid gap-5 md:grid-cols-2">
        <Figure
          plate={PLATES.estate}
          sizes="(max-width: 768px) 100vw, 44vw"
        />
        <Figure
          plate={PLATES.evidence}
          sizes="(max-width: 768px) 100vw, 44vw"
        />
      </Reveal>

      <Reveal delay={40}>
        <Placeholder
          title="Engagement overview"
          summary={
            "Readiness by domain, a 5×5 risk heatmap, and the evidence quality " +
            "meter — what proportion of the estate has been graded, and what " +
            "has not. Deliberately no headline compliance percentage: a domain " +
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
    <Spotlight className="panel overflow-hidden">
      {/* Splits at lg, not md. At exactly 768px a two-column cover left the
          statement line wrapping to five lines in a 380px column and the fact
          grid at three cramped columns — a tablet reading like a squeezed
          desktop rather than a wide phone. */}
      <div className="grid gap-0 lg:grid-cols-[1.15fr_1fr]">
        <div className="flex flex-col justify-between gap-6 p-5 lg:p-7">
          <div>
            <p className="m-0 flex flex-wrap items-center gap-2 text-2xs uppercase tracking-[0.18em] text-n-400">
              <span>Engagement cover</span>
              <span aria-hidden="true" className="h-px w-6 bg-warm-500" />
              <span className="text-warm-600">Synthetic data</span>
            </p>

            {/* The display line carries a SENTENCE. A 38px numeral here
                would be the KPI tile UX 1.1 rejects, and this product's
                argument is precisely that the number is the wrong object. */}
            <p className="m-0 mt-4 max-w-[22ch] font-serif text-3xl leading-tight text-n-800">
              It refuses to state a result its evidence cannot support.
            </p>

            <p className="m-0 mt-4 max-w-prose text-base leading-prose text-n-600">
              AssureLens turns the Digital Personal Data Protection Act 2023
              and the Rules of 13 November 2025 into controls that actually
              execute — against a real target service, over HTTP, on a
              recorded seed. Where the evidence cannot carry a conclusion, the
              result says{" "}
              <span className="font-semibold text-verdict-insufficient">
                insufficient evidence
              </span>{" "}
              and names what would resolve it.
            </p>
          </div>

          <dl className="m-0 grid grid-cols-2 gap-x-5 gap-y-3 border-t border-n-100 pt-5 text-sm sm:grid-cols-3">
            <Fact label="Client" value={ENGAGEMENT.organisation} />
            <Fact label="Location" value={ENGAGEMENT.city} />
            <Fact label="Framework" value="DPDP · ISO 27001 · NIST AI RMF" />
          </dl>
        </div>

        {/* On a phone the photograph sits above nothing and below nothing —
            it is the last element, so it can be dropped from the reading
            order without losing anything. */}
        <div className="relative min-h-[220px] sm:min-h-[300px] lg:min-h-[340px]">
          <Plate
            plate={PLATES.statute}
            sizes="(max-width: 1023px) 100vw, 42vw"
            priority
            fill
            className="!rounded-none absolute inset-0 h-full w-full"
          />
        </div>
      </div>

      <p className="m-0 border-t border-n-100 px-5 py-2 text-2xs text-n-400 lg:px-7">
        {PLATES.statute.caption} Photograph{" "}
        <a
          href={PLATES.statute.credit.href}
          target="_blank"
          rel="noopener noreferrer"
          className="link-grow font-mono no-underline transition-colors duration-base ease-out hover:text-n-600"
        >
          {PLATES.statute.credit.name}
        </a>{" "}
        on Unsplash.
      </p>
    </Spotlight>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-2xs uppercase tracking-[0.18em] text-n-400">
        {label}
      </dt>
      <dd className="m-0 mt-1 text-n-700">{value}</dd>
    </div>
  );
}

/**
 * Three panels, each stating one commitment the engine actually keeps.
 *
 * Marks are drawn inline rather than pulled from an icon set: three shapes
 * at one stroke weight in the product's own palette stay coherent where
 * three glyphs from Lucide would read as a different designer's work.
 * [a11y no-emoji-icons, icon-style-consistent]
 */
function Principles() {
  const items = [
    {
      title: "One clause, quoted",
      body:
        "Every control names a single statutory basis and shows its verbatim text. A paraphrase is where an assurance conclusion quietly becomes an opinion.",
      mark: <MarkClause />,
    },
    {
      title: "A gate before a verdict",
      body:
        "Eight rules stand between a measurement and a published result — structural failures first, then sample size, coverage and interval width.",
      mark: <MarkGate />,
    },
    {
      title: "A seed on every run",
      body:
        "Each run records the seed it was generated from. A result nobody can regenerate is an assertion, not a finding.",
      mark: <MarkSeed />,
    },
  ];

  return (
    <section
      aria-label="How this instrument works"
      className="grid gap-4 md:grid-cols-3"
    >
      {items.map((item, i) => (
        <Reveal key={item.title} as="article" delay={i * 40}>
          <div className="panel panel-raise h-full p-5">
            <div className="text-accent-600">{item.mark}</div>
            <h3 className="mt-4">{item.title}</h3>
            <p className="m-0 mt-2 text-n-600">{item.body}</p>
          </div>
        </Reveal>
      ))}
    </section>
  );
}

function MarkClause() {
  return (
    <svg viewBox="0 0 28 28" width="28" height="28" aria-hidden="true" fill="none">
      <rect x="4.5" y="2.5" width="19" height="23" rx="1.5" stroke="currentColor" strokeWidth="1.3" />
      <path d="M8.5 8h11M8.5 12h11M8.5 16h7" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
      <path d="M8.5 20h4" stroke="var(--warm-500)" strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  );
}

function MarkGate() {
  return (
    <svg viewBox="0 0 28 28" width="28" height="28" aria-hidden="true" fill="none">
      <path d="M3 21V9.5a11 11 0 0 1 22 0V21" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
      <path d="M9 21V10.5M14 21V7.5M19 21V10.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
      <path d="M1.5 21h25" stroke="var(--warm-500)" strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  );
}

function MarkSeed() {
  return (
    <svg viewBox="0 0 28 28" width="28" height="28" aria-hidden="true" fill="none">
      <circle cx="14" cy="14" r="10.5" stroke="currentColor" strokeWidth="1.3" />
      <circle cx="14" cy="14" r="4" stroke="currentColor" strokeWidth="1.3" />
      <path d="M14 3.5v6M14 18.5v6M3.5 14h6M18.5 14h6" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
      <circle cx="14" cy="14" r="1.6" fill="var(--warm-500)" />
    </svg>
  );
}
