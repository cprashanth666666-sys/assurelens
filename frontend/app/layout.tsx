import type { Metadata, Viewport } from "next";
import { Geist, JetBrains_Mono } from "next/font/google";

import { DisclosureFooter } from "@/components/DisclosureFooter";
import { Masthead } from "@/components/Masthead";
import { MotionProvider } from "@/components/MotionProvider";
import { RoleProvider } from "@/components/RoleProvider";
import { TabNav } from "@/components/TabNav";
import { getRole } from "@/lib/role-server";
import "@/styles/globals.css";

/**
 * Two faces: Geist for everything read, JetBrains Mono for identifiers and
 * measurements. v5 retires Source Serif; quoted statute is marked by its rule
 * and size instead. [DESIGN.md 3]
 *
 * `display: swap` shows the fallback immediately, and Next's generated
 * fallback metrics keep the swap from shifting the line. [a11y font-loading]
 */
const sans = Geist({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-geist",
});

const mono = JetBrains_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-jetbrains-mono",
});

export const metadata: Metadata = {
  title: "AssureLens: DPDP + AI Controls Assurance",
  description:
    "Turns the DPDP Act and Rules 2025 into executable controls, runs real " +
    "tests, and gates every verdict on evidence sufficiency.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  // Never `maximum-scale: 1` / `user-scalable: no`. [a11y viewport-meta]
  themeColor: [
    // The browser chrome continues the cobalt masthead.
    { media: "(prefers-color-scheme: light)", color: "#2436e6" },
    { media: "(prefers-color-scheme: dark)", color: "#3342f0" },
  ],
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const role = await getRole();

  return (
    <html
      lang="en"
      className={`${sans.variable} ${mono.variable}`}
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
        {/* A lime rule tracking scroll position, drawn by a CSS
            scroll-driven animation. No listener, no JavaScript. */}
        <div aria-hidden="true" className="scroll-progress" />

        {/* Keyboard users should not have to tab through the masthead, the
            role switch and six tabs to reach a 25-row table.
            [a11y skip-links] */}
        <a
          href="#main"
          className="sr-only fixed left-4 top-4 z-50 bg-lime px-4 py-3 text-sm font-semibold text-on-lime focus:not-sr-only"
        >
          Skip to content
        </a>

        <RoleProvider initialRole={role}>
          <Masthead />
          <TabNav />

          <MotionProvider>
            <main id="main" className="mx-auto max-w-content px-4 pb-9 pt-7 md:px-6 md:pt-8">
              {children}
            </main>
          </MotionProvider>

          <DisclosureFooter />
        </RoleProvider>
      </body>
    </html>
  );
}
