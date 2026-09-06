# Research plan seed

`research-plan.v1.json` is the immutable version-controlled source used to create
the initial Supabase rows and to keep the public site readable during an outage.

After production seeding, Supabase is authoritative for live progress. The seed is
not rewritten by the tracker and must not be treated as a second editable store.
It contains public-safe planning information only: no user identifiers, private
notes, licensed-data locations, credentials, or activity-log records.
