import type { Metadata, Viewport } from "next";
import { Inter_Tight, JetBrains_Mono, Source_Serif_4 } from "next/font/google";

import { DisclosureFooter } from "@/components/DisclosureFooter";
import { Masthead } from "@/components/Masthead";
import { ScrollProgress } from "@/components/ScrollProgress";
import { TabNav } from "@/components/TabNav";
import "@/styles/globals.css";

/**
 * The three faces the design brief has always specified, now actually
 * loaded. Until v2.0 they were named in tokens.css and never fetched, so
 * every screen rendered in the system UI font — a large part of why the
 * product read as unstyled.
 *
 * `display: swap` shows the fallback immediately rather than holding text
 * invisible, and the fallback metrics Next generates keep the swap from
 * shifting the line. [a11y font-loading]
 */
const sans = Inter_Tight({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter-tight",
});

const mono = JetBrains_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-jetbrains-mono",
});

const serif = Source_Serif_4({
  subsets: ["latin"],
  display: "swap",
  style: ["normal", "italic"],
  variable: "--font-source-serif",
});

export const metadata: Metadata = {
  title: "AssureLens — DPDP + AI Controls Assurance",
  description:
    "Turns the DPDP Act and Rules 2025 into executable controls, runs real " +
    "tests, and gates every verdict on evidence sufficiency.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  // Never `maximum-scale: 1` / `user-scalable: no`. [a11y viewport-meta]
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f6f2e8" },
    { media: "(prefers-color-scheme: dark)", color: "#14110d" },
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${sans.variable} ${mono.variable} ${serif.variable}`}
    >
      <head>
        {/* The reveal animation starts at opacity 0 and is cleared by an
            IntersectionObserver. With scripting off that observer never runs,
            so neutralise the start state rather than serving a blank page.
            globals.css covers this via `@media (scripting: none)`; this
            covers browsers that do not support that query. */}
        <noscript>
          <style>{".reveal{opacity:1!important;transform:none!important}"}</style>
        </noscript>
      </head>
      <body>
        <ScrollProgress />

        {/* Keyboard users should not have to tab through the masthead, the
            role switch and six tabs to reach a 25-row table.
            [a11y skip-links] */}
        <a
          href="#main"
          className="sr-only fixed left-4 top-4 z-50 rounded-md border border-accent-600 bg-n-0 px-4 py-2 text-sm font-semibold text-accent-700 focus:not-sr-only"
        >
          Skip to content
        </a>

        <Masthead />
        <TabNav />

        <main id="main" className="mx-auto max-w-content px-4 py-6 md:px-5 md:py-7">
          {children}
        </main>

        <DisclosureFooter />
      </body>
    </html>
  );
}
