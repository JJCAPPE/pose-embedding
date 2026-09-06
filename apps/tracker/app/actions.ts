"use server";

import { revalidatePath, updateTag } from "next/cache";
import { redirect } from "next/navigation";
import { z } from "zod";
import { hasOwnerAccess, requireOwner } from "@/lib/auth";
import { editingIsEnabled } from "@/lib/env";
import { gateStateSchema, taskStateSchema, weekStateSchema } from "@/lib/schema";
import { createSupabaseServerClient } from "@/lib/supabase/server";
import type { ActionState } from "@/lib/action-state";

const idSchema = z.string().min(1).max(100);
const versionSchema = z.coerce.number().int().positive();
const shortText = z.string().trim().min(1).max(500);
const longText = z.string().trim().max(10_000);

function formText(formData: FormData, name: string): string {
  const value = formData.get(name);
  return typeof value === "string" ? value : "";
}

function optionalHttpUrl(value: string): string | null {
  if (!value.trim()) return null;
  const url = new URL(value);
  if (url.protocol !== "https:" && url.protocol !== "http:") {
    throw new Error("Evidence links must use http or https.");
  }
  return url.toString();
}

function requiredHttpsUrl(value: string): string {
  const url = new URL(value);
  if (url.protocol !== "https:") {
    throw new Error("Canonical source links must use https.");
  }
  return url.toString();
}

function databaseError(message?: string): ActionState {
  return {
    status: "error",
    message: message ? `Update failed: ${message}` : "Update failed. Try again.",
  };
}

function conflictError(): ActionState {
  return {
    status: "conflict",
    message: "This record changed in another session. Refresh before trying again.",
  };
}

function refreshPlan(weekNumber?: number) {
  updateTag("plan");
  revalidatePath("/", "layout");
  revalidatePath("/edit");
  revalidatePath("/literature");
  if (weekNumber) {
    revalidatePath("/weeks/[number]", "page");
    revalidatePath(`/edit/weeks/${weekNumber}`);
  }
}

export async function loginAction(
  _previous: ActionState,
  formData: FormData,
): Promise<ActionState> {
  if (!editingIsEnabled()) {
    return {
      status: "error",
      message: "Editing is not enabled for this deployment.",
    };
  }

  const parsed = z
    .object({ email: z.email(), password: z.string().min(1).max(500) })
    .safeParse({
      email: formText(formData, "email"),
      password: formText(formData, "password"),
    });
  if (!parsed.success) {
    return { status: "error", message: "Enter a valid email and password." };
  }

  const supabase = await createSupabaseServerClient();
  if (!supabase) return databaseError("Supabase is not configured.");

  const { data, error } = await supabase.auth.signInWithPassword(parsed.data);
  if (error || !data.user) {
    return { status: "error", message: "The email or password is incorrect." };
  }

  if (!(await hasOwnerAccess(supabase))) {
    await supabase.auth.signOut();
    return { status: "error", message: "This account is not the project owner." };
  }

  redirect("/edit");
}

export async function logoutAction() {
  const supabase = await createSupabaseServerClient();
  if (supabase) await supabase.auth.signOut();
  redirect("/");
}

