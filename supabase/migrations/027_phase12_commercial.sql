-- Phase 12: commercial productization.
create table if not exists subscriptions (
  clinic_id text primary key references clinics(id) on delete cascade,
  plan_code text not null default 'starter',
  status text not null default 'trialing' check (status in ('trialing','active','past_due','paused','cancelled')),
  provider text,
  provider_customer_id text,
  provider_subscription_id text,
  current_period_start timestamptz,
  current_period_end timestamptz,
  cancel_at_period_end boolean not null default false,
  updated_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);
create table if not exists platform_events (
  id uuid primary key default gen_random_uuid(),
  clinic_id text not null references clinics(id) on delete cascade,
  event_type text not null,
  actor_id text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists platform_events_tenant_time on platform_events(clinic_id,created_at desc);
do $$ declare t text; begin
  foreach t in array array['subscriptions','platform_events'] loop
    execute format('alter table %I enable row level security',t);
    execute format('alter table %I force row level security',t);
    execute format('grant select,insert,update,delete on %I to authenticated',t);
  end loop;
end $$;
create policy subscriptions_tenant on subscriptions using (clinic_id=current_setting('app.clerk_org_id',true)) with check (clinic_id=current_setting('app.clerk_org_id',true));
create policy platform_events_tenant on platform_events using (clinic_id=current_setting('app.clerk_org_id',true)) with check (clinic_id=current_setting('app.clerk_org_id',true));
