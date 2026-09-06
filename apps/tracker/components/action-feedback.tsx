import type { ActionState } from "@/lib/action-state";

export function ActionFeedback({ state }: { state: ActionState }) {
  if (state.status === "idle") return null;
  return (
    <p
      className={`action-feedback feedback-${state.status}`}
      role={state.status === "success" ? "status" : "alert"}
    >
      {state.message}
    </p>
  );
}
