INSERT INTO clinics(id,name,clerk_org_id)
VALUES ('ci-test-clinic','CI Test Clinic','test_org')
ON CONFLICT (id) DO UPDATE SET clerk_org_id=EXCLUDED.clerk_org_id,name=EXCLUDED.name;
