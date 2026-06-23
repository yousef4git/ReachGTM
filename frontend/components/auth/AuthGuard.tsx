"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { isAuthenticated } from "@/lib/auth";

// Routes reachable without a token. Everything else requires authentication.
const PUBLIC_PREFIXES = ["/login", "/register"];

function isPublic(pathname: string | null): boolean {
  if (!pathname) return false;
  return PUBLIC_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`));
}

/**
 * Client-side route guard. Static export has no server middleware, so auth is
 * enforced here: unauthenticated users hitting a protected route are redirected
 * to /login instead of rendering a page whose API calls would 401.
 */
export function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const publicRoute = isPublic(pathname);
  const [allowed, setAllowed] = useState(false);

  useEffect(() => {
    if (publicRoute) {
      setAllowed(true);
      return;
    }
    if (!isAuthenticated()) {
      setAllowed(false);
      router.replace("/login");
      return;
    }
    setAllowed(true);
  }, [pathname, publicRoute, router]);

  if (publicRoute) return <>{children}</>;

  if (!allowed) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-flare-600" />
      </div>
    );
  }

  return <>{children}</>;
}
