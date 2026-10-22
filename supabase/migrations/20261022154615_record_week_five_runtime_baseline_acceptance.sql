-- Record independently accepted baseline evidence; states and scientific gates stay unchanged.
do $migration$
declare
  edits constant jsonb := $edits$
[
  {
    "table": "weeks",
    "id": "week-05",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "week-05",
      "version": 40,
      "state": "active",
      "closed_at": null
    },
    "values": {
      "reflection": "October 22: independent review accepted job 8189505's prospective CPU runtime, three fresh initializations per seed 7/17/29, and two-process geometry with all 43 panel IDs and 430 tensor hashes per repeat. Original identities, training-only fallback, source/locks and scientific settings remain fixed; allocated replay, accounting, resources and seals passed. Week 5 remains incomplete. Next: pass fresh identity/authorization/seal/resource/duplicate-job checks, verify the source-bound GPU diagnostic under the accepted baseline, then generate and independently validate fresh parity/five caches. Three complete paired pilots, nine corruption paths/projections/results, full admission replay and measured schema-2 capacity remain required. Tasks 01/03 retain their historical evidence; the two prior non-progress diagnostics remain recorded and the libm investigation stays stopped. October 18 admission was missed; later deadlines are unchanged. Selection, final training and novel opening remain closed. Actual researcher time is unreported."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-02",
      "version": 37,
      "state": "in_progress"
    },
    "values": {
      "completion_note": "IN PROGRESS, October 22: independent acceptance of job 8189505 establishes the prospective CPU runtime, three exact initialization repeats per seed and the two-process 43-ID/430-tensor geometry prerequisite under ADR0008. Accounting, resources, seals, original identities/fallback and unchanged f101f0e r2 bindings passed review. Next: fresh preflights and the source-bound GPU diagnostic under this baseline, then fresh parity/five caches and independent validation. Three complete paired pilots, all nine development corruption paths/projections/results and independent replay remain incomplete. Historical diagnostic stop count stays two; no libm investigation is resumed."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-04",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-04",
      "version": 20,
      "state": "blocked"
    },
    "values": {
      "completion_note": "BLOCKED, October 22: accepted baseline/geometry job 8189505 took 219 scheduler seconds and passed its geometry-only 1 GiB storage increment; this does not establish campaign capacity. October 18 admission was missed. Measure remaining scientific work, full admission and independent recertification, retained/remaining storage, CPU/GPU windows and researcher work with queue/setup and at least 25% slack. Preserve the 200 GiB reserve plus 1.25 times remaining peak bytes, November 29 final locks, December 6 compute and protected December 7–18 delivery. Selection and closure remain gated; actual time remains unreported."
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-gate-03",
      "version": 21,
      "state": "pending"
    },
    "values": {
      "evidence": "UNRESOLVED, October 22: job 8189505's CPU runtime, initialization and geometry prerequisite passed independent acceptance; fresh GPU/scientific inventory, full admission and measured schema-2 capacity remain incomplete. No capacity pass or selection authorization is granted. Retain original panel/fallback, all scientific settings and the two historical non-progress diagnostic attempts. Renew CPU/GPU/storage/researcher availability forecasts including validation, recertification, queue/setup and at least 25% slack. October 18 was missed; later deadlines remain fixed. Acceptance SHA-256: 16106ecafe347dc8d31795e14a88b267e716f82e494311b4753462cfcd88f8aa. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/codex/pose-week5-execution/docs/protocol/week-5-execution.md#october-22-runtime-initialization-and-geometry-accepted"
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
  parent_id text;
begin
  if not exists (select 1 from public.projects where id = 'pose-embed') then
    raise notice 'pose-embed is not seeded; import research-plan.v3.json';
    return;
  end if;
  if not exists (select 1 from public.weeks where id = 'week-04' and project_id = 'pose-embed' and state = 'closed') then
    raise exception using errcode = '40001', message = 'Week 4 must be closed before starting Week 5';
  end if;
  for parent_id in
    select distinct value->>'week_id' from jsonb_array_elements(edits)
    where value->>'week_id' is not null order by 1
  loop
    if parent_id < 'week-05' then raise exception 'Historical week change forbidden'; end if;
    select to_jsonb(w) into current_row from public.weeks w
      where id = parent_id and project_id = 'pose-embed' for update;
    if current_row is null or current_row->>'state' = 'closed'
       or current_row->>'closed_at' is not null then
      raise exception using errcode = '40001',
        message = parent_id || ' is missing or closed; an audited reopen is required';
    end if;
  end loop;
  for edit in select value from jsonb_array_elements(edits)
  loop
    if edit->>'table' not in ('weeks', 'tasks', 'gates')
       or edit->>'operation' <> 'update' or edit->'values' ? 'version' then
      raise exception 'Unexpected amendment scope';
    end if;
    execute format('select to_jsonb(t) from public.%I t where id = $1 and project_id = ''pose-embed'' for update', edit->>'table')
      into current_row using edit->>'id';
    expected_version := (edit->'before'->>'version')::integer;
    expected_row := edit->'before' || edit->'values'
      || jsonb_build_object('version', expected_version + 1);
    if current_row @> expected_row then continue; end if;
    if current_row is null or not (current_row @> (edit->'before')) then
      raise exception using errcode = '40001',
        message = edit->>'id' || ' changed; refusing to overwrite live progress';
    end if;
    select string_agg(format('%I = v.%I', key, key), ', ' order by key)
      into assignments from jsonb_object_keys(edit->'values') key;
    execute format('update public.%I t set %s from jsonb_populate_record(null::public.%I, $1) v where t.id = $2 and t.project_id = ''pose-embed'' and t.version = $3 returning to_jsonb(t)',
      edit->>'table', assignments, edit->>'table')
      into current_row using edit->'values', edit->>'id', expected_version;
    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 or not (current_row @> expected_row) then
      raise exception using errcode = '40001', message = edit->>'id' || ' could not be updated';
    end if;
  end loop;
end
$migration$;
