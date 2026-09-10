"use client";

import { MenuOutlined } from "@ant-design/icons";
import { Button, Drawer, Layout, Menu, Space } from "antd";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import type { ReactNode } from "react";

const navigation = [
  { key: "overview", href: "/", label: "Overview" },
  { key: "protocol", href: "/protocol", label: "Protocol" },
  { key: "sources", href: "/literature", label: "Sources" },
  { key: "manage", href: "/edit", label: "Manage" },
];

function selectedKey(pathname: string) {
  if (pathname.startsWith("/protocol")) return "protocol";
  if (pathname.startsWith("/literature")) return "sources";
  if (pathname.startsWith("/edit") || pathname.startsWith("/login")) return "manage";
  return "overview";
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const activeKey = selectedKey(pathname);
  const items = navigation.map((item) => ({
    key: item.key,
    label: (
      <Link aria-current={activeKey === item.key ? "page" : undefined} href={item.href}>
        {item.label}
      </Link>
    ),
  }));

  return (
    <Layout className="app-layout">
      <Layout.Header className="site-header">
        <div className="header-inner">
          <Link className="wordmark" href="/" aria-label="Pose Embed overview">
            <span aria-hidden="true" className="wordmark-mark">PE</span>
            <span>Pose Embed</span>
          </Link>
          <Menu
            aria-label="Primary navigation"
            className="desktop-navigation"
            items={items}
            mode="horizontal"
            selectedKeys={[activeKey]}
          />
          <Button
            aria-label="Open navigation"
            className="mobile-menu-button"
            icon={<MenuOutlined />}
            onClick={() => setOpen(true)}
            type="text"
          />
        </div>
      </Layout.Header>
      <Layout.Content id="main-content" className="site-content">
        {children}
      </Layout.Content>
      <Layout.Footer className="site-footer">
        <div className="footer-inner">
          <p>Robust human-motion retrieval · Fall 2026</p>
          <Space size="large" wrap>
            <a href="/api/export?format=markdown">Export plan</a>
            <a href="/api/health">Technical status</a>
          </Space>
        </div>
      </Layout.Footer>
      <Drawer
        onClose={() => setOpen(false)}
        open={open}
        placement="right"
        rootClassName="mobile-navigation-drawer"
        title="Pose Embed"
        size="default"
      >
        <Menu
          aria-label="Mobile navigation"
          items={items}
          mode="inline"
          onClick={() => setOpen(false)}
          selectedKeys={[activeKey]}
        />
      </Drawer>
    </Layout>
  );
}
