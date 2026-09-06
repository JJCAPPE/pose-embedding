import { editingIsEnabled } from "@/lib/env";
import { getRequestPublicPlan } from "@/lib/request-plan";

export async function GET() {
  const plan = await getRequestPublicPlan();
  return Response.json(
    {
      status: plan.dataSource === "supabase" ? "ok" : "degraded",
      dataSource: plan.dataSource,
      schemaVersion: plan.schemaVersion,
      planVersion: plan.project.version,
      lastRefreshedAt: plan.lastRefreshedAt,
      buildSha: process.env.VERCEL_GIT_COMMIT_SHA ?? "local",
      editingEnabled: editingIsEnabled(),
    },
    { headers: { "Cache-Control": "no-store" } },
  );
}
