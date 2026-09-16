-- Mirror the completed Week 2 manifest work and its clarified Week 1 source
-- amendment blocker in the hosted tracker. Fresh
-- local databases contain no plan rows during `db reset`, so they skip this
-- data-only migration and receive the same state from the canonical plan when
-- `supabase/scripts/seed_plan.sh` runs.
do $$
declare
  tracker_exists boolean;
  changed_rows integer;
  week_1_task_note constant text :=
    'Input acquisition and structural verification completed on 2026-09-13. The licensed HRNet aggregate is readable and checksummed (1,238,461,428 bytes; SHA-256 aaf1f928b4629fa9a0850528d43fdd8d920532805d16672bfdda78085b649df8); it contains 113,945 unique usable annotations spanning A001-A120, and all 20 official one-shot exemplars are present. The 535-record gap from the nominal 114,480 captures exactly matches the dataset authors'' missing-skeleton list. The task remains blocked pending a result-blind advisor-approved amendment that binds both the usable count and aggregate-aware source verification before the novel test is opened.';
  week_1_gate_evidence constant text :=
    'Verified 2026-09-13: the pretrained MotionBERT checkpoint, locked one-shot definition, and licensed HRNet aggregate are readable and checksummed. The aggregate has 113,945 usable annotations and all 20 exemplars; its 535-record difference from 114,480 exactly matches the official missing-skeleton list. See https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-1-input-inventory.md. This gate remains pending until a result-blind advisor-approved amendment binds both the usable count and aggregate-plus-missing-list verification in place of per-sample files.';
  week_1_evidence_url constant text :=
    'https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-1-input-inventory.md';
  task_01_note constant text :=
    'Implemented a hash-before-deserialization NTU HRNet importer and canonical S/C/P/R/A parser. Normalized 113,945 unique usable samples with frame count, tensor shapes, pose-track count, and nonempty-track count; malformed identifiers, duplicate aliases, label disagreement, invalid body metadata, missing-listed overlap, and non-finite arrays are rejected.';
  task_02_note constant text :=
    'Generated seven immutable JSONL manifests from the locked class and exemplar policy: 76,013 development-train, 18,988 development-validation, 95,001 final-train, 18,944 official-novel, 20 anchor, 18,884 primary-query, and 18,924 exact-official-query records. The audit records every SHA-256 digest and generation input.';
  task_03_note constant text :=
    'Automated checks prove class disjointness, one anchor per novel class, source and manifest identity uniqueness, exact exclusion of 40 synchronized camera mates, stable ordering, and complete 113,945-sample source coverage. An independent regeneration was byte-identical to the published release bundle.';
  task_04_note constant text :=
    'Published a source-safe manifest audit with per-class counts, all manifest digests, body-metadata coverage, invariant results, and one explicit explanation for each of the 40 synchronized-view exclusions. The required result-blind amendment is explicitly scoped to both the 114,480-versus-113,945 count and aggregate-aware source verification.';
  gate_01_evidence constant text :=
    'Seven release manifests are immutable and checksummed for the verified 113,945-sample usable aggregate. This gate remains pending until an advisor-approved, result-blind amendment binds both that usable count plus the official 535-record missing-skeleton list and aggregate-aware physical-source verification in place of 114,480 declared per-sample files. See https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/ntu-manifest-audit.v1.md.';
  gate_02_evidence constant text :=
    'Verified 2026-09-15: automated construction-time and unit-test invariants found zero forbidden class, anchor/query, synchronized-performance, source-identity, or manifest-identity overlap; complete source coverage and byte-stable regeneration also passed. See https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/ntu-manifest-audit.v1.md.';
  gate_03_evidence constant text :=
    'Verified 2026-09-15: the audit enumerates all 40 primary-query exclusions and derives each one as a synchronized camera mate sharing the anchor setup, performer, repetition, and action. See https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/ntu-manifest-audit.v1.md.';
  target_evidence_url constant text :=
    'https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/ntu-manifest-audit.v1.md';
  completion_time constant timestamptz := '2026-09-15T21:58:25-04:00';
