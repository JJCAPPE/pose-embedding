import { describe, expect, it } from "vitest";
import {
  currentWeekNumber,
  dateInTimezone,
  formatDateRange,
  projectProgress,
  recentCompletedTasks,
  weekCanClose,
  weekIsReady,
  weekProgress,
} from "@/lib/domain";
import { seedPlan } from "@/lib/seed";

describe("weekly schedule", () => {
  it("contains exactly 14 contiguous weekly records across the provisional planning horizon", () => {
    expect(seedPlan.weeks).toHaveLength(14);
    expect(seedPlan.weeks[0].startDate).toBe("2026-09-15");
    expect(seedPlan.weeks[13].endDate).toBe("2026-12-18");

    for (let index = 1; index < seedPlan.weeks.length; index += 1) {
      const previousEnd = new Date(`${seedPlan.weeks[index - 1].endDate}T12:00:00Z`);
      const currentStart = new Date(`${seedPlan.weeks[index].startDate}T12:00:00Z`);
      expect((currentStart.getTime() - previousEnd.getTime()) / 86_400_000).toBe(1);
    }
    expect(seedPlan.sources.every((source) => source.version >= 1)).toBe(true);
    expect(seedPlan.weekSources.every((link) => link.version >= 1)).toBe(true);
  });

  it("uses New York calendar dates at week boundaries", () => {
    expect(currentWeekNumber(seedPlan, new Date("2026-09-15T03:59:59Z"))).toBeNull();
    expect(currentWeekNumber(seedPlan, new Date("2026-09-15T04:00:00Z"))).toBe(1);
    expect(currentWeekNumber(seedPlan, new Date("2026-11-02T04:30:00Z"))).toBe(7);
    expect(currentWeekNumber(seedPlan, new Date("2026-11-02T05:30:00Z"))).toBe(8);
    expect(currentWeekNumber(seedPlan, new Date("2026-12-19T05:00:00Z"))).toBeNull();
  });

  it("formats the local date correctly across daylight-saving time", () => {
    expect(dateInTimezone(new Date("2026-11-01T05:30:00Z"), "America/New_York")).toBe("2026-11-01");
    expect(dateInTimezone(new Date("2026-11-01T06:30:00Z"), "America/New_York")).toBe("2026-11-01");
  });

  it("formats a single deadline without a repeated day", () => {
    expect(formatDateRange("2026-09-09", "2026-09-09")).toBe("Sep 9");
  });
});

