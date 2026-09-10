"use client";

import { Alert, Card, Collapse, Result } from "antd";
import Link from "next/link";
import { LoginForm } from "@/components/login-form";
import { InternalLinkButton } from "@/components/internal-link-button";

export function LoginPanel({ enabled, notice }: { enabled: boolean; notice?: string }) {
  return (
    <div className="shell auth-page">
      <Card className="auth-panel">
        <div>
          <h1>Manage the research record.</h1>
          <p>
            Sign in with the project-owner account to record progress, attach evidence, and make
            weekly decisions. The public plan remains available without signing in.
          </p>
        </div>
        {notice ? <Alert className="auth-notice" title={notice} showIcon type="info" /> : null}
        {enabled ? (
          <>
            <LoginForm />
            <Link className="auth-return-link" href="/">Return to overview</Link>
          </>
        ) : (
          <>
            <Result
              extra={<InternalLinkButton href="/">Return to overview</InternalLinkButton>}
              status="info"
              subTitle="You can still review the complete public plan."
              title="Management is not available on this deployment."
            />
            <Collapse
              ghost
              items={[
                {
                  key: "configuration",
                  label: "Technical setup",
                  children: (
                    <p>
                      Configure the Supabase URL and publishable key, then set{" "}
                      <code>EDITING_ENABLED=true</code> in the deployment environment.
                    </p>
                  ),
                },
              ]}
            />
          </>
        )}
      </Card>
    </div>
  );
}
