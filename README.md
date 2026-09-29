# Pose Embed

Pose Embed tests whether Contextual Similarity improves human-motion retrieval.
The first experiment compares Contextual with its exact contrastive component
on development classes. The full study requires all 26 configurations from the
image-paper comparison and supplementary controls, with six paired seeds.
Multi-Similarity is a comparator. Positive, null and negative results all count.

The current planning horizon is September 15 through December 18, 2026;
measured resources determine whether the full study requires an extension. Its companion
tracker provides a public research view of all 14 weeks and an authenticated
owner editor for tasks, evidence, reflections, and advancement gates.

## Repository map

- `plan/` — current v2 schedule and preserved v1 history
- `configs/` — validated research and experiment configurations
- `src/pose_embed/` — data, model, loss, corruption, training, and evaluation code
- `tests/` — unit, integration, and tiny CPU fixtures
- `apps/tracker/` — Next.js public tracker and owner editor
- `supabase/` — local configuration, migration, RLS tests, and seed bridge
- `docs/` — protocol, compliance, decisions, proposal, and result documents
- `third_party/` — pinned source manifest; checkouts live only in ignored `.cache/`
- `lit-review/` and `contextual-similarity-study-pack/` — legacy evidence archives

Raw NTU data, model weights, feature caches, run directories, and licensed
upstream checkouts do not belong in Git.

## Prerequisites

- Python 3.11 and `uv`
- Node.js 24, `pnpm`, and Corepack if required by the local Node installation
- Docker and Supabase CLI 2.105 or newer for database integration tests
- An authorized NTU RGB+D 120 dataset copy and MotionBERT checkpoint for real runs
- An NVIDIA GPU; profile the actual physical batch before choosing resources

## Local setup

```bash
uv sync --locked --group dev
pnpm install --frozen-lockfile
supabase start
```

Load the checked-in schedule into a fresh local database without committing an
Auth UUID:

```bash
export POSE_EMBED_DB_URL='postgresql://postgres:postgres@127.0.0.1:54322/postgres'
bash supabase/scripts/seed_plan.sh
```

To assign the project to an existing local Auth user, also set
`POSE_EMBED_OWNER_EMAIL` for that command. Never commit the email, password,
database URL, secret key, or service-role key.

Run the tracker against its checked-in fallback data with:

```bash
pnpm --filter @pose-embed/tracker dev
```

Copy `apps/tracker/.env.example` only when testing Supabase-backed reads or
owner edits. The browser receives a Supabase publishable key; it must never
receive a secret or service-role key.

## Verification

```bash
python scripts/verify_workspace.py
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
uv run pytest
pnpm --filter @pose-embed/tracker lint
pnpm --filter @pose-embed/tracker typecheck
pnpm --filter @pose-embed/tracker test
pnpm --filter @pose-embed/tracker build
supabase db reset
supabase test db supabase/tests --local
```

Fetch exact licensed/reference upstreams only when needed:

```bash
python scripts/fetch_upstreams.py --name MotionBERT
python scripts/fetch_upstreams.py --check --name MotionBERT
```

See `third_party/README.md` before using upstream code. In particular, the
contextual-similarity repository has no visible license at the pinned revision
and is reference-only.

## Week 3 feature extraction

This is preserved v1 infrastructure. Follow the v2 sequence below for the
current study; full frozen-cache extraction is supplementary. All Week 3
technical gates passed in [SCC job `7761714`](docs/protocol/week-3-scc-execution.md):
fresh parity, two byte-identical full auxiliary extractions, five validated
caches and the declared resource checks. Formal weekly closeout is recorded
separately in the plan. The [Weeks 1–3 handoff](docs/protocol/weeks-1-3-handoff.md)
summarizes verified gates and the next capacity decision.

The [saved execution plan](plan/week-03-execution-plan.md) and
[implementation record](docs/protocol/week-3-implementation.md) describe the
clean frozen-encoder path. Its CLI entry points are:

```bash
uv run pose-embed data development-episode --help
uv run pose-embed features parity --help
uv run pose-embed features extract --backend motionbert --help
uv run pose-embed features verify-repeatability --help
```

