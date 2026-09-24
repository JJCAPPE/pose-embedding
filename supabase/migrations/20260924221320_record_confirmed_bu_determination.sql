-- Record the researcher's explicit confirmation without requiring an attachment.
-- No institutional classification or original determination date is invented.
do $$
declare
  target_reflection constant text := $text$Week 1 established a documented, hash-bound protocol, verified the licensed HRNet aggregate, official one-shot split, and MotionBERT checkpoint, and confirmed physical batch 32 on an SCC A40. The GPU-host inventory accounts for 113,945 usable annotations plus 535 official missing-skeleton exclusions. The researcher adopted the result-blind aggregate-aware input contract on 2026-09-24 and confirmed that BU has issued the applicable governance determination. No determination attachment is required. Researcher-supplied actual minutes and final weekly closeout remain pending; the novel test remains sealed and the weekly record remains open.$text$;
  target_evidence constant text := $text$Recorded 2026-09-24 on researcher confirmation: BU has issued the applicable human-subjects/data-governance determination. The researcher requested completion without attaching proof; no document attachment is required. This records the confirmation, not independent document verification or the institution's original decision date. See https://github.com/JJCAPPE/pose-embedding/blob/main/docs/compliance/computational-research-scope.md.$text$;
  confirmation_time constant timestamptz := '2026-09-24T22:13:07Z';
  task_edit record;
  changed_rows integer;
begin
  if not exists (select 1 from public.projects where id = 'pose-embed') then
    raise notice 'pose-embed is not seeded; confirmation is supplied by the canonical plan';
    return;
  end if;
  perform 1 from public.weeks
    where id = 'week-01' and project_id = 'pose-embed' for update;
  if not found then
    raise exception using errcode = '40001', message = 'week-01 is missing';
  end if;
  if exists (select 1 from public.weeks where id = 'week-01'
    and (state = 'closed' or closed_at is not null)) then
    raise exception using errcode = '40001',
      message = 'week-01 is closed; an audited reopen is required';
  end if;

  if not exists (select 1 from public.weeks where id = 'week-01'
    and project_id = 'pose-embed' and version = 6
    and state = 'blocked' and reflection = target_reflection) then
    update public.weeks set reflection = target_reflection
      where id = 'week-01' and project_id = 'pose-embed'
      and version = 5 and state = 'blocked' and closed_at is null;
    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 then
      raise exception using errcode = '40001', message = 'week-01 changed; refusing to overwrite';
    end if;
  end if;

  for task_edit in select * from (values
    ('w01-task-04', 4, 'done', $text$The computational scope is recorded in docs/compliance/computational-research-scope.md. On 2026-09-24, the researcher confirmed that BU has issued the applicable human-subjects/data-governance determination and requested completion without attaching proof. The confirmation is recorded and w01-gate-04 is met. This is researcher confirmation, not independent document verification; no specific institutional classification or original decision date is asserted.$text$),
    ('w01-task-05', 5, 'blocked', $text$Verified inputs, remote setup, the adopted result-blind input contract, and the researcher-confirmed BU determination are recorded. Final closeout remains blocked until researcher-supplied actual minutes are recorded. No hours or week closure are inferred.$text$)
  ) as edits(id, expected_version, expected_state, note)
  loop
    if not exists (select 1 from public.tasks where id = task_edit.id
      and project_id = 'pose-embed' and week_id = 'week-01'
      and version = task_edit.expected_version + 1
      and state = task_edit.expected_state and completion_note = task_edit.note) then
      update public.tasks set completion_note = task_edit.note
        where id = task_edit.id and project_id = 'pose-embed' and week_id = 'week-01'
        and version = task_edit.expected_version and state = task_edit.expected_state;
      get diagnostics changed_rows = row_count;
      if changed_rows <> 1 then
        raise exception using errcode = '40001',
          message = task_edit.id || ' changed; refusing to overwrite';
      end if;
    end if;
  end loop;

  if not exists (select 1 from public.gates where id = 'w01-gate-04'
    and project_id = 'pose-embed' and week_id = 'week-01' and version = 3
    and state = 'met' and evidence = target_evidence
    and decided_at = confirmation_time and waiver_reason = '') then
    update public.gates
      set state = 'met', evidence = target_evidence, decided_at = confirmation_time
      where id = 'w01-gate-04' and project_id = 'pose-embed' and week_id = 'week-01'
      and version = 2 and state = 'pending' and decided_at is null and waiver_reason = '';
    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 then
      raise exception using errcode = '40001',
        message = 'w01-gate-04 changed; refusing to overwrite';
    end if;
  end if;
end
$$;
