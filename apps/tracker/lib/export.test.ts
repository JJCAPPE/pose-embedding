import { describe, expect, it } from "vitest";
import { planToMarkdown } from "@/lib/export";
import { seedPlan } from "@/lib/seed";

describe("public export", () => {
  const loaded = {
    ...seedPlan,
    dataSource: "seed" as const,
    lastRefreshedAt: seedPlan.generatedAt,
  };

  it("includes every week and the evidence ledger", () => {
    const markdown = planToMarkdown(loaded);
    for (let week = 1; week <= 14; week += 1) {
      expect(markdown).toContain(`## Week ${week}:`);
    }
    expect(markdown).toContain("## Literature");
    expect(markdown).toContain("Required-task progress");
  });

  it("does not introduce the banned typographic dash characters", () => {
    expect(planToMarkdown(loaded)).not.toMatch(/[—–]/u);
  });
});
