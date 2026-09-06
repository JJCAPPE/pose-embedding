"use client";

export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <html lang="en">
      <body>
        <main className="shell state-page">
          <h1>The tracker encountered an unexpected error.</h1>
          <button className="button primary" onClick={reset} type="button">Try again</button>
        </main>
      </body>
    </html>
  );
}