export async function updateWeekAction(
  _previous: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const parsed = z
    .object({
      id: idSchema,
      number: z.coerce.number().int().min(1).max(14),
      version: versionSchema,
      title: shortText,
      phase: shortText,
      objective: longText.pipe(z.string().min(1)),
      deliverable: longText.pipe(z.string().min(1)),
      risks: longText,
      advisorPrompt: longText.pipe(z.string().min(1)),
      reflection: longText,
      plannedMinutes: z.coerce.number().int().min(0).max(10_080),
      actualMinutes: z.coerce.number().int().min(0).max(10_080),
      state: weekStateSchema.exclude(["closed"]),
    })
    .safeParse({
      id: formText(formData, "id"),
      number: formText(formData, "number"),
      version: formText(formData, "version"),
      title: formText(formData, "title"),
      phase: formText(formData, "phase"),
      objective: formText(formData, "objective"),
      deliverable: formText(formData, "deliverable"),
      risks: formText(formData, "risks"),
      advisorPrompt: formText(formData, "advisorPrompt"),
      reflection: formText(formData, "reflection"),
      plannedMinutes: formText(formData, "plannedMinutes"),
      actualMinutes: formText(formData, "actualMinutes"),
      state: formText(formData, "state"),
    });

  if (!parsed.success) {
    return { status: "error", message: "Review the week fields and try again." };
  }
  const { supabase } = await requireOwner();
  const { data, error } = await supabase
    .from("weeks")
    .update({
      title: parsed.data.title,
      phase: parsed.data.phase,
      objective: parsed.data.objective,
      deliverable: parsed.data.deliverable,
      risks: parsed.data.risks
        .split("\n")
        .map((risk) => risk.trim())
        .filter(Boolean),
      advisor_prompt: parsed.data.advisorPrompt,
      reflection: parsed.data.reflection,
      planned_minutes: parsed.data.plannedMinutes,
      actual_minutes: parsed.data.actualMinutes,
      state: parsed.data.state,
    })
    .eq("id", parsed.data.id)
    .eq("version", parsed.data.version)
    .select("version")
    .maybeSingle();

  if (error) return databaseError(error.message);
  if (!data) return conflictError();
  refreshPlan(parsed.data.number);
  return { status: "success", message: "Week details saved." };
}

export async function updateTaskAction(
  _previous: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const parsed = z
    .object({
      id: idSchema,
      weekNumber: z.coerce.number().int().min(1).max(14),
      version: versionSchema,
      position: z.coerce.number().int().positive().max(32_767),
      title: shortText,
      details: longText,
      expectedOutput: longText.pipe(z.string().min(1)),
      estimateMinutes: z.coerce.number().int().min(0).max(10_080),
      state: taskStateSchema,
      completionNote: longText,
      evidenceUrl: z.string().trim().max(2_000),
      required: z.boolean(),
    })
    .safeParse({
      id: formText(formData, "id"),
      weekNumber: formText(formData, "weekNumber"),
      version: formText(formData, "version"),
      position: formText(formData, "position"),
      title: formText(formData, "title"),
      details: formText(formData, "details"),
      expectedOutput: formText(formData, "expectedOutput"),
      estimateMinutes: formText(formData, "estimateMinutes"),
      state: formText(formData, "state"),
      completionNote: formText(formData, "completionNote"),
      evidenceUrl: formText(formData, "evidenceUrl"),
      required: formData.get("required") === "on",
    });

  if (!parsed.success) {
    return { status: "error", message: "Review the task update and try again." };
  }

  let evidenceUrl: string | null;
  try {
    evidenceUrl = optionalHttpUrl(parsed.data.evidenceUrl);
  } catch (error) {
    return { status: "error", message: (error as Error).message };
  }

  const { supabase } = await requireOwner();
  const { data: current, error: readError } = await supabase
    .from("tasks")
    .select("required, version")
    .eq("id", parsed.data.id)
    .maybeSingle();
  if (readError) return databaseError(readError.message);
  if (!current || current.version !== parsed.data.version) return conflictError();

  if (parsed.data.state === "skipped" && parsed.data.required) {
    return { status: "error", message: "A required task cannot be skipped." };
  }
  if (current.required && !parsed.data.required && !parsed.data.completionNote) {
    return {
      status: "error",
      message: "Explain why this task is being changed from required to optional.",
    };
  }

  const { data, error } = await supabase
    .from("tasks")
    .update({
      position: parsed.data.position,
      title: parsed.data.title,
      details: parsed.data.details,
      expected_output: parsed.data.expectedOutput,
      estimate_minutes: parsed.data.estimateMinutes,
      required: parsed.data.required,
      state: parsed.data.state,
      completion_note: parsed.data.completionNote,
      evidence_url: evidenceUrl,
    })
    .eq("id", parsed.data.id)
    .eq("version", parsed.data.version)
    .select("version")
    .maybeSingle();

  if (error) return databaseError(error.message);
  if (!data) return conflictError();
  refreshPlan(parsed.data.weekNumber);
  return { status: "success", message: "Task updated." };
}

