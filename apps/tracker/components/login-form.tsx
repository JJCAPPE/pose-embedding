"use client";

import { useActionState } from "react";
import { loginAction } from "@/app/actions";
import { ActionFeedback } from "@/components/action-feedback";
import { SubmitButton } from "@/components/submit-button";
import { initialActionState } from "@/lib/action-state";

export function LoginForm() {
  const [state, action] = useActionState(loginAction, initialActionState);
  return (
    <form action={action} className="auth-form">
      <div className="field">
        <label htmlFor="email">Email</label>
        <input autoComplete="email" id="email" name="email" required type="email" />
      </div>
      <div className="field">
        <label htmlFor="password">Password</label>
        <input
          autoComplete="current-password"
          id="password"
          name="password"
          required
          type="password"
        />
      </div>
      <ActionFeedback state={state} />
      <SubmitButton pendingLabel="Signing in">Sign in</SubmitButton>
    </form>
  );
}