describe("readiness and progress rules", () => {
  it("requires the preceding week to be closed", () => {
    expect(weekIsReady(seedPlan.weeks, 1)).toBe(true);
    expect(weekIsReady(seedPlan.weeks, 2)).toBe(false);
    const weeks = seedPlan.weeks.map((week) =>
      week.number === 1 ? { ...week, state: "closed" as const } : week,
    );
    expect(weekIsReady(weeks, 2)).toBe(true);
  });

  it("closes only with completed required tasks and decided required gates", () => {
    const initial = seedPlan.weeks[10];
    expect(weekCanClose(initial)).toBe(false);
    const ready = {
      ...initial,
      tasks: initial.tasks.map((task) =>
        task.required ? { ...task, state: "done" as const } : task,
      ),
      gates: initial.gates.map((gate) =>
        gate.required ? { ...gate, state: "met" as const } : gate,
      ),
    };
    expect(weekCanClose(ready)).toBe(true);
  });

  it("counts only required tasks in the primary percentage", () => {
    const progress = projectProgress(seedPlan);
    expect(progress.percent).toBe(28);
    expect(progress.completedRequiredTasks).toBe(17);
    expect(progress.decidedRequiredGates).toBe(16);
    expect(progress.requiredTasks).toBeGreaterThan(50);
    expect(progress.optionalTasks).toBe(0);
  });

  it("keeps Week 1 open for actual time and closeout after the confirmed BU decision", () => {
    const week = seedPlan.weeks[0];
    expect(weekProgress(week)).toEqual({
      required: 5,
      completed: 4,
      percent: 80,
    });
    expect(
      week.gates
        .filter((gate) => gate.required && gate.state === "pending")
        .map((gate) => gate.id),
    ).toEqual([]);
    expect(week.gates.find((gate) => gate.id === "w01-gate-04")).toMatchObject({
      state: "met",
      evidence: expect.stringContaining("researcher confirmation"),
      waiverReason: "",
      decidedAt: "2026-09-24T22:13:07+00:00",
    });
    expect(week.actualMinutes).toBe(0);
    expect(weekCanClose(week)).toBe(false);
    expect(weekIsReady(seedPlan.weeks, 2)).toBe(false);
  });

  it("closes Week 3 after verified SCC preparation and makes Week 4 ready", () => {
    const week = seedPlan.weeks[2];
    expect(weekProgress(week)).toEqual({ required: 7, completed: 7, percent: 100 });
    expect(week.gates.filter((gate) => gate.state === "met").map((gate) => gate.id))
      .toEqual(["w03-gate-01", "w03-gate-02", "w03-gate-03", "w03-gate-04", "w03-gate-05", "w03-gate-06", "w03-gate-07"]);
    expect(week.tasks.slice(0, 5).every((task) => task.state === "done")).toBe(true);
    expect(week.tasks.find((task) => task.id === "w03-task-07")).toMatchObject({
      state: "done",
      completedAt: expect.any(String),
      completionNote: expect.stringContaining("7790916"),
    });
    expect(week.gates.find((gate) => gate.id === "w03-gate-07")).toMatchObject({
      state: "met",
      decidedAt: expect.any(String),
      evidence: expect.stringContaining("39426a3b2ddea74aaa8c1d39737cd9e5fb9c870c21745f5527e4e97b58d14e2d"),
    });
    expect(week.reflection).toContain("Actual researcher minutes remain unreported");
    expect(weekCanClose(week)).toBe(true);
    expect(weekIsReady(seedPlan.weeks, 4)).toBe(true);
    expect(week.state).toBe("closed");
    expect(week.closedAt).not.toBeNull();
    expect(week.actualMinutes).toBe(0);
  });

  it("records the resolved seal audit and verified fixtures while caches and pilots remain open", () => {
    const week = seedPlan.weeks[3];
    expect(weekProgress(week)).toEqual({ required: 4, completed: 2, percent: 50 });
    expect(week.tasks[0].completionNote).toContain("Satisfied by the verified Week 3 handoff");
    expect(week.tasks[0].completionNote).toContain("Revalidation on 2026-10-08");
    expect(week.tasks.map((task) => task.state)).toEqual([
      "done", "done", "in_progress", "todo",
    ]);
    expect(week.tasks.slice(0, 2).every((task) => task.completedAt !== null)).toBe(true);
    expect(week.tasks.slice(2).every((task) => task.completedAt === null)).toBe(true);
    expect(week.tasks[1].completionNote).toContain("7968648");
    expect(week.tasks[1].completionNote).toContain("32-to-16 software fixture");
    expect(week.tasks[2].completionNote).toContain("generated all five fresh v3 caches");
    expect(week.tasks[2].completionNote).toContain("validation receipt passes");
    expect(week.gates.map((gate) => gate.state)).toEqual(["met", "met", "pending"]);
    expect(week.gates[0].evidence).toContain("Satisfied by the verified Week 3 handoff");
    expect(week.gates[0].evidence).toMatch(/researcher confirmation/i);
    expect(week.gates[0].decidedAt).not.toBeNull();
    expect(week.state).toBe("active");
    expect(week.closedAt).toBeNull();
    expect(week.reflection).toContain("Done:");
    expect(week.reflection).toContain("Next:");
    expect(week.reflection).toContain("Open issues:");
    expect(week.actualMinutes).toBe(0);
    expect(weekCanClose(week)).toBe(false);
    expect(weekIsReady(seedPlan.weeks, 5)).toBe(false);
  });

  it("returns the newest completed tasks for the public dashboard", () => {
    const plan = structuredClone(seedPlan);
    for (const week of plan.weeks) {
      for (const task of week.tasks) {
        task.completedAt = null;
      }
    }
    plan.weeks[0].tasks[0] = {
      ...plan.weeks[0].tasks[0],
      state: "done",
      completedAt: "2026-09-16T14:00:00Z",
    };
    plan.weeks[1].tasks[0] = {
      ...plan.weeks[1].tasks[0],
      state: "done",
      completedAt: "2026-09-23T16:30:00Z",
    };

    const completions = recentCompletedTasks(plan, 1);

    expect(completions).toHaveLength(1);
    expect(completions[0]).toMatchObject({
      completedAt: "2026-09-23T16:30:00Z",
      weekNumber: 2,
      weekTitle: "Immutable data manifests",
    });
    expect(completions[0].task.id).toBe("w02-task-01");
  });
});
