"use client";

import { InfoCircleOutlined } from "@ant-design/icons";
import { Alert } from "antd";
import type { LoadedPlan } from "@/lib/schema";

export function DataNotice({
  dataSource,
  lastRefreshedAt,
}: Pick<LoadedPlan, "dataSource" | "lastRefreshedAt">) {
  if (dataSource === "supabase") return null;

  const refreshed = new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(lastRefreshedAt));

  return (
    <Alert
      className="data-notice"
      description="Live progress is unavailable. You can still review the saved plan, but updates may be newer."
      icon={<InfoCircleOutlined />}
      title={`Viewing saved snapshot · ${refreshed}`}
      role="status"
      showIcon
      type="info"
    />
  );
}
