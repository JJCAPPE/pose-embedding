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

  it("presents independent research without advisor prerequisites", () => {
    const markdown = planToMarkdown(loaded);
    expect(markdown).toContain("**Review prompt:**");
    expect(markdown).not.toContain("**Advisor prompt:**");
    expect(JSON.stringify(seedPlan.weeks)).not.toMatch(
      /advisor-approved|advisor approval|advisor approves|to the advisor|advisor feedback/i,
    );
    expect(seedPlan.protocol.lockedDecisions).toContainEqual({
      label: "Governance",
      value: expect.stringContaining("No advisor approval is required."),
    });
    expect(seedPlan.weeks[0].gates.find((gate) => gate.id === "w01-gate-04")?.state).toBe("pending");
    expect(seedPlan.weeks[0].actualMinutes).toBe(0);
  });
});
