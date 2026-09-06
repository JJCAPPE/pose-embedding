# Project instructions

These rules apply to every automated or human change in this repository.

## Canonical intent

- Read `plan/research-plan.v1.json`, the final tracked prospectus, and
  `docs/protocol/protocol-v1.md` before changing scientific behavior.
- The core comparison is contrastive-only, supervised contrastive, and full
  contextual-plus-contrastive with a frozen MotionBERT encoder. Multi-Similarity
  plus its miner is gated stretch work only.
- A null or negative contextual result is a successful scientific result. Never
  adjust a split, corruption, metric, or claim after seeing novel-test outcomes.

## Data and experiment safety

- Never commit NTU data, checkpoints, embeddings, caches, full run artifacts,
  credentials, participant information, or private advisor correspondence.
- Use `POSE_EMBED_DATA_ROOT` and `POSE_EMBED_ARTIFACT_ROOT` for licensed inputs
  and generated runs. Keep only manifests, hashes, configs, compact summaries,
  and permitted final deliverables in Git.
- Final-test commands must validate the locked protocol hash. Do not reuse the
  upstream MotionBERT loop that evaluates the novel classes during training.
- Pair seeds, head initialization, physical `P x K` batches, and query
  corruptions across methods. Gradient accumulation is not a substitute for a
  physical contextual-loss batch.
- Preserve every run manifest. Never overwrite or hand-edit result artifacts.

## Upstream and licensing boundary

- Resolve sources through `third_party/upstreams.toml` and
  `scripts/fetch_upstreams.py`; do not add gitlinks or commit upstream clones.
- The pinned contextual-similarity repository has no license. It is
  reference-only: do not copy, vendor, adapt, or redistribute its code.
- Retain upstream headers and attribution for any permitted minimal MotionBERT
  compatibility port. Do not add a repository-wide license without explicit
  advisor/BU approval.

## Tracker and database

- Public pages contain only public-safe plan and progress data. The activity log
  and owner identity must never enter public loaders or exports.
- Supabase RLS is the authorization boundary. Every exposed table requires
  explicit grants and RLS; `authenticated` alone is never authorization.
- Client updates must filter by both row ID and expected `version`, omit
  `version` from the payload, request returned rows, and treat zero rows as a
  concurrency conflict. Database triggers increment versions.
- Never expose a secret/service-role key or add privileged functions to the
  `public` schema. Keep privileged functions in `private`, fix their search
  path, and revoke execution from API roles. The sole narrow exception is the
  fixed-search-path boolean ownership predicate required by RLS and the
  security-invoker `owner_access` view; `private` must remain outside the
  PostgREST exposed-schema list.
- Keep owner UUIDs only in the non-exposed private ownership mapping. App users
  cannot create projects; production ownership is assigned by the administrative
  seed command after the sole Auth user exists.
- Treat `supabase/config.toml` as local-only. Hosted Auth must have public sign-up
  disabled and its Site URL/redirect origins verified against the live Vercel
  deployment before editing is enabled.
- Closed-week task, gate, source-link, and plan edits require an explicit,
  audited reopen reason. Reflections may be added while closed.

## Change discipline and checks

- Preserve unrelated local changes. Make surgical edits and remove only files
  made obsolete by your own change.
- Keep the Python 3.11 `uv` lock and Node 24 `pnpm` lock reproducible.
- Before handoff, run the applicable subset of:

```bash
python scripts/verify_workspace.py
uv sync --locked --group dev
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
uv run pytest
pnpm --filter @pose-embed/tracker lint
pnpm --filter @pose-embed/tracker typecheck
pnpm --filter @pose-embed/tracker test
pnpm --filter @pose-embed/tracker build
supabase db reset
supabase test db supabase/tests --local
supabase db advisors --local --type security --fail-on warn
```

- Record what was verified and any environmental blocker. Do not claim a live
  deployment, remote migration, dataset result, or GPU result without evidence.
