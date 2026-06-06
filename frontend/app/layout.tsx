import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ReachGTM",
  description: "AI-powered multi-agent Go-To-Market strategy platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
