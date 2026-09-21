"use client";

import { useState } from "react";

import { ROLE_LABEL, type Role } from "@/lib/engagement";

/**
 * The role switch is a lens, not a different product.
 *
 * It changes framing and permissions and NEVER a number. Dressing it up as a
 * dramatic mode switch — a theme change, a layout change — would imply the
 * results differ by audience. They do not. [PRD 4.4, UX 5]
 *
 * Day 1 ships the control and the disclosure band. Day 9 wires it to content.
 */
export function RoleSwitch() {
  const [role, setRole] = useState<Role>("consultant");

  return (
    <div>
      <label
        htmlFor="role-switch"
        className="block text-2xs uppercase tracking-[0.14em] text-n-400"
      >
        Viewing as
      </label>
      <select
        id="role-switch"
        value={role}
        onChange={(e) => setRole(e.target.value as Role)}
        className="mt-1 rounded-sm border border-n-200 bg-n-0 px-2 py-1 text-sm text-n-800"
      >
        {(Object.keys(ROLE_LABEL) as Role[]).map((r) => (
          <option key={r} value={r}>
            {ROLE_LABEL[r]}
          </option>
        ))}
      </select>

      {role === "client" && (
        <p className="m-0 mt-2 text-2xs text-n-500">
          Same results, presented for the data fiduciary.
        </p>
      )}
    </div>
  );
}
