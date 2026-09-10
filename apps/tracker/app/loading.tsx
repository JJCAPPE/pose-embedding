"use client";

import { Card, Skeleton } from "antd";

export default function Loading() {
  return (
    <div
      className="shell page-shell"
      aria-busy="true"
      aria-label="Loading research plan"
      role="status"
    >
      <Skeleton active title={{ width: "54%" }} paragraph={{ rows: 2, width: ["82%", "64%"] }} />
      <div className="loading-grid">
        <Card><Skeleton active paragraph={{ rows: 4 }} /></Card>
        <Card><Skeleton active paragraph={{ rows: 4 }} /></Card>
        <Card><Skeleton active paragraph={{ rows: 2 }} /></Card>
      </div>
    </div>
  );
}
