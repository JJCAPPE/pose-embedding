-- Mirror the researcher-authored governance scope record in the hosted tracker.
-- Fresh local databases intentionally contain no plan rows during `db reset`,
-- so they skip this data-only migration and receive the same state from the
-- canonical plan when `supabase/scripts/seed_plan.sh` runs.
do $$
declare
  tracker_exists boolean;
  task_rows integer;
  gate_rows integer;
  task_already_applied boolean;
  gate_already_applied boolean;
  target_evidence_url constant text :=
    'https://github.com/JJCAPPE/pose-embedding/blob/main/docs/compliance/computational-research-scope.md';
  target_task_note constant text :=
    'Researcher-authored scope statement recorded on 2026-09-15: the project performs computational model training and evaluation on existing licensed pose annotations. It involves no participant recruitment, interaction, intervention, prospective data collection, direct identifiers, re-identification, or animal work. Because the source poses were derived from recordings of people, the statement does not itself establish BU human-subjects/data-governance status. The existing protocol advisor approval remains recorded separately. Unresolved condition (verbatim): ''BU provides the applicable human-subjects/data-governance determination.''';
  target_gate_evidence constant text :=
    'A researcher-authored computational-scope statement is recorded at https://github.com/JJCAPPE/pose-embedding/blob/main/docs/compliance/computational-research-scope.md. It documents no recruitment, interaction, intervention, prospective collection, direct identifiers, re-identification, or animal work, but it is not a BU determination. Unresolved condition (verbatim): ''BU provides the applicable human-subjects/data-governance determination.''';
begin
  select exists (
    select 1
      from public.projects as project
     where project.id = 'pose-embed'
  ) into tracker_exists;

  if not tracker_exists then
    raise notice 'pose-embed tracker is not seeded; skipping governance update';
    return;
  end if;

  select exists (
    select 1
      from public.tasks as task
     where task.id = 'w01-task-04'
       and task.project_id = 'pose-embed'
       and task.version = 2
       and task.state = 'blocked'
       and task.completion_note = target_task_note
       and task.evidence_url = target_evidence_url
       and task.completed_at is null
  ) into task_already_applied;

  if not task_already_applied then
    update public.tasks as task
       set state = 'blocked',
           completion_note = target_task_note,
           evidence_url = target_evidence_url,
           completed_at = null
     where task.id = 'w01-task-04'
       and task.project_id = 'pose-embed'
       and task.version = 1;

    get diagnostics task_rows = row_count;
    if task_rows <> 1 then
      raise exception using
        errcode = '40001',
        message = 'w01-task-04 changed since version 1; refusing to overwrite live progress';
    end if;
  end if;

  select exists (
    select 1
      from public.gates as gate_item
     where gate_item.id = 'w01-gate-04'
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
     where gate_item.id = 'w01-gate-04'
       and gate_item.project_id = 'pose-embed'
       and gate_item.version = 1;

    get diagnostics gate_rows = row_count;
    if gate_rows <> 1 then
      raise exception using
        errcode = '40001',
        message = 'w01-gate-04 changed since version 1; refusing to overwrite live progress';
    end if;
  end if;
end
$$;
