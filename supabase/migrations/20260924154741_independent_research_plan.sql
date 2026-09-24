-- Governance-only update at the researcher's explicit request.
-- Preserve states, time, scientific gates, and historical migrations/artifacts.
-- Row locks and expected versions prevent overwriting intervening owner edits.
do $migration$
declare
  edits constant jsonb := $edits$
[
  {
    "table": "weeks",
    "id": "week-01",
    "week_id": "week-01",
    "version": 3,
    "state": "blocked",
    "values": {
      "objective": "Turn the prospectus into a documented, hash-bound, testable protocol and prove that the required data and compute are reachable.",
      "deliverable": "A documented, hash-bound protocol-v1, verified data and checkpoint inventory, and measured GPU profile.",
      "risks": [
        "NTU or checkpoint access may require manual license acceptance.",
        "GPU availability may not match the planned memory or runtime assumptions.",
        "Protocol amendments or the BU determination may remain unresolved after technical setup begins."
      ],
      "advisor_prompt": "Are the research question, test-opening rule, primary estimand, synchronized-view exclusion, and claim language documented as the binding protocol?",
      "reflection": "Week 1 established a documented, hash-bound protocol, verified the licensed HRNet aggregate, official one-shot split, and MotionBERT checkpoint, and confirmed physical batch 32 on an SCC A40. The required inputs and setup are now verified on the GPU host. The inventory accounts for 113,945 usable annotations plus 535 official missing-skeleton exclusions. Acquisition and setup are complete; the input-contract amendment is not yet adopted, the BU governance determination is pending, and researcher-supplied actual minutes are still required. The novel test remains sealed and the weekly record remains open."
    }
  },
  {
    "table": "tasks",
    "id": "w01-task-01",
    "week_id": "week-01",
    "version": 3,
    "state": "done",
    "values": {
      "expected_output": "Documented, hash-bound protocol document.",
      "completion_note": "All binding scientific choices were confirmed, including mandatory final training on all 100 auxiliary actions. Independent research governance is recorded in docs/protocol/independent-research.md. Protocol SHA-256: 1b43d1bedb833f71936d0bc36d30a9b6f7ed6d2d00a5b8c8b781b787ad66d265.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/independent-research.md"
    }
  },
  {
    "table": "tasks",
    "id": "w01-task-02",
    "week_id": "week-01",
    "version": 5,
    "state": "done",
    "values": {
      "completion_note": "Verified 2026-09-24: dataset access remains active, the complete usable HRNet aggregate, official missing-skeleton list, one-shot definition, and MotionBERT checkpoint are readable and checksummed, and the required inputs and setup are verified on the GPU host. The aggregate contains 113,945 usable annotations and all 20 official exemplars; the official 535-item missing-skeleton list accounts for the remaining nominal captures. This completes input acquisition and verification. The separate w01-gate-02 remains pending because the input-contract amendment is not yet adopted; the novel test remains sealed."
    }
  },
  {
    "table": "tasks",
    "id": "w01-task-04",
    "week_id": "week-01",
    "version": 3,
    "state": "done",
    "values": {
      "details": "Record researcher-controlled protocol decisions and the BU data-governance or human-subjects determination. Record unresolved conditions verbatim.",
      "expected_output": "Decision evidence or a visible blocking record.",
      "completion_note": "Researcher-authored scope statement recorded on 2026-09-15: the project performs computational model training and evaluation on existing licensed pose annotations. It involves no participant recruitment, interaction, intervention, prospective data collection, direct identifiers, re-identification, or animal work. Because the source poses were derived from recordings of people, the statement does not itself establish BU human-subjects/data-governance status. Unresolved condition (verbatim): 'BU provides the applicable human-subjects/data-governance determination.' The visible blocking record satisfies this task's required output; w01-gate-04 remains pending until BU issues the determination."
    }
  },
  {
    "table": "tasks",
    "id": "w01-task-05",
    "week_id": "week-01",
    "version": 3,
    "state": "blocked",
    "values": {
      "completion_note": "Verified input acquisition and remote setup are recorded in the Week 1 evidence. Final closeout remains blocked until researcher-supplied actual minutes, the documented input-contract amendment, and the BU governance determination are recorded. The amendment is not yet adopted; no decision, hours, or week closure is inferred."
    }
  },
  {
    "table": "gates",
    "id": "w01-gate-01",
    "week_id": "week-01",
    "version": 2,
    "state": "met",
    "values": {
      "criterion": "Protocol-v1 is documented under researcher control and its hash is recorded.",
      "evidence": "Independent research governance is recorded in docs/protocol/independent-research.md. Protocol SHA-256: 1b43d1bedb833f71936d0bc36d30a9b6f7ed6d2d00a5b8c8b781b787ad66d265."
    }
  },
  {
    "table": "gates",
    "id": "w01-gate-02",
    "week_id": "week-01",
    "version": 4,
    "state": "pending",
    "values": {
      "criterion": "Verified input inventory matches the recorded protocol input contract.",
      "evidence": "Verified 2026-09-24: the local and GPU-host inputs account for 113,945 usable HRNet annotations plus 535 official missing-skeleton exclusions, with readable, checksummed data and checkpoint inputs. See https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-1-remote-setup.md. The amendment at https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/input-contract-amendment-draft.md remains a draft that has not been adopted. This gate remains pending until a documented result-blind amendment binds the usable count and aggregate-plus-missing-list verification contract; the novel test remains sealed."
    }
  },
  {
    "table": "gates",
    "id": "w02-gate-01",
    "week_id": "week-02",
    "version": 2,
    "state": "pending",
    "values": {
      "evidence": "Seven release manifests are immutable and checksummed for the verified 113,945-sample usable aggregate. This gate remains pending until a documented, result-blind amendment binds both that usable count plus the official 535-record missing-skeleton list and aggregate-aware physical-source verification in place of 114,480 declared per-sample files. See https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/ntu-manifest-audit.v1.md."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-03",
    "week_id": "week-05",
    "version": 1,
    "state": "todo",
    "values": {
      "expected_output": "Reviewable corruption contact sheet and audit notes."
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "version": 1,
    "state": "pending",
    "values": {
      "criterion": "Corruptions-v1 is frozen with no amendment or a documented result-blind geometry-only amendment."
    }
  },
  {
    "table": "weeks",
    "id": "week-07",
    "week_id": "week-07",
    "version": 1,
    "state": "planned",
    "values": {
      "deliverable": "Frozen final configs, analysis plan, and protocol-lock hash.",
      "advisor_prompt": "Are the final hyperparameters, fixed epoch counts, paired seeds, analysis code, and decision to keep or cancel the stretch method documented and frozen?"
    }
  },
  {
    "table": "gates",
    "id": "w07-gate-02",
    "week_id": "week-07",
    "version": 1,
    "state": "pending",
    "values": {
      "criterion": "Final hashes, fairness audit, and analysis plan are recorded before test opening."
    }
  },
  {
    "table": "weeks",
    "id": "week-12",
    "week_id": "week-12",
    "version": 1,
    "state": "planned",
    "values": {
      "deliverable": "A successful fresh-clone reproduction, regenerated results, and a full report draft."
    }
  },
  {
    "table": "tasks",
    "id": "w12-task-04",
    "week_id": "week-12",
    "version": 1,
    "state": "todo",
    "values": {
      "expected_output": "Complete report draft archived with its evidence."
    }
  },
  {
    "table": "gates",
    "id": "w12-gate-03",
    "week_id": "week-12",
    "version": 1,
    "state": "pending",
    "values": {
      "criterion": "A complete report draft is recorded and reviewed against the evidence."
    }
  },
  {
    "table": "weeks",
    "id": "week-13",
    "week_id": "week-13",
    "version": 1,
    "state": "planned",
    "values": {
      "objective": "Resolve documented review findings and package the study so its question, evidence, limits, and reproduction path stand on their own.",
      "deliverable": "Final report, poster or slides, abstract, captions, source ledger, and reproducibility walkthrough."
    }
  },
  {
    "table": "tasks",
    "id": "w13-task-01",
    "week_id": "week-13",
    "version": 1,
    "state": "todo",
    "values": {
      "title": "Resolve documented review findings"
    }
  },
  {
    "table": "tasks",
    "id": "w13-task-02",
    "week_id": "week-13",
    "version": 1,
    "state": "todo",
    "values": {
      "expected_output": "Final publication-ready poster or slide deck."
    }
  },
  {
    "table": "tasks",
    "id": "w13-task-04",
    "week_id": "week-13",
    "version": 1,
    "state": "todo",
    "values": {
      "title": "Run the evidence walkthrough"
    }
  },
  {
    "table": "gates",
    "id": "w13-gate-02",
    "week_id": "week-13",
    "version": 1,
    "state": "pending",
    "values": {
      "criterion": "Documented review findings are resolved or explicitly deferred as future work."
    }
  }
]
$edits$::jsonb;
  edit jsonb;
  parent_id text;
  current_row jsonb;
  assignments text;
  changed_rows integer;
begin
  if not exists (select 1 from public.projects where id = 'pose-embed') then
    raise notice 'pose-embed is not seeded; the canonical plan supplies independent governance';
    return;
  end if;

  for parent_id in select distinct value->>'week_id' from jsonb_array_elements(edits)
  loop
    select to_jsonb(w) into current_row from public.weeks w
     where id = parent_id and project_id = 'pose-embed' for update;
    if current_row is null then
      raise exception using errcode = '40001', message = parent_id || ' is missing';
    end if;
    if current_row->>'state' = 'closed' or current_row->>'closed_at' is not null then
      raise exception using errcode = '40001',
        message = parent_id || ' is closed; an audited reopen is required';
    end if;
  end loop;

  for edit in select value from jsonb_array_elements(edits)
  loop
    -- Table and column identifiers come only from this fixed migration payload.
    if edit->>'table' not in ('weeks', 'tasks', 'gates') then
      raise exception 'Unexpected migration table';
    end if;
    execute format('select to_jsonb(t) from public.%I t where id = $1 and project_id = $2 for update', edit->>'table')
      into current_row using edit->>'id', 'pose-embed';
    if current_row is null or
       (edit->>'table' <> 'weeks' and current_row->>'week_id' <> edit->>'week_id') then
      raise exception using errcode = '40001', message = edit->>'id' || ' is missing or moved';
    end if;
    if (current_row->>'version')::integer = (edit->>'version')::integer + 1
       and current_row->>'state' = edit->>'state'
       and current_row @> (edit->'values') then
      continue;
    end if;
    if (current_row->>'version')::integer <> (edit->>'version')::integer
       or current_row->>'state' <> edit->>'state' then
      raise exception using errcode = '40001',
        message = edit->>'id' || ' changed; refusing to overwrite live progress';
    end if;
    select string_agg(format('%I = v.%I', key, key), ', ' order by key)
      into assignments from jsonb_object_keys(edit->'values') key;
    execute format('update public.%I t set %s from jsonb_populate_record(null::public.%I, $1) v where t.id = $2 and t.project_id = $3 and t.version = $4',
      edit->>'table', assignments, edit->>'table')
      using edit->'values', edit->>'id', 'pose-embed', (edit->>'version')::integer;
    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 then
      raise exception using errcode = '40001', message = edit->>'id' || ' could not be updated';
    end if;
  end loop;
end
$migration$;
