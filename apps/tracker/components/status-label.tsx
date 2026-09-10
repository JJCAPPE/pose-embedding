"use client";

import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  LockOutlined,
  MinusCircleOutlined,
  PauseCircleOutlined,
  PlayCircleOutlined,
  StopOutlined,
  UnlockOutlined,
} from "@ant-design/icons";
import { Tag } from "antd";
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

const ICONS: Record<Status, React.ReactNode> = {
  todo: <ClockCircleOutlined />,
  in_progress: <PlayCircleOutlined />,
  blocked: <StopOutlined />,
  done: <CheckCircleOutlined />,
  skipped: <MinusCircleOutlined />,
  pending: <ClockCircleOutlined />,
  met: <CheckCircleOutlined />,
  waived: <MinusCircleOutlined />,
  planned: <PauseCircleOutlined />,
  active: <PlayCircleOutlined />,
  closed: <LockOutlined />,
  ready: <UnlockOutlined />,
  not_ready: <CloseCircleOutlined />,
};

export function StatusLabel({ status }: { status: Status }) {
  return (
    <Tag className={`status-tag status-${status}`} icon={ICONS[status]}>
      {LABELS[status]}
    </Tag>
  );
}
