-- Record verified acquisition and remote setup separately from the remaining
-- protocol and BU decisions. The week stays open and actual time is unchanged.
-- Unseeded databases obtain this state later from the canonical plan.
do $$
declare
  changed_rows integer;
  completion_time constant timestamptz := '2026-09-24T15:35:26Z';
  target_evidence_url constant text :=
    'https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-1-remote-setup.md';
  target_reflection constant text :=
    'Week 1 established an advisor-approved, hash-bound protocol, verified the licensed HRNet aggregate, official one-shot split, and MotionBERT checkpoint, and confirmed physical batch 32 on an SCC A40. The required inputs and setup are now verified on the GPU host. The inventory accounts for 113,945 usable annotations plus 535 official missing-skeleton exclusions. Acquisition and setup are complete; the input-contract amendment draft is unapproved, the BU governance determination is pending, and researcher-supplied actual minutes are still required. The novel test remains sealed and the weekly record remains open.';
  input_note constant text :=
    'Verified 2026-09-24: dataset access remains active, the complete usable HRNet aggregate, official missing-skeleton list, one-shot definition, and MotionBERT checkpoint are readable and checksummed, and the required inputs and setup are verified on the GPU host. The aggregate contains 113,945 usable annotations and all 20 official exemplars; the official 535-item missing-skeleton list accounts for the remaining nominal captures. This completes input acquisition and verification. The separate w01-gate-02 remains pending because the input-contract amendment draft is unapproved; the novel test remains sealed.';
  closeout_note constant text :=
    'Verified input acquisition and remote setup are recorded in the Week 1 evidence. Final closeout remains blocked until researcher-supplied actual minutes, the advisor-approved input-contract amendment, and the BU governance determination are recorded. The amendment draft is unapproved; no approval, hours, or week closure is inferred.';
  target_criterion constant text :=
    'Verified input inventory matches the approved protocol input contract.';
  input_evidence constant text :=
    'Verified 2026-09-24: the local and GPU-host inputs account for 113,945 usable HRNet annotations plus 535 official missing-skeleton exclusions, with readable, checksummed data and checkpoint inputs. See https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-1-remote-setup.md. The amendment at https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/input-contract-amendment-draft.md remains an unapproved draft. This gate remains pending until advisor approval binds the usable count and aggregate-plus-missing-list verification contract; the novel test remains sealed.';
begin
  if not exists (select 1 from public.projects where id = 'pose-embed') then
    raise notice 'pose-embed tracker is not seeded; skipping Week 1 remote setup';
    return;
  end if;

  perform 1 from public.weeks
   where id = 'week-01' and project_id = 'pose-embed'
   for update;
  if not found then
    raise exception using
      errcode = '40001',
      message = 'week-01 is missing; refusing to record remote setup';
  end if;
  if exists (
    select 1 from public.weeks
     where id = 'week-01' and project_id = 'pose-embed'
       and (state = 'closed' or closed_at is not null)
  ) then
    raise exception using
      errcode = '40001',
      message = 'week-01 is closed; an audited reopen is required before recording remote setup';
  end if;

  if not exists (
    select 1 from public.weeks
     where id = 'week-01' and project_id = 'pose-embed'
       and version = 3 and state = 'blocked'
       and reflection = target_reflection and closed_at is null
  ) then
    update public.weeks
       set reflection = target_reflection
     where id = 'week-01' and project_id = 'pose-embed'
       and version = 2 and state = 'blocked' and closed_at is null;
    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 then
      raise exception using
        errcode = '40001',
        message = 'week-01 changed since blocked version 2; refusing to overwrite live progress';
    end if;
  end if;

  if not exists (
    select 1 from public.tasks
     where id = 'w01-task-02' and project_id = 'pose-embed' and week_id = 'week-01'
       and version = 5 and state = 'done' and completion_note = input_note
       and evidence_url = target_evidence_url and completed_at = completion_time
  ) then
    update public.tasks
       set state = 'done', completion_note = input_note,
           evidence_url = target_evidence_url, completed_at = completion_time
     where id = 'w01-task-02' and project_id = 'pose-embed' and week_id = 'week-01'
       and version = 4 and state = 'blocked' and completed_at is null;
    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 then
      raise exception using
        errcode = '40001',
        message = 'w01-task-02 changed since blocked version 4; refusing to overwrite live progress';
    end if;
  end if;

  if not exists (
    select 1 from public.tasks
     where id = 'w01-task-05' and project_id = 'pose-embed' and week_id = 'week-01'
       and version = 3 and state = 'blocked' and completion_note = closeout_note
       and evidence_url = target_evidence_url and completed_at is null
  ) then
    update public.tasks
       set completion_note = closeout_note, evidence_url = target_evidence_url
     where id = 'w01-task-05' and project_id = 'pose-embed' and week_id = 'week-01'
       and version = 2 and state = 'blocked' and completed_at is null;
    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 then
      raise exception using
        errcode = '40001',
        message = 'w01-task-05 changed since blocked version 2; refusing to overwrite live progress';
    end if;
  end if;

  if not exists (
    select 1 from public.gates
     where id = 'w01-gate-02' and project_id = 'pose-embed' and week_id = 'week-01'
       and version = 4 and state = 'pending' and criterion = target_criterion
       and evidence = input_evidence and waiver_reason = '' and decided_at is null
  ) then
    update public.gates
       set criterion = target_criterion, evidence = input_evidence
     where id = 'w01-gate-02' and project_id = 'pose-embed' and week_id = 'week-01'
       and version = 3 and state = 'pending'
       and waiver_reason = '' and decided_at is null;
    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 then
      raise exception using
        errcode = '40001',
        message = 'w01-gate-02 changed since pending version 3; refusing to overwrite live progress';
    end if;
  end if;
end
$$;