To reproduce that completed gate, use a clean committed checkout, the locked GPU
environment, and `scripts/extract_motionbert_week3.qsub`. Inputs stay under
`POSE_EMBED_DATA_ROOT`; caches and evidence stay under
`POSE_EMBED_ARTIFACT_ROOT`. The job also requires
`POSE_EMBED_MANIFEST_SET` pointing to the adopted `manifest-set.json`.
Pre-head caches contain 8,704 values per sample, not trained retrieval embeddings.
Submit from the repository root with scheduler logs outside the checkout:

```bash
mkdir -p "$POSE_EMBED_ARTIFACT_ROOT/logs"
qsub -o "$POSE_EMBED_ARTIFACT_ROOT/logs" scripts/extract_motionbert_week3.qsub
```

The wrapper now records a fresh SCC project-quota snapshot and requires the
repeatability gate to check it alongside filesystem free space.

## Scientific guardrails

- [Protocol v2](docs/protocol/protocol-v2.md) and its
  [scope amendment](docs/decisions/0003-motion-retrieval-v2.md) define the
  current study. The final prospectus and v1 protocol remain historical records.
- Select settings only on the class-disjoint auxiliary development split.
- Never open the official novel-action test through an upstream training script.
- Final-test evaluation requires the complete v2 locks and final-run records.
- The primary v2 outcome is clean multi-positive retrieval. One-shot and query
  corruption are separately declared supplementary studies. Corruption applies
  only to evaluation queries; reference galleries remain clean.
- Report every prespecified condition and paired seed, including null or
  negative results and resource costs.

## Manual external setup for a new deployment

For a new hosted deployment, create the dedicated Supabase Free organization
and acknowledge its displayed project cost. The automation can then provision
the project; after that, create one owner Auth user in the dashboard. In hosted
Supabase Auth, disable all public
sign-up, set and verify the Site URL against the final Vercel production origin,
and allow only the exact redirect origins needed. The checked
`supabase/config.toml` is local-only and must not be copied to hosted Auth.
Keep private evidence of dataset-terms acceptance outside Git. SCC GPU access
is documented in the [Week 1 profile](docs/protocol/week-1-gpu-profile.md), and
the BU determination is [researcher-confirmed](docs/compliance/computational-research-scope.md).
Scientific decisions follow the
[independent research governance record](docs/protocol/independent-research.md),
with no advisor approval requirement. Everything else is represented as checked code,
migrations, CI, or tracker gates.

The repository keeps a reference copy of the
[NTU RGB+D release agreement](docs/compliance/ntu-rgbd-release-agreement.md).
It is not proof of acceptance; keep private acceptance evidence outside Git.

This repository intentionally has no project-wide reuse license. Adding one
requires an explicit researcher decision after rights review and applicable BU
requirements. Third-party material retains its own license and
attribution requirements.

## V2: Contextual versus baseline first

Read [protocol v2](docs/protocol/protocol-v2.md), the
[scope amendment](docs/decisions/0003-motion-retrieval-v2.md), and the
[method adaptation inventory](docs/protocol/remaining-method-adaptations.md).
The main study fine-tunes MotionBERT with 512-dimensional embeddings, with a
separate 1,536-dimensional matched group. The first frozen pilot verifies the
plumbing and is supplementary to that study. Neither pilot opens the novel test.

```bash
uv run pose-embed benchmark coverage
uv run pose-embed benchmark profile --help
uv run pose-embed benchmark train --help
uv run pose-embed benchmark compare --help
```

`configs/benchmark.v2.yaml` declares the frozen pilot;
`configs/benchmark.finetune.v2.yaml` declares the trainable-backbone track.
Both fix physical P=8, K=4, six seeds, 1,000 development steps and validation
every 100 steps. These are development settings, not selected final recipes.
Use a new result-blind configuration to change them; a CLI track override cannot
change the hashed setting. A one-seed pilot does not establish superiority.

On SCC, from a clean committed checkout and the locked Linux environment:

