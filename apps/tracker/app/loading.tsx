export default function Loading() {
  return (
    <div className="shell page-shell" aria-busy="true" aria-label="Loading research plan" role="status">
      <div className="loading-heading" />
      <div className="loading-line" />
      <div className="loading-grid">
        <div />
        <div />
        <div />
      </div>
    </div>
  );
}
