import type { Metadata } from "next";
import { Suspense } from "react";
import Loading from "@/app/loading";
import { JourneyExperience } from "@/components/journey/journey-experience";
import { getRequestPublicPlan } from "@/lib/request-plan";
import "./journey.css";

export const metadata: Metadata = {
  title: "The research journey",
  description:
    "Explore how Pose Embed tests one-shot human-motion retrieval: an interactive 3D explanation and the fourteen-week path from a fair question to a defensible answer.",
};

export default function JourneyPage() {
  return (
    <Suspense fallback={<Loading />}>
      <JourneyPageContent />
    </Suspense>
  );
}

async function JourneyPageContent() {
  const plan = await getRequestPublicPlan();
  return (
    <JourneyExperience
      weeks={plan.weeks}
      dataSource={plan.dataSource}
      lastRefreshedAt={plan.lastRefreshedAt}
    />
  );
}
