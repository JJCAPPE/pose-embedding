"use client";

export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="shell state-page">
      <p className="eyebrow">Plan unavailable</p>
      <h1>The research record could not be loaded.</h1>
      <p>Try the request again. The checked-in plan remains available through the repository.</p>
      <button className="button primary" onClick={reset} type="button">Try again</button>
    </div>
  );
}
