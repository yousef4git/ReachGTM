"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { FileText, MessageCircle, Newspaper, Megaphone, Upload } from "lucide-react";
import { ContentType } from "@/types";

const LABELS: Record<string, string> = {
  [ContentType.COLD_EMAIL]: "Cold Emails",
  [ContentType.LINKEDIN_POST]: "LinkedIn Posts",
  [ContentType.BLOG_OUTLINE]: "Blog Outlines",
  [ContentType.AD_COPY]: "Ad Copy",
};

const ICONS: Record<string, React.ReactNode> = {
  [ContentType.COLD_EMAIL]: <FileText className="h-4 w-4" />,
  [ContentType.LINKEDIN_POST]: <MessageCircle className="h-4 w-4" />,
  [ContentType.BLOG_OUTLINE]: <Newspaper className="h-4 w-4" />,
  [ContentType.AD_COPY]: <Megaphone className="h-4 w-4" />,
};

function SideLink({
  href,
  label,
  icon,
  pathname,
}: {
  href: string;
  label: string;
  icon: React.ReactNode;
  pathname: string;
}) {
  const active = pathname === href || pathname.startsWith(href.split("?")[0]);
  return (
    <Link
      href={href}
      className={cn(
        "flex items-center gap-2.5 rounded-lg px-3 py-2 text-[0.8125rem] font-medium transition-colors",
        active
          ? "bg-flare-50 text-flare-700"
          : "text-ink-muted hover:bg-sunken hover:text-ink"
      )}
    >
      {icon}
      {label}
    </Link>
  );
}

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-60 shrink-0 border-r border-hairline bg-surface">
      <div className="p-4">
        <p className="eyebrow mb-2.5 px-3">Content Types</p>
        <div className="space-y-1">
          {Object.values(ContentType).map((type) => (
            <SideLink
              key={type}
              href={`/content?type=${type}`}
              label={LABELS[type] ?? type}
              icon={ICONS[type]}
              pathname={pathname}
            />
          ))}
        </div>

        <div className="mt-6 border-t border-hairline pt-4">
          <p className="eyebrow mb-2.5 px-3">Actions</p>
          <SideLink
            href="/content/create"
            label="Create Content"
            icon={<FileText className="h-4 w-4" />}
            pathname={pathname}
          />
          <SideLink
            href="/knowledge"
            label="Upload Knowledge"
            icon={<Upload className="h-4 w-4" />}
            pathname={pathname}
          />
        </div>
      </div>
    </aside>
  );
}
