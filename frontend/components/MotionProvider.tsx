"use client";

import { MotionConfig } from "motion/react";

/**
 * One switch for every Motion animation in the product: `reducedMotion="user"`
 * makes all of them honour the OS "reduce motion" setting (transforms are
 * skipped, opacity still fades), so no component can forget to.
 */
export function MotionProvider({ children }: { children: React.ReactNode }) {
  return <MotionConfig reducedMotion="user">{children}</MotionConfig>;
}
