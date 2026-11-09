-- Record independently accepted measurement and its capacity blocker; Week 5 stays open.
do $migration$
declare
  edits constant jsonb := $edits$[
  {
    "table": "weeks",
    "id": "week-05",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "week-05",
      "version": 55,
      "state": "active",
      "closed_at": null
    },
    "values": {
      "reflection": "November 9: Admission-cost measurement 8539455 passed independent review, but its necessary calendar forecast fails. At the measured profile, repeated validation alone needs 2,225.815 hours with 25% slack versus the entire 168-hour November 30\u2013December 6 interval. Accepted baselines, caches, paired pilots, development execution and resident timing remain preserved. A result-blind researcher decision is required before further admission work. Week 5 stays open; selection runs, final training and novel opening remain closed. Actual researcher time remains unreported."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-02",
      "version": 52,
      "state": "in_progress"
    },
    "values": {
      "completion_note": "IN PROGRESS, November 9: Measurement 8539455 passed independent operational and semantic review: three commands, 167 operation resource records, runtime gate, four seals and exact first/reuse/fresh proof counters 42/24, 0/66, 42/24. First, reused and fresh validation prefixes took 3263.363, 3087.310 and 3223.896 seconds; the job took 9712 seconds. The intended reuse occurred, but the necessary calendar bound fails. Full admission and independent recertification remain held; this is measurement acceptance, not campaign admission. Earlier accepted evidence and all storage safeguards are preserved."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-04",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-task-04",
      "version": 28,
      "state": "blocked"
    },
    "values": {
      "completion_note": "BLOCKED, November 9: The independently reviewed admission-cost measurement fails the necessary fixed-calendar condition: 2225.815 forecast hours with 25% slack versus 168 hours, before omitted work. Task 04 remains blocked. Recommend a result-blind engineering amendment for an immutable successor that reduces redundant deterministic validation while preserving full first checks, complete content rehash on reuse, fresh dynamic guards and independent command recertification. This remedy is proposed, not authorized or tested. No further SCC job will be submitted pending a researcher decision. November 29 locks, December 6 compute, December 7\u201318 delivery, 200 GiB reserve and 25% margin remain binding.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-9-measured-capacity-blocker"
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "operation": "update",
    "before": {
      "id": "w05-gate-03",
      "version": 33,
      "state": "pending"
    },
    "values": {
      "evidence": "UNRESOLVED, November 9: Accepted measurement 8539455 establishes a measured-profile capacity no-go. With C=3263.363371 seconds and R=3087.310327 seconds, the source-derived necessary prefix cost is 392C+1662R: 2225.815 hours with 25% slack versus 168 available, excluding remaining evaluation/reporting work and queue/setup. Even zero-cost reuse leaves 444.180 hours. No full admission, capacity pass or selection authorization exists. A result-blind researcher decision is required; all deadlines and safeguards remain unchanged. Evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-5-execution.md#november-9-measured-capacity-blocker"
    }
  }
]$edits$::jsonb;

  edit jsonb;
  current_row jsonb;
  expected_row jsonb;
  assignments text;
  changed_rows integer;
  expected_version integer;
  parent_id text;
begin
  if not exists (select 1 from public.projects where id = 'pose-embed') then
    raise notice 'pose-embed is not seeded; import research-plan.v3.json';
    return;
  end if;
  if not exists (select 1 from public.weeks where id = 'week-04' and project_id = 'pose-embed' and state = 'closed') then
    raise exception using errcode = '40001', message = 'Week 4 must be closed before starting Week 5';
  end if;
  for parent_id in
    select distinct value->>'week_id' from jsonb_array_elements(edits)
    where value->>'week_id' is not null order by 1
  loop
    if parent_id < 'week-05' then raise exception 'Historical week change forbidden'; end if;
    select to_jsonb(w) into current_row from public.weeks w
      where id = parent_id and project_id = 'pose-embed' for update;
    if current_row is null or current_row->>'state' = 'closed'
       or current_row->>'closed_at' is not null then
      raise exception using errcode = '40001',
        message = parent_id || ' is missing or closed; an audited reopen is required';
    end if;
  end loop;
  for edit in select value from jsonb_array_elements(edits)
  loop
    if edit->>'table' not in ('weeks', 'tasks', 'gates')
       or edit->>'operation' <> 'update' or edit->'values' ? 'version' then
      raise exception 'Unexpected amendment scope';
    end if;
    execute format('select to_jsonb(t) from public.%I t where id = $1 and project_id = ''pose-embed'' for update', edit->>'table')
      into current_row using edit->>'id';
    expected_version := (edit->'before'->>'version')::integer;
    expected_row := edit->'before' || edit->'values'
      || jsonb_build_object('version', expected_version + 1);
    if current_row @> expected_row then continue; end if;
    if current_row is null or not (current_row @> (edit->'before')) then
      raise exception using errcode = '40001',
        message = edit->>'id' || ' changed; refusing to overwrite live progress';
    end if;
    select string_agg(format('%I = v.%I', key, key), ', ' order by key)
      into assignments from jsonb_object_keys(edit->'values') key;
    execute format('update public.%I t set %s from jsonb_populate_record(null::public.%I, $1) v where t.id = $2 and t.project_id = ''pose-embed'' and t.version = $3 returning to_jsonb(t)',
      edit->>'table', assignments, edit->>'table')
      into current_row using edit->'values', edit->>'id', expected_version;
    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 or not (current_row @> expected_row) then
      raise exception using errcode = '40001', message = edit->>'id' || ' could not be updated';
    end if;
  end loop;
end
$migration$;
