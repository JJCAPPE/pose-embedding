-- Complete the governance-recording task because its defined output allows a
-- visible blocking record. This does not decide or waive the separate BU gate.
-- Fresh local databases contain no plan rows during `db reset`, so they skip
-- this data-only migration and receive the same state from the canonical plan
-- when the seed command runs.
do $$
declare
  tracker_exists boolean;
  changed_rows integer;
  completion_time constant timestamptz := '2026-09-16T12:07:48-04:00';
  target_evidence_url constant text :=
    'https://github.com/JJCAPPE/pose-embedding/blob/main/docs/compliance/computational-research-scope.md';
  previous_note constant text :=
    'Researcher-authored scope statement recorded on 2026-09-15: the project performs computational model training and evaluation on existing licensed pose annotations. It involves no participant recruitment, interaction, intervention, prospective data collection, direct identifiers, re-identification, or animal work. Because the source poses were derived from recordings of people, the statement does not itself establish BU human-subjects/data-governance status. The existing protocol advisor approval remains recorded separately. Unresolved condition (verbatim): ''BU provides the applicable human-subjects/data-governance determination.''';
  target_note constant text := previous_note ||
    ' The visible blocking record satisfies this task''s required output; w01-gate-04 remains pending until BU issues the determination.';
begin
  select exists (
    select 1
      from public.projects as project
     where project.id = 'pose-embed'
  ) into tracker_exists;

  if not tracker_exists then
    raise notice 'pose-embed tracker is not seeded; skipping Week 1 governance-record completion';
    return;
  end if;

  if exists (
    select 1
      from public.tasks as task
     where task.id = 'w01-task-04'
       and task.project_id = 'pose-embed'
       and task.version = 3
       and task.state = 'done'
       and task.completion_note = target_note
       and task.evidence_url = target_evidence_url
       and task.completed_at = completion_time
  ) then
    return;
  end if;

  update public.tasks as task
     set state = 'done',
         completion_note = target_note,
         evidence_url = target_evidence_url,
         completed_at = completion_time
   where task.id = 'w01-task-04'
     and task.project_id = 'pose-embed'
     and task.version = 2
     and task.state = 'blocked'
     and task.completion_note = previous_note
     and task.evidence_url = target_evidence_url
     and task.completed_at is null;

  get diagnostics changed_rows = row_count;
  if changed_rows <> 1 then
    raise exception using
      errcode = '40001',
      message = 'w01-task-04 changed since version 2; refusing to overwrite live progress';
  end if;
end
$$;
