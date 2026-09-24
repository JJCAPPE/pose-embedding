-- Record the result-blind NTU input-contract amendment after its protocol hash
-- is fixed. The affected weeks stay open and all unrelated decisions remain.
-- Seeded deployments use this migration; fresh databases use the canonical plan.
do $migration$
declare
  edits constant jsonb := $edits$
[
  {
    "table": "weeks",
    "id": "week-01",
    "week_id": "week-01",
    "version": 4,
    "from_state": "blocked",
    "to_state": "blocked",
    "values": {
      "reflection": "Week 1 established a documented, hash-bound protocol, verified the licensed HRNet aggregate, official one-shot split, and MotionBERT checkpoint, and confirmed physical batch 32 on an SCC A40. The GPU-host inventory accounts for 113,945 usable annotations plus 535 official missing-skeleton exclusions. The researcher adopted the result-blind aggregate-aware input contract on 2026-09-24. The BU governance determination and researcher-supplied actual minutes remain pending; the novel test remains sealed and the weekly record remains open."
    }
  },
  {
    "table": "tasks",
    "id": "w01-task-01",
    "week_id": "week-01",
    "version": 4,
    "from_state": "done",
    "to_state": "done",
    "values": {
      "completion_note": "All binding scientific choices were confirmed, including mandatory final training on all 100 auxiliary actions. Independent research governance is recorded in docs/protocol/independent-research.md. The result-blind NTU input-contract amendment was adopted on 2026-09-24. Current protocol SHA-256: c8b08b6867bc14dc0a947ebfa94e40b16ea3f0dae38dfa6d86187afecb4fd45f."
    }
  },
  {
    "table": "tasks",
    "id": "w01-task-02",
    "week_id": "week-01",
    "version": 6,
    "from_state": "done",
    "to_state": "done",
    "values": {
      "completion_note": "Verified 2026-09-24: dataset access remains active, the complete usable HRNet aggregate, official missing-skeleton list, one-shot definition, and MotionBERT checkpoint are readable and checksummed on the GPU host. The aggregate contains 113,945 usable annotations and all 20 official exemplars; the official 535-item missing-skeleton list accounts for the remaining nominal captures. The result-blind aggregate-aware input contract is adopted in docs/protocol/input-contract-amendment.v1.md, and w01-gate-02 is met. The novel test remains sealed."
    }
  },
  {
    "table": "tasks",
    "id": "w01-task-05",
    "week_id": "week-01",
    "version": 4,
    "from_state": "blocked",
    "to_state": "blocked",
    "values": {
      "completion_note": "Verified input acquisition, remote setup, and the adopted result-blind input contract are recorded in the Week 1 evidence. Final closeout remains blocked until researcher-supplied actual minutes and the BU governance determination are recorded. No hours or week closure are inferred."
    }
  },
  {
    "table": "gates",
    "id": "w01-gate-01",
    "week_id": "week-01",
    "version": 3,
    "from_state": "met",
    "to_state": "met",
    "values": {
      "evidence": "Independent research governance is recorded in docs/protocol/independent-research.md. The result-blind NTU input-contract amendment is recorded in docs/protocol/input-contract-amendment.v1.md. Current protocol SHA-256: c8b08b6867bc14dc0a947ebfa94e40b16ea3f0dae38dfa6d86187afecb4fd45f."
    }
  },
  {
    "table": "gates",
    "id": "w01-gate-02",
    "week_id": "week-01",
    "version": 5,
    "from_state": "pending",
    "to_state": "met",
    "values": {
      "state": "met",
      "evidence": "Verified 2026-09-24: the local and GPU-host inputs account for 113,945 usable HRNet annotations plus 535 official missing-skeleton exclusions, totaling 114,480 nominal captures. The hash-pinned aggregate and official missing-skeleton list passed aggregate-aware physical-source verification. The researcher adopted the result-blind contract in https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/input-contract-amendment.v1.md; current protocol SHA-256: c8b08b6867bc14dc0a947ebfa94e40b16ea3f0dae38dfa6d86187afecb4fd45f. GPU-host evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-1-remote-setup.md. The novel test remains sealed.",
      "decided_at": "2026-09-24T16:25:10+00:00"
    }
  },
  {
    "table": "gates",
    "id": "w02-gate-01",
    "week_id": "week-02",
    "version": 3,
    "from_state": "pending",
    "to_state": "met",
    "values": {
      "state": "met",
      "evidence": "Seven immutable release manifests have frozen counts and SHA-256 checksums for the verified 113,945-sample usable aggregate; the 535 official missing-skeleton exclusions account for all 114,480 nominal captures. Aggregate-aware physical-source verification and independent byte-identical regeneration passed. The researcher adopted the result-blind contract in https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/input-contract-amendment.v1.md; current protocol SHA-256: c8b08b6867bc14dc0a947ebfa94e40b16ea3f0dae38dfa6d86187afecb4fd45f. Manifest audit: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/ntu-manifest-audit.v2.md.",
      "decided_at": "2026-09-24T16:25:10+00:00"
    }
  }
]
$edits$::jsonb;
  edit jsonb;
  parent_id text;
  current_row jsonb;
  assignments text;
  changed_rows integer;
begin
  if not exists (select 1 from public.projects where id = 'pose-embed') then
    raise notice 'pose-embed is not seeded; the canonical plan supplies the adopted contract';
    return;
  end if;

  for parent_id in select distinct value->>'week_id' from jsonb_array_elements(edits)
  loop
    select to_jsonb(w) into current_row from public.weeks w
     where id = parent_id and project_id = 'pose-embed' for update;
    if current_row is null then
      raise exception using errcode = '40001', message = parent_id || ' is missing';
    end if;
    if current_row->>'state' = 'closed' or current_row->>'closed_at' is not null then
      raise exception using errcode = '40001',
        message = parent_id || ' is closed; an audited reopen is required';
    end if;
  end loop;

  for edit in select value from jsonb_array_elements(edits)
  loop
    -- Identifiers come only from this fixed migration payload.
    if edit->>'table' not in ('weeks', 'tasks', 'gates') then
      raise exception 'Unexpected migration table';
    end if;
    execute format('select to_jsonb(t) from public.%I t where id = $1 and project_id = $2 for update', edit->>'table')
      into current_row using edit->>'id', 'pose-embed';
    if current_row is null or
       (edit->>'table' <> 'weeks' and current_row->>'week_id' <> edit->>'week_id') then
      raise exception using errcode = '40001', message = edit->>'id' || ' is missing or moved';
    end if;
    if (current_row->>'version')::integer = (edit->>'version')::integer + 1
       and current_row->>'state' = edit->>'to_state'
       and current_row @> (edit->'values') then
      continue;
    end if;
    if (current_row->>'version')::integer <> (edit->>'version')::integer
       or current_row->>'state' <> edit->>'from_state' then
      raise exception using errcode = '40001',
        message = edit->>'id' || ' changed; refusing to overwrite live progress';
    end if;
    select string_agg(format('%I = v.%I', key, key), ', ' order by key)
      into assignments from jsonb_object_keys(edit->'values') key;
    execute format('update public.%I t set %s from jsonb_populate_record(null::public.%I, $1) v where t.id = $2 and t.project_id = $3 and t.version = $4',
      edit->>'table', assignments, edit->>'table')
      using edit->'values', edit->>'id', 'pose-embed', (edit->>'version')::integer;
    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 then
      raise exception using errcode = '40001', message = edit->>'id' || ' could not be updated';
    end if;
  end loop;
end
$migration$;