export async function createTaskAction(
  _previous: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const parsed = z
    .object({
      weekId: idSchema,
      weekNumber: z.coerce.number().int().min(1).max(14),
      title: shortText,
      details: longText,
      expectedOutput: longText.pipe(z.string().min(1)),
      estimateMinutes: z.coerce.number().int().min(0).max(10_080),
      required: z.boolean(),
    })
    .safeParse({
      weekId: formText(formData, "weekId"),
      weekNumber: formText(formData, "weekNumber"),
      title: formText(formData, "title"),
      details: formText(formData, "details"),
      expectedOutput: formText(formData, "expectedOutput"),
      estimateMinutes: formText(formData, "estimateMinutes"),
      required: formData.get("required") === "on",
    });
  if (!parsed.success) {
    return { status: "error", message: "Review the new task fields and try again." };
  }

  const { supabase, projectId } = await requireOwner();
  const { data: lastTask, error: positionError } = await supabase
    .from("tasks")
    .select("position")
    .eq("week_id", parsed.data.weekId)
    .order("position", { ascending: false })
    .limit(1)
    .maybeSingle();
  if (positionError) return databaseError(positionError.message);

  const position = (lastTask?.position ?? 0) + 1;
  const { error } = await supabase.from("tasks").insert({
    id: `task-${crypto.randomUUID()}`,
    project_id: projectId,
    week_id: parsed.data.weekId,
    position,
    title: parsed.data.title,
    details: parsed.data.details,
    expected_output: parsed.data.expectedOutput,
    required: parsed.data.required,
    estimate_minutes: parsed.data.estimateMinutes,
    state: "todo",
  });
  if (error) return databaseError(error.message);
  refreshPlan(parsed.data.weekNumber);
  return { status: "success", message: "Task added to the week." };
}

export async function createGateAction(
  _previous: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const parsed = z
    .object({
      weekId: idSchema,
      weekNumber: z.coerce.number().int().min(1).max(14),
      criterion: longText.pipe(z.string().min(1)),
      required: z.boolean(),
    })
    .safeParse({
      weekId: formText(formData, "weekId"),
      weekNumber: formText(formData, "weekNumber"),
      criterion: formText(formData, "criterion"),
      required: formData.get("required") === "on",
    });
  if (!parsed.success) {
    return { status: "error", message: "Review the new gate fields and try again." };
  }

  const { supabase, projectId } = await requireOwner();
  const { data: lastGate, error: positionError } = await supabase
    .from("gates")
    .select("position")
    .eq("week_id", parsed.data.weekId)
    .order("position", { ascending: false })
    .limit(1)
    .maybeSingle();
  if (positionError) return databaseError(positionError.message);

  const { error } = await supabase.from("gates").insert({
    id: `gate-${crypto.randomUUID()}`,
    project_id: projectId,
    week_id: parsed.data.weekId,
    position: (lastGate?.position ?? 0) + 1,
    criterion: parsed.data.criterion,
    required: parsed.data.required,
    state: "pending",
  });
  if (error) return databaseError(error.message);
  refreshPlan(parsed.data.weekNumber);
  return { status: "success", message: "Gate added to the week." };
}

export async function updateGateAction(
  _previous: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const parsed = z
    .object({
      id: idSchema,
      weekNumber: z.coerce.number().int().min(1).max(14),
      version: versionSchema,
      position: z.coerce.number().int().positive().max(32_767),
      criterion: longText.pipe(z.string().min(1)),
      required: z.boolean(),
      state: gateStateSchema,
      evidence: longText,
      waiverReason: longText,
    })
    .safeParse({
      id: formText(formData, "id"),
      weekNumber: formText(formData, "weekNumber"),
      version: formText(formData, "version"),
      position: formText(formData, "position"),
      criterion: formText(formData, "criterion"),
      required: formData.get("required") === "on",
      state: formText(formData, "state"),
      evidence: formText(formData, "evidence"),
      waiverReason: formText(formData, "waiverReason"),
    });

  if (!parsed.success) {
    return { status: "error", message: "Review the gate update and try again." };
  }
  if (parsed.data.state === "met" && !parsed.data.evidence) {
    return { status: "error", message: "A met gate needs evidence." };
  }
  if (parsed.data.state === "waived" && !parsed.data.waiverReason) {
    return { status: "error", message: "A waived gate needs a reason." };
  }

  const { supabase } = await requireOwner();
  const { data: current, error: readError } = await supabase
    .from("gates")
    .select("required, version")
    .eq("id", parsed.data.id)
    .maybeSingle();
  if (readError) return databaseError(readError.message);
  if (!current || current.version !== parsed.data.version) return conflictError();
  if (current.required && !parsed.data.required && !parsed.data.waiverReason) {
    return {
      status: "error",
      message: "Explain why this gate is being changed from required to optional.",
    };
  }

  const { data, error } = await supabase
    .from("gates")
    .update({
      position: parsed.data.position,
      criterion: parsed.data.criterion,
      required: parsed.data.required,
      state: parsed.data.state,
      evidence: parsed.data.evidence,
      waiver_reason: parsed.data.waiverReason,
    })
    .eq("id", parsed.data.id)
    .eq("version", parsed.data.version)
    .select("version")
    .maybeSingle();

  if (error) return databaseError(error.message);
  if (!data) return conflictError();
  refreshPlan(parsed.data.weekNumber);
  return { status: "success", message: "Gate updated." };
}

