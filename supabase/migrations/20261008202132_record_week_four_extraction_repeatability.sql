-- Record the verified full-auxiliary repeatability milestone only.
-- Development caches are still running; task/week status and hours stay unchanged.
-- Exact version/content guards preserve concurrent progress and closed-week records.
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
      "completion_note": "In progress on 2026-10-08: Fresh cache job 7968689 was submitted through the existing frozen launcher after the immutable historical-root retirement resolution. Latest available quota was 1,024.44 decimal GB and filesystem free space was 1,207,359,766,528 bytes. Fresh parity, both full auxiliary extraction repeats and development train/gallery/query cache outputs remain pending; no cache result is claimed.",
      "evidence_url": null,
      "completed_at": null,
      "version": 5,
      "project_id": "pose-embed"
    },
    "values": {
      "completion_note": "In progress on 2026-10-08: Fresh cache job 7968689 was submitted through the existing frozen launcher after the immutable historical-root retirement resolution. Latest available quota was 1,024.44 decimal GB and filesystem free space was 1,207,359,766,528 bytes. Fresh parity, both full auxiliary extraction repeats and development train/gallery/query cache outputs remain pending; no cache result is claimed. Milestone at 20:17:48 UTC on 2026-10-08: Job 7968689 remains running. Two independent fresh-process auxiliary extractions, run sequentially on the same GPU, passed repeatability for all 95,001 rows × 8,704 features: arrays, labels, ordered IDs and serialized bytes are identical. The passed repeatability report has SHA-256 b3f4139f7f9b3ff459d23940799e7db5a55de023d767751b833b1c9236a2af26. Both artifacts have SHA-256 43209789c08e8a5e461f72ec5bbeb9bf986bb862e6b828dc0c0b446ad684ee8d; their separate sidecars have SHA-256 4bd3668372b8efadab7a52ed3df2dcb42dae21f79a95995bf9c102da4d87d1a4 and 55fd1e0b7ec72cf04a40dd3ae28068f7c1975774db307b4cb57de60e989695dd. Development train/gallery/query caches are still running; no real-data pilot has been submitted. This partial milestone does not complete the feature-cache task or the week.",
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
      "reflection": "Done: The October 8 preflight verified unchanged protocol, design-lock and manifest-set hashes. The initial missing-root blocker was resolved using the September 29 sealed audit, dated automatic October 5 workspace cleanup records and researcher confirmation about the intervening interval. The supplemental immutable retirement resolution is 85ea2aa45930bb6525b5142b973e6671704a801f2048c42e2a5ae6e14e94e08d; original evidence remains unchanged and no artifacts were recovered or recreated. All 46 focused numerical/source checks passed without skips. Full-size synthetic L40S job 7968648 completed all three 1,000-update fixtures with finite training and 1.0 self-excluded same-label retrieval (failed=0, exit_status=0; 73 seconds). A separate reduced-dimension 32-to-16, 20-epoch/20-update software fixture verified paired initialization and batch-plan hashes. Neither fixture accessed licensed data. Latest usable SCC space was 1,024.44 decimal GB, above the bounded Week 4 requirement; this is not an allocation commitment. Fresh cache job 7968689 was submitted through the frozen launcher after retirement resolution; results are pending. Next: Verify fresh parity, both full extraction repeats and all development caches, then run and verify the three complete 20-epoch engineering pilots under the unchanged design. Open issues: No fresh v3 cache or real-data pilot result is verified yet; real-data pilot pairing/provenance must still be checked. Actual researcher time remains unreported; no hours were invented and Week 4 remains open.",
      "planned_minutes": 480,
      "actual_minutes": 0,
      "state": "active",
      "closed_at": null,
      "version": 5
    },
    "values": {
      "reflection": "Done: The October 8 preflight verified unchanged protocol, design-lock and manifest-set hashes. The initial missing-root blocker was resolved using the September 29 sealed audit, dated automatic October 5 workspace cleanup records and researcher confirmation about the intervening interval. The supplemental immutable retirement resolution is 85ea2aa45930bb6525b5142b973e6671704a801f2048c42e2a5ae6e14e94e08d; original evidence remains unchanged and no artifacts were recovered or recreated. All 46 focused numerical/source checks passed without skips. Full-size synthetic L40S job 7968648 completed all three 1,000-update fixtures with finite training and 1.0 self-excluded same-label retrieval (failed=0, exit_status=0; 73 seconds). A separate reduced-dimension 32-to-16, 20-epoch/20-update software fixture verified paired initialization and batch-plan hashes. Neither fixture accessed licensed data. Latest usable SCC space was 1,024.44 decimal GB, above the bounded Week 4 requirement; this is not an allocation commitment. Milestone at 20:17:48 UTC on 2026-10-08: Job 7968689 remains running. Two independent fresh-process auxiliary extractions, run sequentially on the same GPU, passed repeatability for all 95,001 rows × 8,704 features: arrays, labels, ordered IDs and serialized bytes are identical. The passed repeatability report has SHA-256 b3f4139f7f9b3ff459d23940799e7db5a55de023d767751b833b1c9236a2af26. Both artifacts have SHA-256 43209789c08e8a5e461f72ec5bbeb9bf986bb862e6b828dc0c0b446ad684ee8d; their separate sidecars have SHA-256 4bd3668372b8efadab7a52ed3df2dcb42dae21f79a95995bf9c102da4d87d1a4 and 55fd1e0b7ec72cf04a40dd3ae28068f7c1975774db307b4cb57de60e989695dd. Development train/gallery/query caches are still running; no real-data pilot has been submitted. This partial milestone does not complete the feature-cache task or the week. Next: Verify the complete development train/gallery/query cache set and final cache-job accounting, including fresh encoder-parity evidence, then run and verify the three complete 20-epoch engineering pilots under the unchanged design. Open issues: Development-cache completion and successful whole-job exit remain unverified; no real-data pilot result is available and pilot pairing/provenance must still be checked. Actual researcher time remains unreported; no hours were invented and Week 4 remains open."
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
    raise exception using errcode = '40001', message = 'Week 3 must be closed before this repeatability update';
  end if;
  for edit in select value from jsonb_array_elements(edits)
  loop
    if not (
      (edit->>'table' = 'tasks' and edit->>'id' = 'w04-task-03')
      or (edit->>'table' = 'weeks' and edit->>'id' = 'week-04')
    ) or edit->'values' ? 'version' then
      raise exception 'Unexpected Week 4 repeatability scope';
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
