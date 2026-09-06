import type { SupabaseClient } from "@supabase/supabase-js";
import { redirect } from "next/navigation";
import { editingIsEnabled } from "@/lib/env";
import { createSupabaseServerClient } from "@/lib/supabase/server";

export const trackerProjectId = "pose-embed";

export async function hasOwnerAccess(supabase: SupabaseClient): Promise<boolean> {
  const { data, error } = await supabase
    .from("owner_access")
    .select("project_id")
    .eq("project_id", trackerProjectId)
    .maybeSingle();
  return !error && data?.project_id === trackerProjectId;
}

export async function requireOwner() {
  if (!editingIsEnabled()) redirect("/login?reason=editing-disabled");

  const supabase = await createSupabaseServerClient();
  if (!supabase) redirect("/login?reason=not-configured");

  const { data, error } = await supabase.auth.getClaims();
  const subject = typeof data?.claims?.sub === "string" ? data.claims.sub : null;
  if (error || !subject) redirect("/login?reason=sign-in");

  if (!(await hasOwnerAccess(supabase))) redirect("/login?reason=not-owner");
  return { supabase, projectId: trackerProjectId };
}
