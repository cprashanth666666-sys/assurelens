"use client";

import { useSyncExternalStore } from "react";

import { ENGAGEMENT } from "@/lib/engagement";

/**
 * Whole days until DPDP Rules obligations commence.
 *
 * The count depends on the reader's clock, so it is not computed during SSR
 * (wrong for another timezone, and a hydration mismatch). useSyncExternalStore
 * gives the server `null` and the client the count; rounding to whole days
 * keeps the snapshot stable across renders, which the hook requires.
 */
const DEADLINE_MS = Date.parse(`${ENGAGEMENT.complianceDeadline}T00:00:00Z`);
const noSubscribe = () => () => {};
const daysRemaining = () =>
  Math.max(0, Math.ceil((DEADLINE_MS - Date.now()) / 86_400_000));

export function DeadlineCount({ suffix = "" }: { suffix?: string }) {
  const days = useSyncExternalStore(noSubscribe, daysRemaining, () => null);
  return (
    <span style={{ opacity: days === null ? 0 : 1 }}>
      {days === null ? " " : `${days.toLocaleString()}${suffix}`}
    </span>
  );
}
