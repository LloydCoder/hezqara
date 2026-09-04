"""Application configuration.

All secrets are supplied through environment variables. No production secret
has a code-level fallback.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_port: int = 8004
    app_secret_key: str = ""
    log_level: str = "info"

    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/hezqara"
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    redis_url: str = "redis://localhost:6379/0"

    clerk_secret_key: str = ""
    clerk_webhook_secret: str = ""

    lemonsqueezy_api_key: str = ""
    lemonsqueezy_store_id: str = "247127"
    lemonsqueezy_webhook_secret: str = ""
    paystack_secret_key: str = ""
    paystack_webhook_secret: str = ""
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_enterprise_price_id: str = ""

    resend_api_key: str = ""
    resend_from_email: str = ""

    retell_api_key: str = ""
    retell_phone_number: str = ""
    retell_webhook_secret: str = ""

    whatsapp_business_api_token: str = ""
    whatsapp_phone_number_id: str = ""

    athena_client_id: str = ""
    athena_client_secret: str = ""
    athena_practice_id: str = ""
    athena_base_url: str = "https://api.preview.platform.athenahealth.com"
    epic_client_id: str = ""
    epic_sandbox_base_url: str = "https://fhir.epic.com/interconnect-fhir-oauth"

    anthropic_api_key: str = ""
    groq_api_key: str = ""

    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_audio: str = "hezqara-audio"
    r2_bucket_docs: str = "hezqara-docs"

    graphiti_url: str = "http://localhost:8005"
    falkordb_url: str = "redis://localhost:6379"

    fusionops_url: str = ""
    fusionops_api_key: str = ""
    ai_shield_url: str = ""
    ai_shield_api_key: str = ""
    threatfade_url: str = ""
    threatfade_api_key: str = ""
    resilientai_url: str = ""
    resilientai_api_key: str = ""
    fadereach_url: str = ""
    fadereach_api_key: str = ""
    hezcast_url: str = ""
    hezcast_api_key: str = ""
    kalevioai_url: str = ""
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

    availity_client_id: str = ""
    availity_client_secret: str = ""
    change_healthcare_api_key: str = ""

    posthog_api_key: str = ""
    sentry_dsn: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
