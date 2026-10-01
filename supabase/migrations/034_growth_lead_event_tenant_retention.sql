-- Keep the event tenant anchor when its referenced lead is removed.
-- A composite SET NULL would also null clinic_id, making the event disappear
-- from its tenant and destroying its ownership boundary.
DO $$
BEGIN
  IF to_regclass('public.growth_campaign_events') IS NOT NULL THEN
    ALTER TABLE public.growth_campaign_events DROP CONSTRAINT IF EXISTS growth_events_clinic_lead_key;
    IF to_regclass('public.growth_leads') IS NOT NULL THEN
      ALTER TABLE public.growth_campaign_events
        ADD CONSTRAINT growth_events_clinic_lead_key
        FOREIGN KEY (clinic_id,lead_id)
        REFERENCES public.growth_leads(clinic_id,id)
        ON DELETE RESTRICT;
    END IF;
  END IF;
END $$;
