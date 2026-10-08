-- Complete independently validated fresh caches and record the first pilot start.
-- Pilot results, the final gate and weekly closure remain pending; preserve hours.
-- Exact version/content guards preserve concurrent progress and closed records.
do $migration$
declare
  edits constant jsonb := $edits$
[
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
      "state": "in_progress",
      "completion_note": "Cache generation completed on 2026-10-08: Job 7968689 generated all five fresh v3 caches and exited with failed=0 and exit_status=0 (19:08:54–20:42:58 UTC; 5,644 seconds). Encoder parity and exact repeatability of two independent 95,001-row × 8,704-feature extractions passed; the repeatability report SHA-256 is b3f4139f7f9b3ff459d23940799e7db5a55de023d767751b833b1c9236a2af26. Development train/gallery/query cache row counts are 76,013/20/18,929. Independent CPU validation job 7969962 was queued at 20:52 UTC. This task remains in progress until its validation receipt passes; no pilot has been submitted.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/codex/pose-week4-execution/docs/protocol/week-4-execution.md",
      "completed_at": null,
      "version": 7,
      "project_id": "pose-embed"
    },
    "values": {
      "state": "done",
      "completion_note": "Verified on 2026-10-08: Independent CPU validation job 7969962 passed all five fresh v3 cache bindings, exact repeatability and bounded extraction resource checks, with failed=0 and exit_status=0. The validation receipt SHA-256 is 4e87fd994e36f0a5159226138f079a7cf5c68e69aeb03d6a94aed3a4d9288b93. The immutable caches contain two 95,001-row auxiliary repeats plus 76,013/20/18,929 development train/gallery/query rows, all with 8,704 features. Fresh encoder parity passed. These checks complete the feature-cache task; they do not establish the full-campaign capacity gate or pilot results.",
      "completed_at": "2026-10-08T21:13:26+00:00"
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
      "completion_note": "Awaiting successful fresh v3 parity and cache verification from job 7968689, then three complete 20-epoch engineering pilots. Independent loss and synthetic paired-training fixtures are complete. No pilot was submitted; real-data pilot pairing, checkpoints, scores and runtime remain unverified.",
      "evidence_url": null,
      "completed_at": null,
      "version": 5,
      "project_id": "pose-embed"
    },
    "values": {
      "state": "in_progress",
      "completion_note": "In progress on 2026-10-08: First fixed 20-epoch Contrastive engineering pilot job 7970697 started at 21:13:26 UTC and its startup fixture passed at 21:14:43 UTC. The pilot is running; its training/checkpoint/score results are not yet verified. Contextual and SupCon pilots remain pending. Completion requires all three full pilot records, the four prescribed checkpoint/score records per recipe, finite/collapse checks and paired real-data initialization/batch evidence; submission alone is not completion.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/codex/pose-week4-execution/docs/protocol/week-4-execution.md"
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
      "reflection": "Done: Loss and synthetic paired-training fixtures are verified. Job 7968689 generated all five fresh v3 cache files and exited successfully. Encoder parity and exact repeatability of the two 95,001-row extractions passed; development train/gallery/query cache counts are 76,013/20/18,929. Next: Await independent CPU validation job 7969962, queued at 20:52 UTC on October 8, then submit and verify the three fixed 20-epoch engineering pilots. Open issues: The independent validation receipt and all three real-data pilots are pending; no pilot has been submitted. Actual researcher time remains unreported and Week 4 remains open.",
      "planned_minutes": 480,
      "actual_minutes": 0,
      "state": "active",
      "closed_at": null,
      "version": 7
    },
    "values": {
      "reflection": "Done: Seal revalidation, loss verification and synthetic paired-training fixtures are complete. All five fresh v3 caches passed independent CPU validation job 7969962, with fresh parity, exact repeatability and bounded extraction resource checks. Next: Verify completion and outputs for running Contrastive pilot 7970697, then complete and verify the Contextual and SupCon pilots under the fixed 20-epoch design. Open issues: The first Contrastive pilot started at 21:13:26 UTC and passed its startup fixture; training results are unverified. All three complete real-data pilot records and their pairing/health checks remain required; the final Week 4 gate is pending. Actual researcher time remains unreported and Week 4 remains open."
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
    raise exception using errcode = '40001', message = 'Week 3 must be closed before this cache-validation update';
  end if;
  for edit in select value from jsonb_array_elements(edits)
  loop
    if not (
      (edit->>'table' = 'tasks' and edit->>'id' in ('w04-task-03', 'w04-task-04'))
      or (edit->>'table' = 'weeks' and edit->>'id' = 'week-04')
    ) or edit->'values' ? 'version' then
      raise exception 'Unexpected Week 4 cache-validation scope';
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
