class PatientEngagementService:
    def __init__(self,messaging): self.messaging=messaging
    async def send(self,tenant_id:str,patient_id:str,channel:str,message:str):
        if channel not in {"sms","email","whatsapp"}: raise ValueError("unsupported channel")
        return await self.messaging.send(tenant_id=tenant_id,patient_id=patient_id,channel=channel,message=message)
