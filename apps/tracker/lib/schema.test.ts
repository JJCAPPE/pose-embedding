import { describe, expect, it } from "vitest";
import { researchPlanSchema } from "@/lib/schema";
import { seedPlan } from "@/lib/seed";

describe("database timestamp compatibility", () => {
  it("accepts RFC 3339 offsets returned by Postgres timestamptz", () => {
    const plan = structuredClone(seedPlan);
    plan.weeks[0].tasks[0].completedAt = "2026-09-06T20:16:39.271+00:00";
    plan.weeks[0].gates[0].decidedAt = "2026-09-06T20:16:39+00:00";
    plan.weeks[0].closedAt = "2026-09-06T20:16:39+00:00";

    expect(researchPlanSchema.safeParse(plan).success).toBe(true);
  });
});
