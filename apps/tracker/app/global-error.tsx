"use client";

import { Button, Result } from "antd";
import { DesignProvider } from "@/components/design-provider";
import "./globals.css";

export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body>
        <DesignProvider>
          <main className="shell state-page">
            <Result
              extra={<Button onClick={reset} type="primary">Try again</Button>}
              status="error"
              subTitle="Reload the tracker. No research data was changed."
              title={<h1>The tracker encountered an unexpected error.</h1>}
            />
          </main>
        </DesignProvider>
      </body>
    </html>
  );
}
