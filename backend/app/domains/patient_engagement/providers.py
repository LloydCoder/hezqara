from app.core.config import settings
from app.domains.patient_engagement.service import CommunicationProvider, DeterministicTestProvider, WhatsAppCloudProvider

def build_communication_provider() -> CommunicationProvider:
    if settings.app_env == 'test': return DeterministicTestProvider()
    if settings.whatsapp_business_api_token and settings.whatsapp_phone_number_id: return WhatsAppCloudProvider(settings.whatsapp_business_api_token,settings.whatsapp_phone_number_id)
    return CommunicationProvider()
