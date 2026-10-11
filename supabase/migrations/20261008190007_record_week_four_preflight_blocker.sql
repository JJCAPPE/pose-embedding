-- Record the October 8 seal-revalidation blocker without changing prior evidence.
-- Preserve time, all previous weeks and pending gates; no schema or Auth changes.
-- Version/content guards make retries idempotent and protect concurrent progress.
do $migration$
declare
  edits constant jsonb := $edits$
[
  {
    "table": "tasks",
    "id": "w04-task-01",
    "before": {
      "id": "w04-task-01",
      "week_id": "week-04",
      "position": 1,
      "title": "Freeze and validate the v3 path",
      "details": "Complete explicit v3 configuration/manifest validation, dataset-wide seal checks and auxiliary/novel source access separation. Register historical roots, preserve old artifacts, and freeze the complete design and cache-affecting code before extraction.",
      "expected_output": "An immutable v3 design/pilot specification and passing version, provenance and seal checks.",
      "required": true,
      "estimate_minutes": 90,
      "state": "done",
      "completion_note": "Satisfied by the verified Week 3 handoff on 2026-09-29, not a second freeze: SCC job 7790916 completed with failed=0 and exit_status=0. Explicit v3 validators, registered historical-root seals and auxiliary/novel source separation passed; all eight identity sets and the auxiliary preparation are bound to the corrected immutable design lock 39426a3b2ddea74aaa8c1d39737cd9e5fb9c870c21745f5527e4e97b58d14e2d. The active scientific release is 2897f4fe4c1fb1857432a0e92a7391dde68307f5. Fresh v3 parity/caches, loss/paired-training evidence and three complete pilots remain Week 4 work. Recheck runtime seals before every job. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-3-v3-readiness.md",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-3-v3-readiness.md",
      "completed_at": "2026-09-29T22:28:17.544258+00:00",
      "version": 4,
      "project_id": "pose-embed"
    },
    "values": {
      "state": "blocked",
      "completion_note": "Satisfied by the verified Week 3 handoff on 2026-09-29, not a second freeze: SCC job 7790916 completed with failed=0 and exit_status=0. Explicit v3 validators, registered historical-root seals and auxiliary/novel source separation passed; all eight identity sets and the auxiliary preparation are bound to the corrected immutable design lock 39426a3b2ddea74aaa8c1d39737cd9e5fb9c870c21745f5527e4e97b58d14e2d. The active scientific release is 2897f4fe4c1fb1857432a0e92a7391dde68307f5. Fresh v3 parity/caches, loss/paired-training evidence and three complete pilots remain Week 4 work. Recheck runtime seals before every job. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-3-v3-readiness.md Revalidation on 2026-10-08: Two previously registered local historical artifact roots are now unavailable, so their current test-seal status cannot be verified. The available local root and inspected SCC roots/releases contained no opening records; this bounded observation does not resolve the missing roots. The protocol file, immutable design lock and manifest-set hashes still match. Fresh v3 caches and pilots are blocked until the historical roots are recovered or an auditable, result-blind resolution establishes their provenance and seal status. No licensed-data extraction or pilot job was submitted. Synthetic-only L40S learnable-fixture job 7968648 was submitted separately without licensed-data access; its result is pending. The September 29 evidence above is preserved as a dated observation.",
      "completed_at": null
    }
  },
  {
    "table": "tasks",
    "id": "w04-task-02",
    "before": {
      "id": "w04-task-02",
      "week_id": "week-04",
      "position": 2,
      "title": "Verify losses and paired training",
      "details": "Check independent labeled forward/backward fixtures, the physical 8 × 4 sampler and shared initialization. Run the constructed 32-row learnable fixture for 1,000 updates per arm; require finite training and 100% self-excluded same-label retrieval.",
      "expected_output": "Verified three-arm numerical behavior and paired initialization/batch hashes.",
      "required": true,
      "estimate_minutes": 180,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 3,
      "project_id": "pose-embed"
    },
    "values": {
      "state": "in_progress",
      "completion_note": "In progress on 2026-10-08: Baseline numerical checks passed 45 tests with one skipped optional source oracle. Additional independent loss fixtures and paired-training verification are being completed. Synthetic-only L40S learnable-fixture job 7968648 was submitted separately without licensed-data access; its result is pending. No completed three-arm learnable-fixture or pairing result is claimed yet."
    }
  },
  {
    "table": "tasks",
    "id": "w04-task-03",
    "before": {
      "id": "w04-task-03",
      "week_id": "week-04",
      "position": 3,
      "title": "Generate fresh frozen features",
      "details": "Create v3-bound manifests with unchanged sample identities; run encoder parity and two fresh-process all-auxiliary extractions on the same GPU. Retain both repeats and development train/gallery/query caches with hashes.",
      "expected_output": "Fresh v3 parity/repeatability evidence and five immutable clean feature caches.",
      "required": true,
      "estimate_minutes": 120,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 3,
      "project_id": "pose-embed"
    },
    "values": {
      "state": "blocked",
      "completion_note": "Blocked on 2026-10-08 by two unavailable registered historical artifact roots and the resulting unresolved current test-seal audit. Scheduler validation of the cache launcher passed, but no extraction job was submitted and no fresh v3 parity or cache result is claimed."
    }
  },
  {
    "table": "tasks",
    "id": "w04-task-04",
    "before": {
      "id": "w04-task-04",
      "week_id": "week-04",
      "position": 4,
      "title": "Run three complete engineering pilots",
      "details": "Run Contrastive, Contextual and SupCon for 20 epochs at seed 7 and rate 3e-4. Preserve epoch-5/10/15/20 checkpoints and complete clean scores plus epoch-zero diagnostics, finite/collapse checks and measured timing/memory/bytes.",
      "expected_output": "Three valid full pilots, ineligible for learning-rate selection, with complete diagnostic evidence.",
      "required": true,
      "estimate_minutes": 90,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 3,
      "project_id": "pose-embed"
    },
    "values": {
      "state": "blocked",
      "completion_note": "Blocked on 2026-10-08 pending a complete historical-root seal audit, verified loss/paired-training fixtures and fresh v3 parity/caches. No pilot was submitted; no pilot checkpoint, score or runtime result is claimed."
    }
  },
  {
    "table": "gates",
    "id": "w04-gate-01",
    "before": {
      "id": "w04-gate-01",
      "week_id": "week-04",
      "position": 1,
      "criterion": "The complete v3 design and cache-affecting release are frozen; source identities are preserved and historical seal audits are resolved.",
      "required": true,
      "state": "met",
      "evidence": "Satisfied by the verified Week 3 handoff on 2026-09-29, not a second freeze: SCC job 7790916 completed with failed=0 and exit_status=0. Explicit v3 validators, registered historical-root seals and auxiliary/novel source separation passed; all eight identity sets and the auxiliary preparation are bound to the corrected immutable design lock 39426a3b2ddea74aaa8c1d39737cd9e5fb9c870c21745f5527e4e97b58d14e2d. The active scientific release is 2897f4fe4c1fb1857432a0e92a7391dde68307f5. Fresh v3 parity/caches, loss/paired-training evidence and three complete pilots remain Week 4 work. Recheck runtime seals before every job. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-3-v3-readiness.md",
      "waiver_reason": "",
      "decided_at": "2026-09-29T22:28:17.544258+00:00",
      "version": 4,
      "project_id": "pose-embed"
    },
    "values": {
      "state": "pending",
      "evidence": "Satisfied by the verified Week 3 handoff on 2026-09-29, not a second freeze: SCC job 7790916 completed with failed=0 and exit_status=0. Explicit v3 validators, registered historical-root seals and auxiliary/novel source separation passed; all eight identity sets and the auxiliary preparation are bound to the corrected immutable design lock 39426a3b2ddea74aaa8c1d39737cd9e5fb9c870c21745f5527e4e97b58d14e2d. The active scientific release is 2897f4fe4c1fb1857432a0e92a7391dde68307f5. Fresh v3 parity/caches, loss/paired-training evidence and three complete pilots remain Week 4 work. Recheck runtime seals before every job. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-3-v3-readiness.md Revalidation on 2026-10-08: Two previously registered local historical artifact roots are now unavailable, so their current test-seal status cannot be verified. The available local root and inspected SCC roots/releases contained no opening records; this bounded observation does not resolve the missing roots. The protocol file, immutable design lock and manifest-set hashes still match. Fresh v3 caches and pilots are blocked until the historical roots are recovered or an auditable, result-blind resolution establishes their provenance and seal status. No licensed-data extraction or pilot job was submitted. Synthetic-only L40S learnable-fixture job 7968648 was submitted separately without licensed-data access; its result is pending. The September 29 evidence above is preserved as a dated observation.",
      "decided_at": null
    }
  },
  {
    "table": "weeks",
    "id": "week-04",
    "before": {
      "id": "week-04",
      "project_id": "pose-embed",
      "number": 4,
      "start_date": "2026-10-05",
      "end_date": "2026-10-11",
      "phase": "Implementation and engineering",
      "title": "Verified recipes and full pilots",
      "objective": "Verify the three fixed recipes and the frozen-head path, then complete three full 20-epoch pilots under the immutable v3 design.",
      "deliverable": "Loss fixtures, paired initialization/batch evidence, fresh parity and clean caches, and three complete pilot records with timing and diagnostics.",
      "risks": [
        "The v3 protocol, shared seal checks and all cache-affecting code must be frozen before fresh extraction.",
        "A mathematical, nonfinite or collapse failure blocks selection; pilot accuracy cannot justify tuning recipes or duration."
      ],
      "advisor_prompt": "Do the mathematics, immutable inputs and complete pilot records demonstrate a valid fixed-budget comparison?",
      "reflection": "",
      "planned_minutes": 480,
      "actual_minutes": 0,
      "state": "planned",
      "closed_at": null,
      "version": 3
    },
    "values": {
      "state": "blocked",
      "reflection": "Done: On 2026-10-08, read-only preflight checks found unchanged protocol, design-lock and manifest-set hashes and no opening records in the accessible inspected roots/releases. At 18:50:52 UTC, usable SCC space was 1,025.40 decimal GB, above the bounded Week 4 requirement; capacity is a dated observation, not an allocation commitment. The cache launcher passed scheduler validation only; no extraction or pilot job was submitted. Baseline numerical checks passed 45 tests with one skipped optional source oracle. Synthetic-only L40S learnable-fixture job 7968648 was submitted separately without licensed-data access; its result is pending. Next: Locate or recover the two unavailable registered historical roots and resolve the complete seal audit, finish independent loss and paired-training fixtures, then repeat preflight before fresh v3 caches and the three full pilots. Open issues: The missing roots block fresh extraction and pilots. No fresh v3 cache or pilot result is verified. Actual researcher time remains unreported; no hours were invented and Week 4 remains open."
    }
  }
]
$edits$::jsonb;
  edit jsonb;
  current_row jsonb;
  expected_row jsonb;
  assignments text;
  changed_rows integer;
  expected_version integer;
  week_closed boolean;
