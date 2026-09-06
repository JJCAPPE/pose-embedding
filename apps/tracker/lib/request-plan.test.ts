import { beforeEach, describe, expect, it, vi } from "vitest";
import { seedPlan } from "@/lib/seed";

const mocks = vi.hoisted(() => ({
  connection: vi.fn<() => Promise<void>>(),
  getPublicPlan: vi.fn<() => Promise<unknown>>(),
}));

vi.mock("next/server", () => ({ connection: mocks.connection }));
vi.mock("@/lib/data", () => ({ getPublicPlan: mocks.getPublicPlan }));

import { getRequestPublicPlan } from "@/lib/request-plan";

describe("request-time public plan loading", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.connection.mockResolvedValue();
  });

  it("crosses the request boundary before reading the tagged plan cache", async () => {
    const expected = {
      ...seedPlan,
      dataSource: "seed" as const,
      lastRefreshedAt: seedPlan.generatedAt,
    };
    mocks.getPublicPlan.mockResolvedValue(expected);

    await expect(getRequestPublicPlan()).resolves.toBe(expected);
    expect(mocks.connection).toHaveBeenCalledOnce();
    expect(mocks.getPublicPlan).toHaveBeenCalledOnce();
    expect(mocks.connection.mock.invocationCallOrder[0]).toBeLessThan(
      mocks.getPublicPlan.mock.invocationCallOrder[0],
    );
  });
});
