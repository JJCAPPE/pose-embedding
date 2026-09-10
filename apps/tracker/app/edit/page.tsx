import type { Metadata } from "next";
import { EditDashboard } from "@/components/editor-forms";
import { requireOwner } from "@/lib/auth";
import { loadPlanFromSupabase } from "@/lib/data";
import { projectProgress } from "@/lib/domain";

export const metadata: Metadata = {
  title: "Update",
};

export default async function EditDashboardPage() {
  const { supabase } = await requireOwner();
  const plan = await loadPlanFromSupabase(supabase);

  return (
    <EditDashboard
      closedWeeks={plan.weeks.filter((week) => week.state === "closed").length}
      progress={projectProgress(plan)}
      sources={plan.sources}
      weekSourcesCount={plan.weekSources.length}
      weeks={plan.weeks}
    />
  );
}
