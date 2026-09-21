import { ENGAGEMENT } from "@/lib/engagement";
import { RoleSwitch } from "./RoleSwitch";

/**
 * A masthead, not a nav bar: the entity name carries the weight and the
 * product name is secondary, because a workpaper is headed by whose it is.
 * [UX 3]
 */
export function Masthead() {
  return (
    <header className="border-b border-n-200 bg-n-0">
      <div className="mx-auto flex max-w-content flex-wrap items-end justify-between gap-4 px-4 py-4">
        <div>
          <p className="m-0 text-2xs uppercase tracking-[0.14em] text-n-400">
            AssureLens
          </p>
          <h1 className="mt-1 text-lg">{ENGAGEMENT.organisation}</h1>
          <p className="m-0 mt-1 text-xs text-n-500">
            {ENGAGEMENT.engagementName} &middot; {ENGAGEMENT.city}
          </p>
        </div>

        <div className="flex items-end gap-6">
          <div className="text-right">
            <p className="m-0 text-2xs uppercase tracking-[0.14em] text-n-400">
              DPDP obligations commence
            </p>
            <p className="m-0 mt-1 font-mono text-sm text-n-700">
              {ENGAGEMENT.complianceDeadline}
            </p>
          </div>
          <RoleSwitch />
        </div>
      </div>
    </header>
  );
}
