-- Reconcile the remaining open Week 3 tracker wording with the v2 seed.
-- Hosted Weeks 1 and 2 were already closed with zero recorded minutes; they are
-- deliberately excluded pending researcher reconciliation through an audited
-- reopen. This migration changes Week 3 wording only; it does not change
-- actual time, week state, or novel-test access. Exact predecessor content and
-- version guard both updates.
-- Seed revision counters are independent of live database counters; here the
-- observed live Week 3 versions advance once from 5 to 6 and 3 to 4.
do $migration$
declare
  edits constant jsonb := $edits$
[
  {
    "table": "weeks",
    "id": "week-03",
    "week_id": "week-03",
    "before": {
      "id": "week-03",
      "project_id": "pose-embed",
      "number": 3,
      "start_date": "2026-09-28",
      "end_date": "2026-10-04",
      "phase": "Representation",
      "title": "Frozen encoder and evaluator",
      "objective": "Build a deterministic frozen MotionBERT feature path and a trustworthy one-shot retrieval evaluator.",
      "deliverable": "Repeatable clean feature caches, verified retrieval metrics, and measured extraction cost.",
      "risks": [
        "The legacy upstream code assumes CUDA DataParallel and outdated dependencies.",
        "Pooling or normalization drift can invalidate comparison with MotionBERT.",
        "Feature caching without provenance can mix incompatible experiments."
      ],
      "advisor_prompt": "Are the frozen encoder, 2,048-dimensional head interface, cosine retrieval, and reported metrics faithful to the prospectus?",
      "reflection": "All five Week 3 technical tasks and gates are verified complete as of 2026-09-28. SCC job 7761714, release b92e7dd88fc261c0b8585039fbe99ad67ee8b445, completed successfully on one L40S at 01:40:59Z. Fresh parity passed, both complete 95,001-row extractions were byte-identical, and all five final/development caches validated. The conservative full-input forecast is 44.12 minutes and 4.07 GiB per cache, with 3.63 GiB peak GPU and 7.65 GiB peak host memory; the declared storage reserve passed. Prior encoder and independent v1/v2 metric/test-seal evidence is preserved. BU determination remains confirmed, and both novel-test opening ledgers remain absent. Actual researcher minutes remain unreported and unchanged at 0; the week remains formally planned and open because earlier weekly records have not closed. This completes Week 3 technical deliverables without claiming completion of the broader v2 study. Report: https://github.com/JJCAPPE/pose-embedding/blob/da439697358c795bc7d44a78b062eb1b63af2e0a/docs/protocol/week-3-scc-execution.md",
      "planned_minutes": 480,
      "actual_minutes": 0,
      "state": "planned",
      "closed_at": null,
      "version": 5
    },
    "values": {
      "objective": "Build a deterministic frozen MotionBERT feature path and independently verify historical one-shot and current v2 multi-positive retrieval behavior.",
      "deliverable": "Repeatable clean auxiliary feature caches, independent retrieval and test-seal fixtures, and measured extraction cost.",
      "advisor_prompt": "What further fine-tuning, quota, and full-roster measurements are needed before the v2 campaign can launch?",
      "reflection": "All five Week 3 technical tasks and gates are verified complete as of 2026-09-28. SCC job 7761714, release b92e7dd88fc261c0b8585039fbe99ad67ee8b445, completed successfully on one L40S at 01:40:59Z. Fresh parity passed, both complete 95,001-row extractions were byte-identical, and all five final/development caches validated. The conservative full-input forecast is 44.12 minutes and 4.07 GiB per cache, with 3.63 GiB peak GPU and 7.65 GiB peak host memory; the declared storage reserve passed. Prior encoder and independent v1/v2 metric/test-seal evidence is preserved. BU determination remains confirmed, and both novel-test opening ledgers remained absent at the September 28 observation. Actual researcher minutes remain unreported; Week 3 stays formally open. The hosted Week 1 and 2 records were closed later on September 28 with zero minutes while their prior notes said time was unreported; those closures require researcher reconciliation and are not treated here as evidence of zero work. This completes Week 3 technical deliverables without claiming completion of the broader v2 study. Report: https://github.com/JJCAPPE/pose-embedding/blob/da439697358c795bc7d44a78b062eb1b63af2e0a/docs/protocol/week-3-scc-execution.md"
    }
  },
  {
    "table": "gates",
    "id": "w03-gate-04",
    "week_id": "week-03",
    "before": {
      "id": "w03-gate-04",
      "project_id": "pose-embed",
      "week_id": "week-03",
      "position": 4,
      "criterion": "Measured extraction time and storage fit the remaining schedule.",
      "required": true,
      "state": "met",
      "evidence": "Verified 2026-09-28: the slower complete run forecasts 2,647.44 seconds (44.12 minutes) for 113,945 rows with the declared 25% time margin, and 4.07 GiB per cache with the 10% storage margin. Peak GPU memory (larger allocated/reserved) is 3.63 GiB and peak host memory is 7.65 GiB. Runtime, cache storage, GPU memory, host memory and remaining-storage checks all passed; post-run project quota remained above the required 200 GiB reserve. These measurements establish Week 3 extraction feasibility only. Report: https://github.com/JJCAPPE/pose-embedding/blob/da439697358c795bc7d44a78b062eb1b63af2e0a/docs/protocol/week-3-scc-execution.md",
      "waiver_reason": "",
      "decided_at": "2026-09-28T02:44:47.635174+00:00",
      "version": 3
    },
    "values": {
      "criterion": "Measured extraction time and storage fit the Week 3 limits."
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
    raise notice 'pose-embed is not seeded; import research-plan.v2.json';
    return;
  end if;

  for parent_id in
    select distinct value->>'week_id' from jsonb_array_elements(edits)
  loop
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
    if edit->>'table' not in ('weeks', 'tasks', 'gates') then
      raise exception 'Unexpected migration table';
    end if;
    execute format(
      'select to_jsonb(t) from public.%I t where id = $1 and project_id = ''pose-embed'' for update',
      edit->>'table') into current_row using edit->>'id';

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
    execute format(
      'update public.%I t set %s from jsonb_populate_record(null::public.%I, $1) v where t.id = $2 and t.project_id = ''pose-embed'' and t.version = $3',
      edit->>'table', assignments, edit->>'table')
      using edit->'values', edit->>'id', expected_version;
    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 then
      raise exception using errcode = '40001',
        message = edit->>'id' || ' could not be updated';
    end if;
  end loop;
end
$migration$;
