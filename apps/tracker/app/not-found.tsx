import Link from "next/link";

export default function NotFound() {
  return (
    <div className="shell state-page">
      <p className="eyebrow">Not found</p>
      <h1>That week is outside the plan.</h1>
      <p>The tracked schedule contains Weeks 1 through 14.</p>
      <Link className="button primary" href="/">Return to the plan</Link>
    </div>
  );
}
