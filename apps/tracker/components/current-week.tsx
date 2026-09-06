"use client";

import { useSyncExternalStore } from "react";
import { dateInTimezone } from "@/lib/domain";

const subscribe = () => () => undefined;

export function CurrentWeekMarker({
  startDate,
  endDate,
  timezone,
}: {
  startDate: string;
  endDate: string;
  timezone: string;
}) {
  const isCurrent = useSyncExternalStore(
    subscribe,
    () => {
      const today = dateInTimezone(new Date(), timezone);
      return startDate <= today && today <= endDate;
    },
    () => false,
  );

  return isCurrent ? <span className="current-marker">Current week</span> : null;
}
