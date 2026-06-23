import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // "standalone" matches the production Dockerfile (node server.js) and the
  // documented ECS Fargate deploy. "export" (static) broke every dynamic route
  // — e.g. /strategy/[id] 500s with "missing param in generateStaticParams"
  // because real IDs are never pre-rendered — and is incompatible with the
  // standalone server the Dockerfile builds.
  output: "standalone",
  images: { unoptimized: true },
  // Hide the on-screen Next.js dev indicator badge. Compile/runtime errors are
  // still reported in the terminal and overlay.
  devIndicators: false,
};

export default nextConfig;
