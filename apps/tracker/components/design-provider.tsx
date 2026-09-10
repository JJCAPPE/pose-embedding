"use client";

import { ConfigProvider } from "antd";
import type { ReactNode } from "react";

const systemFont =
  "-apple-system, BlinkMacSystemFont, \"SF Pro Text\", \"SF Pro Display\", \"Helvetica Neue\", Arial, sans-serif";

export function DesignProvider({ children }: { children: ReactNode }) {
  return (
    <ConfigProvider
      theme={{
        cssVar: { key: "pose-embed" },
        hashed: false,
        token: {
          colorPrimary: "#111111",
          colorInfo: "#111111",
          colorSuccess: "#111111",
          colorWarning: "#111111",
          colorError: "#111111",
          colorText: "#1d1d1f",
          colorTextSecondary: "#6e6e73",
          colorTextTertiary: "#6e6e73",
          colorBgBase: "#ffffff",
          colorBgLayout: "#f5f5f7",
          colorBgContainer: "#ffffff",
          colorBgElevated: "#ffffff",
          colorBorder: "#d2d2d7",
          colorBorderSecondary: "#e5e5e7",
          colorFill: "rgba(0, 0, 0, 0.06)",
          colorFillSecondary: "rgba(0, 0, 0, 0.04)",
          colorFillTertiary: "rgba(0, 0, 0, 0.025)",
          borderRadius: 12,
          borderRadiusLG: 16,
          borderRadiusSM: 8,
          controlHeight: 44,
          controlHeightSM: 36,
          fontFamily: systemFont,
          fontSize: 15,
          lineHeight: 1.5,
          boxShadow: "0 8px 30px rgba(0, 0, 0, 0.06)",
          boxShadowSecondary: "0 16px 48px rgba(0, 0, 0, 0.08)",
          motionDurationFast: "0.16s",
          motionDurationMid: "0.22s",
          motionDurationSlow: "0.3s",
        },
        components: {
          Alert: {
            defaultPadding: "14px 16px",
            withDescriptionPadding: "16px 18px",
          },
          Button: {
            borderRadius: 10,
            defaultShadow: "none",
            primaryShadow: "none",
            fontWeight: 600,
          },
          Card: {
            bodyPadding: 24,
            headerHeight: 56,
          },
          Collapse: {
            contentBg: "#ffffff",
            headerBg: "transparent",
          },
          Input: {
            activeBorderColor: "#111111",
            hoverBorderColor: "#86868b",
            activeShadow: "0 0 0 3px rgba(0, 0, 0, 0.10)",
          },
          InputNumber: {
            activeBorderColor: "#111111",
            hoverBorderColor: "#86868b",
            activeShadow: "0 0 0 3px rgba(0, 0, 0, 0.10)",
          },
          Menu: {
            itemBg: "transparent",
            itemColor: "#6e6e73",
            itemHoverBg: "#f5f5f7",
            itemHoverColor: "#111111",
            itemSelectedBg: "#eeeeef",
            itemSelectedColor: "#111111",
            itemBorderRadius: 10,
          },
          Progress: {
            defaultColor: "#111111",
            remainingColor: "#e8e8ed",
          },
          Segmented: {
            itemColor: "#515154",
            itemHoverColor: "#111111",
            itemSelectedBg: "#ffffff",
            itemSelectedColor: "#111111",
            trackBg: "#e8e8ed",
          },
          Tabs: {
            inkBarColor: "#111111",
            itemActiveColor: "#111111",
            itemHoverColor: "#111111",
            itemSelectedColor: "#111111",
          },
        },
      }}
    >
      {children}
    </ConfigProvider>
  );
}
