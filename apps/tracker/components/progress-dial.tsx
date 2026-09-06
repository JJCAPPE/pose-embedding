export function ProgressDial({ percent }: { percent: number }) {
  const bounded = Math.max(0, Math.min(percent, 100));
  return (
    <div
      className="progress-dial"
      style={{ "--progress": `${bounded * 3.6}deg` } as React.CSSProperties}
      role="img"
      aria-label={`${bounded}% of required tasks complete`}
    >
      <span>{bounded}%</span>
    </div>
  );
}
