import type { GateState, TaskState, WeekState } from "@/lib/schema";

type Status = TaskState | GateState | WeekState | "ready" | "not_ready";

const LABELS: Record<Status, string> = {
  todo: "To do",
  in_progress: "In progress",
  blocked: "Blocked",
  done: "Done",
  skipped: "Skipped",
  pending: "Pending",
  met: "Met",
  waived: "Waived",
  planned: "Planned",
  active: "Active",
  closed: "Closed",
  ready: "Ready",
  not_ready: "Waiting",
};

export function StatusLabel({ status }: { status: Status }) {
  return <span className={`status-label status-${status}`}>{LABELS[status]}</span>;
}
