"use client";

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
  return (
    <button className={className} disabled={disabled || pending} type="submit">
      {pending ? pendingLabel : children}
    </button>
  );
}
