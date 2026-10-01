-- Phase 11: multi-clinic scale and usage controls.
create table if not exists tenant_limits (
  clinic_id text primary key references clinics(id) on delete cascade,
  plan_code text not null default 'starter',
  monthly_executions bigint not null default 1000,
  monthly_voice_minutes bigint not null default 500,
  monthly_messages bigint not null default 5000,
  max_users integer not null default 5,
  max_locations integer not null default 1,
  updated_at timestamptz not null default now()
);
create table if not exists platform_usage_daily (
  clinic_id text not null references clinics(id) on delete cascade,
  usage_date date not null,
  metric text not null,
  quantity bigint not null default 0 check (quantity >= 0),
  primary key (clinic_id,usage_date,metric)
);
create table if not exists platform_jobs (
  id uuid primary key default gen_random_uuid(),
  clinic_id text not null references clinics(id) on delete cascade,
  job_type text not null,
  idempotency_key text not null,
  status text not null default 'queued' check (status in ('queued','running','completed','failed','cancelled')),
  attempts integer not null default 0 check (attempts >= 0),
  payload jsonb not null default '{}'::jsonb,
  last_error text,
  available_at timestamptz not null default now(),
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(clinic_id,idempotency_key)
);
create index if not exists platform_jobs_queue on platform_jobs(status,available_at);
create index if not exists platform_usage_month on platform_usage_daily(clinic_id,usage_date,metric);
do $$ declare t text; begin
  foreach t in array array['tenant_limits','platform_usage_daily','platform_jobs'] loop
    execute format('alter table %I enable row level security',t);
    execute format('alter table %I force row level security',t);
    execute format('grant select,insert,update,delete on %I to authenticated',t);
  end loop;
end $$;
create policy tenant_limits_tenant on tenant_limits using (clinic_id=current_setting('app.clerk_org_id',true)) with check (clinic_id=current_setting('app.clerk_org_id',true));
create policy platform_usage_daily_tenant on platform_usage_daily using (clinic_id=current_setting('app.clerk_org_id',true)) with check (clinic_id=current_setting('app.clerk_org_id',true));
create policy platform_jobs_tenant on platform_jobs using (clinic_id=current_setting('app.clerk_org_id',true)) with check (clinic_id=current_setting('app.clerk_org_id',true));
