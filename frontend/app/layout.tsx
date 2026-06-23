import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { AppChrome } from "@/components/layout/AppChrome";

export const metadata: Metadata = {
  title: "ReachGTM",
  description: "AI-powered multi-agent Go-To-Market strategy platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <AppChrome>{children}</AppChrome>
        </Providers>
      </body>
    </html>
  );
}
