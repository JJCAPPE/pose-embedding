begin;

select private.import_research_plan(:'plan_json'::jsonb);

select private.assign_project_owner(
  (:'plan_json'::jsonb #>> '{project,slug}'),
  :'owner_email'
)
where nullif(:'owner_email', '') is not null;

commit;
