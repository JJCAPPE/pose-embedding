import { afterEach, describe, expect, it, vi } from "vitest";
import { seedPlan } from "@/lib/seed";

const mocks = vi.hoisted(() => ({
  cacheTag: vi.fn(),
  createClient: vi.fn(),
}));

vi.mock("next/cache", () => ({ cacheLife: vi.fn(), cacheTag: mocks.cacheTag }));
vi.mock("@supabase/supabase-js", () => ({ createClient: mocks.createClient }));
vi.mock("@/lib/env", () => ({
  supabaseEnvironment: () => ({ url: "https://example.invalid", publishableKey: "public-test-key" }),
}));

import { getPublicPlan } from "@/lib/data";

describe("versioned public plan cache", () => {
  afterEach(() => vi.restoreAllMocks());

  it("keeps owner invalidation and v3 tags while falling back to the v3 snapshot", async () => {
    vi.spyOn(console, "error").mockImplementation(() => undefined);
    mocks.createClient.mockImplementation(() => { throw new Error("Database unavailable"); });

    const result = await getPublicPlan();

    expect(mocks.cacheTag).toHaveBeenCalledWith("plan", "research-plan.v3");
    expect(result.dataSource).toBe("seed");
    expect(result.protocol).toEqual(seedPlan.protocol);
    expect(result.weeks).toEqual(seedPlan.weeks);
  });
});
