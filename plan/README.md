# Research plan revisions

`research-plan.v2.json` is the active public-safe schedule and bundled protocol
summary for the motion-domain comparison. `research-plan.v1.json` preserves the
previous scope and its historical completion evidence. The JSON schema remains
`1.0.0`: the scientific revision is v2, while the tracker data shape is unchanged.

The 14 calendar records through December 18 are a provisional planning horizon.
They do not promise that all 26 configurations can be implemented and evaluated
within the previous eight-hour weekly budget. The measured all-method resource
gate must determine whether a dated continuation is needed. The complete method
roster remains required.

After production seeding, Supabase is authoritative for live progress. Changing
the fallback JSON does not overwrite live rows. The tracker combines live rows
with the protocol summary bundled in its deployed seed, so a revision requires a
coordinated data migration and deployment. The administrative seed importer is
for fresh databases and refuses to overwrite an existing project.

The original v2 migration is based on a public live snapshot from September 24
at 22:35 UTC, including the confirmed BU determination. A September 29 read of
the hosted tracker found Weeks 1 and 2 already closed with zero recorded minutes,
despite notes that time was unreported; the checked-in fallback still shows the
earlier open states. An initial all-week reconciliation attempt aborted without
row changes at its closed-week guard. The revised September 29 migration touches
only the still-open Week 3 objective, deliverable, review prompt, reflection
and extraction-gate wording. It does not invent actual researcher time or close a week. Seed
and hosted row versions are independent concurrency counters. Refresh the live
snapshot before any hosted migration; never force a conflict or reset production.
The narrowed migration was applied to the hosted tracker on September 29;
read-only verification found Week 3 version 6 and extraction gate 4 version 4,
with hosted Weeks 1–2 unchanged.
See the [Weeks 1–3 handoff](../docs/protocol/weeks-1-3-handoff.md) for the
evidence boundaries and required researcher reconciliation.

Plans and public exports contain no owner identifiers, private notes, licensed
data locations, credentials or activity-log records. Preserve prior run artifacts
and hashes; old evidence does not automatically validate the v2 protocol.
