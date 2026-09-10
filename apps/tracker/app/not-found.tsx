"use client";

import { SearchOutlined } from "@ant-design/icons";
import { Result } from "antd";
import { InternalLinkButton } from "@/components/internal-link-button";

export default function NotFound() {
  return (
    <div className="shell state-page">
      <Result
        extra={<InternalLinkButton href="/" type="primary">Return to overview</InternalLinkButton>}
        icon={<SearchOutlined />}
        status="info"
        subTitle="The address may be incorrect, or this page may have moved."
        title={<h1>Page not found</h1>}
      />
    </div>
  );
}
