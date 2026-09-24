"use client";

import { motion } from "motion/react";

/**
 * Page change: the new page rises 8px and fades in over 280ms. A template
 * (not the layout) so it remounts on every navigation; the masthead and tab
 * rail live in the layout and never move. Under reduced motion MotionConfig
 * drops the rise and keeps only the fade.
 */
export default function Template({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}
