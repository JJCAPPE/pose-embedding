-- Record two completed scheduled pilot runs and the third pilot start.
-- Independent three-pilot validation, the final gate and weekly closure remain pending.
-- Exact version/content guards preserve concurrent progress and researcher time.
do $migration$
declare
  edits constant jsonb := $edits$
[
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
      "state": "in_progress",
      "completion_note": "In progress on 2026-10-08: First fixed 20-epoch Contrastive engineering pilot job 7970697 started at 21:13:26 UTC and its startup fixture passed at 21:14:43 UTC. The pilot is running; its training/checkpoint/score results are not yet verified. Contextual and SupCon pilots remain pending. Completion requires all three full pilot records, the four prescribed checkpoint/score records per recipe, finite/collapse checks and paired real-data initialization/batch evidence; submission alone is not completion.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/codex/pose-week4-execution/docs/protocol/week-4-execution.md",
      "completed_at": null,
      "version": 6,
      "project_id": "pose-embed"
    },
    "values": {
      "completion_note": "Progress on 2026-10-08: Contrastive job 7970697 completed at 21:21:48 UTC and Contextual job 7970756 at 21:33:18 UTC; scheduler accounting reports failed=0 and exit_status=0 for both (502 and 525 seconds). Their run records each report 20 epochs, 47,520 updates, 21 diagnostics and the required epoch-0/5/10/15/20 records. Both report initial-state hash 035a3e5e57569c0ae765b797f705b3a9f70353a6832fcb757c7622ebfa9b3284 and batch-plan hash 67128877ad2ac134c5c218ddd6c366903faa6cbfca270036dc2979e30ec859f5. SupCon job 7970877 started at 21:36:25 UTC and its startup fixture passed at 21:37:10 UTC; training results remain unverified. Independent validation of all three complete pilots, including pairing, provenance and health checks, remains pending; the pilot task and final Week 4 gate remain open."
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
      "reflection": "Done: Seal revalidation, loss verification and synthetic paired-training fixtures are complete. All five fresh v3 caches passed independent CPU validation job 7969962, with fresh parity, exact repeatability and bounded extraction resource checks. Next: Verify completion and outputs for running Contrastive pilot 7970697, then complete and verify the Contextual and SupCon pilots under the fixed 20-epoch design. Open issues: The first Contrastive pilot started at 21:13:26 UTC and passed its startup fixture; training results are unverified. All three complete real-data pilot records and their pairing/health checks remain required; the final Week 4 gate is pending. Actual researcher time remains unreported and Week 4 remains open.",
      "planned_minutes": 480,
      "actual_minutes": 0,
      "state": "active",
      "closed_at": null,
      "version": 8
    },
    "values": {
      "reflection": "Done: Seal and loss checks, synthetic paired-training fixtures and independent validation of all five fresh v3 caches are complete. Contrastive job 7970697 and Contextual job 7970756 exited successfully; both run records report the fixed 20 epochs, 47,520 updates and required diagnostics/checkpoints, with matching initial-state and batch-plan hashes. Next: Verify completion of running SupCon job 7970877, then independently validate all three complete pilot records and their paired provenance/health checks. Open issues: SupCon started at 21:36:25 UTC and its startup fixture passed at 21:37:10 UTC; training results and independent validation of the three pilots remain pending. No final Week 4 gate or weekly closure is claimed; actual researcher time remains unreported."
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
    raise exception using errcode = '40001', message = 'Week 3 must be closed before this pilot-progress update';
  end if;
  for edit in select value from jsonb_array_elements(edits)
  loop
    if not (
      (edit->>'table' = 'tasks' and edit->>'id' = 'w04-task-04')
      or (edit->>'table' = 'weeks' and edit->>'id' = 'week-04')
    ) or edit->'values' ? 'version' then
      raise exception 'Unexpected Week 4 pilot-progress scope';
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
