-- Reconcile the open Week 3 record with the final v3 September 29-October 4 plan.
-- Preserve original tasks/gates 01-05, their evidence, actual time and all closed weeks.
-- Add software evidence separately from pending real SCC preparation/design freeze.
-- No scientific artifacts, ownership, grants, RLS or test-opening records change.
-- Empty databases import the matching research-plan.v3.json administrative seed.
do $migration$
declare
  edits constant jsonb := $edits$
[
  {
    "table": "weeks",
    "id": "week-03",
    "before": {
      "id": "week-03",
      "project_id": "pose-embed",
      "number": 3,
      "start_date": "2026-09-28",
      "end_date": "2026-10-04",
      "phase": "Representation",
      "title": "Frozen encoder and evaluator",
      "objective": "Build a deterministic frozen MotionBERT feature path and independently verify historical one-shot and current v2 multi-positive retrieval behavior.",
      "deliverable": "Repeatable clean auxiliary feature caches, independent retrieval and test-seal fixtures, and measured extraction cost.",
      "risks": [
        "The legacy upstream code assumes CUDA DataParallel and outdated dependencies.",
        "Pooling or normalization drift can invalidate comparison with MotionBERT.",
        "Feature caching without provenance can mix incompatible experiments."
      ],
      "advisor_prompt": "What further fine-tuning, quota, and full-roster measurements are needed before the v2 campaign can launch?",
      "reflection": "All five Week 3 technical tasks and gates are verified complete as of 2026-09-28. SCC job 7761714, release b92e7dd88fc261c0b8585039fbe99ad67ee8b445, completed successfully on one L40S at 01:40:59Z. Fresh parity passed, both complete 95,001-row extractions were byte-identical, and all five final/development caches validated. The conservative full-input forecast is 44.12 minutes and 4.07 GiB per cache, with 3.63 GiB peak GPU and 7.65 GiB peak host memory; the declared storage reserve passed. Prior encoder and independent v1/v2 metric/test-seal evidence is preserved. BU determination remains confirmed, and both novel-test opening ledgers remained absent at the September 28 observation. Actual researcher minutes remain unreported; Week 3 stays formally open. The hosted Week 1 and 2 records were closed later on September 28 with zero minutes while their prior notes said time was unreported; those closures require researcher reconciliation and are not treated here as evidence of zero work. This completes Week 3 technical deliverables without claiming completion of the broader v2 study. Report: https://github.com/JJCAPPE/pose-embedding/blob/da439697358c795bc7d44a78b062eb1b63af2e0a/docs/protocol/week-3-scc-execution.md",
      "planned_minutes": 480,
      "actual_minutes": 0,
      "state": "planned",
      "closed_at": null,
      "version": 6
    },
    "values": {
      "phase": "V3 implementation and design freeze",
      "title": "Verified v3 implementation and sealed preparation",
      "objective": "Complete the frozen one-shot v3 protocol and pilot specification, corruption operators and fallback, versioned validators, shared dataset seals, source access separation and pilot instrumentation; freeze cache-affecting code and configuration before fresh extraction.",
      "deliverable": "Verified v3 software with historical evidence preserved, plus auxiliary-only SCC preparation, measured fallback evidence, a complete root audit and an immutable design lock before Week 4 caches and pilots.",
      "risks": [
        "The historical v1/v2 caches and GPU evidence do not establish v3 preparation, fallback selection or a frozen v3 design.",
        "Fresh extraction must wait for the measured auxiliary fallback, shared root audit and cache-affecting source/configuration freeze.",
        "Actual researcher minutes remain unreported; completion of software checks does not close the week or authorize novel access."
      ],
      "advisor_prompt": "Do auxiliary-only preparation, the measured fallback, the shared seal audit and the immutable design lock authorize fresh Week 4 caches and three engineering pilots?",
      "reflection": "All five Week 3 technical tasks and gates are verified complete as of 2026-09-28. SCC job 7761714, release b92e7dd88fc261c0b8585039fbe99ad67ee8b445, completed successfully on one L40S at 01:40:59Z. Fresh parity passed, both complete 95,001-row extractions were byte-identical, and all five final/development caches validated. The conservative full-input forecast is 44.12 minutes and 4.07 GiB per cache, with 3.63 GiB peak GPU and 7.65 GiB peak host memory; the declared storage reserve passed. Prior encoder and independent v1/v2 metric/test-seal evidence is preserved. BU determination remains confirmed, and both novel-test opening ledgers remained absent at the September 28 observation. Actual researcher minutes remain unreported; Week 3 stays formally open. The hosted Week 1 and 2 records were closed later on September 28 with zero minutes while their prior notes said time was unreported; those closures require researcher reconciliation and are not treated here as evidence of zero work. This completes Week 3 technical deliverables without claiming completion of the broader v2 study. Report: https://github.com/JJCAPPE/pose-embedding/blob/da439697358c795bc7d44a78b062eb1b63af2e0a/docs/protocol/week-3-scc-execution.md V3 reconciliation on 2026-09-29: the five tasks and gates above remain historical v1/v2 evidence. The current Week 3 objective now follows the final v3 September 29–October 4 plan. V3 software and fixture coverage are recorded separately; real SCC auxiliary preparation, fallback measurement, canonical root audit and immutable design freeze remain pending. No v3 scientific cache, pilot, novel access or weekly closure is claimed. Actual researcher minutes remain unreported. V3 status: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-3-v3-readiness.md",
      "state": "active"
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w03-task-06",
    "values": {
      "id": "w03-task-06",
      "week_id": "week-03",
      "position": 6,
      "title": "Implement and verify the v3 frozen study path",
      "details": "Implement the fixed three-recipe protocol, auxiliary preparation and fallback, immutable design validation, shared dataset seals, source separation and engineering-pilot diagnostics. Retain historical scientific behavior and verify the v3 boundaries with synthetic fixtures.",
      "expected_output": "Reviewed v3 implementation and passing applicable software checks; no real-data preparation or GPU result inferred.",
      "required": true,
      "estimate_minutes": 0,
      "state": "done",
      "completion_note": "V3 protocol/configuration validation, result-blind fallback, cross-version dataset seals, source separation, fixed-budget pilot snapshots and diagnostics, and fail-closed launchers are implemented and checked with software fixtures. The complete Python suite passed 1,012 tests with no skips; all 21 tracker tests, lint, typecheck and build passed. Ruff, formatting and workspace checks also passed. This records software capability only; SCC auxiliary preparation and the real immutable design freeze are tracked separately. Detailed verification: docs/protocol/week-3-v3-readiness.md.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-3-v3-readiness.md",
      "completed_at": "2026-09-29T21:04:11.106877+00:00",
      "version": 1,
      "project_id": "pose-embed"
    },
    "operation": "insert"
  },
  {
    "table": "tasks",
    "id": "w03-task-07",
    "values": {
      "id": "w03-task-07",
      "week_id": "week-03",
      "position": 7,
      "title": "Prepare auxiliary inputs and freeze the real v3 design on SCC",
      "details": "Deploy the reviewed release to SCC, audit and register every historical and current artifact root, prepare only the auxiliary inputs, measure the prespecified fallback without novel access, and freeze the cache-affecting source/configuration and preparation evidence before Week 4 extraction.",
      "expected_output": "Immutable auxiliary preparation and fallback evidence, canonical root audit and a validated v3 design lock from the real SCC inputs.",
      "required": true,
      "estimate_minutes": 0,
      "state": "todo",
      "completion_note": "Pending. No real v3 auxiliary preparation, measured fallback or immutable design lock has been verified on SCC. The historical five caches and job 7761714 remain evidence for their original protocol only.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-3-v3-readiness.md",
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "operation": "insert"
  },
  {
    "table": "gates",
    "id": "w03-gate-06",
    "values": {
      "id": "w03-gate-06",
      "week_id": "week-03",
      "position": 6,
      "criterion": "V3 protocol, corruption, shared-seal, source-separation and pilot instrumentation checks pass while historical behavior is preserved.",
      "required": true,
      "state": "met",
      "evidence": "Software implementation and synthetic-fixture verification are recorded in docs/protocol/week-3-v3-readiness.md, including the complete 1,012-test Python suite with no skips, all 21 tracker tests, lint/typecheck/build, and Ruff/format/workspace checks. Pilot attempts retain immutable diagnostics and failures and remain ineligible for selection. This gate asserts implementation correctness only, not real SCC preparation, v3 parity, caches, pilots or test access. Report: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-3-v3-readiness.md",
      "waiver_reason": "",
      "decided_at": "2026-09-29T21:04:11.106877+00:00",
      "version": 1,
      "project_id": "pose-embed"
    },
    "operation": "insert"
  },
  {
    "table": "gates",
    "id": "w03-gate-07",
    "values": {
      "id": "w03-gate-07",
      "week_id": "week-03",
      "position": 7,
      "criterion": "Real auxiliary-only preparation, measured fallback and canonical root audit are bound to an immutable v3 design lock before fresh feature extraction.",
      "required": true,
      "state": "pending",
      "evidence": "Pending real SCC execution and verification. Required evidence is the auxiliary-only preparation record, prespecified fallback measurement, all-root test-seal audit and frozen cache-affecting code/configuration digests. Historical v1/v2 GPU evidence cannot satisfy this v3 gate.",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "operation": "insert"
  },
  {
    "table": "week_sources",
    "id": "week-03:source-plan-v3",
    "operation": "insert",
    "values": {
      "week_id": "week-03",
      "source_id": "source-plan-v3",
      "project_id": "pose-embed",
      "purpose": "Use the final frozen one-shot v3 plan for current Week 3 implementation, auxiliary preparation and immutable design-freeze readiness; retain existing links as historical evidence.",
      "priority": "required",
      "version": 1
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
begin
  if not exists (select 1 from public.projects where id = 'pose-embed') then
    raise notice 'pose-embed is not seeded; import research-plan.v3.json';
    return;
  end if;

  -- Serialize against owner edits; planning reconciliation cannot reopen a week.
  select to_jsonb(w) into current_row from public.weeks w
    where id = 'week-03' and project_id = 'pose-embed' for update;
  if current_row is null or current_row->>'state' = 'closed'
     or current_row->>'closed_at' is not null then
    raise exception using errcode = '40001',
      message = 'week-03 is missing or closed; an audited reopen is required';
  end if;

  for edit in select value from jsonb_array_elements(edits)
  loop
    if not (
      (edit->>'table' = 'weeks' and edit->>'id' = 'week-03'
        and edit->>'operation' = 'update')
      or (edit->>'table' = 'tasks' and edit->>'id' in ('w03-task-06', 'w03-task-07')
        and edit->>'operation' = 'insert')
      or (edit->>'table' = 'gates' and edit->>'id' in ('w03-gate-06', 'w03-gate-07')
        and edit->>'operation' = 'insert')
      or (edit->>'table' = 'week_sources' and edit->>'id' = 'week-03:source-plan-v3'
        and edit->>'operation' = 'insert')
    ) then
      raise exception 'Unexpected Week 3 reconciliation scope';
    end if;
    if edit->>'table' = 'week_sources' then
      select to_jsonb(t) into current_row from public.week_sources t
        where project_id = 'pose-embed' and week_id = 'week-03'
          and source_id = 'source-plan-v3' for update;
    else
      execute format('select to_jsonb(t) from public.%I t where id = $1 and project_id = ''pose-embed'' for update', edit->>'table')
        into current_row using edit->>'id';
    end if;

    if edit->>'operation' = 'insert' then
      expected_row := edit->'values';
      if expected_row->>'week_id' <> 'week-03'
         or expected_row->>'project_id' <> 'pose-embed'
         or (expected_row->>'version')::integer <> 1 then
        raise exception 'Unexpected Week 3 child row';
      end if;
      if edit->>'table' = 'week_sources' then
        if expected_row->>'source_id' <> 'source-plan-v3' then
          raise exception 'Unexpected Week 3 source';
        end if;
      elsif expected_row->>'id' <> edit->>'id' then
        raise exception 'Unexpected Week 3 child identity';
      end if;
      if current_row is not null then
        if current_row @> expected_row then continue; end if;
        raise exception using errcode = '40001',
          message = edit->>'id' || ' already exists with different content';
      end if;
      select string_agg(format('%I', key), ', ' order by key),
             string_agg(format('v.%I', key), ', ' order by key)
        into columns_sql, assignments from jsonb_object_keys(expected_row) key;
      execute format('insert into public.%I as t (%s) select %s from jsonb_populate_record(null::public.%I, $1) v returning to_jsonb(t)',
        edit->>'table', columns_sql, assignments, edit->>'table')
        into current_row using expected_row;
    else
      if edit->'values' ? 'version' then
        raise exception 'The version trigger owns update versions';
      end if;
      expected_version := (edit->'before'->>'version')::integer;
      expected_row := edit->'before' || edit->'values'
        || jsonb_build_object('version', expected_version + 1);
      if current_row @> expected_row then continue; end if;
      if current_row is null or not (current_row @> (edit->'before')) then
        raise exception using errcode = '40001',
          message = 'week-03 changed; refusing to overwrite live progress';
      end if;
      select string_agg(format('%I = v.%I', key, key), ', ' order by key)
        into assignments from jsonb_object_keys(edit->'values') key;
      execute format('update public.weeks t set %s from jsonb_populate_record(null::public.weeks, $1) v where t.id = ''week-03'' and t.project_id = ''pose-embed'' and t.version = $2 returning to_jsonb(t)', assignments)
        into current_row using edit->'values', expected_version;
    end if;
    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 then
      raise exception using errcode = '40001',
        message = edit->>'id' || ' could not be reconciled';
    end if;
  end loop;
end
$migration$;
