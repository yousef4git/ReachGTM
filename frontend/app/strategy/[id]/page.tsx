import StrategyDetailClient from "./StrategyDetailClient";

// Server-rendered on demand (output: "standalone"). The client component
// resolves the strategy by id at runtime via useStrategy().
export default async function StrategyPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <StrategyDetailClient id={id} />;
}
