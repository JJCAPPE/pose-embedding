# Pose Embed tracker

The tracker is a public, static-first Next.js application. It always builds from
`plan/research-plan.v1.json`; when Supabase is configured, public reads use the live
database and fall back to that checked-in seed on failure.

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
Public plan subtrees cross a request-time boundary while their loading shells remain
prerendered, so an invalidated cache cannot be hidden behind build-time page output.
Owner updates invalidate the tag immediately. A failed cache revalidation preserves the
last successful Supabase snapshot; a cold-start failure shows the checked-in seed with a
visible read-only notice. Owner routes verify the signed-in account through the
authenticated-only `owner_access` view and enforce every mutation again through RLS.
