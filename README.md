# Pose Embed

Pose Embed is a reproducible study of one-shot human-action retrieval from
noisy pose sequences. It compares contrastive, supervised-contrastive, and
contextual metric-learning objectives while holding the frozen MotionBERT
encoder, data protocol, physical batches, tuning budget, and evaluator fixed.

The project runs from September 15 through December 18, 2026. Its companion
tracker provides a public advisor view of all 14 weeks and an authenticated
owner editor for tasks, evidence, reflections, and advancement gates.

## Repository map

- `plan/` — immutable v1 schedule seed consumed by the tracker
- `configs/` — validated research and experiment configurations
- `src/pose_embed/` — data, model, loss, corruption, training, and evaluation code
- `tests/` — unit, integration, and tiny CPU fixtures
- `apps/tracker/` — Next.js public tracker and owner editor
- `supabase/` — local configuration, migration, RLS tests, and seed bridge
- `docs/` — protocol, decisions, proposal, and result documents
- `third_party/` — pinned source manifest; checkouts live only in ignored `.cache/`
- `lit-review/` and `contextual-similarity-study-pack/` — legacy evidence archives

Raw NTU data, model weights, feature caches, run directories, and licensed
upstream checkouts do not belong in Git.

## Prerequisites

- Python 3.11 and `uv`
- Node.js 24, `pnpm`, and Corepack if required by the local Node installation
- Docker and Supabase CLI 2.105 or newer for database integration tests
- An authorized NTU RGB+D 120 dataset copy and MotionBERT checkpoint for real runs
- An NVIDIA GPU with at least 16 GB VRAM for scheduled experiments

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

## Scientific guardrails

- The tracked final prospectus and `docs/protocol/protocol-v1.md` define scope;
  the broader UROP draft does not expand the core experiment.
- Tune only on the class-disjoint auxiliary validation split.
- Never open the official novel-action test through an upstream training script.
- Final-test evaluation requires the locked protocol hash.
- Keep galleries clean and apply deterministic corruption only to queries.
- Report all preregistered conditions and seeds, including null or negative results.

## Manual external setup

Before production editing can be enabled, create the dedicated Supabase Free
organization and acknowledge its displayed project cost. The automation can
then provision the project; after that, create one owner Auth user in the
dashboard. In hosted Supabase Auth, disable all public
sign-up, set and verify the Site URL against the final Vercel production origin,
and allow only the exact redirect origins needed. The checked
`supabase/config.toml` is local-only and must not be copied to hosted Auth.
Dataset terms, GPU access, advisor approval, and BU governance determinations
also require the researcher. Everything else is represented as checked code,
migrations, CI, or tracker gates.

This repository intentionally has no project-wide reuse license while advisor
and BU review is pending. Third-party material retains its own license and
attribution requirements.
