import { cookies } from "next/headers";

import type { Role } from "./engagement";

const COOKIE = "assurelens-role";

/**
 * The role switch's server-side read: a plain, non-sensitive cookie the
 * client sets directly (no route handler needed) and Server Components read
 * on every render. [PRD 4.4] Paired with `RoleSwitch`'s `router.refresh()`
 * on change, so server-rendered framing (EvidenceViewer, the roadmap's
 * column set) updates on the same click as the client-side context does.
 */
export async function getRole(): Promise<Role> {
  const store = await cookies();
  return store.get(COOKIE)?.value === "client" ? "client" : "consultant";
}
