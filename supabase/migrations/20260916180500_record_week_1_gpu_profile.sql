-- Mirror the completed Week 1 GPU profile in the hosted tracker. Fresh local
-- databases intentionally contain no plan rows during `db reset`, so they skip
-- this data-only migration and receive the same state from the canonical plan
-- when `supabase/scripts/seed_plan.sh` runs.
do $$
declare
  tracker_exists boolean;
  changed_rows integer;
  target_evidence_url constant text :=
    'https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-1-gpu-profile.md';
  target_task_note constant text :=
    'Completed 2026-09-16: a real frozen MotionBERT encoder profile ran on a scheduler-assigned BU SCC A40 using dense protocol-shaped float32 inputs. Physical batch 32 completed with 2.572 GiB peak allocated, 2.855 GiB peak reserved, and an 842.164 ms median forward; batch 64 completed with 4.977 GiB allocated, 5.514 GiB reserved, and a 1,685.400 ms median. Required device, CUDA, scheduler, quota, and job-limit evidence was captured. Physical batch 32 remains selected because protocol v1 permits 64 only after all core methods fit. This is compute evidence only, not preprocessing or encoder-parity evidence.';
  target_gate_evidence constant text :=
    'Verified 2026-09-16: frozen MotionBERT completed the protocol-shaped physical batch 32 profile on a scheduler-assigned BU SCC A40, and all required device, CUDA, memory, runtime, scheduler, quota, and job-limit evidence was captured. Physical batch 32 is feasible and remains selected pending the Week 4 all-core-method batch-64 profile. See https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-1-gpu-profile.md.';
  completion_time constant timestamptz := '2026-09-16T12:41:15-04:00';
begin
  select exists (
    select 1
      from public.projects as project
     where project.id = 'pose-embed'
  ) into tracker_exists;

  if not tracker_exists then
    raise notice 'pose-embed tracker is not seeded; skipping Week 1 GPU profile update';
    return;
  end if;

  if not exists (
    select 1
      from public.tasks as task
     where task.id = 'w01-task-03'
       and task.project_id = 'pose-embed'
       and task.version = 2
       and task.state = 'done'
       and task.completion_note = target_task_note
       and task.evidence_url = target_evidence_url
       and task.completed_at = completion_time
  ) then
    update public.tasks as task
       set state = 'done',
           completion_note = target_task_note,
           evidence_url = target_evidence_url,
           completed_at = completion_time
     where task.id = 'w01-task-03'
       and task.project_id = 'pose-embed'
       and task.version = 1;

    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 then
      raise exception using
        errcode = '40001',
        message = 'w01-task-03 changed since version 1; refusing to overwrite live progress';
    end if;
  end if;

  if not exists (
    select 1
      from public.gates as gate_item
     where gate_item.id = 'w01-gate-03'
       and gate_item.project_id = 'pose-embed'
       and gate_item.version = 2
       and gate_item.state = 'met'
       and gate_item.evidence = target_gate_evidence
       and gate_item.waiver_reason = ''
       and gate_item.decided_at = completion_time
  ) then
    update public.gates as gate_item
       set state = 'met',
           evidence = target_gate_evidence,
           waiver_reason = '',
           decided_at = completion_time
     where gate_item.id = 'w01-gate-03'
       and gate_item.project_id = 'pose-embed'
       and gate_item.version = 1;

    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 then
      raise exception using
        errcode = '40001',
        message = 'w01-gate-03 changed since version 1; refusing to overwrite live progress';
    end if;
  end if;
end
$$;
