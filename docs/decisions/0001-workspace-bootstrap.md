# Workspace bootstrap decision

Date: 2026-09-06

The repository is being converted from a literature/proposal archive into a
reproducible research workspace plus a public progress tracker. The tracked
August 2026 prospectus remains the scientific source of truth; the broader UROP
draft is retained as historical proposal material only.

## Preservation record

- Baseline commit: `2b981b5`
- Existing proposal sources, generator, DOCX, PDF, and TeX were preserved under
  `docs/proposal/2026/` before cleanup.
- The preserved DOCX passed ZIP validation and the PDF passed `qpdf --check`.
- After the new workspace passed its verification suite, render-only files were
  moved recoverably to
  `~/.Trash/pose-embed-render-tmp-20260906/`; legacy upstream worktrees were
  moved to `~/.Trash/pose-embed-legacy-upstreams-20260906/` after their pinned
  commits were verified in the replacement cache. Superseded output scratch was
  moved to `~/.Trash/pose-embed-output-scratch-20260906/` after the retained
  proposal artifacts were verified.

## Repository decisions

- Do not rewrite Git history during this bootstrap.
- Remove Finder metadata from version control.
- Replace invalid gitlinks under `lit-review/repos/` with a manifest of upstream
  URLs and immutable commits. Fetched upstream code belongs in an ignored cache.
- Stop tracking literature PDFs at the current tip and retain a URL/checksum
  manifest instead.
- Never commit licensed datasets, checkpoints, embeddings, run directories,
  credentials, or environment files.
- Do not add a repository-wide software license until BU/advisor review. Keep
  third-party license and provenance notices with any adapted code.

## Scientific implementation boundary

The bootstrap provides tested interfaces, deterministic fixtures, the audited
losses/corruptions/evaluator, manifests, protocol locking, and run provenance.
It cannot manufacture licensed NTU data, a MotionBERT checkpoint, GPU access,
institutional approval, or final experimental results. Those enter through the
explicit weekly gates in the tracker.
