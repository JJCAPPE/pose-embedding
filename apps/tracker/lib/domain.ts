import type { LoadedPlan, ResearchPlan, Task, Week } from "@/lib/schema";

const DATE_FORMATTERS = new Map<string, Intl.DateTimeFormat>();

function dateFormatter(timezone: string) {
  const existing = DATE_FORMATTERS.get(timezone);
  if (existing) return existing;

  const formatter = new Intl.DateTimeFormat("en-CA", {
    timeZone: timezone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
  DATE_FORMATTERS.set(timezone, formatter);
  return formatter;
}

export function dateInTimezone(date: Date, timezone: string): string {
  const parts = dateFormatter(timezone).formatToParts(date);
  const value = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${value.year}-${value.month}-${value.day}`;
}

export function currentWeekNumber(
  plan: Pick<ResearchPlan, "project" | "weeks">,
  now = new Date(),
): number | null {
  const today = dateInTimezone(now, plan.project.timezone);
  return (
    plan.weeks.find((week) => week.startDate <= today && today <= week.endDate)
      ?.number ?? null
  );
}

export function weekIsReady(weeks: Week[], weekNumber: number): boolean {
  if (weekNumber === 1) return true;
  return weeks.find((week) => week.number === weekNumber - 1)?.state === "closed";
}

export function weekCanClose(week: Week): boolean {
  return (
    week.tasks.every((task) => !task.required || task.state === "done") &&
    week.gates.every(
      (gate) => !gate.required || gate.state === "met" || gate.state === "waived",
    )
  );
}

export function projectProgress(plan: Pick<ResearchPlan, "weeks">) {
  let requiredTasks = 0;
  let completedRequiredTasks = 0;
  let optionalTasks = 0;
  let completedOptionalTasks = 0;
  let requiredGates = 0;
  let decidedRequiredGates = 0;

  for (const week of plan.weeks) {
    for (const task of week.tasks) {
      if (task.required) {
        requiredTasks += 1;
        if (task.state === "done") completedRequiredTasks += 1;
      } else {
        optionalTasks += 1;
        if (task.state === "done") completedOptionalTasks += 1;
      }
    }
    for (const gate of week.gates) {
      if (!gate.required) continue;
      requiredGates += 1;
      if (gate.state === "met" || gate.state === "waived") {
        decidedRequiredGates += 1;
      }
    }
  }

  return {
    requiredTasks,
    completedRequiredTasks,
    optionalTasks,
    completedOptionalTasks,
    requiredGates,
    decidedRequiredGates,
    percent:
      requiredTasks === 0
        ? 0
        : Math.round((completedRequiredTasks / requiredTasks) * 100),
  };
}

export function recentCompletedTasks(
  plan: Pick<ResearchPlan, "weeks">,
  limit = 5,
) {
  const completions: Array<{
    completedAt: string;
    task: Task;
    weekNumber: number;
    weekTitle: string;
  }> = [];

  for (const week of plan.weeks) {
    for (const task of week.tasks) {
      if (task.state !== "done" || task.completedAt === null) continue;
      completions.push({
        completedAt: task.completedAt,
        task,
        weekNumber: week.number,
        weekTitle: week.title,
      });
    }
  }

  return completions
    .sort((left, right) => Date.parse(right.completedAt) - Date.parse(left.completedAt))
    .slice(0, Math.max(0, limit));
}

export function weekProgress(week: Week) {
  const required = week.tasks.filter((task) => task.required);
  const completed = required.filter((task) => task.state === "done");
  return {
    required: required.length,
    completed: completed.length,
    percent:
      required.length === 0
        ? 0
        : Math.round((completed.length / required.length) * 100),
  };
}

export function formatDateRange(startDate: string, endDate: string): string {
  const start = new Date(`${startDate}T12:00:00Z`);
  const end = new Date(`${endDate}T12:00:00Z`);
  const month = new Intl.DateTimeFormat("en-US", { month: "short" });
  const day = new Intl.DateTimeFormat("en-US", { day: "numeric" });

  if (startDate === endDate) return `${month.format(start)} ${day.format(start)}`;
  if (start.getUTCMonth() === end.getUTCMonth()) {
    return `${month.format(start)} ${day.format(start)}-${day.format(end)}`;
  }
  return `${month.format(start)} ${day.format(start)}-${month.format(end)} ${day.format(end)}`;
}

export function publicPlan(plan: LoadedPlan): LoadedPlan {
  return JSON.parse(JSON.stringify(plan)) as LoadedPlan;
}