begin
  select exists (
    select 1
      from public.projects as project
     where project.id = 'pose-embed'
  ) into tracker_exists;

  if not tracker_exists then
    raise notice 'pose-embed tracker is not seeded; skipping Week 2 progress update';
    return;
  end if;

  if not exists (
    select 1
      from public.tasks as task
     where task.id = 'w01-task-02'
       and task.project_id = 'pose-embed'
       and task.version = 4
       and task.state = 'blocked'
       and task.completion_note = week_1_task_note
       and task.evidence_url = week_1_evidence_url
       and task.completed_at is null
  ) then
    update public.tasks as task
       set state = 'blocked',
           completion_note = week_1_task_note,
           evidence_url = week_1_evidence_url,
           completed_at = null
     where task.id = 'w01-task-02'
       and task.project_id = 'pose-embed'
       and task.version = 3;

    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 then
      raise exception using
        errcode = '40001',
        message = 'w01-task-02 changed since version 3; refusing to overwrite live progress';
    end if;
  end if;

  if not exists (
    select 1
      from public.gates as gate_item
     where gate_item.id = 'w01-gate-02'
       and gate_item.project_id = 'pose-embed'
       and gate_item.version = 3
       and gate_item.state = 'pending'
       and gate_item.evidence = week_1_gate_evidence
       and gate_item.waiver_reason = ''
       and gate_item.decided_at is null
  ) then
    update public.gates as gate_item
       set state = 'pending',
           evidence = week_1_gate_evidence,
           waiver_reason = '',
           decided_at = null
     where gate_item.id = 'w01-gate-02'
       and gate_item.project_id = 'pose-embed'
       and gate_item.version = 2;

    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 then
      raise exception using
        errcode = '40001',
        message = 'w01-gate-02 changed since version 2; refusing to overwrite live progress';
    end if;
  end if;

  if not exists (
    select 1
      from public.tasks as task
     where task.id = 'w02-task-01'
       and task.project_id = 'pose-embed'
       and task.version = 2
       and task.state = 'done'
       and task.completion_note = task_01_note
       and task.evidence_url = target_evidence_url
       and task.completed_at = completion_time
  ) then
    update public.tasks as task
       set state = 'done',
           completion_note = task_01_note,
           evidence_url = target_evidence_url,
           completed_at = completion_time
     where task.id = 'w02-task-01'
       and task.project_id = 'pose-embed'
       and task.version = 1;

    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 then
      raise exception using
        errcode = '40001',
        message = 'w02-task-01 changed since version 1; refusing to overwrite live progress';
    end if;
  end if;

  if not exists (
    select 1
      from public.tasks as task
     where task.id = 'w02-task-02'
       and task.project_id = 'pose-embed'
       and task.version = 2
       and task.state = 'done'
       and task.completion_note = task_02_note
       and task.evidence_url = target_evidence_url
       and task.completed_at = completion_time
  ) then
    update public.tasks as task
       set state = 'done',
           completion_note = task_02_note,
           evidence_url = target_evidence_url,
           completed_at = completion_time
     where task.id = 'w02-task-02'
       and task.project_id = 'pose-embed'
       and task.version = 1;

    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 then
      raise exception using
        errcode = '40001',
        message = 'w02-task-02 changed since version 1; refusing to overwrite live progress';
    end if;
  end if;

  if not exists (
    select 1
      from public.tasks as task
     where task.id = 'w02-task-03'
       and task.project_id = 'pose-embed'
       and task.version = 2
       and task.state = 'done'
       and task.completion_note = task_03_note
       and task.evidence_url = target_evidence_url
       and task.completed_at = completion_time
  ) then
    update public.tasks as task
       set state = 'done',
           completion_note = task_03_note,
           evidence_url = target_evidence_url,
           completed_at = completion_time
     where task.id = 'w02-task-03'
       and task.project_id = 'pose-embed'
       and task.version = 1;

    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 then
      raise exception using
        errcode = '40001',
        message = 'w02-task-03 changed since version 1; refusing to overwrite live progress';
    end if;
  end if;

  if not exists (
    select 1
      from public.tasks as task
     where task.id = 'w02-task-04'
       and task.project_id = 'pose-embed'
       and task.version = 2
       and task.state = 'done'
       and task.completion_note = task_04_note
       and task.evidence_url = target_evidence_url
       and task.completed_at = completion_time
  ) then
    update public.tasks as task
       set state = 'done',
           completion_note = task_04_note,
           evidence_url = target_evidence_url,
           completed_at = completion_time
     where task.id = 'w02-task-04'
       and task.project_id = 'pose-embed'
       and task.version = 1;

    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 then
      raise exception using
        errcode = '40001',
        message = 'w02-task-04 changed since version 1; refusing to overwrite live progress';
    end if;
  end if;

  if not exists (
    select 1
      from public.gates as gate_item
     where gate_item.id = 'w02-gate-01'
       and gate_item.project_id = 'pose-embed'
       and gate_item.version = 2
       and gate_item.state = 'pending'
       and gate_item.evidence = gate_01_evidence
       and gate_item.waiver_reason = ''
       and gate_item.decided_at is null
  ) then
    update public.gates as gate_item
       set state = 'pending',
           evidence = gate_01_evidence,
           waiver_reason = '',
           decided_at = null
     where gate_item.id = 'w02-gate-01'
       and gate_item.project_id = 'pose-embed'
       and gate_item.version = 1;

    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 then
      raise exception using
        errcode = '40001',
        message = 'w02-gate-01 changed since version 1; refusing to overwrite live progress';
    end if;
  end if;

  if not exists (
    select 1
      from public.gates as gate_item
     where gate_item.id = 'w02-gate-02'
       and gate_item.project_id = 'pose-embed'
       and gate_item.version = 2
       and gate_item.state = 'met'
       and gate_item.evidence = gate_02_evidence
       and gate_item.waiver_reason = ''
       and gate_item.decided_at = completion_time
  ) then
    update public.gates as gate_item
       set state = 'met',
           evidence = gate_02_evidence,
           waiver_reason = '',
           decided_at = completion_time
     where gate_item.id = 'w02-gate-02'
       and gate_item.project_id = 'pose-embed'
       and gate_item.version = 1;

    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 then
      raise exception using
        errcode = '40001',
        message = 'w02-gate-02 changed since version 1; refusing to overwrite live progress';
    end if;
  end if;

  if not exists (
    select 1
      from public.gates as gate_item
     where gate_item.id = 'w02-gate-03'
       and gate_item.project_id = 'pose-embed'
       and gate_item.version = 2
       and gate_item.state = 'met'
       and gate_item.evidence = gate_03_evidence
       and gate_item.waiver_reason = ''
       and gate_item.decided_at = completion_time
  ) then
    update public.gates as gate_item
       set state = 'met',
           evidence = gate_03_evidence,
           waiver_reason = '',
           decided_at = completion_time
     where gate_item.id = 'w02-gate-03'
       and gate_item.project_id = 'pose-embed'
       and gate_item.version = 1;

    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 then
      raise exception using
        errcode = '40001',
        message = 'w02-gate-03 changed since version 1; refusing to overwrite live progress';
    end if;
  end if;
end
$$;
