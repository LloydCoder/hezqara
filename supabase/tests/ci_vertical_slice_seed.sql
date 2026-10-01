INSERT INTO clinics(id,name,clerk_org_id)
VALUES ('ci-test-clinic','CI Test Clinic','test_org')
ON CONFLICT (id) DO UPDATE SET clerk_org_id=EXCLUDED.clerk_org_id,name=EXCLUDED.name;

INSERT INTO ai_capabilities (
  id,clinic_id,name,description,domain,owner,status,risk_tier,phi_classification,
  allowed_data_classes,allowed_actions,prohibited_actions,approval_required,escalation_required
) VALUES (
  'message_classification','ci-test-clinic','Message Classification',
  'Deterministic CI capability for governed operational message classification.',
  'patient_engagement','ci','active',0,'operational',
  '["operational"]'::jsonb,'["classify_message"]'::jsonb,'[]'::jsonb,false,false
) ON CONFLICT (clinic_id,id) DO UPDATE SET status='active',risk_tier=0,
  allowed_data_classes='["operational"]'::jsonb,allowed_actions='["classify_message"]'::jsonb,
  prohibited_actions='[]'::jsonb,approval_required=false,escalation_required=false;

INSERT INTO ai_capability_versions (
  clinic_id,capability_id,version,prompt_version,system_instruction_version,
  tool_policy_version,output_schema_version,model_provider,model_version,
  evaluation_suite_version,max_output_tokens,max_tool_calls,max_retries,
  quality_threshold,safety_threshold,allowed_tools,status
) VALUES (
  'ci-test-clinic','message_classification','ci-1','ci-prompt-1','ci-system-1',
  'ci-tools-1','ci-output-1',NULL,NULL,NULL,1024,0,0,0.8000,1.0000,
  '[]'::jsonb,'active'
) ON CONFLICT (clinic_id,capability_id,version) DO UPDATE SET status='active',allowed_tools='[]'::jsonb;

INSERT INTO ai_policy_versions (clinic_id,version,rules,status)
VALUES (
  'ci-test-clinic','ci-policy-1',
  '{"allowed_data_classes":["operational"],"allowed_tools":[],"prohibited_actions":[],"approval_required":false}'::jsonb,
  'active'
) ON CONFLICT (clinic_id,version) DO UPDATE SET status='active',rules=EXCLUDED.rules;

INSERT INTO ai_control_state (clinic_id,ai_enabled,force_human_approval,force_deterministic_fallback,tool_access_enabled)
VALUES ('ci-test-clinic',true,false,true,true)
ON CONFLICT (clinic_id) DO UPDATE SET ai_enabled=true,force_human_approval=false,force_deterministic_fallback=true,tool_access_enabled=true;
