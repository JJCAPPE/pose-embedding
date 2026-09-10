import type { Metadata } from "next";
import { AntdRegistry } from "@ant-design/nextjs-registry";
import { connection } from "next/server";
import { Suspense, type ReactNode } from "react";
import { AppShell } from "@/components/app-shell";
import { DesignProvider } from "@/components/design-provider";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Pose Embed research tracker",
    template: "%s | Pose Embed",
  },
  description:
    "A public weekly execution plan for robust one-shot human-motion retrieval research.",
};

async function AntdRuntime({ children }: { children: ReactNode }) {
  // The Ant registry creates request-specific style IDs. Cache Components rejects that
  // nondeterminism during prerender, so keep the provider tree inside this request boundary.
  await connection();
  return (
    <AntdRegistry>
      <DesignProvider>
        <AppShell>{children}</AppShell>
      </DesignProvider>
    </AntdRegistry>
  );
}

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <template
          aria-hidden="true"
          dangerouslySetInnerHTML={{
            __html: `<!--
THESIS: Pose Embed is a research briefing that answers what happens next before exposing technical detail; it refuses the generic metric-card dashboard.
OWN-WORLD: Monochrome white, graphite, and cool-gray surfaces; system typography; restrained Ant Design controls; soft grouped depth and precise dividers.
STORY: Understand the study in plain language, act on the next required task, see the promised deliverable, then resolve the decision that permits advancement.
FIRST VIEWPORT: Slim active navigation above a concise summary, followed by a dominant next-step panel, a decision ledger, and a full-width deliverable band.
FORM: Decision-led research review workspace; selected from the brief's pinned Apple/Ant direction; seed ad6cbdce.
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, and DESIGN.md
-->`,
          }}
        />
        <a className="skip-link" href="#main-content">
          Skip to content
        </a>
        <Suspense
          fallback={
            <main className="app-loading-frame" aria-busy="true" aria-label="Loading Pose Embed">
              <div className="app-loading-brand">
                <span aria-hidden="true">PE</span>
                <strong>Pose Embed</strong>
              </div>
              <div className="app-loading-surface" />
            </main>
          }
        >
          <AntdRuntime>{children}</AntdRuntime>
        </Suspense>
      </body>
    </html>
  );
}
