# 0003 — Replicate the full contextual comparison in motion

Date: 2026-09-24. Status: researcher-directed scope revision; implementation and
final scientific lock remain pending.

The researcher requested a motion-domain replication of the original image
retrieval comparison and subsequently identified contextual similarity as the
method of interest. Multi-Similarity and Multi-Similarity with mining are distinct
required comparators. First establish Contextual versus its exact contrastive
component on development data, then complete the full 26-configuration registry.
A two-method result does not complete the requested study.

The main experiment uses a common fine-tuned pretrained MotionBERT backbone,
512-dimensional embeddings, six paired seeds and clean multi-positive held-out
action retrieval. The paper's PA + AVSL and Contextual comparison is a separate
matched 1,536-dimensional group. Frozen-encoder, one-shot and corruption work is
supplementary. Architecture-specific methods require their actual mechanisms,
explicit motion adaptations and permitted code provenance.

`docs/protocol/protocol-v2.md`, `configs/benchmark.v2.yaml` and
`configs/benchmark-methods.v2.json` define the new work. They supersede the old
three-method robustness scope, its nine-run final set and its post-test MS stretch
exception. All declared final configurations must be selected and trained before
any novel outcome is viewed. A negative or null result is scientifically valid.

Preserve the prospectus, v1 plan/protocol, adopted input contract, prior manifests,
run records, and verified GPU/software evidence. Revalidate compatibility rather
than relabeling earlier work as a completed v2 benchmark. The BU determination
was researcher-confirmed on September 24; actual research hours remain unprovided.
Neither this amendment nor the tracker migration invents hours or closes a week.

The public schedule retains 14 records through December 18 as a planning horizon.
The full study has not been shown feasible within that horizon. Real backward
memory, training time, storage and implementation work determine an explicit
continuation if required. Missing methods remain blockers to complete replication.

Publication requires both a guarded Supabase data migration and a deployment of
the v2 protocol bundle. Preserve live row versions, RLS, private ownership and
append-only audit records. A rollback uses a new compensating migration and a
matching deployment; redeploying v1 alone cannot undo live progress.
