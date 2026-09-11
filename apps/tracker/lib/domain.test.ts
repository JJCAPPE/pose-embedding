import { describe, expect, it } from "vitest";
import {
  currentWeekNumber,
  dateInTimezone,
  formatDateRange,
  projectProgress,
  recentCompletedTasks,
  weekCanClose,
  weekIsReady,
} from "@/lib/domain";
import { seedPlan } from "@/lib/seed";

describe("weekly schedule", () => {
  it("contains exactly 14 contiguous weekly records across the locked dates", () => {
    expect(seedPlan.weeks).toHaveLength(14);
    expect(seedPlan.weeks[0].startDate).toBe("2026-09-15");
    expect(seedPlan.weeks[13].endDate).toBe("2026-12-18");

    for (let index = 1; index < seedPlan.weeks.length; index += 1) {
      const previousEnd = new Date(`${seedPlan.weeks[index - 1].endDate}T12:00:00Z`);
      const currentStart = new Date(`${seedPlan.weeks[index].startDate}T12:00:00Z`);
      expect((currentStart.getTime() - previousEnd.getTime()) / 86_400_000).toBe(1);
    }
    expect(seedPlan.sources.every((source) => source.version === 1)).toBe(true);
    expect(seedPlan.weekSources.every((link) => link.version === 1)).toBe(true);
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
    expect(progress.percent).toBe(2);
    expect(progress.completedRequiredTasks).toBe(1);
    expect(progress.decidedRequiredGates).toBe(1);
    expect(progress.requiredTasks).toBeGreaterThan(50);
    expect(progress.optionalTasks).toBe(2);
  });

  it("returns the newest completed tasks for the public dashboard", () => {
    const plan = structuredClone(seedPlan);
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
