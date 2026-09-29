import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import historicalPlan from "../../../plan/research-plan.v2.json";
import { GET } from "@/app/protocol/[document]/source/route";
import {
  isProtocolDocumentName,
  protocolDocumentLink,
  protocolDocuments,
} from "@/lib/protocol-documents";
import { seedPlan } from "@/lib/seed";
import { weekIsReady } from "@/lib/domain";

describe("published v3 protocol", () => {
  it("bundles the exact tracked final plan and decision", () => {
    for (const document of Object.values(protocolDocuments)) {
      expect(document.markdown).toBe(readFileSync(resolve("../..", document.sourcePath), "utf8"));
    }
    expect(protocolDocuments.plan.markdown).toContain("100 GB");
    expect(protocolDocuments.plan.markdown).toContain("200 GiB");
    expect(protocolDocuments.plan.markdown).toContain("20 epochs");
    expect(protocolDocuments.decision.markdown).toContain("final planning direction");
  });

  it("preserves historical evidence while tracking Week 3 v3 readiness separately", () => {
    expect(seedPlan.weeks.slice(0, 2)).toEqual(historicalPlan.weeks.slice(0, 2));
    const historicalWeek3 = historicalPlan.weeks[2];
    const week3 = seedPlan.weeks[2];
    expect(week3.tasks.slice(0, 5)).toEqual(historicalWeek3.tasks);
    expect(week3.gates.slice(0, 5)).toEqual(historicalWeek3.gates);
    expect(week3.reflection.startsWith(historicalWeek3.reflection)).toBe(true);
    expect(week3.actualMinutes).toBe(historicalWeek3.actualMinutes);
    expect(week3.state).toBe("closed");
    expect(week3.closedAt).not.toBeNull();
    expect(weekIsReady(seedPlan.weeks, 4)).toBe(true);
    expect(week3.tasks.every((task) => !task.required || task.state === "done")).toBe(true);
    expect(week3.gates.every((gate) => !gate.required || gate.state === "met")).toBe(true);
    const summary = JSON.stringify(seedPlan.protocol);
    expect(summary).toMatch(/frozen/i);
    expect(summary).toMatch(/20 epochs/);
    expect(summary).toMatch(/7, 17, 29/);
    expect(summary).toContain("180");
    expect(summary).toMatch(/100 GB/);
    expect(summary).not.toMatch(/26 declared configurations|six paired seeds/);
    expect(seedPlan.weeks[3].tasks.slice(1).every((task) => task.state === "todo")).toBe(true);
    expect(seedPlan.weeks.slice(4).every((week) => week.tasks.every((task) => task.state === "todo"))).toBe(true);
  });

  it("resolves local document links without exposing a filesystem path", () => {
    expect(protocolDocumentLink("../docs/decisions/0004-frozen-one-shot-v3.md")).toBe("/protocol/decision");
    expect(protocolDocumentLink("../../plan/research-plan.v3.md")).toBe("/protocol/plan");
    expect(isProtocolDocumentName("../../AGENTS.md")).toBe(false);
    expect(isProtocolDocumentName("toString")).toBe(false);
  });

  it("serves only the two public bundled documents", async () => {
    const source = await GET(new Request("http://localhost/protocol/plan/source"), {
      params: Promise.resolve({ document: "plan" }),
    });
    expect(source.status).toBe(200);
    expect(source.headers.get("Content-Type")).toContain("text/markdown");
    expect(await source.text()).toBe(protocolDocuments.plan.markdown);
    const denied = await GET(new Request("http://localhost/protocol/private/source"), {
      params: Promise.resolve({ document: "private" }),
    });
    expect(denied.status).toBe(404);
  });
});
