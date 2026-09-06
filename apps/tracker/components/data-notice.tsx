import type { LoadedPlan } from "@/lib/schema";

export function DataNotice({ plan }: { plan: LoadedPlan }) {
  if (plan.dataSource === "supabase") return null;

  return (
    <aside className="data-notice" role="status">
      <strong>Read-only plan snapshot.</strong> Live progress is unavailable, so this
      page is showing the checked-in schedule from September 6, 2026.
    </aside>
  );
}
