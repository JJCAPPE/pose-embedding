import { Suspense } from "react";
import Loading from "@/app/loading";
import { OverviewContent } from "@/components/overview-content";
import { getRequestPublicPlan } from "@/lib/request-plan";

export default function HomePage() {
  return (
    <Suspense fallback={<Loading />}>
      <HomePageContent />
    </Suspense>
  );
}

async function HomePageContent() {
  const plan = await getRequestPublicPlan();
  return <OverviewContent plan={plan} />;
}
