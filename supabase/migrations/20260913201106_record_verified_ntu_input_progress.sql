-- Mirror the verified NTU input status in the hosted tracker. Fresh local
-- databases intentionally contain no plan rows during `db reset`, so they
-- skip this data-only migration and receive the same state from the canonical
-- plan when `supabase/scripts/seed_plan.sh` runs.
do $$
declare
  tracker_exists boolean;
  task_rows integer;
  gate_rows integer;
  task_already_applied boolean;
  gate_already_applied boolean;
  target_evidence_url constant text :=
    'https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-1-input-inventory.md';
  target_task_note constant text :=
    'Input acquisition and structural verification completed on 2026-09-13. The licensed HRNet aggregate is readable and checksummed (1,238,461,428 bytes; SHA-256 aaf1f928b4629fa9a0850528d43fdd8d920532805d16672bfdda78085b649df8); it contains 113,945 unique usable annotations spanning A001-A120, and all 20 official one-shot exemplars are present. The 535-record gap from the nominal 114,480 captures exactly matches the dataset authors'' missing-skeleton list. The task remains blocked pending a result-blind advisor-approved protocol-count amendment before the novel test is opened.';
  target_gate_evidence constant text :=
    'Verified 2026-09-13: the pretrained MotionBERT checkpoint, locked one-shot definition, and licensed HRNet aggregate are readable and checksummed. The aggregate has 113,945 usable annotations and all 20 exemplars; its 535-record difference from 114,480 exactly matches the official missing-skeleton list. See https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-1-input-inventory.md. This gate remains pending until the required protocol-count amendment is approved.';
begin
  select exists (
    select 1
      from public.projects as project
     where project.id = 'pose-embed'
  ) into tracker_exists;

  if not tracker_exists then
    raise notice 'pose-embed tracker is not seeded; skipping progress update';
    return;
  end if;

  select exists (
    select 1
      from public.tasks as task
     where task.id = 'w01-task-02'
       and task.project_id = 'pose-embed'
       and task.version = 3
       and task.state = 'blocked'
       and task.completion_note = target_task_note
       and task.evidence_url = target_evidence_url
  ) into task_already_applied;

  if not task_already_applied then
    update public.tasks as task
       set state = 'blocked',
           completion_note = target_task_note,
           evidence_url = target_evidence_url
     where task.id = 'w01-task-02'
       and task.project_id = 'pose-embed'
       and task.version = 2;

    get diagnostics task_rows = row_count;
    if task_rows <> 1 then
      raise exception using
        errcode = '40001',
        message = 'w01-task-02 changed since version 2; refusing to overwrite live progress';
    end if;
  end if;

  select exists (
    select 1
      from public.gates as gate_item
     where gate_item.id = 'w01-gate-02'
       and gate_item.project_id = 'pose-embed'
       and gate_item.version = 2
       and gate_item.state = 'pending'
       and gate_item.evidence = target_gate_evidence
       and gate_item.waiver_reason = ''
       and gate_item.decided_at is null
  ) into gate_already_applied;

  if not gate_already_applied then
    update public.gates as gate_item
       set state = 'pending',
           evidence = target_gate_evidence,
           waiver_reason = '',
           decided_at = null
     where gate_item.id = 'w01-gate-02'
       and gate_item.project_id = 'pose-embed'
       and gate_item.version = 1;

    get diagnostics gate_rows = row_count;
    if gate_rows <> 1 then
      raise exception using
        errcode = '40001',
        message = 'w01-gate-02 changed since version 1; refusing to overwrite live progress';
    end if;
  end if;
end
$$;
