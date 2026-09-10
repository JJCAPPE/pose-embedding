"use client";

import { LockOutlined, MailOutlined } from "@ant-design/icons";
import { Input } from "antd";
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
        <Input
          autoComplete="email"
          id="email"
          name="email"
          prefix={<MailOutlined />}
          required
          size="large"
          type="email"
        />
      </div>
      <div className="field">
        <label htmlFor="password">Password</label>
        <Input.Password
          autoComplete="current-password"
          id="password"
          name="password"
          prefix={<LockOutlined />}
          required
          size="large"
        />
      </div>
      <ActionFeedback state={state} />
      <SubmitButton pendingLabel="Signing in">Sign in</SubmitButton>
    </form>
  );
}
