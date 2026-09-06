# Tracker database

This directory is a Supabase CLI project for the public-read, owner-write
tracker. The initial migration creates all tables, constraints, explicit Data
API grants, RLS policies, database-managed versions, closed-week gates, and an
append-only owner-visible audit trail.

## Local verification

```bash
supabase db start
supabase db reset
supabase test db supabase/tests --local
supabase db lint --local --schema public,private --level warning --fail-on error
supabase db advisors --local --type security --level warn --fail-on warn
```

`supabase db reset` applies only migrations. It intentionally does not duplicate
the version-controlled plan in `seed.sql`. Import the canonical plan afterward:

```bash
export POSE_EMBED_DB_URL='postgresql://postgres:postgres@127.0.0.1:54322/postgres'
bash supabase/scripts/seed_plan.sh
```

## Production bootstrap

1. Link the dedicated project locally without committing its ref or credentials.
2. Run `supabase db push --linked` and review the migration list.
3. In the hosted Auth dashboard, disable new-user sign-up for email and every
   other provider. There is no public sign-up flow for this project.
4. Set the hosted Auth Site URL to the verified Vercel production URL. Allow
   only that production origin and the exact Vercel preview URL(s) needed for
   deployment verification as redirect URLs; remove temporary entries after
   verification.
5. Create and confirm the sole email/password owner in the Auth dashboard.
6. Temporarily set `POSE_EMBED_DB_URL` to an administrator connection and
   `POSE_EMBED_OWNER_EMAIL` to that existing Auth user's email.
7. Run `bash supabase/scripts/seed_plan.sh`, then unset both variables.
8. Run the linked database security and performance advisors.
9. Before enabling production editing, verify in the hosted dashboard or
   Management API that sign-up remains disabled and the Site URL exactly matches
   the live Vercel production origin. Then test anonymous denial, owner login,
   and owner editing against production.

`supabase/config.toml` is for the local stack and deliberately contains localhost
URLs. Its global `auth.enable_signup = false` blocks self-registration, while
the email provider remains enabled so administrator-created test users can sign
in. `supabase db push` applies migrations only. Do not copy or push the local
Auth configuration to the hosted project; configure and verify hosted Auth
settings independently.

The plan importer is admin-only, rejects an existing project instead of
overwriting progress, and never reads an owner UUID from source control. The
ownership helper resolves exactly one existing `auth.users` row by email and
refuses reassignment from a different owner. Ownership is stored only in the
non-exposed `private.project_owners` table; public project rows and exports do
not contain an owner UUID.

The web application needs only `NEXT_PUBLIC_SUPABASE_URL` and
`NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`. Never configure a secret or service-role
key in a `NEXT_PUBLIC_` variable or in Vercel previews.
