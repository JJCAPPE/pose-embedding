-- Record researcher-authorized kernel-only qualification; acceptance and later stages remain pending.
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
      "version": 68,
      "state": "active",
      "closed_at": null
    },
    "values": {
      "reflection": "November 14: The researcher approved result-blind ADR0013 to qualify kernel 4.18.0-553.184.2.el8_10.x86_64 as the only changed field in accepted CPU 8561360's complete profile. Fresh CPU qualification requires three initializations per seed 7/17/29 and two complete original 43-panel geometry processes, retaining all 430 comparisons, existing historical equality checks and numerical tolerances, followed by independent acceptance. Retain required GPU qualification; repeat the existing bounded 48-sample, 12-layer parity check only if the actual changed runtime or path needs fresh coverage. ADR0012 preserves historical accepted evidence and original provenance without a new adoption campaign or second full recertification. Qualification, corrected-prefix timing, full capacity and admission remain pending. Week 5 stays open; selection runs, final training and novel opening remain closed. No qualification result or capacity pass is claimed."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-02",
      "version": 64,
      "state": "in_progress"
    },
    "values": {
      "completion_note": "IN PROGRESS, November 14: Researcher-approved ADR0013 resolves the authorization blocker for the exact kernel-only 553.184.2 candidate derived from accepted CPU 8561360; every other profile field remains fixed. Fresh CPU initialization and original 43-panel geometry qualification, all 430 comparisons and independent acceptance remain pending. Retain required GPU qualification; repeat only bounded 48-sample, 12-layer parity if the changed runtime or path needs fresh coverage. Historical CPU/GPU evidence retains its original profile and provenance under ADR0012. No new qualification or admission result is accepted.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-14-kernel-only-qualification-authorized"
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-04",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-04",
      "version": 39,
      "state": "blocked"
    },
    "values": {
      "completion_note": "BLOCKED ON QUALIFICATION AND MEASURED CAPACITY, November 14: ADR0013 authorizes the exact 553.184.2 kernel-only candidate, without declaring it accepted. Fresh bounded CPU qualification and independent acceptance, plus coverage of required GPU qualification, precede the existing single corrected admission-prefix measurement. Complete CPU/GPU/storage/calendar/researcher capacity and genuine admission remain pending. The 873.911-hour estimate describes only the old call graph. Preserve the 200 GiB reserve, 25% margin and November 29/December 6/December 7-18 deadlines.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-14-kernel-only-qualification-authorized"
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-gate-03",
      "version": 45,
      "state": "pending"
    },
    "values": {
      "evidence": "UNRESOLVED, November 14: The researcher approved ADR0013 for kernel-only 553.184.2 qualification with every other accepted CPU 8561360 profile field unchanged. The amendment grants no runtime acceptance, measurement, capacity pass or scientific-stage authorization. Fresh CPU qualification and independent acceptance are pending; retain required GPU qualification and repeat bounded parity only if the changed runtime or path needs fresh coverage. ADR0012 continues to preserve historical evidence without a new adoption campaign or second full recertification. Corrected-prefix timing, full feasible capacity and admission remain pending. Selection runs, final training, novel opening and Week 5 closure remain unauthorized. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-14-kernel-only-qualification-authorized"
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
