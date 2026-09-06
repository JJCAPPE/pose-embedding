import { z } from "zod";

export const taskStateSchema = z.enum([
  "todo",
  "in_progress",
  "blocked",
  "done",
  "skipped",
]);

export const gateStateSchema = z.enum(["pending", "met", "waived"]);
export const weekStateSchema = z.enum(["planned", "active", "blocked", "closed"]);

export const taskSchema = z.object({
  id: z.string().min(1),
  weekId: z.string().min(1),
  position: z.number().int().positive(),
  title: z.string().min(1),
  details: z.string(),
  expectedOutput: z.string(),
  required: z.boolean(),
  estimateMinutes: z.number().int().nonnegative(),
  state: taskStateSchema,
  completionNote: z.string(),
  evidenceUrl: z.string().url().nullable(),
  completedAt: z.string().datetime({ offset: true }).nullable(),
  version: z.number().int().positive(),
});

export const gateSchema = z.object({
  id: z.string().min(1),
  weekId: z.string().min(1),
  position: z.number().int().positive(),
  criterion: z.string().min(1),
  required: z.boolean(),
  state: gateStateSchema,
  evidence: z.string(),
  waiverReason: z.string(),
  decidedAt: z.string().datetime({ offset: true }).nullable(),
  version: z.number().int().positive(),
});

export const weekSchema = z.object({
  id: z.string().min(1),
  projectId: z.string().min(1),
  number: z.number().int().min(1).max(14),
  startDate: z.string().date(),
  endDate: z.string().date(),
  phase: z.string().min(1),
  title: z.string().min(1),
  objective: z.string().min(1),
  deliverable: z.string().min(1),
  risks: z.array(z.string().min(1)),
  advisorPrompt: z.string().min(1),
  reflection: z.string(),
  plannedMinutes: z.number().int().nonnegative(),
  actualMinutes: z.number().int().nonnegative(),
  state: weekStateSchema,
  closedAt: z.string().datetime({ offset: true }).nullable(),
  version: z.number().int().positive(),
  tasks: z.array(taskSchema),
  gates: z.array(gateSchema),
});

export const projectSchema = z.object({
  id: z.string().min(1),
  slug: z.string().min(1),
  title: z.string().min(1),
  researchQuestion: z.string().min(1),
  summary: z.string().min(1),
  startDate: z.string().date(),
  endDate: z.string().date(),
  timezone: z.string().min(1),
  visibility: z.literal("public"),
  version: z.number().int().positive(),
});

export const sourceSchema = z.object({
  id: z.string().min(1),
  title: z.string().min(1),
  authors: z.string().min(1),
  year: z.number().int().min(1900),
  canonicalUrl: z.string().url(),
  purpose: z.string().min(1),
  verifiedAt: z.string().date(),
  version: z.number().int().positive().default(1),
});

export const weekSourceSchema = z.object({
  weekId: z.string().min(1),
  sourceId: z.string().min(1),
  purpose: z.string().min(1),
  priority: z.enum(["required", "recommended"]),
  version: z.number().int().positive().default(1),
});

export const manualActionSchema = z.object({
  id: z.string().min(1),
  dueDate: z.string().date(),
  title: z.string().min(1),
  details: z.string().min(1),
  whyManual: z.string().min(1),
  weekTaskId: z.string().nullable(),
});

const protocolItemSchema = z.object({
  label: z.string().min(1),
  value: z.string().min(1),
});

export const protocolSchema = z.object({
  bindingSource: z.string().min(1),
  successDefinition: z.string().min(1),
  lockedDecisions: z.array(protocolItemSchema),
  experimentalDesign: z.array(protocolItemSchema),
  corruptionPrinciple: z.string().min(1),
  corruptions: z.array(protocolItemSchema),
  primaryFormula: z.string().min(1),
  effectFormula: z.string().min(1),
  analysisRules: z.array(z.string().min(1)),
  scopeExclusions: z.array(z.string().min(1)),
});

export const researchPlanSchema = z.object({
  schemaVersion: z.literal("1.0.0"),
  generatedAt: z.string().datetime({ offset: true }),
  project: projectSchema,
  manualActions: z.array(manualActionSchema),
  protocol: protocolSchema,
  weeks: z.array(weekSchema).length(14),
  sources: z.array(sourceSchema),
  weekSources: z.array(weekSourceSchema),
});

export type TaskState = z.infer<typeof taskStateSchema>;
export type GateState = z.infer<typeof gateStateSchema>;
export type WeekState = z.infer<typeof weekStateSchema>;
export type Task = z.infer<typeof taskSchema>;
export type Gate = z.infer<typeof gateSchema>;
export type Week = z.infer<typeof weekSchema>;
export type Project = z.infer<typeof projectSchema>;
export type Source = z.infer<typeof sourceSchema>;
export type WeekSource = z.infer<typeof weekSourceSchema>;
export type ManualAction = z.infer<typeof manualActionSchema>;
export type Protocol = z.infer<typeof protocolSchema>;
export type ResearchPlan = z.infer<typeof researchPlanSchema>;

export type LoadedPlan = ResearchPlan & {
  dataSource: "supabase" | "seed";
  lastRefreshedAt: string;
};
