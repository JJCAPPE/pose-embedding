"use client";

import { Alert } from "antd";
import type { ActionState } from "@/lib/action-state";

export function ActionFeedback({ state }: { state: ActionState }) {
  if (state.status === "idle") return null;
  return (
    <Alert
      className="action-feedback"
      title={state.message}
      role={state.status === "success" ? "status" : "alert"}
      showIcon
      type={state.status === "success" ? "success" : "error"}
    />
  );
}
