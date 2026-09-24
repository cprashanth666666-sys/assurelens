"use client";

import { PauseIcon, PlayIcon } from "@phosphor-icons/react";
import { useEffect, useRef, useState } from "react";

import type { Clip } from "@/lib/media";

/**
 * A muted, looping clip that behaves.
 *
 * - Plays only while at least 40% on screen, and pauses when it leaves, so
 *   three clips on a page never decode at once off-screen.
 * - `mode="ambient"` starts playing when in view; `mode="hover"` waits for
 *   hover or keyboard focus on the card (and on touch screens, falls back to
 *   playing in view, since there is no hover).
 * - Under `prefers-reduced-motion` or Save-Data it does not autoplay: the
 *   poster frame shows and the button starts it on request.
 * - A visible Pause/Play button on every clip, because anything that moves
 *   for more than five seconds needs one. [WCAG 2.2.2]
 */
export function MediaClip({
  clip,
  mode = "ambient",
  priority = false,
  className = "",
}: {
  clip: Clip;
  mode?: "ambient" | "hover";
  priority?: boolean;
  className?: string;
}) {
  const wrap = useRef<HTMLDivElement>(null);
  const video = useRef<HTMLVideoElement>(null);
  const [playing, setPlaying] = useState(false);
  // Set once the reader presses Pause, so scrolling back into view does not
  // override their choice.
  const userPaused = useRef(false);
  // Set when the reader presses Play, so an explicit request is never undone
  // by the autoplay rules (reduced motion, leaving a hover card).
  const userPlayed = useRef(false);
  const inView = useRef(false);
  const hovered = useRef(false);

  useEffect(() => {
    const node = wrap.current;
    const v = video.current;
    if (!node || !v) return;

    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const saveData = (navigator as Navigator & { connection?: { saveData?: boolean } })
      .connection?.saveData === true;
    const coarse = window.matchMedia("(hover: none)").matches;
    const autoplayAllowed = !reduce && !saveData;

    const sync = () => {
      // An explicit Play is permission to resume when the clip scrolls back
      // into view, even where autoplay is off.
      const want =
        (autoplayAllowed || userPlayed.current) &&
        !userPaused.current &&
        inView.current &&
        (mode === "ambient" || hovered.current || coarse || userPlayed.current);
      if (want && v.paused) v.play().catch(() => {});
      if (!want && !v.paused && !userPlayed.current && !hovered.current) v.pause();
      if (!inView.current && !v.paused) v.pause();
    };

    const io = new IntersectionObserver(
      (entries) => {
        inView.current = entries.some((e) => e.isIntersecting);
        sync();
      },
      { threshold: 0.4 },
    );
    io.observe(node);

    const card = node.closest<HTMLElement>("[data-clip-card]") ?? node;
    const enter = () => {
      hovered.current = true;
      sync();
    };
    const leave = () => {
      hovered.current = false;
      if (mode === "hover" && !coarse && !userPlayed.current) v.pause();
    };
    if (mode === "hover") {
      card.addEventListener("pointerenter", enter);
      card.addEventListener("pointerleave", leave);
      card.addEventListener("focusin", enter);
      card.addEventListener("focusout", leave);
    }

    const onPlay = () => setPlaying(true);
    const onPause = () => setPlaying(false);
    v.addEventListener("play", onPlay);
    v.addEventListener("pause", onPause);

    return () => {
      io.disconnect();
      card.removeEventListener("pointerenter", enter);
      card.removeEventListener("pointerleave", leave);
      card.removeEventListener("focusin", enter);
      card.removeEventListener("focusout", leave);
      v.removeEventListener("play", onPlay);
      v.removeEventListener("pause", onPause);
    };
  }, [mode]);

  function toggle() {
    const v = video.current;
    if (!v) return;
    if (v.paused) {
      userPaused.current = false;
      userPlayed.current = true;
      v.play().catch(() => {});
    } else {
      userPaused.current = true;
      userPlayed.current = false;
      v.pause();
    }
  }

  return (
    <div ref={wrap} className={`clip relative overflow-hidden bg-band ${className}`}>
      <video
        ref={video}
        src={clip.src}
        poster={clip.poster}
        muted
        loop
        playsInline
        preload={priority ? "auto" : "none"}
        aria-label={clip.label}
        className="h-full w-full object-cover"
      />
      <button
        type="button"
        onClick={toggle}
        aria-label={playing ? "Pause video" : "Play video"}
        className="clip-control"
      >
        {playing ? <PauseIcon size={16} weight="fill" aria-hidden /> : <PlayIcon size={16} weight="fill" aria-hidden />}
        <span>{playing ? "Pause" : "Play"}</span>
      </button>
    </div>
  );
}
