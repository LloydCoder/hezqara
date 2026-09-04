"""Runtime configuration; secrets are environment-only and never committed."""
from pydantic import Field
from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    app_env:str='development'; app_port:int=8004; log_level:str='info'; database_url:str=''
    db_pool_size:int=Field(default=10,ge=1,le=100); db_max_overflow:int=Field(default=20,ge=0,le=200)
    clerk_secret_key:str=''; clerk_publishable_key:str=''; clerk_jwt_key:str=''; clerk_authorized_parties:str=''; clerk_webhook_secret:str=''
    redis_url:str='redis://localhost:6379/0'
    stripe_secret_key:str=''; stripe_webhook_secret:str=''; retell_api_key:str=''; retell_webhook_secret:str=''; whatsapp_webhook_secret:str=''; whatsapp_business_api_token:str=''; whatsapp_phone_number_id:str=''
    anthropic_api_key:str=''; openai_api_key:str=''; ai_provider:str='anthropic'; ai_model:str='claude-3-5-sonnet-latest'; ai_timeout_seconds:float=Field(default=30.0,gt=0,le=120)
    model_config=SettingsConfigDict(env_file='.env',env_file_encoding='utf-8',case_sensitive=False,extra='ignore')
    @property
    def authorized_parties(self): return [x.strip() for x in self.clerk_authorized_parties.split(',') if x.strip()]
settings=Settings()
