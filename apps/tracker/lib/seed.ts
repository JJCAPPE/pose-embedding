import planJson from "../../../plan/research-plan.v1.json";
import { researchPlanSchema } from "@/lib/schema";

export const seedPlan = researchPlanSchema.parse(planJson);
