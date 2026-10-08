-- Record the resolved historical-root audit and verified synthetic/software fixtures.
-- Fresh caches are in progress; real-data pilots and weekly closure remain pending.
-- Preserve time/history; exact version/content guards protect concurrent updates.
do $migration$
declare
  edits constant jsonb := $edits$
[
  {
    "table": "tasks",
    "id": "w04-task-01",
    "before": {
      "id": "w04-task-01",
      "week_id": "week-04",
      "position": 1,
      "title": "Freeze and validate the v3 path",
      "details": "Complete explicit v3 configuration/manifest validation, dataset-wide seal checks and auxiliary/novel source access separation. Register historical roots, preserve old artifacts, and freeze the complete design and cache-affecting code before extraction.",
      "expected_output": "An immutable v3 design/pilot specification and passing version, provenance and seal checks.",
      "required": true,
      "estimate_minutes": 90,
      "state": "blocked",
      "completion_note": "Satisfied by the verified Week 3 handoff on 2026-09-29, not a second freeze: SCC job 7790916 completed with failed=0 and exit_status=0. Explicit v3 validators, registered historical-root seals and auxiliary/novel source separation passed; all eight identity sets and the auxiliary preparation are bound to the corrected immutable design lock 39426a3b2ddea74aaa8c1d39737cd9e5fb9c870c21745f5527e4e97b58d14e2d. The active scientific release is 2897f4fe4c1fb1857432a0e92a7391dde68307f5. Fresh v3 parity/caches, loss/paired-training evidence and three complete pilots remain Week 4 work. Recheck runtime seals before every job. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-3-v3-readiness.md Revalidation on 2026-10-08: Two previously registered local historical artifact roots are now unavailable, so their current test-seal status cannot be verified. The available local root and inspected SCC roots/releases contained no opening records; this bounded observation does not resolve the missing roots. The protocol file, immutable design lock and manifest-set hashes still match. Fresh v3 caches and pilots are blocked until the historical roots are recovered or an auditable, result-blind resolution establishes their provenance and seal status. No licensed-data extraction or pilot job was submitted. Synthetic-only L40S learnable-fixture job 7968648 was submitted separately without licensed-data access; its result is pending. The September 29 evidence above is preserved as a dated observation.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-3-v3-readiness.md",
      "completed_at": null,
      "version": 5,
      "project_id": "pose-embed"
    },
    "values": {
      "state": "done",
      "completion_note": "Satisfied by the verified Week 3 handoff on 2026-09-29, not a second freeze: SCC job 7790916 completed with failed=0 and exit_status=0. Explicit v3 validators, registered historical-root seals and auxiliary/novel source separation passed; all eight identity sets and the auxiliary preparation are bound to the corrected immutable design lock 39426a3b2ddea74aaa8c1d39737cd9e5fb9c870c21745f5527e4e97b58d14e2d. The active scientific release is 2897f4fe4c1fb1857432a0e92a7391dde68307f5. Fresh v3 parity/caches, loss/paired-training evidence and three complete pilots remain Week 4 work. Recheck runtime seals before every job. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-3-v3-readiness.md Revalidation on 2026-10-08: Two previously registered local historical artifact roots are now unavailable, so their current test-seal status cannot be verified. The available local root and inspected SCC roots/releases contained no opening records; this bounded observation does not resolve the missing roots. The protocol file, immutable design lock and manifest-set hashes still match. Fresh v3 caches and pilots are blocked until the historical roots are recovered or an auditable, result-blind resolution establishes their provenance and seal status. No licensed-data extraction or pilot job was submitted. Synthetic-only L40S learnable-fixture job 7968648 subsequently passed all three recipes at 1,000 updates and 1.0 self-excluded same-label retrieval without licensed-data access. The September 29 evidence above is preserved as a dated observation. Resolution on 2026-10-08: Dated automatic workspace cleanup records explain retirement of the two historical roots on October 5. Researcher confirmation of no intervening scientific runs or novel-pose, embedding or score access in the retired roots resolves the historical interval together with the September 29 audit and cleanup evidence. The immutable supplemental resolution has SHA-256 85ea2aa45930bb6525b5142b973e6671704a801f2048c42e2a5ae6e14e94e08d. The original registry, audit and scientific locks remain unchanged; no artifacts were recovered or recreated. Fresh cache job 7968689 was submitted through the frozen launcher after this resolution; cache results remain pending. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/codex/pose-week4-execution/docs/protocol/week-4-root-recovery.md",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/codex/pose-week4-execution/docs/protocol/week-4-root-recovery.md",
      "completed_at": "2026-10-08T19:10:01+00:00"
    }
  },
  {
    "table": "tasks",
    "id": "w04-task-02",
    "before": {
      "id": "w04-task-02",
      "week_id": "week-04",
      "position": 2,
      "title": "Verify losses and paired training",
      "details": "Check independent labeled forward/backward fixtures, the physical 8 × 4 sampler and shared initialization. Run the constructed 32-row learnable fixture for 1,000 updates per arm; require finite training and 100% self-excluded same-label retrieval.",
      "expected_output": "Verified three-arm numerical behavior and paired initialization/batch hashes.",
      "required": true,
      "estimate_minutes": 180,
      "state": "in_progress",
      "completion_note": "In progress on 2026-10-08: Baseline numerical checks passed 45 tests with one skipped optional source oracle. Additional independent loss fixtures and paired-training verification are being completed. Synthetic-only L40S learnable-fixture job 7968648 was submitted separately without licensed-data access; its result is pending. No completed three-arm learnable-fixture or pairing result is claimed yet.",
      "evidence_url": null,
      "completed_at": null,
      "version": 4,
      "project_id": "pose-embed"
    },
    "values": {
      "state": "done",
      "completion_note": "Verified on 2026-10-08: All 46 focused numerical/source checks passed with no remaining skips, including independent labeled forward/backward fixtures. Synthetic-only L40S job 7968648 completed all three recipes for 1,000 finite updates on the constructed 32-row physical 8 × 4 fixture with full 8,704-to-2,048 heads; each reached 1.0 self-excluded same-label retrieval. Scheduler accounting reports failed=0, exit_status=0, 18:57:39–18:58:52 UTC and 73 seconds. The shared initial-state hash is 035a3e5e57569c0ae765b797f705b3a9f70353a6832fcb757c7622ebfa9b3284. A separate repeated reduced-dimension 32-to-16 software fixture completed 20 epochs/20 updates per recipe with paired initial-state hash f5d2d3619a1d0121cbea51afc35375719ccb1701a8c35f7de933018c648da9d2 and batch-plan hash f581a887be8f1e2c01d48980ec0f1b99a6c6317661e9ed68591c499432ccfcac. These synthetic and software fixtures used no licensed data; real-data pilot pairing and provenance still require validation. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/codex/pose-week4-execution/docs/protocol/week-4-execution.md",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/codex/pose-week4-execution/docs/protocol/week-4-execution.md",
      "completed_at": "2026-10-08T19:10:01+00:00"
    }
  },
  {
    "table": "tasks",
    "id": "w04-task-03",
    "before": {
      "id": "w04-task-03",
      "week_id": "week-04",
      "position": 3,
      "title": "Generate fresh frozen features",
      "details": "Create v3-bound manifests with unchanged sample identities; run encoder parity and two fresh-process all-auxiliary extractions on the same GPU. Retain both repeats and development train/gallery/query caches with hashes.",
      "expected_output": "Fresh v3 parity/repeatability evidence and five immutable clean feature caches.",
      "required": true,
      "estimate_minutes": 120,
      "state": "blocked",
      "completion_note": "Blocked on 2026-10-08 by two unavailable registered historical artifact roots and the resulting unresolved current test-seal audit. Scheduler validation of the cache launcher passed, but no extraction job was submitted and no fresh v3 parity or cache result is claimed.",
      "evidence_url": null,
      "completed_at": null,
      "version": 4,
      "project_id": "pose-embed"
    },
    "values": {
      "state": "in_progress",
      "completion_note": "In progress on 2026-10-08: Fresh cache job 7968689 was submitted through the existing frozen launcher after the immutable historical-root retirement resolution. Latest available quota was 1,024.44 decimal GB and filesystem free space was 1,207,359,766,528 bytes. Fresh parity, both full auxiliary extraction repeats and development train/gallery/query cache outputs remain pending; no cache result is claimed."
    }
  },
  {
    "table": "tasks",
    "id": "w04-task-04",
    "before": {
      "id": "w04-task-04",
      "week_id": "week-04",
      "position": 4,
      "title": "Run three complete engineering pilots",
      "details": "Run Contrastive, Contextual and SupCon for 20 epochs at seed 7 and rate 3e-4. Preserve epoch-5/10/15/20 checkpoints and complete clean scores plus epoch-zero diagnostics, finite/collapse checks and measured timing/memory/bytes.",
      "expected_output": "Three valid full pilots, ineligible for learning-rate selection, with complete diagnostic evidence.",
      "required": true,
      "estimate_minutes": 90,
      "state": "blocked",
      "completion_note": "Blocked on 2026-10-08 pending a complete historical-root seal audit, verified loss/paired-training fixtures and fresh v3 parity/caches. No pilot was submitted; no pilot checkpoint, score or runtime result is claimed.",
      "evidence_url": null,
      "completed_at": null,
      "version": 4,
      "project_id": "pose-embed"
    },
    "values": {
      "state": "todo",
      "completion_note": "Awaiting successful fresh v3 parity and cache verification from job 7968689, then three complete 20-epoch engineering pilots. Independent loss and synthetic paired-training fixtures are complete. No pilot was submitted; real-data pilot pairing, checkpoints, scores and runtime remain unverified."
    }
  },
  {
    "table": "gates",
    "id": "w04-gate-01",
    "before": {
      "id": "w04-gate-01",
      "week_id": "week-04",
      "position": 1,
      "criterion": "The complete v3 design and cache-affecting release are frozen; source identities are preserved and historical seal audits are resolved.",
      "required": true,
      "state": "pending",
      "evidence": "Satisfied by the verified Week 3 handoff on 2026-09-29, not a second freeze: SCC job 7790916 completed with failed=0 and exit_status=0. Explicit v3 validators, registered historical-root seals and auxiliary/novel source separation passed; all eight identity sets and the auxiliary preparation are bound to the corrected immutable design lock 39426a3b2ddea74aaa8c1d39737cd9e5fb9c870c21745f5527e4e97b58d14e2d. The active scientific release is 2897f4fe4c1fb1857432a0e92a7391dde68307f5. Fresh v3 parity/caches, loss/paired-training evidence and three complete pilots remain Week 4 work. Recheck runtime seals before every job. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-3-v3-readiness.md Revalidation on 2026-10-08: Two previously registered local historical artifact roots are now unavailable, so their current test-seal status cannot be verified. The available local root and inspected SCC roots/releases contained no opening records; this bounded observation does not resolve the missing roots. The protocol file, immutable design lock and manifest-set hashes still match. Fresh v3 caches and pilots are blocked until the historical roots are recovered or an auditable, result-blind resolution establishes their provenance and seal status. No licensed-data extraction or pilot job was submitted. Synthetic-only L40S learnable-fixture job 7968648 was submitted separately without licensed-data access; its result is pending. The September 29 evidence above is preserved as a dated observation.",
      "waiver_reason": "",
      "decided_at": null,
      "version": 5,
      "project_id": "pose-embed"
    },
    "values": {
      "state": "met",
      "evidence": "Satisfied by the verified Week 3 handoff on 2026-09-29, not a second freeze: SCC job 7790916 completed with failed=0 and exit_status=0. Explicit v3 validators, registered historical-root seals and auxiliary/novel source separation passed; all eight identity sets and the auxiliary preparation are bound to the corrected immutable design lock 39426a3b2ddea74aaa8c1d39737cd9e5fb9c870c21745f5527e4e97b58d14e2d. The active scientific release is 2897f4fe4c1fb1857432a0e92a7391dde68307f5. Fresh v3 parity/caches, loss/paired-training evidence and three complete pilots remain Week 4 work. Recheck runtime seals before every job. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-3-v3-readiness.md Revalidation on 2026-10-08: Two previously registered local historical artifact roots are now unavailable, so their current test-seal status cannot be verified. The available local root and inspected SCC roots/releases contained no opening records; this bounded observation does not resolve the missing roots. The protocol file, immutable design lock and manifest-set hashes still match. Fresh v3 caches and pilots are blocked until the historical roots are recovered or an auditable, result-blind resolution establishes their provenance and seal status. No licensed-data extraction or pilot job was submitted. Synthetic-only L40S learnable-fixture job 7968648 subsequently passed all three recipes at 1,000 updates and 1.0 self-excluded same-label retrieval without licensed-data access. The September 29 evidence above is preserved as a dated observation. Resolution on 2026-10-08: Dated automatic workspace cleanup records explain retirement of the two historical roots on October 5. Researcher confirmation of no intervening scientific runs or novel-pose, embedding or score access in the retired roots resolves the historical interval together with the September 29 audit and cleanup evidence. The immutable supplemental resolution has SHA-256 85ea2aa45930bb6525b5142b973e6671704a801f2048c42e2a5ae6e14e94e08d. The original registry, audit and scientific locks remain unchanged; no artifacts were recovered or recreated. Fresh cache job 7968689 was submitted through the frozen launcher after this resolution; cache results remain pending. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/codex/pose-week4-execution/docs/protocol/week-4-root-recovery.md",
      "decided_at": "2026-10-08T19:10:01+00:00"
    }
  },
  {
    "table": "gates",
    "id": "w04-gate-02",
    "before": {
      "id": "w04-gate-02",
      "week_id": "week-04",
      "position": 2,
      "criterion": "All three losses pass independent numerical and learnable-fixture checks; initialization and physical batch plans pair exactly.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 3,
      "project_id": "pose-embed"
    },
    "values": {
      "state": "met",
      "evidence": "Verified on 2026-10-08: All 46 focused numerical/source checks passed with no remaining skips, including independent labeled forward/backward fixtures. Synthetic-only L40S job 7968648 completed all three recipes for 1,000 finite updates on the constructed 32-row physical 8 × 4 fixture with full 8,704-to-2,048 heads; each reached 1.0 self-excluded same-label retrieval. Scheduler accounting reports failed=0, exit_status=0, 18:57:39–18:58:52 UTC and 73 seconds. The shared initial-state hash is 035a3e5e57569c0ae765b797f705b3a9f70353a6832fcb757c7622ebfa9b3284. A separate repeated reduced-dimension 32-to-16 software fixture completed 20 epochs/20 updates per recipe with paired initial-state hash f5d2d3619a1d0121cbea51afc35375719ccb1701a8c35f7de933018c648da9d2 and batch-plan hash f581a887be8f1e2c01d48980ec0f1b99a6c6317661e9ed68591c499432ccfcac. These synthetic and software fixtures used no licensed data; real-data pilot pairing and provenance still require validation. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/codex/pose-week4-execution/docs/protocol/week-4-execution.md",
      "decided_at": "2026-10-08T19:10:01+00:00"
    }
  },
  {
    "table": "weeks",
    "id": "week-04",
    "before": {
      "id": "week-04",
      "project_id": "pose-embed",
      "number": 4,
      "start_date": "2026-10-05",
      "end_date": "2026-10-11",
      "phase": "Implementation and engineering",
      "title": "Verified recipes and full pilots",
      "objective": "Verify the three fixed recipes and the frozen-head path, then complete three full 20-epoch pilots under the immutable v3 design.",
      "deliverable": "Loss fixtures, paired initialization/batch evidence, fresh parity and clean caches, and three complete pilot records with timing and diagnostics.",
      "risks": [
        "The v3 protocol, shared seal checks and all cache-affecting code must be frozen before fresh extraction.",
        "A mathematical, nonfinite or collapse failure blocks selection; pilot accuracy cannot justify tuning recipes or duration."
      ],
      "advisor_prompt": "Do the mathematics, immutable inputs and complete pilot records demonstrate a valid fixed-budget comparison?",
      "reflection": "Done: On 2026-10-08, read-only preflight checks found unchanged protocol, design-lock and manifest-set hashes and no opening records in the accessible inspected roots/releases. At 18:50:52 UTC, usable SCC space was 1,025.40 decimal GB, above the bounded Week 4 requirement; capacity is a dated observation, not an allocation commitment. The cache launcher passed scheduler validation only; no extraction or pilot job was submitted. Baseline numerical checks passed 45 tests with one skipped optional source oracle. Synthetic-only L40S learnable-fixture job 7968648 was submitted separately without licensed-data access; its result is pending. Next: Locate or recover the two unavailable registered historical roots and resolve the complete seal audit, finish independent loss and paired-training fixtures, then repeat preflight before fresh v3 caches and the three full pilots. Open issues: The missing roots block fresh extraction and pilots. No fresh v3 cache or pilot result is verified. Actual researcher time remains unreported; no hours were invented and Week 4 remains open.",
      "planned_minutes": 480,
      "actual_minutes": 0,
      "state": "blocked",
      "closed_at": null,
      "version": 4
    },
    "values": {
      "state": "active",
      "reflection": "Done: The October 8 preflight verified unchanged protocol, design-lock and manifest-set hashes. The initial missing-root blocker was resolved using the September 29 sealed audit, dated automatic October 5 workspace cleanup records and researcher confirmation about the intervening interval. The supplemental immutable retirement resolution is 85ea2aa45930bb6525b5142b973e6671704a801f2048c42e2a5ae6e14e94e08d; original evidence remains unchanged and no artifacts were recovered or recreated. All 46 focused numerical/source checks passed without skips. Full-size synthetic L40S job 7968648 completed all three 1,000-update fixtures with finite training and 1.0 self-excluded same-label retrieval (failed=0, exit_status=0; 73 seconds). A separate reduced-dimension 32-to-16, 20-epoch/20-update software fixture verified paired initialization and batch-plan hashes. Neither fixture accessed licensed data. Latest usable SCC space was 1,024.44 decimal GB, above the bounded Week 4 requirement; this is not an allocation commitment. Fresh cache job 7968689 was submitted through the frozen launcher after retirement resolution; results are pending. Next: Verify fresh parity, both full extraction repeats and all development caches, then run and verify the three complete 20-epoch engineering pilots under the unchanged design. Open issues: No fresh v3 cache or real-data pilot result is verified yet; real-data pilot pairing/provenance must still be checked. Actual researcher time remains unreported; no hours were invented and Week 4 remains open."
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
    raise exception using errcode = '40001', message = 'Week 3 must be closed before this fixture update';
  end if;
  for edit in select value from jsonb_array_elements(edits)
  loop
    if not (
      (edit->>'table' = 'tasks' and edit->>'id' in ('w04-task-01', 'w04-task-02', 'w04-task-03', 'w04-task-04'))
      or (edit->>'table' = 'gates' and edit->>'id' in ('w04-gate-01', 'w04-gate-02'))
      or (edit->>'table' = 'weeks' and edit->>'id' = 'week-04')
    ) or edit->'values' ? 'version' then
      raise exception 'Unexpected Week 4 fixture scope';
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
