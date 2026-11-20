# Pose Embed study guide

Start with [the PDF](main.pdf). It explains the frozen v3 study from first
principles: the question, pose data, representations, three objectives, fair
comparison, controlled damage, statistical analysis, code provenance, decision
history, and what verification does and does not establish. The final sections
include explanation practice and answered study questions.

Prepared October 30, 2026, using scientific records through October 28. Earlier
successful runs retain their historical status. The guide does not claim a
completed final comparison or current cluster capacity.

The mathematical prerequisites are calculus, linear algebra, and introductory
probability/statistics. Programming familiarity is assumed. Private academic
records were used only to calibrate the level and are not included.

## Companion notebooks

All data are synthetic. Each notebook is self-contained, uses only NumPy, has
executed outputs, and needs no dataset, checkpoint, network, or cluster access.

- [01: Embeddings and learning](notebooks/01_embeddings_and_learning.ipynb):
  cosine geometry, normalization, and a small analytic gradient calculation.
- [02: A fair comparison](notebooks/02_designing_a_fair_comparison.ipynb):
  action splits, camera-view leakage, pairing, and equal tuning opportunities.
- [03: Effects and cluster bootstrap](notebooks/03_effects_and_cluster_bootstrap.ipynb):
  the degradation effect, absolute accuracy, and query-weighted cluster resampling.

Open them in a notebook-capable editor using the project's Python environment.
Notebook 1 deliberately simplifies the objective; it is not a production-loss
implementation. Notebook 3 illustrates the specified analysis on invented data;
its output is not a scientific result for Pose Embed.

## Rebuild

The editable source is [main.tex](main.tex), with chapters in `chapters/`.
From this directory, run:

```bash
tectonic main.tex
```

Tectonic may download missing standard TeX packages during the first build.
The diagrams are vector TikZ drawings embedded in the source; no figure generator
or real-data image is required. `main.pdf` is the checked-in readable deliverable.

## Evidence and scope

Repository links in the PDF are pinned to main commit
`b32d50f66206b561fa34867c9274fac6ba7c287d`, with the October 28 preparation
checkpoint pinned to `5d50410b07e19a980fe3b711e63b10417b40b818`. The canonical
protocol and accepted amendments remain authoritative; this teaching guide
changes no experiment, acceptance rule, or dataset access permission.

This guide follows the structure of the existing rowing study guide: a
mathematical explanation, concrete examples, source map, and small executable
labs. It omits a walkthrough of individual test implementations and historical
v2 methods that are outside the current comparison.

## Verification

The 36-page PDF compiled without TeX warnings and every page was rendered and
visually inspected. Independent reviews checked mathematical definitions,
provenance, experimental design, statistics, and historical/current status
against the pinned records. Repository source targets were verified.

All 13 notebook code cells executed on Python 3.11.14 with NumPy 2.4.6; assertions
passed and saved outputs reproduced exactly. The notebooks also passed schema
validation. Workspace verification passed. No real experiment, application,
database, or cluster validation was rerun for this documentation-only change.
