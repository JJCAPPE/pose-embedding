import type { Metadata } from "next";
import Link from "next/link";
import { LoginForm } from "@/components/login-form";
import { editingIsEnabled } from "@/lib/env";

export const metadata: Metadata = { title: "Owner sign in" };

type LoginPageProps = { searchParams: Promise<{ reason?: string }> };

const REASON_COPY: Record<string, string> = {
  "editing-disabled": "Editing is disabled on this deployment.",
  "not-configured": "Supabase has not been configured for this deployment.",
  "sign-in": "Sign in with the project-owner account to continue.",
  "not-owner": "The signed-in account is not the project owner.",
};

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const { reason } = await searchParams;
  const enabled = editingIsEnabled();
  return (
    <div className="shell auth-page">
      <section className="auth-panel">
        <div>
          <p className="eyebrow">Owner access</p>
          <h1>Update the research record.</h1>
          <p>
            Public visitors can read the plan. Only the configured project owner can change it.
          </p>
        </div>
        {reason && REASON_COPY[reason] ? (
          <p className="auth-notice" role="status">{REASON_COPY[reason]}</p>
        ) : null}
        {enabled ? (
          <LoginForm />
        ) : (
          <div className="empty-state align-left">
            <h2>Editing is not configured yet.</h2>
            <p>
              Set the Supabase URL, publishable key, and EDITING_ENABLED=true in the deployment environment.
            </p>
            <Link className="text-link" href="/">Return to the public plan</Link>
          </div>
        )}
      </section>
    </div>
  );
}
