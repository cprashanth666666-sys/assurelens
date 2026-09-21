import type { Metadata } from "next";

import { DisclosureFooter } from "@/components/DisclosureFooter";
import { Masthead } from "@/components/Masthead";
import { TabNav } from "@/components/TabNav";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "AssureLens — DPDP + AI Controls Assurance",
  description:
    "Turns the DPDP Act and Rules 2025 into executable controls, runs real " +
    "tests, and gates every verdict on evidence sufficiency.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Masthead />
        <TabNav />
        <main className="mx-auto max-w-content px-4 py-6">{children}</main>
        <DisclosureFooter />
      </body>
    </html>
  );
}
