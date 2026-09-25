"use client";

import { useRoleSwitch } from "./RoleProvider";
import { ROLE_LABEL, type Role } from "@/lib/engagement";

/**
 * The role switch is a lens, not a different product: it changes framing and
 * permissions and never a number. [PRD 4.4, UX 5]
 *
 * Wired to `RoleProvider`: setting a role updates the cookie `getRole()`
 * reads server-side and calls `router.refresh()`, so server-rendered
 * framing changes on the same click as this component's own.
 */
export function RoleSwitch() {
  const { role, setRole } = useRoleSwitch();

  return (
    <div className="relative">
      <label htmlFor="role-switch" className="sr-only">
        Viewing as
      </label>
      <select
        id="role-switch"
        value={role}
        onChange={(e) => setRole(e.target.value as Role)}
        className="field cursor-pointer border-on-cobalt bg-surface font-medium"
      >
        {(Object.keys(ROLE_LABEL) as Role[]).map((r) => (
          <option key={r} value={r}>
            Viewing as {ROLE_LABEL[r]}
          </option>
        ))}
      </select>

      {role === "client" && (
        <p className="m-0 mt-1 text-xs text-on-cobalt-2">
          Same results, presented for the data fiduciary.
        </p>
      )}
    </div>
  );
}
