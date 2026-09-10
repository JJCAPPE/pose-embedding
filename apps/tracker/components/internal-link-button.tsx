"use client";

import { Button } from "antd";
import type { ButtonProps } from "antd";
import Link from "next/link";

export function InternalLinkButton({
  href,
  ...buttonProps
}: Omit<ButtonProps, "href"> & { href: string }) {
  return (
    <Link href={href} legacyBehavior passHref>
      <Button {...buttonProps} />
    </Link>
  );
}
