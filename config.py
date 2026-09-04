"""
Carenova Application Configuration.
All settings loaded from environment variables.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    app_env: str = "development"
    app_port: int = 8004
    app_secret_key: str = "dev_secret_change_in_production"
    log_level: str = "info"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/carenova"
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379/4"

    # Auth — Clerk
    clerk_secret_key: str = ""
    clerk_webhook_secret: str = ""

    # Billing — LemonSqueezy
    lemonsqueezy_api_key: str = ""
    lemonsqueezy_store_id: str = "247127"
    lemonsqueezy_webhook_secret: str = ""

    # Billing — Paystack (Nigeria)
    paystack_secret_key: str = ""
    paystack_webhook_secret: str = ""
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_enterprise_price_id: str = ""

    # Email — Resend
    resend_api_key: str = ""
    resend_from_email: str = "hello@carenova.ai"

    # Voice — Retell AI
    retell_api_key: str = ""
    retell_phone_number: str = ""
    retell_webhook_secret: str = ""

    # WhatsApp (Nigeria)
    whatsapp_business_api_token: str = ""
    whatsapp_phone_number_id: str = ""

    # EHR — athenahealth
    athena_client_id: str = ""
    athena_client_secret: str = ""
    athena_practice_id: str = ""
    athena_base_url: str = "https://api.preview.platform.athenahealth.com"

    # LLM
    anthropic_api_key: str = ""
    groq_api_key: str = ""

    # Storage — Cloudflare R2
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_audio: str = "carenova-audio"
    r2_bucket_docs: str = "carenova-docs"

    # Memory — Graphiti
    graphiti_url: str = "http://localhost:8005"
    falkordb_url: str = "redis://localhost:6379"

    # Ecosystem Bridges
    fusionops_url: str = "http://13.50.16.19:8080"
    fusionops_api_key: str = ""
    ai_shield_url: str = "http://13.50.16.19:8002"
    ai_shield_api_key: str = ""
    threatfade_url: str = "http://13.50.16.19:8000"
    threatfade_api_key: str = ""
    resilientai_url: str = "http://13.50.16.19:8003"
    resilientai_api_key: str = ""
    fadereach_url: str = ""
    fadereach_api_key: str = ""

    # Monitoring
    posthog_api_key: str = ""
    sentry_dsn: str = ""


    # Insurance APIs
    availity_client_id: str = ""
    availity_client_secret: str = ""
    change_healthcare_api_key: str = ""

    # EHR — Epic SMART on FHIR (Phase 2)
    epic_client_id: str = ""
    epic_sandbox_base_url: str = "https://fhir.epic.com/interconnect-fhir-oauth"

    # Ecosystem Bridges — Tier 2
    hezcast_url: str = ""
    hezcast_api_key: str = ""
    kalevioai_url: str = "https://kalevio.tinlance.com"
    kalevioai_api_key: str = ""
    olvrix_url: str = ""
    olvrix_api_key: str = ""
    resonaforge_url: str = ""
    resonaforge_api_key: str = ""
    voquo_url: str = ""
    voquo_api_key: str = ""
    bugflow_url: str = ""
    bugflow_api_key: str = ""
    twinguard_url: str = ""
    twinguard_api_key: str = ""
    reconos_url: str = ""
    reconos_api_key: str = ""

    # Storage — Cloudflare R2
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_audio: str = "carenova-audio"
    r2_bucket_docs: str = "carenova-docs"

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()
