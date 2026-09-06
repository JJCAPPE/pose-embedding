import { requireOwner } from "@/lib/auth";
import { loadPlanFromSupabase } from "@/lib/data";

export async function GET() {
  const { supabase, projectId } = await requireOwner();
  const [plan, activity] = await Promise.all([
    loadPlanFromSupabase(supabase),
    supabase
      .from("activity_log")
      .select(
        "id, project_id, actor_id, table_name, row_id, action, before_state, after_state, occurred_at",
      )
      .eq("project_id", projectId)
      .order("occurred_at", { ascending: true }),
  ]);

  if (activity.error) {
    return Response.json({ error: "The private activity log could not be exported." }, { status: 500 });
  }

  return new Response(
    `${JSON.stringify(
      {
        exportedAt: new Date().toISOString(),
        plan,
        activityLog: activity.data,
      },
      null,
      2,
    )}\n`,
    {
      headers: {
        "Cache-Control": "no-store",
        "Content-Disposition": "attachment; filename=pose-embed-owner-archive.json",
        "Content-Type": "application/json; charset=utf-8",
      },
    },
  );
}
