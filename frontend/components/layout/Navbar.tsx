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
  Compass,
  Users,
  LogOut,
} from "lucide-react";

const LINKS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/strategy/new", label: "New Strategy", icon: Compass },
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
    <header className="sticky top-0 z-40 border-b border-hairline bg-canvas/80 backdrop-blur-xl">
      <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-5 sm:px-8">
        <Link
          href="/dashboard"
          className="flex items-center gap-2.5 transition-opacity hover:opacity-80"
        >
          <LogoMark className="h-8 w-8" />
          <span className="hidden text-[0.9375rem] font-semibold tracking-tight text-ink sm:inline">
            Reach<span className="text-ink-muted">GTM</span>
          </span>
        </Link>

        <div className="hidden items-center gap-0.5 md:flex">
          {LINKS.map(({ href, label, icon: Icon }) => {
            const active =
              pathname === href || pathname.startsWith(`${href}/`);
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "relative flex items-center gap-1.5 px-3.5 py-2 text-[0.8125rem] font-medium transition-colors duration-200",
                  active
                    ? "text-ink"
                    : "text-ink-muted hover:text-ink"
                )}
              >
                <Icon className="h-4 w-4" strokeWidth={2} />
                {label}
                {active && (
                  <span className="absolute inset-x-2.5 -bottom-[1px] h-[2px] rounded-full bg-flare-600" />
                )}
              </Link>
            );
          })}
        </div>

        <div ref={menuRef} className="relative flex items-center gap-3">
          <span className="hidden items-center gap-1.5 sm:flex">
            <span className="h-1.5 w-1.5 rounded-full bg-success" />
            <span className="eyebrow !text-ink-muted">Live</span>
          </span>
          <button
            onClick={() => setMenuOpen((v) => !v)}
            className="flex h-9 w-9 items-center justify-center rounded-full bg-ink text-[0.8125rem] font-semibold text-canvas transition-transform active:scale-95"
            aria-label="Account menu"
          >
            {(role ?? "U").charAt(0).toUpperCase()}
          </button>

          {menuOpen && (
            <div className="animate-rise absolute right-0 top-12 w-56 overflow-hidden rounded-xl border border-hairline bg-surface p-1.5 shadow-lg">
              <div className="px-3 py-2.5">
                <p className="eyebrow">Signed in</p>
                <p className="mt-1 text-[0.875rem] font-semibold capitalize text-ink">
                  {role ?? "Member"}
                </p>
              </div>
              <div className="rule my-1" />
              <button
                onClick={logout}
                className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-[0.8125rem] font-medium text-ink transition-colors hover:bg-sunken"
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
