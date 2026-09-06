export type ActionState = {
  status: "idle" | "success" | "error" | "conflict";
  message: string;
};

export const initialActionState: ActionState = { status: "idle", message: "" };
