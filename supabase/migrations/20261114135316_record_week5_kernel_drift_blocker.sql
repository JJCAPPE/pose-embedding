-- Record the independently reviewed kernel-drift failure and researcher-action blocker.
do $migration$
declare
  edits constant jsonb := $edits$[
  {
    "table": "weeks",
    "id": "week-05",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "week-05",
      "version": 67,
      "state": "active",
      "closed_at": null
    },
    "values": {
      "reflection": "November 14: Independent review found that replacement CPU job 8616892 stopped after 13 scheduler seconds before the admission controller ran. CUBLAS_WORKSPACE_CONFIG is restored to the accepted :4096:8 value. The sole remaining startup-profile difference is kernel 4.18.0-553.184.2.el8_10.x86_64 instead of the accepted 4.18.0-553.182.1.el8_10.x86_64; every other recorded profile field matches. No measurement operation or admission timing was produced. Existing amendments do not authorize this kernel change. Continuation awaits an explicit result-blind kernel-only researcher decision, with bounded fresh CPU qualification proposed under ADR0012. Retain required GPU qualification, repeating only the existing bounded parity check if the changed runtime or path requires it. Historical accepted evidence retains its provenance; no new whole-history adoption campaign or second full recertification is proposed. No replacement job was submitted; the completion watcher is disarmed and legacy automation remains paused. Week 5 stays open; selection, final training and novel opening remain closed."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-02",
      "version": 63,
      "state": "in_progress"
    },
    "values": {
      "completion_note": "IN PROGRESS, November 14: CPU 8561360 and bounded GPU parity 8580442 remain accepted under their recorded profiles. Replacement measurement job 8616892 restored the accepted environment setting but failed the startup check because the allocated kernel changed from 553.182.1 to 553.184.2. All other recorded profile fields match. The admission controller did not run; no operation or timing was produced. The new kernel is not authorized or qualified. A result-blind kernel-only amendment and bounded fresh CPU qualification are proposed, pending a researcher decision. Retain required GPU qualification, repeating only the existing bounded parity check if the changed runtime or path requires it. Preserve ADR0012 historical evidence and minimum validation scope.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-14-changed-kernel-blocks-the-replacement-measurement"
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-04",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-04",
      "version": 38,
      "state": "blocked"
    },
    "values": {
      "completion_note": "BLOCKED ON RUNTIME AUTHORIZATION AND MEASURED CAPACITY, November 14: Job 8616892 stopped before the admission controller because the kernel changed from the accepted 553.182.1 to 553.184.2. No admission timing was produced. Continuation requires a researcher decision on a result-blind kernel-only amendment, then successful bounded CPU qualification and coverage of the required GPU qualification before the corrected-prefix measurement. Repeat only the existing bounded GPU parity check if the changed runtime or path requires it. Complete CPU/GPU/storage/calendar/researcher capacity and actual admission remain pending. The 873.911-hour estimate describes only the old call graph. Preserve the 200 GiB reserve, 25% margin and fixed deadlines.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-14-changed-kernel-blocks-the-replacement-measurement"
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-gate-03",
      "version": 44,
      "state": "pending"
    },
    "values": {
      "evidence": "UNRESOLVED, November 14: Independent review of job 8616892 accepts the startup-failure diagnosis only. The accepted environment setting is restored; the sole remaining profile difference is kernel 553.184.2 versus accepted 553.182.1. No measurement operation or timing exists. Existing amendments do not authorize the new kernel, so continuation awaits a result-blind researcher decision and bounded qualification. Corrected-prefix timing, complete feasible capacity and admission remain pending. No replacement job, selection runs, final training, novel opening or Week 5 closure are authorized. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-14-changed-kernel-blocks-the-replacement-measurement"
    }
  }
]$edits$::jsonb;

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
