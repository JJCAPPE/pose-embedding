import { connection } from "next/server";
import { getPublicPlan } from "@/lib/data";

export async function getRequestPublicPlan() {
  await connection();
  return getPublicPlan();
}
