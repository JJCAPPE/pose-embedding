-- Record the authorized review and continued allocation hold; no scientific gate changes.
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
      "version": 38,
      "state": "active",
      "closed_at": null
    },
    "values": {
      "reflection": "October 19 checkpoint: Week 5 remains incomplete. Execution-r2 release f101f0e9d9bd64275d2088deab1b0bdcfcc53620 retains accepted installation, rehearsal 8044010, preparation 8045152 and supplementary checks 8048540. Tasks 01 and 03 retain accepted execution-r1 history, which does not admit execution-r2. Job 8135335 failed October 15 at 1:54:30 PM EDT after five scheduler seconds; the October 19 observation verified Missing/ambiguous ELF build ID before either resolver child ran. After inconclusive 8104416 and failed 8135335, two consecutive allocated attempts have neither narrowed nor unblocked geometry. Stop further diagnostic jobs/tool-building for this blocker. The researcher authorized the focused runtime review and explicitly held new allocations. The completed review distinguishes an interpreter provenance representation failure from the unresolved numerical mismatch; no compatible common runtime is proven. Next: BU Research Computing Services consultation is recommended to resolve missing interpreter-note and vendor-runtime evidence before choosing another comparison. No contact was made. The two-attempt count remains two; diagnostic jobs and tool-building remain held. Preserve exact equality/identity checks and the original panel/fallback. Fresh scientific regeneration, full admission replay and measured CPU/GPU capacity remain incomplete. Tasks 02 and 04 are blocked; all scientific gates remain pending. October 18 passed without admission; re-estimate the remaining schedule before selection. No active job was observed October 19 and no new job was submitted. Selection, final training and novel opening remain closed. Actual researcher time remains unreported."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-02",
      "version": 35,
      "state": "blocked"
    },
    "values": {
      "completion_note": "BLOCKED, October 19: execution-r2 setup receipts remain accepted, but geometry and a compatible runtime remain unproven. Job 8135335 failed October 15 at 17:54:30 UTC after five scheduler seconds with Missing/ambiguous ELF build ID, before resolver children. Together with inconclusive 8104416, this reaches two consecutive allocated attempts without narrowing or unblocking the blocker. The authorized focused runtime review is complete: the interpreter-note failure is operational, and no single runtime is proven for both original geometry and locked initialization. New allocations and diagnostic tool-building remain held; the stopping count stays two. Recommend BU RCS compatibility consultation using retained evidence before choosing another comparison; no contact was made. Fresh parity/five caches, three paired full pilots, nine corruption paths, projections/results and independent replay remain required; predecessor artifacts cannot substitute. Terminal observation: study-v3/operations/week5-status/20261019T153819Z/observation.json; SHA-256 04f51f12fed2eea628c45e6cccb4f837f45bf039b0be02a28655cbaedcc7342b."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-04",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-04",
      "version": 18,
      "state": "blocked"
    },
    "values": {
      "completion_note": "BLOCKED, October 19: the October 18 go/no-go did not pass. The predecessor measured-profile no-go remains preserved; execution-r2 capacity is unproven while geometry, scientific regeneration and full admission replay remain incomplete. Include every diagnostic allocation, hashing/replay, independent recertification, memory/storage, CPU/GPU windows, queue/setup and at least 25% slack in a renewed schedule. Retain the 200 GiB reserve plus 1.25 times remaining peak bytes, November 29 final-lock deadline, December 6 compute deadline and protected December 7–18 delivery time. The researcher-authorized runtime review is complete without new allocations or a capacity result. BU RCS compatibility consultation is recommended before another comparison; allocations remain held and the diagnostic stopping count stays two. No selection authorization or closure is granted; actual time remains unreported."
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-gate-03",
      "version": 19,
      "state": "pending"
    },
    "values": {
      "evidence": "UNRESOLVED, October 19: no measured successor capacity pass or selection authorization exists. Accepted execution-r2 setup does not replace scientific regeneration and full admission validation. Resolver job 8135335 failed before comparison; following inconclusive 8104416, the stopping count remains two. The researcher authorized a focused runtime review and kept new allocations on hold. That review is complete but proves no common runtime or scientific gate. Recommend BU RCS compatibility consultation to resolve missing interpreter-note and vendor-runtime evidence before choosing another comparison. No contact was made; diagnostic jobs/tool-building remain held and exact equality/identity checks remain required. October 18 passed without admission. The renewed schema-2 CPU/GPU schedule must include all remaining scientific work, validation/recertification, retained/remaining storage, researcher availability, queue/setup and at least 25% slack. Predecessor no-go and every failed attempt remain retained. Terminal observation: study-v3/operations/week5-status/20261019T153819Z/observation.json; SHA-256 04f51f12fed2eea628c45e6cccb4f837f45bf039b0be02a28655cbaedcc7342b. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/codex/pose-week5-execution/docs/protocol/week-5-execution.md"
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
