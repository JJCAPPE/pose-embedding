-- Close Week 4 only after independent verification of all three complete pilots.
-- Apply the final task, gate and weekly closure atomically; preserve unreported time.
-- Exact version/content guards and audit triggers preserve the prior evidence.
do $migration$
declare
  edits constant jsonb := $edits$
[
  {
    "table": "tasks",
    "id": "w04-task-04",
    "before": {
      "id": "w04-task-04",
      "state": "in_progress",
      "title": "Run three complete engineering pilots",
      "details": "Run Contrastive, Contextual and SupCon for 20 epochs at seed 7 and rate 3e-4. Preserve epoch-5/10/15/20 checkpoints and complete clean scores plus epoch-zero diagnostics, finite/collapse checks and measured timing/memory/bytes.",
      "version": 7,
      "week_id": "week-04",
      "position": 4,
      "required": true,
      "project_id": "pose-embed",
      "completed_at": null,
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/codex/pose-week4-execution/docs/protocol/week-4-execution.md",
      "completion_note": "Progress on 2026-10-08: Contrastive job 7970697 completed at 21:21:48 UTC and Contextual job 7970756 at 21:33:18 UTC; scheduler accounting reports failed=0 and exit_status=0 for both (502 and 525 seconds). Their run records each report 20 epochs, 47,520 updates, 21 diagnostics and the required epoch-0/5/10/15/20 records. Both report initial-state hash 035a3e5e57569c0ae765b797f705b3a9f70353a6832fcb757c7622ebfa9b3284 and batch-plan hash 67128877ad2ac134c5c218ddd6c366903faa6cbfca270036dc2979e30ec859f5. SupCon job 7970877 started at 21:36:25 UTC and its startup fixture passed at 21:37:10 UTC; training results remain unverified. Independent validation of all three complete pilots, including pairing, provenance and health checks, remains pending; the pilot task and final Week 4 gate remain open.",
      "expected_output": "Three valid full pilots, ineligible for learning-rate selection, with complete diagnostic evidence.",
      "estimate_minutes": 90
    },
    "values": {
      "state": "done",
      "completion_note": "Verified on 2026-10-08: Contrastive 7970697, Contextual 7970756 and SupCon 7970877 completed all 20 epochs with 47,520 updates each. Independent CPU validation job 7971490 passed all three complete pilot records, shared initialization and batch-plan hashes, four immutable checkpoint/score records per recipe with 18,929 queries each, epoch-zero health and 21 diagnostics per recipe. Finite/collapse, timing, memory and retained-byte checks passed; all three pilot jobs and the validator exited with failed=0 and exit_status=0. The three attempts retain 150 files totaling 2,859,496,735 bytes. Validation SHA-256: 498116254ff24929183c261c93f0d647b9d97f832d572340068f6a54d3468a9e. Metadata audit SHA-256: e6a9b9a0c46cd1bb3ad43f8fba627ceab3ff5593251b04c0dbb7b5881023102d. These are engineering pilots and are ineligible for learning-rate selection.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/codex/pose-week4-execution/docs/protocol/week-4-execution.md",
      "completed_at": "2026-10-08T21:57:06+00:00"
    }
  },
  {
    "table": "gates",
    "id": "w04-gate-03",
    "before": {
      "id": "w04-gate-03",
      "state": "pending",
      "version": 3,
      "week_id": "week-04",
      "evidence": "",
      "position": 3,
      "required": true,
      "criterion": "Fresh parity/repeatability checks and all three 20-epoch pilots pass with four immutable checkpoint/score records each.",
      "decided_at": null,
      "project_id": "pose-embed",
      "waiver_reason": ""
    },
    "values": {
      "state": "met",
      "evidence": "Verified on 2026-10-08: Fresh parity and exact 95,001-row extraction repeatability passed; independent cache validation job 7969962 passed all five fresh v3 cache bindings. Independent pilot validation job 7971490 passed all three fixed 20-epoch pilots, paired initialization and batches, four immutable checkpoint/score records per recipe and the required health/resource checks. Validation SHA-256: 498116254ff24929183c261c93f0d647b9d97f832d572340068f6a54d3468a9e. Metadata audit SHA-256: e6a9b9a0c46cd1bb3ad43f8fba627ceab3ff5593251b04c0dbb7b5881023102d. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/codex/pose-week4-execution/docs/protocol/week-4-execution.md",
      "decided_at": "2026-10-08T21:57:06+00:00"
    }
  },
  {
    "table": "weeks",
    "id": "week-04",
    "before": {
      "id": "week-04",
      "phase": "Implementation and engineering",
      "risks": [
        "The v3 protocol, shared seal checks and all cache-affecting code must be frozen before fresh extraction.",
        "A mathematical, nonfinite or collapse failure blocks selection; pilot accuracy cannot justify tuning recipes or duration."
      ],
      "state": "active",
      "title": "Verified recipes and full pilots",
      "number": 4,
      "version": 9,
      "end_date": "2026-10-11",
      "closed_at": null,
      "objective": "Verify the three fixed recipes and the frozen-head path, then complete three full 20-epoch pilots under the immutable v3 design.",
      "project_id": "pose-embed",
      "reflection": "Done: Seal and loss checks, synthetic paired-training fixtures and independent validation of all five fresh v3 caches are complete. Contrastive job 7970697 and Contextual job 7970756 exited successfully; both run records report the fixed 20 epochs, 47,520 updates and required diagnostics/checkpoints, with matching initial-state and batch-plan hashes. Next: Verify completion of running SupCon job 7970877, then independently validate all three complete pilot records and their paired provenance/health checks. Open issues: SupCon started at 21:36:25 UTC and its startup fixture passed at 21:37:10 UTC; training results and independent validation of the three pilots remain pending. No final Week 4 gate or weekly closure is claimed; actual researcher time remains unreported.",
      "start_date": "2026-10-05",
      "deliverable": "Loss fixtures, paired initialization/batch evidence, fresh parity and clean caches, and three complete pilot records with timing and diagnostics.",
      "reopen_reason": "",
      "actual_minutes": 0,
      "advisor_prompt": "Do the mathematics, immutable inputs and complete pilot records demonstrate a valid fixed-budget comparison?",
      "planned_minutes": 480
    },
    "values": {
      "state": "closed",
      "reflection": "Done: Seal revalidation, loss and paired-training fixtures, all five fresh v3 caches and all three fixed 20-epoch engineering pilots are independently verified. Validator 7971490 passed the paired provenance, complete checkpoint/score records and health/resource checks, so all four required tasks and all three gates are complete and Week 4 is closed. Next: Complete Week 5 corruption, analysis and measured capacity/availability checks before learning-rate selection. Open issues: Actual researcher time remains unreported; zero recorded minutes is not a claim of zero work. The full-campaign capacity/availability gate and final-test authorization remain pending. Pilot accuracy is ineligible for selection; no Week 5 work or novel-test opening is claimed.",
      "closed_at": "2026-10-08T21:57:06+00:00"
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
    raise exception using errcode = '40001', message = 'Week 3 must be closed before Week 4 closure';
  end if;
  for edit in select value from jsonb_array_elements(edits)
  loop
    if not (
      (edit->>'table' = 'tasks' and edit->>'id' = 'w04-task-04')
      or (edit->>'table' = 'gates' and edit->>'id' = 'w04-gate-03')
      or (edit->>'table' = 'weeks' and edit->>'id' = 'week-04')
    ) or edit->'values' ? 'version' then
      raise exception 'Unexpected Week 4 completion scope';
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
