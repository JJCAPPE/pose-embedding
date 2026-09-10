"use client";

import { Button } from "antd";
import { useFormStatus } from "react-dom";

export function SubmitButton({
  children,
  disabled = false,
  pendingLabel = "Saving",
  className = "button primary compact-button",
}: {
  children: React.ReactNode;
  disabled?: boolean;
  pendingLabel?: string;
  className?: string;
}) {
  const { pending } = useFormStatus();
  const type = className.includes("secondary") ? "default" : "primary";
  return (
    <Button
      className={className}
      disabled={disabled || pending}
      htmlType="submit"
      loading={pending}
      type={type}
    >
      {pending ? pendingLabel : children}
    </Button>
  );
}
