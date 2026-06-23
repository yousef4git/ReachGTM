"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import { getRole } from "@/lib/auth";
import { LogoMark } from "@/components/brand/Logo";
import {
  LayoutDashboard,
  FileText,
  BookOpen,
  Sparkles,
  Users,
  LogOut,
} from "lucide-react";

const LINKS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/strategy/new", label: "New Strategy", icon: Sparkles },
  { href: "/content", label: "Content", icon: FileText },
  { href: "/knowledge", label: "Knowledge", icon: BookOpen },
  { href: "/team", label: "Team", icon: Users },
];

export function Navbar() {
  const pathname = usePathname();
  const { logout } = useAuth();
  const [role, setRole] = useState<string | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => setRole(getRole()), []);

  // Close the profile menu on outside click.
  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  return (
    <header className="sticky top-0 z-40 border-b border-hairline bg-surface/85 backdrop-blur-xl">
      <nav className="mx-auto flex h-14 max-w-7xl items-center justify-between gap-4 px-5">
        <Link
          href="/dashboard"
          className="flex items-center gap-2 transition-opacity hover:opacity-80"
        >
          <LogoMark className="h-7 w-7" />
          <span className="text-[0.9375rem] font-semibold tracking-tight text-ink">
            ReachGTM
          </span>
        </Link>

        <div className="hidden items-center gap-0.5 md:flex">
          {LINKS.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || pathname.startsWith(`${href}/`);
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "relative flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[0.8125rem] font-medium transition-colors duration-200",
                  active
                    ? "text-blue-700"
                    : "text-ink-muted hover:bg-black/[0.04] hover:text-ink"
                )}
              >
                {active && (
                  <span className="absolute inset-0 -z-10 rounded-lg bg-blue-50" />
                )}
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            );
          })}
        </div>

        <div ref={menuRef} className="relative">
          <button
            onClick={() => setMenuOpen((v) => !v)}
            className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-[0.8125rem] font-semibold text-white transition-transform active:scale-95"
            aria-label="Account menu"
          >
            {(role ?? "U").charAt(0).toUpperCase()}
          </button>

          {menuOpen && (
            <div className="animate-rise absolute right-0 top-11 w-52 overflow-hidden rounded-xl border border-hairline bg-surface p-1 shadow-lg">
              <div className="px-3 py-2">
                <p className="text-[0.8125rem] font-medium text-ink">Signed in</p>
                {role && (
                  <p className="mt-0.5 text-xs capitalize text-ink-muted">{role}</p>
                )}
              </div>
              <div className="my-1 h-px bg-hairline" />
              <button
                onClick={logout}
                className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-[0.8125rem] font-medium text-ink transition-colors hover:bg-black/[0.04]"
              >
                <LogOut className="h-4 w-4 text-ink-muted" />
                Sign out
              </button>
            </div>
          )}
        </div>
      </nav>
    </header>
  );
}
