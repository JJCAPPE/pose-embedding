"use client";

import { useSyncExternalStore } from "react";
import { Tag } from "antd";
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

  return isCurrent ? <Tag className="current-marker">Current week</Tag> : null;
}