export async function closeWeekAction(
  _previous: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const parsed = z
    .object({
      id: idSchema,
      number: z.coerce.number().int().min(1).max(14),
      version: versionSchema,
    })
    .safeParse({
      id: formText(formData, "id"),
      number: formText(formData, "number"),
      version: formText(formData, "version"),
    });
  if (!parsed.success) return databaseError("Invalid week record.");

  const { supabase } = await requireOwner();
  const [tasks, gates] = await Promise.all([
    supabase.from("tasks").select("state").eq("week_id", parsed.data.id).eq("required", true),
    supabase.from("gates").select("state").eq("week_id", parsed.data.id).eq("required", true),
  ]);
  if (tasks.error || gates.error) return databaseError(tasks.error?.message ?? gates.error?.message);

  const unfinishedTask = tasks.data.some((task) => task.state !== "done");
  const unresolvedGate = gates.data.some(
    (gate) => gate.state !== "met" && gate.state !== "waived",
  );
  if (unfinishedTask || unresolvedGate) {
    return {
      status: "error",
      message: "Complete every required task and decide every required gate first.",
    };
  }

  const { data, error } = await supabase
    .from("weeks")
    .update({ state: "closed" })
    .eq("id", parsed.data.id)
    .eq("version", parsed.data.version)
    .select("version")
    .maybeSingle();
  if (error) return databaseError(error.message);
  if (!data) return conflictError();
  refreshPlan(parsed.data.number);
  return { status: "success", message: "Week closed. The next week is ready." };
}

export async function reopenWeekAction(
  _previous: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const parsed = z
    .object({
      id: idSchema,
      number: z.coerce.number().int().min(1).max(14),
      version: versionSchema,
      reason: z.string().trim().min(1).max(2_000),
    })
    .safeParse({
      id: formText(formData, "id"),
      number: formText(formData, "number"),
      version: formText(formData, "version"),
      reason: formText(formData, "reason"),
    });
  if (!parsed.success) {
    return { status: "error", message: "A reopening reason is required." };
  }

  const { supabase } = await requireOwner();
  const { data, error } = await supabase
    .from("weeks")
    .update({
      state: "active",
      reopen_reason: parsed.data.reason,
    })
    .eq("id", parsed.data.id)
    .eq("version", parsed.data.version)
    .select("version")
    .maybeSingle();
  if (error) return databaseError(error.message);
  if (!data) return conflictError();
  refreshPlan(parsed.data.number);
  return { status: "success", message: "Week reopened and the reason was recorded." };
}

export async function updateReflectionAction(
  _previous: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const parsed = z
    .object({
      id: idSchema,
      number: z.coerce.number().int().min(1).max(14),
      version: versionSchema,
      reflection: longText,
    })
    .safeParse({
      id: formText(formData, "id"),
      number: formText(formData, "number"),
      version: formText(formData, "version"),
      reflection: formText(formData, "reflection"),
    });
  if (!parsed.success) return databaseError("Invalid reflection record.");

  const { supabase } = await requireOwner();
  const { data, error } = await supabase
    .from("weeks")
    .update({ reflection: parsed.data.reflection })
    .eq("id", parsed.data.id)
    .eq("version", parsed.data.version)
    .select("version")
    .maybeSingle();
  if (error) return databaseError(error.message);
  if (!data) return conflictError();
  refreshPlan(parsed.data.number);
  return { status: "success", message: "Reflection saved." };
}

