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

The v2 migration is based on a public live snapshot from September 24 at 22:35 UTC,
including the confirmed BU determination. It preserves completed v1 work and
actual time, records only evidenced local Week 3 software progress, and adds a
separate uncompleted v2 retrieval gate. Row-version drift and edits to closed
weeks abort the migration. Refresh the live snapshot before publication; do not
force it through a conflict or reset production.

Plans and public exports contain no owner identifiers, private notes, licensed
data locations, credentials or activity-log records. Preserve prior run artifacts
and hashes; old evidence does not automatically validate the v2 protocol.
