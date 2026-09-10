import type { Metadata } from "next";
import { Suspense } from "react";
import { LoginPanel } from "@/components/login-panel";
import { editingIsEnabled } from "@/lib/env";

export const metadata: Metadata = { title: "Owner sign in" };

type LoginPageProps = { searchParams: Promise<{ reason?: string }> };

const REASON_COPY: Record<string, string> = {
  "editing-disabled": "Management is disabled on this deployment.",
  "not-configured": "The live research record is not configured on this deployment.",
  "sign-in": "Sign in with the project-owner account to continue.",
  "not-owner": "This account does not have permission to manage the project.",
};

async function LoginPageContent({ searchParams }: LoginPageProps) {
  const { reason } = await searchParams;
  return (
    <LoginPanel
      enabled={editingIsEnabled()}
      notice={reason ? REASON_COPY[reason] : undefined}
    />
  );
}

export default function LoginPage(props: LoginPageProps) {
  return (
    <Suspense fallback={<div className="shell auth-page" aria-busy="true">Loading sign in…</div>}>
      <LoginPageContent {...props} />
    </Suspense>
  );
}
