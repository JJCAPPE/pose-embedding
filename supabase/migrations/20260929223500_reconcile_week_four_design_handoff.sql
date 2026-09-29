-- Reuse the verified Week 3 design-freeze evidence for its duplicate Week 4
-- prerequisite. Leave Week 4 planned, remaining work pending and time unchanged.
-- Version/content guards preserve concurrent progress and closed-week records.
do $migration$
declare
  edits constant jsonb := $edits$
[
  {
    "table": "tasks",
    "id": "w04-task-01",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Complete explicit v3 configuration/manifest validation, dataset-wide seal checks and auxiliary/novel source access separation. Register historical roots, preserve old artifacts, and freeze the complete design and cache-affecting code before extraction.",
      "estimate_minutes": 90,
      "evidence_url": null,
      "expected_output": "An immutable v3 design/pilot specification and passing version, provenance and seal checks.",
      "id": "w04-task-01",
      "position": 1,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Freeze and validate the v3 path",
      "version": 3,
      "week_id": "week-04"
    },
    "values": {
      "state": "done",
      "completion_note": "Satisfied by the verified Week 3 handoff on 2026-09-29, not a second freeze: SCC job 7790916 completed with failed=0 and exit_status=0. Explicit v3 validators, registered historical-root seals and auxiliary/novel source separation passed; all eight identity sets and the auxiliary preparation are bound to the corrected immutable design lock 39426a3b2ddea74aaa8c1d39737cd9e5fb9c870c21745f5527e4e97b58d14e2d. The active scientific release is 2897f4fe4c1fb1857432a0e92a7391dde68307f5. Fresh v3 parity/caches, loss/paired-training evidence and three complete pilots remain Week 4 work. Recheck runtime seals before every job. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-3-v3-readiness.md",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-3-v3-readiness.md",
      "completed_at": "2026-09-29T22:28:17.544258+00:00"
    }
  },
  {
    "table": "gates",
    "id": "w04-gate-01",
    "before": {
      "criterion": "The complete v3 design and cache-affecting release are frozen; source identities are preserved and historical seal audits are resolved.",
      "decided_at": null,
      "evidence": "",
      "id": "w04-gate-01",
      "position": 1,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 3,
      "waiver_reason": "",
      "week_id": "week-04"
    },
    "values": {
      "state": "met",
      "evidence": "Satisfied by the verified Week 3 handoff on 2026-09-29, not a second freeze: SCC job 7790916 completed with failed=0 and exit_status=0. Explicit v3 validators, registered historical-root seals and auxiliary/novel source separation passed; all eight identity sets and the auxiliary preparation are bound to the corrected immutable design lock 39426a3b2ddea74aaa8c1d39737cd9e5fb9c870c21745f5527e4e97b58d14e2d. The active scientific release is 2897f4fe4c1fb1857432a0e92a7391dde68307f5. Fresh v3 parity/caches, loss/paired-training evidence and three complete pilots remain Week 4 work. Recheck runtime seals before every job. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-3-v3-readiness.md",
      "decided_at": "2026-09-29T22:28:17.544258+00:00"
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
    raise exception using errcode = '40001', message = 'Week 3 must be closed before this handoff';
  end if;
  for edit in select value from jsonb_array_elements(edits)
  loop
    if not (
      (edit->>'table' = 'tasks' and edit->>'id' = 'w04-task-01')
      or (edit->>'table' = 'gates' and edit->>'id' = 'w04-gate-01')
    ) or edit->'values' ? 'version' then
      raise exception 'Unexpected Week 4 handoff scope';
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
        message = edit->>'id' || ' could not be completed';
    end if;
  end loop;
end
$migration$;
