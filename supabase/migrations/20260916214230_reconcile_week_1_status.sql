-- Reconcile the public Week 1 record without claiming either external approval
-- or inventing the researcher's actual hours. Fresh local databases contain no
-- plan rows during `db reset`, so they skip this data-only migration and receive
-- the same state from the canonical plan when the seed command runs.
do $$
declare
  tracker_exists boolean;
  changed_rows integer;
  target_objective constant text :=
    'Turn the prospectus into an advisor-approved, hash-bound, testable protocol and prove that the required data and compute are reachable.';
  target_deliverable constant text :=
    'An advisor-approved, hash-bound protocol-v1, verified data and checkpoint inventory, and measured GPU profile.';
  target_reflection constant text :=
    'Week 1 established an advisor-approved, hash-bound protocol, verified the licensed HRNet aggregate, official one-shot split, and MotionBERT checkpoint, and confirmed physical batch 32 on an SCC A40. The input audit found a result-blind contract mismatch: the authorized aggregate has 113,945 usable annotations and the official missing-skeleton list accounts for all 535 omitted captures, while protocol v1 still binds 114,480. The novel test remains sealed pending advisor approval of that amendment. BU''s governance determination and the researcher''s actual-hours record also remain pending.';
  protocol_output constant text :=
    'Advisor-approved, hash-bound protocol document.';
  protocol_evidence_url constant text :=
    'https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/protocol-v1-approval.md';
  closeout_note constant text :=
    'Week 1 evidence, blockers, and a factual status reflection were reconciled on 2026-09-16. Final closeout remains blocked until the advisor-approved input-contract amendment, BU governance determination, and researcher-supplied actual minutes are recorded; no approvals or hours were inferred.';
begin
  select exists (
    select 1
      from public.projects as project
     where project.id = 'pose-embed'
  ) into tracker_exists;

  if not tracker_exists then
    raise notice 'pose-embed tracker is not seeded; skipping Week 1 status reconciliation';
    return;
  end if;

  if not exists (
    select 1
      from public.weeks as week
     where week.id = 'week-01'
       and week.project_id = 'pose-embed'
       and week.version = 2
       and week.objective = target_objective
       and week.deliverable = target_deliverable
       and week.reflection = target_reflection
       and week.actual_minutes = 0
       and week.state = 'blocked'
       and week.closed_at is null
  ) then
    update public.weeks as week
       set objective = target_objective,
           deliverable = target_deliverable,
           reflection = target_reflection,
           state = 'blocked'
     where week.id = 'week-01'
       and week.project_id = 'pose-embed'
       and week.version = 1;

    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 then
      raise exception using
        errcode = '40001',
        message = 'week-01 changed since version 1; refusing to overwrite live progress';
    end if;
  end if;

  if not exists (
    select 1
      from public.tasks as task
     where task.id = 'w01-task-01'
       and task.project_id = 'pose-embed'
       and task.version = 3
       and task.state = 'done'
       and task.expected_output = protocol_output
       and task.evidence_url = protocol_evidence_url
  ) then
    update public.tasks as task
       set expected_output = protocol_output,
           evidence_url = protocol_evidence_url
     where task.id = 'w01-task-01'
       and task.project_id = 'pose-embed'
       and task.version = 2;

    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 then
      raise exception using
        errcode = '40001',
        message = 'w01-task-01 changed since version 2; refusing to overwrite live progress';
    end if;
  end if;

  if not exists (
    select 1
      from public.tasks as task
     where task.id = 'w01-task-05'
       and task.project_id = 'pose-embed'
       and task.version = 2
       and task.state = 'blocked'
       and task.completion_note = closeout_note
       and task.evidence_url is null
       and task.completed_at is null
  ) then
    update public.tasks as task
       set state = 'blocked',
           completion_note = closeout_note,
           evidence_url = null,
           completed_at = null
     where task.id = 'w01-task-05'
       and task.project_id = 'pose-embed'
       and task.version = 1;

    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 then
      raise exception using
        errcode = '40001',
        message = 'w01-task-05 changed since version 1; refusing to overwrite live progress';
    end if;
  end if;
end
$$;
