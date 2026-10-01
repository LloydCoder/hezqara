-- Phase 10: production/enterprise hardening primitives.
create table if not exists platform_settings (
  clinic_id text primary key references clinics(id) on delete cascade,
  retention_days integer not null default 365 check (retention_days between 30 and 3650),
  require_request_id boolean not null default true,
  allow_cross_origin boolean not null default false,
  maintenance_mode boolean not null default false,
  updated_by text,
  updated_at timestamptz not null default now()
);
create table if not exists platform_health_checks (
  id bigserial primary key,
  clinic_id text not null references clinics(id) on delete cascade,
  component text not null,
  status text not null check (status in ('healthy','degraded','unavailable')),
  latency_ms integer,
  detail text,
  checked_at timestamptz not null default now()
);
create table if not exists platform_security_events (
  id bigserial primary key,
  clinic_id text not null references clinics(id) on delete cascade,
  event_type text not null,
  severity text not null check (severity in ('info','low','medium','high','critical')),
  actor_id text,
  request_id text,
  detail jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists platform_health_checks_tenant_time on platform_health_checks(clinic_id,checked_at desc);
create index if not exists platform_security_events_tenant_time on platform_security_events(clinic_id,created_at desc);

do $$ declare t text; begin
  foreach t in array array['platform_settings','platform_health_checks','platform_security_events'] loop
    execute format('alter table %I enable row level security',t);
    execute format('alter table %I force row level security',t);
    execute format('grant select,insert,update,delete on %I to authenticated',t);
  end loop;
end $$;
create policy platform_settings_tenant on platform_settings using (clinic_id=current_setting('app.clerk_org_id',true)) with check (clinic_id=current_setting('app.clerk_org_id',true));
create policy platform_health_checks_tenant on platform_health_checks using (clinic_id=current_setting('app.clerk_org_id',true)) with check (clinic_id=current_setting('app.clerk_org_id',true));
create policy platform_security_events_tenant on platform_security_events using (clinic_id=current_setting('app.clerk_org_id',true)) with check (clinic_id=current_setting('app.clerk_org_id',true));
grant usage,select on sequence platform_health_checks_id_seq to authenticated;
grant usage,select on sequence platform_security_events_id_seq to authenticated;
