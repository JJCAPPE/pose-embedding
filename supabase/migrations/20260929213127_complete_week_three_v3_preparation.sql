-- Complete verified real SCC v3 preparation; preserve historical evidence and time.
-- Only task 07, gate 07 and the open Week 3 record change. Required gates still
-- govern closure through the existing database trigger. No scientific, RLS,
-- ownership or Auth settings change. Exact retries are idempotent.
do $migration$
declare
  edits constant jsonb := $edits$
[
  {
    "table": "tasks",
    "id": "w03-task-07",
    "before": {
      "completed_at": null,
      "completion_note": "Pending. No real v3 auxiliary preparation, measured fallback or immutable design lock has been verified on SCC. The historical five caches and job 7761714 remain evidence for their original protocol only.",
      "details": "Deploy the reviewed release to SCC, audit and register every historical and current artifact root, prepare only the auxiliary inputs, measure the prespecified fallback without novel access, and freeze the cache-affecting source/configuration and preparation evidence before Week 4 extraction.",
      "estimate_minutes": 0,
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-3-v3-readiness.md",
      "expected_output": "Immutable auxiliary preparation and fallback evidence, canonical root audit and a validated v3 design lock from the real SCC inputs.",
      "id": "w03-task-07",
      "position": 7,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Prepare auxiliary inputs and freeze the real v3 design on SCC",
      "version": 1,
      "week_id": "week-03"
    },
    "values": {
      "state": "done",
      "completion_note": "Verified 2026-09-29: SCC completion job 7790916 passed the corrected design freeze, independent verification process and capacity checks with failed=0 and exit_status=0. Auxiliary preparation came from job 7790703; its failed initial JSON reload and verification attempt are preserved under decision 0005. The auxiliary container contains 95,001 authorized rows; the fallback was measured from the fixed 76,013-row development-training set and is 0.6601371765136719. All eight identity sets, unchanged manifest bytes and the historical development episode are bound to the immutable design. Both SCC artifact roots and three local historical roots were audited; no opening records were found. Protocol digest: 52241fefab4d1a5aa0fb313d7af4e37bdc6923e2f8277e01cd179bc27a46beea. Design-lock SHA-256: 39426a3b2ddea74aaa8c1d39737cd9e5fb9c870c21745f5527e4e97b58d14e2d. This completes Week 3 preparation; fresh v3 parity, caches and three pilots belong to Week 4. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-3-v3-readiness.md",
      "completed_at": "2026-09-29T22:28:17.544258+00:00"
    }
  },
  {
    "table": "gates",
    "id": "w03-gate-07",
    "before": {
      "criterion": "Real auxiliary-only preparation, measured fallback and canonical root audit are bound to an immutable v3 design lock before fresh feature extraction.",
      "decided_at": null,
      "evidence": "Pending real SCC execution and verification. Required evidence is the auxiliary-only preparation record, prespecified fallback measurement, all-root test-seal audit and frozen cache-affecting code/configuration digests. Historical v1/v2 GPU evidence cannot satisfy this v3 gate.",
      "id": "w03-gate-07",
      "position": 7,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 1,
      "waiver_reason": "",
      "week_id": "week-03"
    },
    "values": {
      "state": "met",
      "evidence": "Verified 2026-09-29: SCC completion job 7790916 passed the corrected design freeze, independent verification process and capacity checks with failed=0 and exit_status=0. Auxiliary preparation came from job 7790703; its failed initial JSON reload and verification attempt are preserved under decision 0005. The auxiliary container contains 95,001 authorized rows; the fallback was measured from the fixed 76,013-row development-training set and is 0.6601371765136719. All eight identity sets, unchanged manifest bytes and the historical development episode are bound to the immutable design. Both SCC artifact roots and three local historical roots were audited; no opening records were found. Protocol digest: 52241fefab4d1a5aa0fb313d7af4e37bdc6923e2f8277e01cd179bc27a46beea. Design-lock SHA-256: 39426a3b2ddea74aaa8c1d39737cd9e5fb9c870c21745f5527e4e97b58d14e2d. This completes Week 3 preparation; fresh v3 parity, caches and three pilots belong to Week 4. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-3-v3-readiness.md",
      "decided_at": "2026-09-29T22:28:17.544258+00:00"
    }
  },
  {
    "table": "weeks",
    "id": "week-03",
    "before": {
      "actual_minutes": 0,
      "advisor_prompt": "Do auxiliary-only preparation, the measured fallback, the shared seal audit and the immutable design lock authorize fresh Week 4 caches and three engineering pilots?",
      "closed_at": null,
      "deliverable": "Verified v3 software with historical evidence preserved, plus auxiliary-only SCC preparation, measured fallback evidence, a complete root audit and an immutable design lock before Week 4 caches and pilots.",
      "end_date": "2026-10-04",
      "id": "week-03",
      "number": 3,
      "objective": "Complete the frozen one-shot v3 protocol and pilot specification, corruption operators and fallback, versioned validators, shared dataset seals, source access separation and pilot instrumentation; freeze cache-affecting code and configuration before fresh extraction.",
      "phase": "V3 implementation and design freeze",
      "planned_minutes": 480,
      "project_id": "pose-embed",
      "reflection": "All five Week 3 technical tasks and gates are verified complete as of 2026-09-28. SCC job 7761714, release b92e7dd88fc261c0b8585039fbe99ad67ee8b445, completed successfully on one L40S at 01:40:59Z. Fresh parity passed, both complete 95,001-row extractions were byte-identical, and all five final/development caches validated. The conservative full-input forecast is 44.12 minutes and 4.07 GiB per cache, with 3.63 GiB peak GPU and 7.65 GiB peak host memory; the declared storage reserve passed. Prior encoder and independent v1/v2 metric/test-seal evidence is preserved. BU determination remains confirmed, and both novel-test opening ledgers remained absent at the September 28 observation. Actual researcher minutes remain unreported; Week 3 stays formally open. The hosted Week 1 and 2 records were closed later on September 28 with zero minutes while their prior notes said time was unreported; those closures require researcher reconciliation and are not treated here as evidence of zero work. This completes Week 3 technical deliverables without claiming completion of the broader v2 study. Report: https://github.com/JJCAPPE/pose-embedding/blob/da439697358c795bc7d44a78b062eb1b63af2e0a/docs/protocol/week-3-scc-execution.md V3 reconciliation on 2026-09-29: the five tasks and gates above remain historical v1/v2 evidence. The current Week 3 objective now follows the final v3 September 29\u2013October 4 plan. V3 software and fixture coverage are recorded separately; real SCC auxiliary preparation, fallback measurement, canonical root audit and immutable design freeze remain pending. No v3 scientific cache, pilot, novel access or weekly closure is claimed. Actual researcher minutes remain unreported. V3 status: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-3-v3-readiness.md",
      "reopen_reason": "",
      "risks": [
        "The historical v1/v2 caches and GPU evidence do not establish v3 preparation, fallback selection or a frozen v3 design.",
        "Fresh extraction must wait for the measured auxiliary fallback, shared root audit and cache-affecting source/configuration freeze.",
        "Actual researcher minutes remain unreported; completion of software checks does not close the week or authorize novel access."
      ],
      "start_date": "2026-09-28",
      "state": "active",
      "title": "Verified v3 implementation and sealed preparation",
      "version": 7
    },
    "values": {
      "risks": [
        "Historical v1/v2 caches remain preserved; Week 4 must generate fresh v3 parity and caches under the frozen design.",
        "Week 4 bounded storage passed at the recorded observation; the October 18 full-campaign capacity and availability gate still needs fresh evidence.",
        "Actual researcher minutes remain unreported and are displayed as No time recorded; the zero placeholder is not a claim of zero work."
      ],
      "reflection": "All five Week 3 technical tasks and gates are verified complete as of 2026-09-28. SCC job 7761714, release b92e7dd88fc261c0b8585039fbe99ad67ee8b445, completed successfully on one L40S at 01:40:59Z. Fresh parity passed, both complete 95,001-row extractions were byte-identical, and all five final/development caches validated. The conservative full-input forecast is 44.12 minutes and 4.07 GiB per cache, with 3.63 GiB peak GPU and 7.65 GiB peak host memory; the declared storage reserve passed. Prior encoder and independent v1/v2 metric/test-seal evidence is preserved. BU determination remains confirmed, and both novel-test opening ledgers remained absent at the September 28 observation. Actual researcher minutes remain unreported; Week 3 stays formally open. The hosted Week 1 and 2 records were closed later on September 28 with zero minutes while their prior notes said time was unreported; those closures require researcher reconciliation and are not treated here as evidence of zero work. This completes Week 3 technical deliverables without claiming completion of the broader v2 study. Report: https://github.com/JJCAPPE/pose-embedding/blob/da439697358c795bc7d44a78b062eb1b63af2e0a/docs/protocol/week-3-scc-execution.md V3 reconciliation on 2026-09-29: the five tasks and gates above remain historical v1/v2 evidence. The current Week 3 objective now follows the final v3 September 29\u2013October 4 plan. V3 software and fixture coverage are recorded separately; real SCC auxiliary preparation, fallback measurement, canonical root audit and immutable design freeze remain pending. No v3 scientific cache, pilot, novel access or weekly closure is claimed. Actual researcher minutes remain unreported. V3 status: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-3-v3-readiness.md V3 completion on 2026-09-29: Verified 2026-09-29: SCC completion job 7790916 passed the corrected design freeze, independent verification process and capacity checks with failed=0 and exit_status=0. Auxiliary preparation came from job 7790703; its failed initial JSON reload and verification attempt are preserved under decision 0005. The auxiliary container contains 95,001 authorized rows; the fallback was measured from the fixed 76,013-row development-training set and is 0.6601371765136719. All eight identity sets, unchanged manifest bytes and the historical development episode are bound to the immutable design. Both SCC artifact roots and three local historical roots were audited; no opening records were found. Protocol digest: 52241fefab4d1a5aa0fb313d7af4e37bdc6923e2f8277e01cd179bc27a46beea. Design-lock SHA-256: 39426a3b2ddea74aaa8c1d39737cd9e5fb9c870c21745f5527e4e97b58d14e2d. This completes Week 3 preparation; fresh v3 parity, caches and three pilots belong to Week 4. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-3-v3-readiness.md All seven required tasks and gates now pass, so Week 3 is closed and Week 4 is ready to start. The tracker permits closure on task/gate evidence while preserving unreported actual time; no hours were invented. Seven superseded dependency environments and the retired package-download cache were removed after recording their provenance. Historical scientific artifacts remain preserved. Measured available space after cleanup was 274.72 decimal GB; the bounded Week 4 requirement is 239.7484 GB. The initial full-campaign requirement remains 314.7484 GB and must be remeasured at the October gate.",
      "state": "closed",
      "closed_at": "2026-09-29T22:28:17.544258+00:00"
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
    where id = 'week-03' and project_id = 'pose-embed' for update;
  if week_closed is null then
    raise exception using errcode = '40001', message = 'week-03 is missing';
  end if;
  for edit in select value from jsonb_array_elements(edits)
  loop
    if not (
      (edit->>'table' = 'tasks' and edit->>'id' = 'w03-task-07')
      or (edit->>'table' = 'gates' and edit->>'id' = 'w03-gate-07')
      or (edit->>'table' = 'weeks' and edit->>'id' = 'week-03')
    ) or edit->'values' ? 'version' then
      raise exception 'Unexpected Week 3 completion scope';
    end if;
    execute format('select to_jsonb(t) from public.%I t where id = $1 and project_id = ''pose-embed'' for update', edit->>'table')
      into current_row using edit->>'id';
    expected_version := (edit->'before'->>'version')::integer;
    expected_row := edit->'before' || edit->'values'
      || jsonb_build_object('version', expected_version + 1);
    if current_row @> expected_row then continue; end if;
    if week_closed or current_row is null or not (current_row @> (edit->'before')) then
      raise exception using errcode = '40001',
        message = edit->>'id' || ' changed or Week 3 is closed; refusing to overwrite progress';
    end if;
    select string_agg(format('%I = v.%I', key, key), ', ' order by key)
      into assignments from jsonb_object_keys(edit->'values') key;
    execute format('update public.%I t set %s from jsonb_populate_record(null::public.%I, $1) v where t.id = $2 and t.project_id = ''pose-embed'' and t.version = $3 returning to_jsonb(t)',
      edit->>'table', assignments, edit->>'table')
      into current_row using edit->'values', edit->>'id', expected_version;
    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 or not (current_row @> expected_row) then
      raise exception using errcode = '40001',
        message = edit->>'id' || ' could not be completed';
    end if;
  end loop;
end
$migration$;
