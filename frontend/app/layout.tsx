import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { AppChrome } from "@/components/layout/AppChrome";

export const metadata: Metadata = {
  title: "ReachGTM — Go-to-market, on autopilot",
  description: "AI-powered multi-agent Go-To-Market strategy platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-scroll-behavior="smooth">
      <head>
        {/* Distinctive type: Fraunces (editorial display) + Hanken Grotesk (UI)
            + JetBrains Mono (data). Loaded over the network so the static export
            never depends on a build-time font fetch. */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Hanken+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <Providers>
          <AppChrome>{children}</AppChrome>
        </Providers>
      </body>
    </html>
  );
}
