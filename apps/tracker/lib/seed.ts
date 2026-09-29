import planJson from "../../../plan/research-plan.v3.json";
import { researchPlanSchema } from "@/lib/schema";

export const seedPlan = researchPlanSchema.parse(planJson);
