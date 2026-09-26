import planJson from "../../../plan/research-plan.v2.json";
import { researchPlanSchema } from "@/lib/schema";

export const seedPlan = researchPlanSchema.parse(planJson);
