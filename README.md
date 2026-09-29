# Pose Embed

Pose Embed tests whether the full contextual training recipe reduces one-shot
human-motion retrieval degradation relative to standard contrastive training.
The [final v3 plan](plan/research-plan.v3.md) fixes a frozen MotionBERT encoder,
three objectives, three paired seeds, 20 epochs, and nine query corruptions.
Positive, null and negative results all count. The broader v2 benchmark remains
preserved as historical work, outside the December study.

The current planning horizon is September 15 through December 18, 2026;
selection requires the measured capacity and validity gates. Its companion
tracker provides a public research view of all 14 weeks and an authenticated
owner editor for tasks, evidence, reflections, and advancement gates.

## Repository map

- `plan/` — current v3 schedule and preserved v1/v2 history
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

## Current v3 execution

The active study is the [final v3 plan](plan/research-plan.v3.md) and
[protocol v3](docs/protocol/protocol-v3.md): frozen MotionBERT, a biased
8,704-to-2,048 head, Contrastive/Contextual/SupCon, three paired seeds and
20 epochs. The [Week 3 readiness record](docs/protocol/week-3-v3-readiness.md)
separates implemented preparation from measured SCC evidence.

```bash
uv run pose-embed protocol verify --config configs/protocol.v3.yaml
uv run pose-embed study-v3 --help
```

The checked-in protocol is a non-executable template. Before the Week 4 GPU
work, register every historical artifact root, package the auxiliary-only
source, measure the training-only fallback, rebind the unchanged identities,
and freeze the resolved design. Follow the
[SCC v3 runbook](docs/protocol/scc-v3-runbook.md). Preparation uses
`scripts/prepare_v3.qsub`; fresh caches and the three engineering pilots use
`scripts/study_v3.qsub`. Inputs remain under `POSE_EMBED_DATA_ROOT`, and v3
outputs live under the existing canonical artifact root in `study-v3/`.

Historical Week 3 extraction completed in
[SCC job 7761714](docs/protocol/week-3-scc-execution.md). Those immutable caches
prove the earlier path worked; v3 requires fresh parity and caches after its
design freeze. The [v1](docs/protocol/protocol-v1.md) and
[v2](docs/protocol/protocol-v2.md) configurations, implementations and evidence
remain for provenance. Their fine-tuning and 26-method campaign instructions
are retired from the active workflow.

## Scientific guardrails

- Select only on the class-disjoint auxiliary development episode. Engineering
  pilots and corrupted development scores are ineligible for selection.
- Freeze every cache-affecting input before extraction. Preserve every attempt,
  failure, manifest and historical cache; never relabel an old artifact as v3.
- Use the registered canonical artifact root. Test opening is dataset-wide
  across protocol versions, and source readers check the shared seal.
- Complete and lock all nine fresh final heads before any novel pose processing.
  Later selection and final-opening authorizers remain closed until their
  measured gates have been independently verified.
- Keep galleries clean. Corrupt queries using the exact fixed v3 operators,
  fallback and paired seeds; report all prespecified conditions and costs.
- A null or negative result is a successful scientific result.

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
