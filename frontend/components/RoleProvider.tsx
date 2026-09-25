"use client";

import { useRouter } from "next/navigation";
import { createContext, useContext, useState } from "react";

import type { Role } from "@/lib/engagement";

const COOKIE = "assurelens-role";

const RoleContext = createContext<{ role: Role; setRole: (role: Role) => void } | null>(null);

/**
 * Wraps the whole app (`app/layout.tsx`) so any component, server or
 * client, can know the current role: a Server Component reads the cookie
 * directly via `getRole()`; a Client Component anywhere in the tree reads
 * this context, which `router.refresh()` keeps in step with the cookie on
 * every switch. [PRD 4.4]
 */
export function RoleProvider({
  initialRole, children,
}: {
  initialRole: Role;
  children: React.ReactNode;
}) {
  const [role, setRoleState] = useState<Role>(initialRole);
  const router = useRouter();

  function setRole(next: Role) {
    setRoleState(next);
    document.cookie = `${COOKIE}=${next}; path=/; max-age=31536000; samesite=lax`;
    router.refresh();
  }

  return <RoleContext.Provider value={{ role, setRole }}>{children}</RoleContext.Provider>;
}

export function useRole(): Role {
  return useContext(RoleContext)?.role ?? "consultant";
}

export function useRoleSwitch() {
  const ctx = useContext(RoleContext);
  if (ctx === null) throw new Error("useRoleSwitch must be used within RoleProvider");
  return ctx;
}
