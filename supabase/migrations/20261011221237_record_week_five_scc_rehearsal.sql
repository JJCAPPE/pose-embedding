-- Record the verified SCC software rehearsal; no scientific gate passes.
-- Full row/version checks preserve concurrent progress and closed-week history.
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
      "actual_minutes": 0,
      "advisor_prompt": "Do all October 18 validity, seal, storage, runtime and researcher-availability criteria pass without changing the declared study?",
      "closed_at": null,
      "deliverable": "A reviewed completion release, full fixture-to-report rehearsal, fresh bound admission evidence, nine verified development conditions and immutable go/no-go report.",
      "end_date": "2026-10-18",
      "id": "week-05",
      "number": 5,
      "objective": "Complete one successor release, revalidate its caches/pilots and meet every scientific/resource prerequisite before selection.",
      "phase": "Preselection go/no-go",
      "planned_minutes": 300,
      "project_id": "pose-embed",
      "reflection": "Done: Reviewed and corrected successor authorization, opening recovery, subset provenance and reporting boundaries; added monitored SCC launchers and independent validation commands, with focused regression checks. Captured researcher availability: up to 5 hours weekly normally, 10 if necessary, with limited Thanksgiving time. Next: Complete the full command-to-report rehearsal and release verification, then freeze the successor and regenerate its required admission evidence. Open issues: All four Week 5 tasks and all three gates remain unfinished. Budget no guaranteed Thanksgiving hours; ordinary queued SCC access is not a reservation. A dated allocation calendar and measured pipeline/resource forecast are still required. Actual researcher time remains unreported. No selection, final training or novel-test opening is authorized.",
      "reopen_reason": "",
      "risks": [
        "Frozen final-training/extraction guards require a new release and fresh evidence; preserve original locks and Week 4 closure.",
        "Inherited five-hour tracker estimates are not a measured forecast: re-estimate implementation, revalidation, corruptions, reporting and resource planning before October 18.",
        "Current quota and remaining peak bytes must pass; dated capacity readings and prior GPU access are not reservations."
      ],
      "start_date": "2026-10-12",
      "state": "active",
      "title": "Complete the execution path and preselection evidence",
      "version": 5
    },
    "values": {
      "reflection": "Done: Committed release 731938a, verified its exact SCC source, locked dependencies and upstream, and passed CPU rehearsal job 8028010: 41 checks, no failures or skips, 414 seconds scheduler wall time. The real dataset seal remained intact. Next: Prepare and verify successor manifests and metadata-dependence tables, then regenerate caches/pilots and complete geometry, corruption and capacity evidence. Open issues: Task 03 remains in progress until prepared-source metadata tables are verified; all four tasks and three gates remain unfinished. The dated allocation calendar and measured pipeline forecast are still required. Availability remains up to 5 hours weekly normally, 10 if necessary; budget no guaranteed Thanksgiving hours. Actual researcher time remains unreported. No selection, final training or novel-test opening is authorized."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-03",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "completed_at": null,
      "completion_note": "Implementation review and focused regressions are in progress; full fixture-to-report rehearsal, clean successor release and independent admission evidence remain required. See the Week 5 execution record. This task is not complete.",
      "details": "Do this dependency first: finish selection/final authorization, final training, novel roles, corrupted-development evaluation and actual v3 report dispatch in one completion release. Preserve old locks at the canonical root; use study-v3/revisions/execution-r1/ with reviewed scientific-field equality and new provenance. Rehearse actual commands on fixtures: 180 cells, ordered subsets, bootstrap/report identity, tamper/revision rejection, pre-loader atomic opening, crash/concurrency recovery and cross-version training denial. Add the metadata-dependence table and interpretation template. Opening fixtures use only a temporary synthetic registry/artifact root, never the real ledger; verify real opening records remain absent/unchanged.",
      "estimate_minutes": 60,
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/codex/pose-week5-execution/docs/protocol/week-5-execution.md",
      "expected_output": "Reviewed successor release and regeneration matrix; complete fixture-to-v3-report receipts and fixed analysis/interpretation template before real revalidation.",
      "id": "w05-task-03",
      "position": 3,
      "project_id": "pose-embed",
      "required": true,
      "state": "in_progress",
      "title": "Complete and rehearse the execution/report path",
      "version": 6,
      "week_id": "week-05"
    },
    "values": {
      "completion_note": "Release 731938a was synchronized and verified on SCC. CPU rehearsal job 8028010 passed 41 checks with no failures or skips (390.055 seconds test time; 414 seconds scheduler wall time), with the real seal intact before and after. Prepared successor manifests and their actual metadata-dependence tables still require verification, so this task remains in progress. See the Week 5 execution record; no scientific admission is implied."
    }
  }
]
$edits$::jsonb;

  edit jsonb;
  current_row jsonb;
  expected_row jsonb;
  assignments text;
  columns_sql text;
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
    if edit->>'table' not in ('weeks', 'tasks', 'gates', 'sources', 'week_sources')
       or edit->'values' ? 'version' then
      raise exception 'Unexpected amendment scope';
    end if;
    if edit->>'table' = 'week_sources' then
      select to_jsonb(t) into current_row from public.week_sources t
        where project_id = 'pose-embed' and week_id = edit->>'week_id'
          and source_id = edit->>'source_id' for update;
    else
      execute format('select to_jsonb(t) from public.%I t where id = $1 and project_id = ''pose-embed'' for update', edit->>'table')
        into current_row using edit->>'id';
    end if;
    if edit->>'operation' = 'insert' then
      expected_row := edit->'values' || jsonb_build_object('version', 1);
      if current_row is not null then
        if current_row @> expected_row then continue; end if;
        raise exception using errcode = '40001', message = edit->>'id' || ' already exists with different content';
      end if;
      select string_agg(format('%I', key), ', ' order by key),
             string_agg(format('v.%I', key), ', ' order by key)
        into columns_sql, assignments from jsonb_object_keys(expected_row) key;
      execute format('insert into public.%I (%s) select %s from jsonb_populate_record(null::public.%I, $1) v',
        edit->>'table', columns_sql, assignments, edit->>'table') using expected_row;
      continue;
    end if;
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
