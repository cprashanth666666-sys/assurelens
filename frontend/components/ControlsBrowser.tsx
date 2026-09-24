"use client";

import { MagnifyingGlassIcon, XIcon } from "@phosphor-icons/react";
import { useEffect, useMemo, useRef, useState } from "react";

import { DOMAINS, DOMAIN_LABEL, type ControlSummary, type Domain } from "@/lib/api";
import { ControlTable } from "./ControlTable";

/**
 * Search and filter the control library without a round trip.
 *
 * v5 filtered on the server, so every chip click was a full page request to
 * an API that takes about 3.5s to answer (measured on production). 25 rows
 * fit in the browser, so v6 loads them once and filters as the reader types.
 * The URL is kept in sync with `history.replaceState`, so a filtered view is
 * still linkable and survives reload. "/" focuses the search box.
 */
type Exec = "all" | "true" | "false";

export function ControlsBrowser({
  controls,
  initialDomain,
  initialExec,
}: {
  controls: ControlSummary[];
  initialDomain?: string;
  initialExec?: string;
}) {
  const [query, setQuery] = useState("");
  const [domain, setDomain] = useState<Domain | "all">(
    DOMAINS.includes(initialDomain as Domain) ? (initialDomain as Domain) : "all",
  );
  const [exec, setExec] = useState<Exec>(
    initialExec === "true" || initialExec === "false" ? initialExec : "all",
  );
  const search = useRef<HTMLInputElement>(null);

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    return controls.filter((c) => {
      if (domain !== "all" && c.domain !== domain) return false;
      if (exec !== "all" && String(c.is_executable) !== exec) return false;
      if (!q) return true;
      return [c.ref, c.title, DOMAIN_LABEL[c.domain], c.primary_clause ?? "", c.suite ?? ""]
        .join(" ")
        .toLowerCase()
        .includes(q);
    });
  }, [controls, query, domain, exec]);

  // Keep the URL shareable without a navigation.
  useEffect(() => {
    const p = new URLSearchParams();
    if (domain !== "all") p.set("domain", domain);
    if (exec !== "all") p.set("executable", exec);
    const qs = p.toString();
    window.history.replaceState(null, "", qs ? `/controls?${qs}` : "/controls");
  }, [domain, exec]);

  // "/" jumps to search, as in most data tools. Not while typing elsewhere.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement;
      if (e.key !== "/" || t.closest("input, textarea, select, [contenteditable]")) return;
      e.preventDefault();
      search.current?.focus();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const filtered = rows.length !== controls.length;

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col gap-5">
        <div className="flex flex-col gap-2">
          <label htmlFor="control-search" className="label">
            Search
          </label>
          <div className="relative w-full max-w-[34rem]">
            <MagnifyingGlassIcon
              size={18}
              weight="bold"
              aria-hidden
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-3"
            />
            <input
              ref={search}
              id="control-search"
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ref, title, clause or suite"
              autoComplete="off"
              className="field w-full border-2 border-ink pl-[40px] pr-[64px] text-base"
            />
            {!query && <kbd className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 border border-control px-2 font-mono text-xs text-ink-3">
              /
            </kbd>}
          </div>
        </div>

        <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
          <FilterGroup label="Domain">
            <Chip on={domain === "all"} onClick={() => setDomain("all")}>All</Chip>
            {DOMAINS.map((d) => (
              <Chip key={d} on={domain === d} onClick={() => setDomain(d)}>
                {DOMAIN_LABEL[d]}
              </Chip>
            ))}
          </FilterGroup>
          <FilterGroup label="Type">
            <Chip on={exec === "all"} onClick={() => setExec("all")}>All</Chip>
            <Chip on={exec === "true"} onClick={() => setExec("true")}>Executable</Chip>
            <Chip on={exec === "false"} onClick={() => setExec("false")}>Documented</Chip>
          </FilterGroup>
        </div>
      </div>

      <p className="m-0 flex flex-wrap items-center gap-3 text-sm text-ink-2" aria-live="polite">
        <span>
          Showing <strong className="font-mono text-ink">{rows.length}</strong> of{" "}
          <span className="font-mono">{controls.length}</span> controls
        </span>
        {filtered && (
          <button
            type="button"
            className="link inline-flex items-center gap-1 font-semibold"
            onClick={() => { setQuery(""); setDomain("all"); setExec("all"); }}
          >
            <XIcon size={14} weight="bold" aria-hidden />
            Clear filters
          </button>
        )}
      </p>

      {rows.length > 0 ? (
        <ControlTable controls={rows} />
      ) : (
        <div className="border-2 border-dashed border-control bg-surface px-5 py-7">
          <p className="m-0 text-lg font-semibold text-ink">No control matches.</p>
          <p className="m-0 mt-2 text-base text-ink-2">
            Nothing in the library fits
            {query ? <> &ldquo;<span className="font-mono">{query}</span>&rdquo;</> : null} with
            these filters. Clear them to see all {controls.length}.
          </p>
        </div>
      )}
    </div>
  );
}

function FilterGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div role="group" aria-label={label} className="min-w-0">
      <p className="label m-0">{label}</p>
      <div className="scroll-x edge-fade mt-2 flex flex-nowrap gap-2 pb-1 md:flex-wrap">{children}</div>
    </div>
  );
}

function Chip({ on, onClick, children }: { on: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button type="button" aria-pressed={on} data-selected={on ? "true" : "false"} onClick={onClick} className="toggle">
      {children}
    </button>
  );
}
