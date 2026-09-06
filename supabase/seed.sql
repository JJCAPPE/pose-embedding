-- A normal `supabase db reset` intentionally leaves the tracker empty. This
-- avoids committing an owner UUID or maintaining a second copy of
-- plan/research-plan.v1.json. Run supabase/scripts/seed_plan.sh after reset.
do $$
begin
  raise notice 'Tracker seed skipped; run supabase/scripts/seed_plan.sh to import the versioned plan.';
end
$$;