```bash
source ~/pose-embed-scc/environment.sh
export POSE_EMBED_MANIFEST_SET="$POSE_EMBED_ARTIFACT_ROOT/manifests/ntu-input-v2-7721684/manifest-set.json"
qsub -o "$POSE_EMBED_ARTIFACT_ROOT/logs" scripts/verify_scc_setup.qsub
qsub -o "$POSE_EMBED_ARTIFACT_ROOT/logs" scripts/benchmark_v2.qsub \
  pilot configs/benchmark.v2.yaml 7
qsub -l gpu_memory=80G -o "$POSE_EMBED_ARTIFACT_ROOT/logs" \
  scripts/benchmark_v2.qsub profile configs/benchmark.finetune.v2.yaml 7
```

The pilot job verifies the upstream adapter, measures three real optimizer
steps per method, trains Contrastive then Contextual, and writes the paired
development comparison. All attempts, failures, batches, initializations,
checkpoints, selected metrics and timings are immutable under
`$POSE_EMBED_ARTIFACT_ROOT/benchmark-v2`. Logs and licensed data stay outside Git.
Use a separate locked environment for each active release. Complete its setup
verification first; it validates the adopted bundle before regeneration and
compares the complete new bundle without replacing the existing one. The setup
job allows two hours and logs each test plus the ten slowest test durations.

All 26 method adapters are implemented. `benchmark coverage` reports their
identities explicitly; implementation does not establish GPU feasibility or
retrieval performance. The physical fine-tuning batch failed on an L40S and
passed on an A100 80 GB for the priority pair. The seed-7 paired fine-tuning
pilot then completed in SCC job `7748592`: each method ran 1,000 updates and ten
development validations, taking about 6,500 seconds per method. This is
engineering evidence, not a six-seed or novel-test result. Every other method
still requires its own allocated-GPU profile; see the
[implementation record](docs/protocol/v2-implementation-record.md).

Profile the complete roster using the completed comparison as a prerequisite:

```bash
qsub -o "$POSE_EMBED_ARTIFACT_ROOT/logs" \
  scripts/benchmark_v2_profiles.qsub configs/benchmark.selection.v2.yaml 7 \
  "$POSE_EMBED_ARTIFACT_ROOT/benchmark-v2/pilots/20260926T204338Z-7748592-0ef858379c36/comparison.json"
```

The wrapper verifies successful paired evidence before broader GPU work. Each
method runs three real optimizer steps and a fixed, bounded
development retrieval profile. A failed profile remains recorded; other methods
are still attempted. No profile is eligible for scientific selection.

The [selection campaign](docs/protocol/selection-campaign-v2.md) declares three
learning-rate candidates and six paired seeds for each method: **468 development
runs**, followed by **156 selected final runs**. The provisional 50,000-update
budget requires a complete time/storage forecast before launch. The
[continuation protocol](docs/protocol/checkpoint-segments.md) supports immutable
segments across scheduler allocations; `scripts/benchmark_v2_train.qsub` passes
explicit training arguments with a ten-hour soft checkpoint boundary. Retain
every segment and use the printed resume command for the next allocation.

The [secondary studies](docs/protocol/secondary-studies-v2.md) add one-shot and
query-corruption evaluation, loss-component ablations, training label noise,
pose replacement and reduced training classes. They declare 276 development
and 276 final training runs, with fixed inherited recipes. All **432 main and
secondary final runs** must complete before novel-test opening.

The [storage floor](docs/protocol/v2-resource-floor.md) exceeds the previously
observed available SCC project space even before full auxiliary state and
segments. A September 29, 02:36 UTC read-only quota check found 293.44 GB
remaining in the shared allocation, below the 599.27 GB checkpoint-only floor.
Available capacity can change; recheck it, and resolve storage and measured
runtime before launching the complete campaign.

Selection, final training and test-opening locks require the full 26 × 6 matrix,
matched initialization/batches, verified inputs and the statistical analysis
plan. Final evaluation uses all eligible held-out motions, excludes self and
synchronized camera views, and reports Recall@K, mAP, mAP@R and MRR. The v1
one-shot evaluator and its old three-method lock do not authorize this study.
