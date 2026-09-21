import { DEMO_RUNS } from "@/lib/demoData";
import { RunDetailClient } from "./RunDetailClient";

export function generateStaticParams() {
  return DEMO_RUNS.map((run) => ({ id: run.id }));
}

interface RunDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function RunDetailPage({ params }: RunDetailPageProps) {
  const { id } = await params;
  return <RunDetailClient runId={id} />;
}
