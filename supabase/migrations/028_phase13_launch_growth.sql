-- Phase 13: launch, growth, onboarding, and acquisition primitives.
create table if not exists onboarding_checklist (
  clinic_id text not null references clinics(id) on delete cascade,
  step text not null,
  status text not null default 'pending' check (status in ('pending','completed','skipped')),
  completed_at timestamptz,
  completed_by text,
  primary key (clinic_id,step)
);
create table if not exists growth_leads (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  clinic_name text,
  source text not null default 'direct',
  campaign text,
  status text not null default 'new' check (status in ('new','qualified','contacted','demo','pilot','won','lost','unsubscribed')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create table if not exists growth_referrals (
  id uuid primary key default gen_random_uuid(),
  referrer_clinic_id text not null references clinics(id) on delete cascade,
  referred_email text not null,
  status text not null default 'created' check (status in ('created','qualified','converted','expired')),
  converted_clinic_id text references clinics(id) on delete set null,
  created_at timestamptz not null default now(),
  unique(referrer_clinic_id,referred_email)
);
create table if not exists growth_campaign_events (
  id uuid primary key default gen_random_uuid(),
  clinic_id text references clinics(id) on delete cascade,
  lead_id uuid references growth_leads(id) on delete set null,
  event_type text not null,
  source text,
  campaign text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists growth_campaign_events_time on growth_campaign_events(created_at desc);
do $$ declare t text; begin
  foreach t in array array['onboarding_checklist','growth_leads','growth_referrals','growth_campaign_events'] loop
    execute format('alter table %I enable row level security',t);
    execute format('alter table %I force row level security',t);
    execute format('grant select,insert,update,delete on %I to authenticated',t);
  end loop;
end $$;
create policy onboarding_tenant on onboarding_checklist using (clinic_id=current_setting('app.clerk_org_id',true)) with check (clinic_id=current_setting('app.clerk_org_id',true));
create policy growth_leads_tenant on growth_leads using (exists(select 1 from clinics c where c.id=current_setting('app.clerk_org_id',true))) with check (exists(select 1 from clinics c where c.id=current_setting('app.clerk_org_id',true)));
create policy growth_referrals_tenant on growth_referrals using (referrer_clinic_id=current_setting('app.clerk_org_id',true) or converted_clinic_id=current_setting('app.clerk_org_id',true)) with check (referrer_clinic_id=current_setting('app.clerk_org_id',true));
create policy growth_events_tenant on growth_campaign_events using (clinic_id=current_setting('app.clerk_org_id',true)) with check (clinic_id=current_setting('app.clerk_org_id',true));
