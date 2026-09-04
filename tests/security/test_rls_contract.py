from pathlib import Path

MIGRATION=Path(__file__).parents[2]/"supabase"/"migrations"/"015_harden_tenant_rls.sql"
TABLES=("patients","appointments","calls","insurance","prior_auth","refills","referrals","recalls","documents","audit_log")

def test_tenant_rls_migration_covers_all_core_tables():
    sql=MIGRATION.read_text(encoding="utf-8")
    assert "FORCE ROW LEVEL SECURITY" in sql
    assert "current_setting(''app.clerk_org_id'',true)" in sql
    for table in TABLES: assert f"public.%I" in sql and table in sql

def test_update_policy_has_using_and_with_check():
    sql=MIGRATION.read_text(encoding="utf-8")
    assert "FOR UPDATE TO authenticated USING" in sql
    assert "WITH CHECK" in sql
