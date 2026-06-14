"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { LayoutDashboard, FileText, BookOpen, Sparkles } from "lucide-react";

export function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="border-b bg-white px-6 py-3">
      <div className="mx-auto flex max-w-7xl items-center justify-between">
        <Link href="/dashboard" className="text-lg font-bold text-gray-900">
          ReachGTM
        </Link>

        <div className="flex items-center gap-1">
          <NavLink href="/dashboard" label="Dashboard" icon={<LayoutDashboard className="h-4 w-4" />} pathname={pathname} />
          <NavLink href="/strategy/new" label="New Strategy" icon={<Sparkles className="h-4 w-4" />} pathname={pathname} />
          <NavLink href="/content" label="Content" icon={<FileText className="h-4 w-4" />} pathname={pathname} />
          <NavLink href="/knowledge" label="Knowledge" icon={<BookOpen className="h-4 w-4" />} pathname={pathname} />
        </div>
      </div>
    </nav>
  );
}

function NavLink({ href, label, icon, pathname }: { href: string; label: string; icon: React.ReactNode; pathname: string }) {
  const active = pathname.startsWith(href);
  return (
    <Link
      href={href}
      className={cn(
        "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
        active
          ? "bg-blue-50 text-blue-700"
          : "text-gray-500 hover:bg-gray-100 hover:text-gray-700"
      )}
    >
      {icon}
      {label}
    </Link>
  );
}