const sourceFieldsSchema = z.object({
  title: shortText,
  authors: shortText,
  year: z.coerce.number().int().min(1900).max(2200),
  canonicalUrl: z.string().trim().min(1).max(2_000),
  purpose: longText.pipe(z.string().min(1)),
  verifiedAt: z.string().date(),
});

function sourceFields(formData: FormData) {
  return {
    title: formText(formData, "title"),
    authors: formText(formData, "authors"),
    year: formText(formData, "year"),
    canonicalUrl: formText(formData, "canonicalUrl"),
    purpose: formText(formData, "purpose"),
    verifiedAt: formText(formData, "verifiedAt"),
  };
}

export async function createSourceAction(
  _previous: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const parsed = sourceFieldsSchema.safeParse(sourceFields(formData));
  if (!parsed.success) {
    return { status: "error", message: "Review the new source fields and try again." };
  }

  let canonicalUrl: string;
  try {
    canonicalUrl = requiredHttpsUrl(parsed.data.canonicalUrl);
  } catch (error) {
    return { status: "error", message: (error as Error).message };
  }

  const { supabase, projectId } = await requireOwner();
  const { error } = await supabase.from("sources").insert({
    id: `source-${crypto.randomUUID()}`,
    project_id: projectId,
    title: parsed.data.title,
    authors: parsed.data.authors,
    year: parsed.data.year,
    canonical_url: canonicalUrl,
    purpose: parsed.data.purpose,
    verified_at: parsed.data.verifiedAt,
  });
  if (error) return databaseError(error.message);
  refreshPlan();
  return { status: "success", message: "Source added to the ledger." };
}

export async function updateSourceAction(
  _previous: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const parsed = sourceFieldsSchema
    .extend({ id: idSchema, version: versionSchema })
    .safeParse({
      id: formText(formData, "id"),
      version: formText(formData, "version"),
      ...sourceFields(formData),
    });
  if (!parsed.success) {
    return { status: "error", message: "Review the source fields and try again." };
  }

  let canonicalUrl: string;
  try {
    canonicalUrl = requiredHttpsUrl(parsed.data.canonicalUrl);
  } catch (error) {
    return { status: "error", message: (error as Error).message };
  }

  const { supabase, projectId } = await requireOwner();
  const { data, error } = await supabase
    .from("sources")
    .update({
      title: parsed.data.title,
      authors: parsed.data.authors,
      year: parsed.data.year,
      canonical_url: canonicalUrl,
      purpose: parsed.data.purpose,
      verified_at: parsed.data.verifiedAt,
    })
    .eq("id", parsed.data.id)
    .eq("project_id", projectId)
    .eq("version", parsed.data.version)
    .select("version")
    .maybeSingle();
  if (error) return databaseError(error.message);
  if (!data) return conflictError();
  refreshPlan();
  return { status: "success", message: "Source updated." };
}

export async function linkSourceAction(
  _previous: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const parsed = z
    .object({
      weekId: idSchema,
      sourceId: idSchema,
      purpose: longText.pipe(z.string().min(1)),
      priority: z.enum(["required", "recommended"]),
    })
    .safeParse({
      weekId: formText(formData, "weekId"),
      sourceId: formText(formData, "sourceId"),
      purpose: formText(formData, "purpose"),
      priority: formText(formData, "priority"),
    });
  if (!parsed.success) {
    return { status: "error", message: "Choose a source, week, purpose, and priority." };
  }

  const { supabase, projectId } = await requireOwner();
  const { data: week, error: weekError } = await supabase
    .from("weeks")
    .select("number, state")
    .eq("id", parsed.data.weekId)
    .eq("project_id", projectId)
    .maybeSingle();
  if (weekError) return databaseError(weekError.message);
  if (!week) return databaseError("Week not found.");
  if (week.state === "closed") {
    return { status: "error", message: "Reopen the week before changing its sources." };
  }

  const { error } = await supabase.from("week_sources").insert({
    project_id: projectId,
    week_id: parsed.data.weekId,
    source_id: parsed.data.sourceId,
    purpose: parsed.data.purpose,
    priority: parsed.data.priority,
  });
  if (error) return databaseError(error.message);
  refreshPlan(week.number);
  return { status: "success", message: `Source linked to Week ${week.number}.` };
}