begin
  if not exists (select 1 from public.projects where id = 'pose-embed') then
    raise notice 'pose-embed is not seeded; import research-plan.v3.json';
    return;
  end if;
  select state = 'closed' into week_closed from public.weeks
    where id = 'week-04' and project_id = 'pose-embed' for update;
  if week_closed is null then
    raise exception using errcode = '40001', message = 'week-04 is missing';
  end if;
  if not exists (select 1 from public.weeks where id = 'week-03' and project_id = 'pose-embed' and state = 'closed') then
    raise exception using errcode = '40001', message = 'Week 3 must be closed before this preflight update';
  end if;
  for edit in select value from jsonb_array_elements(edits)
  loop
    if not (
      (edit->>'table' = 'tasks' and edit->>'id' in ('w04-task-01', 'w04-task-02', 'w04-task-03', 'w04-task-04'))
      or (edit->>'table' = 'gates' and edit->>'id' = 'w04-gate-01')
      or (edit->>'table' = 'weeks' and edit->>'id' = 'week-04')
    ) or edit->'values' ? 'version' then
      raise exception 'Unexpected Week 4 preflight scope';
    end if;
    execute format('select to_jsonb(t) from public.%I t where id = $1 and project_id = ''pose-embed'' for update', edit->>'table')
      into current_row using edit->>'id';
    expected_version := (edit->'before'->>'version')::integer;
    expected_row := edit->'before' || edit->'values'
      || jsonb_build_object('version', expected_version + 1);
    if current_row @> expected_row then continue; end if;
    if week_closed or current_row is null or not (current_row @> (edit->'before')) then
      raise exception using errcode = '40001',
        message = edit->>'id' || ' changed or Week 4 is closed; refusing to overwrite progress';
    end if;
    select string_agg(format('%I = v.%I', key, key), ', ' order by key)
      into assignments from jsonb_object_keys(edit->'values') key;
    execute format('update public.%I t set %s from jsonb_populate_record(null::public.%I, $1) v where t.id = $2 and t.project_id = ''pose-embed'' and t.version = $3 returning to_jsonb(t)',
      edit->>'table', assignments, edit->>'table')
      into current_row using edit->'values', edit->>'id', expected_version;
    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 or not (current_row @> expected_row) then
      raise exception using errcode = '40001',
        message = edit->>'id' || ' could not be updated';
    end if;
  end loop;
end
$migration$;
