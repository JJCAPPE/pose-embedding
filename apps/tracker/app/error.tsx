"use client";

import { Button, Result, Space } from "antd";
import { InternalLinkButton } from "@/components/internal-link-button";

export default function ErrorPage({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="shell state-page">
      <Result
        extra={
          <Space wrap>
            <Button onClick={reset} type="primary">Try again</Button>
            <InternalLinkButton href="/">Return to overview</InternalLinkButton>
          </Space>
        }
        status="warning"
        subTitle="Try loading it again. If the problem continues, the checked-in plan is still available from the overview."
        title={<h1>The research record could not be loaded.</h1>}
      />
    </div>
  );
}
