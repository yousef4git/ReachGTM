"use client";

import { usePathname } from "next/navigation";
import { Navbar } from "./Navbar";
import { AuthGuard } from "@/components/auth/AuthGuard";

const PUBLIC_PREFIXES = ["/login", "/register"];

function isPublic(pathname: string | null): boolean {
  if (!pathname) return false;
  return PUBLIC_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`));
}

/** Renders the app chrome: navbar (hidden on auth pages) + the auth guard. */
export function AppChrome({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const publicRoute = isPublic(pathname);

  return (
    <>
      {!publicRoute && <Navbar />}
      <AuthGuard>{children}</AuthGuard>
    </>
  );
}
