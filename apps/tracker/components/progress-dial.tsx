"use client";

import { Progress } from "antd";

export function ProgressDial({ percent }: { percent: number }) {
  const bounded = Math.max(0, Math.min(percent, 100));
  return (
    <Progress
      aria-label={`${bounded}% of required tasks complete`}
      className="progress-dial"
      percent={bounded}
      strokeLinecap="round"
    />
  );
}
