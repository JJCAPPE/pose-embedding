import { describe, expect, it } from "vitest";
import canonicalPlan from "../../../plan/research-plan.v3.json";
import { journeyWeeks } from "@/lib/journey-content";

describe("public research journey", () => {
  it("covers every canonical week exactly once in calendar order", () => {
    const numbers = journeyWeeks.map((week) => week.number);

    expect(numbers).toHaveLength(14);
    expect(new Set(numbers).size).toBe(numbers.length);
    expect(numbers).toEqual(canonicalPlan.weeks.map((week) => week.number));
  });

  it("keeps progress and private records out of the static narrative", () => {
    const narrativeFields = ["title", "question", "action", "outcome", "why"] as const;
    const allowedFields = ["number", "phase", "stage", ...narrativeFields].sort();

    for (const week of journeyWeeks) {
      expect(Object.keys(week).sort()).toEqual(allowedFields);
      for (const field of narrativeFields) {
        expect(week[field].trim().length).toBeGreaterThan(0);
      }
      // These narratives explain intentions. Current completion belongs to the
      // public plan loader and must never be inferred from the calendar copy.
      expect(narrativeFields.map((field) => week[field]).join(" ")).not.toMatch(
        /\b(?:we have (?:completed|trained|verified|proved)|results (?:show|prove)|is now complete|test has been opened)\b/i,
      );
    }
  });

  it("preserves the prerequisites and limits of the scientific claim", () => {
    expect(journeyWeeks[3].why).toContain("cannot pick learning rates");
    expect(journeyWeeks[5].why).toContain("Corrupted development scores");
    expect(journeyWeeks[7].action).toContain("Keep MotionBERT frozen");
    expect(journeyWeeks[10].why).toContain("keeps the test sealed");
    expect(journeyWeeks[11].action).toContain("before loading novel poses");
    expect(journeyWeeks[11].action).toContain("Keep the gallery clean");
    expect(journeyWeeks[12].question).toContain("full contextual recipe");
    expect(journeyWeeks[12].action).toContain("show absolute scores");
    expect(journeyWeeks[12].why).toContain("upper bound below zero");
    expect(journeyWeeks[12].why).toContain("null and contrary outcomes");
    expect(journeyWeeks[13].outcome).toContain("incomplete-study record");
  });
});
