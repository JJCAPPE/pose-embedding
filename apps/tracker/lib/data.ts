import { cacheLife, cacheTag } from "next/cache";
import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import { supabaseEnvironment } from "@/lib/env";
import { researchPlanSchema, type LoadedPlan, type ResearchPlan } from "@/lib/schema";
import { seedPlan } from "@/lib/seed";

type DbRow = Record<string, unknown>;

function text(row: DbRow, key: string, fallback = ""): string {
  const value = row[key];
  return typeof value === "string" ? value : fallback;
}

function integer(row: DbRow, key: string, fallback = 0): number {
  const value = row[key];
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function bool(row: DbRow, key: string, fallback = false): boolean {
  const value = row[key];
  return typeof value === "boolean" ? value : fallback;
}

function nullableText(row: DbRow, key: string): string | null {
  const value = row[key];
  return typeof value === "string" ? value : null;
}

function stringArray(row: DbRow, key: string): string[] {
  const value = row[key];
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

function rows(value: unknown): DbRow[] {
  return Array.isArray(value)
    ? value.filter(
        (item): item is DbRow =>
          typeof item === "object" && item !== null && !Array.isArray(item),
      )
    : [];
}

function mapPlan(
  projectRow: DbRow,
  weekRows: DbRow[],
  taskRows: DbRow[],
  gateRows: DbRow[],
  sourceRows: DbRow[],
  weekSourceRows: DbRow[],
): ResearchPlan {
  const projectId = text(projectRow, "id");
  const weeks = weekRows.map((week) => {
    const weekId = text(week, "id");
    return {
      id: weekId,
      projectId,
      number: integer(week, "number"),
      startDate: text(week, "start_date"),
      endDate: text(week, "end_date"),
      phase: text(week, "phase"),
      title: text(week, "title"),
      objective: text(week, "objective"),
      deliverable: text(week, "deliverable"),
      risks: stringArray(week, "risks"),
      advisorPrompt: text(week, "advisor_prompt"),
      reflection: text(week, "reflection"),
      plannedMinutes: integer(week, "planned_minutes"),
      actualMinutes: integer(week, "actual_minutes"),
      state: text(week, "state", "planned"),
      closedAt: nullableText(week, "closed_at"),
      version: integer(week, "version", 1),
      tasks: taskRows
        .filter((task) => text(task, "week_id") === weekId)
        .map((task) => ({
          id: text(task, "id"),
          weekId,
          position: integer(task, "position"),
          title: text(task, "title"),
          details: text(task, "details"),
          expectedOutput: text(task, "expected_output"),
          required: bool(task, "required"),
          estimateMinutes: integer(task, "estimate_minutes"),
          state: text(task, "state", "todo"),
          completionNote: text(task, "completion_note"),
          evidenceUrl: nullableText(task, "evidence_url"),
          completedAt: nullableText(task, "completed_at"),
          version: integer(task, "version", 1),
        }))
        .sort((a, b) => a.position - b.position),
      gates: gateRows
        .filter((gate) => text(gate, "week_id") === weekId)
        .map((gate) => ({
          id: text(gate, "id"),
          weekId,
          position: integer(gate, "position"),
          criterion: text(gate, "criterion"),
          required: bool(gate, "required"),
          state: text(gate, "state", "pending"),
          evidence: text(gate, "evidence"),
          waiverReason: text(gate, "waiver_reason"),
          decidedAt: nullableText(gate, "decided_at"),
          version: integer(gate, "version", 1),
        }))
        .sort((a, b) => a.position - b.position),
    };
  });

  return researchPlanSchema.parse({
    schemaVersion: "1.0.0",
    generatedAt: new Date().toISOString(),
    project: {
      id: projectId,
      slug: text(projectRow, "slug"),
      title: text(projectRow, "title"),
      researchQuestion: text(projectRow, "research_question"),
      summary: text(projectRow, "summary"),
      startDate: text(projectRow, "start_date"),
      endDate: text(projectRow, "end_date"),
      timezone: text(projectRow, "timezone"),
      visibility: "public",
      version: integer(projectRow, "version", 1),
    },
    manualActions: seedPlan.manualActions,
    protocol: seedPlan.protocol,
    weeks: weeks.sort((a, b) => a.number - b.number),
    sources: sourceRows.map((source) => ({
      id: text(source, "id"),
      title: text(source, "title"),
      authors: text(source, "authors"),
      year: integer(source, "year"),
      canonicalUrl: text(source, "canonical_url"),
      purpose: text(source, "purpose"),
      verifiedAt: text(source, "verified_at"),
      version: integer(source, "version", 1),
    })),
    weekSources: weekSourceRows.map((weekSource) => ({
      weekId: text(weekSource, "week_id"),
      sourceId: text(weekSource, "source_id"),
      purpose: text(weekSource, "purpose"),
      priority: text(weekSource, "priority", "recommended"),
      version: integer(weekSource, "version", 1),
    })),
  });
}

export async function loadPlanFromSupabase(
  supabase: SupabaseClient,
): Promise<ResearchPlan> {
  const { data: projectData, error: projectError } = await supabase
    .from("projects")
    .select(
      "id, slug, title, research_question, summary, start_date, end_date, timezone, visibility, version",
    )
    .eq("slug", "pose-embed")
    .eq("visibility", "public")
    .single();

  if (projectError || !projectData) {
    throw new Error(projectError?.message ?? "Published project not found.");
  }

  const projectId = text(projectData as DbRow, "id");
  const [weeks, tasks, gates, sources, weekSources] = await Promise.all([
    supabase
      .from("weeks")
      .select(
        "id, project_id, number, start_date, end_date, phase, title, objective, deliverable, risks, advisor_prompt, reflection, planned_minutes, actual_minutes, state, closed_at, version",
      )
      .eq("project_id", projectId)
      .order("number"),
    supabase
      .from("tasks")
      .select(
        "id, project_id, week_id, position, title, details, expected_output, required, estimate_minutes, state, completion_note, evidence_url, completed_at, version",
      )
      .eq("project_id", projectId)
      .order("position"),
    supabase
      .from("gates")
      .select(
        "id, project_id, week_id, position, criterion, required, state, evidence, waiver_reason, decided_at, version",
      )
      .eq("project_id", projectId)
      .order("position"),
    supabase
      .from("sources")
      .select(
        "id, project_id, title, authors, year, canonical_url, purpose, verified_at, version",
      )
      .eq("project_id", projectId)
      .order("year"),
    supabase
      .from("week_sources")
      .select("project_id, week_id, source_id, purpose, priority, version")
      .eq("project_id", projectId),
  ]);

  const firstError = [weeks, tasks, gates, sources, weekSources].find(
    (result) => result.error,
  )?.error;
  if (firstError) throw new Error(firstError.message);

  return mapPlan(
    projectData as DbRow,
    rows(weeks.data),
    rows(tasks.data),
    rows(gates.data),
    rows(sources.data),
    rows(weekSources.data),
  );
}

async function loadLivePlan(): Promise<LoadedPlan> {
  const environment = supabaseEnvironment();
  if (!environment) throw new Error("Supabase is not configured.");

  const supabase = createClient(environment.url, environment.publishableKey, {
    auth: {
      autoRefreshToken: false,
      detectSessionInUrl: false,
      persistSession: false,
    },
  });
  const plan = await loadPlanFromSupabase(supabase);
  return {
    ...plan,
    dataSource: "supabase",
    lastRefreshedAt: new Date().toISOString(),
  };
}

async function getCachedLivePlan(): Promise<LoadedPlan> {
  "use cache";
  cacheLife({ stale: 300, revalidate: 3600, expire: 31_536_000 });
  cacheTag("plan");
  return loadLivePlan();
}

export async function getPublicPlan(): Promise<LoadedPlan> {
  if (!supabaseEnvironment()) {
    return {
      ...seedPlan,
      dataSource: "seed",
      lastRefreshedAt: seedPlan.generatedAt,
    };
  }

  try {
    // Failed revalidation is not converted into a successful cached seed value.
    // Next can retain the last successful cache entry; a cold failure reaches the
    // checked-in fallback below.
    return await getCachedLivePlan();
  } catch (error) {
    console.error("No live tracker snapshot is available; using the plan seed.", error);
    return {
      ...seedPlan,
      dataSource: "seed",
      lastRefreshedAt: seedPlan.generatedAt,
    };
  }
}
