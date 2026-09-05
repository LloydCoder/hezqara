-- Phase 3 RLS contract test. Runs as a non-superuser RLS role inside one explicit transaction.
INSERT INTO clinics(id,name,clerk_org_id) VALUES ('clinic-a','Synthetic A','org-a'),('clinic-b','Synthetic B','org-b');
BEGIN;
SET LOCAL ROLE authenticated;
SET LOCAL app.clerk_org_id='org-a';
INSERT INTO patients(clinic_id,first_name,last_name) VALUES ('clinic-a','Synthetic','Patient A');
INSERT INTO tasks(clinic_id,title) VALUES ('clinic-a','Tenant A task');
DO $$ BEGIN IF (SELECT count(*) FROM patients)<>1 OR (SELECT max(last_name) FROM patients)<>'Patient A' THEN RAISE EXCEPTION 'tenant A patient isolation failed'; END IF; IF (SELECT count(*) FROM tasks)<>1 THEN RAISE EXCEPTION 'tenant A task isolation failed'; END IF; END $$;
SET LOCAL app.clerk_org_id='org-b';
INSERT INTO patients(clinic_id,first_name,last_name) VALUES ('clinic-b','Synthetic','Patient B');
INSERT INTO tasks(clinic_id,title) VALUES ('clinic-b','Tenant B task');
DO $$ BEGIN IF (SELECT count(*) FROM patients)<>1 OR (SELECT max(last_name) FROM patients)<>'Patient B' THEN RAISE EXCEPTION 'tenant B patient isolation failed'; END IF; IF (SELECT count(*) FROM tasks)<>1 THEN RAISE EXCEPTION 'tenant B task isolation failed'; END IF; END $$;
SET LOCAL app.clerk_org_id='org-a';
UPDATE patients SET last_name='Tampered' WHERE clinic_id='clinic-b';
UPDATE tasks SET title='Tampered' WHERE clinic_id='clinic-b';
SET LOCAL app.clerk_org_id='org-b';
DO $$ BEGIN IF (SELECT max(last_name) FROM patients)<>'Patient B' THEN RAISE EXCEPTION 'cross-tenant patient mutation succeeded'; END IF; IF (SELECT max(title) FROM tasks)<>'Tenant B task' THEN RAISE EXCEPTION 'cross-tenant task mutation succeeded'; END IF; END $$;
COMMIT;
