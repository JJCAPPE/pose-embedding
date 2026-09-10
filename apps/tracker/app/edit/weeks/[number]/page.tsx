import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { EditWeekWorkspace } from "@/components/editor-forms";
import { requireOwner } from "@/lib/auth";
import { loadPlanFromSupabase } from "@/lib/data";
import { weekIsReady } from "@/lib/domain";

type EditWeekPageProps = {
  params: Promise<{ number: string }>;
};

export async function generateMetadata({ params }: EditWeekPageProps): Promise<Metadata> {
  const { number } = await params;
  return { title: `Update Week ${number}` };
}

export default async function EditWeekPage({ params }: EditWeekPageProps) {
  const { number } = await params;
  const { supabase } = await requireOwner();
  const plan = await loadPlanFromSupabase(supabase);
  const week = plan.weeks.find((candidate) => candidate.number === Number(number));
  if (!week) notFound();

  return <EditWeekWorkspace ready={weekIsReady(plan.weeks, week.number)} week={week} />;
}
