# Pose Embed tracker

The tracker is a public, static-first Next.js application. It always builds from
`plan/research-plan.v3.json`; when Supabase is configured, public reads use the live
database and fall back to that checked-in seed on failure.

The protocol overview links to the full final v3 plan at `/protocol/plan` and
its scope decision at `/protocol/decision`. These public Markdown documents are
bundled in `lib/protocol-documents.json`, with readable tables and source downloads.
After changing either tracked document, refresh the bundle from the repository root:

```sh
pnpm --filter @pose-embed/tracker sync:protocol-documents
```

The tracker tests require exact agreement with `plan/research-plan.v3.md` and
`docs/decisions/0004-frozen-one-shot-v3.md`. The bundle contains only these two
public planning records; document routes never read arbitrary filesystem paths.

## Local development

Use Node 24 and pnpm 10. From the repository root:

```sh
pnpm install --frozen-lockfile
pnpm web:dev
```

No environment variables are required for the public site. To test authenticated
editing, copy `.env.example` to `.env.local`, provide the dedicated project's URL
and publishable key, and set `EDITING_ENABLED=true`. Never add a Supabase secret or
service-role key to this application.

## Checks

```sh
pnpm web:lint
pnpm web:typecheck
pnpm web:test
pnpm web:build
pnpm --filter @pose-embed/tracker exec playwright install chromium
pnpm --filter @pose-embed/tracker e2e
```

Public reads use Next.js 16 Cache Components with a five-minute stale window,
hourly background revalidation, a one-year hard expiry, and the `plan` cache tag.
The cached loader takes the `research-plan.v3` revision as part of its cache key,
so a retained v2 live snapshot cannot populate the v3 deployment. Both `plan`
and revision tags are attached; owner edits continue to invalidate `plan`.
Public plan subtrees cross a request-time boundary while their loading shells remain
prerendered, so an invalidated cache cannot be hidden behind build-time page output.
Owner updates invalidate the tag immediately. A failed cache revalidation preserves the
last successful Supabase snapshot; a cold-start failure shows the checked-in seed with a
visible read-only notice. Owner routes verify the signed-in account through the
authenticated-only `owner_access` view and enforce every mutation again through RLS.
