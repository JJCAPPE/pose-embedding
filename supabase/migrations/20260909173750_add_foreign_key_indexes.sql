-- Cover the referencing columns in their declared foreign-key order.
-- PostgreSQL does not create these indexes automatically; they keep joins and
-- cascading deletes bounded as tracker history grows.

create index gates_week_project_fk_idx
  on public.gates (week_id, project_id);

create index tasks_week_project_fk_idx
  on public.tasks (week_id, project_id);

create index week_sources_source_project_fk_idx
  on public.week_sources (source_id, project_id);

create index week_sources_week_project_fk_idx
  on public.week_sources (week_id, project_id);
