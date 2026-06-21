import StrategyDetailClient from "./StrategyDetailClient";

// Static export (Cloudflare Pages SPA): Next's `output: export` requires a
// dynamic route to pre-render at least one param, so we emit a single throwaway
// placeholder page. Real strategy IDs are never pre-rendered — the
// public/_redirects rule `/strategy/* -> /index.html` serves the SPA shell and
// the client resolves the [id] at runtime via useStrategy(). generateStaticParams
// must live in this server component — a "use client" module cannot export it.
export function generateStaticParams() {
  return [{ id: "_placeholder" }];
}

export default async function StrategyPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <StrategyDetailClient id={id} />;
}
