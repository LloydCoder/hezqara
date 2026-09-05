from dataclasses import dataclass
from app.integrations.core.contracts import IntegrationCapabilities, IntegrationHealth, IntegrationResponse

@dataclass
class TestFHIRProvider:
    name:str='test-fhir'; version:str='R4'; capabilities:IntegrationCapabilities=IntegrationCapabilities(fhir=True,webhooks=True,resources=('Patient','Organization','Practitioner','PractitionerRole','Appointment','Coverage','Account','Claim','ClaimResponse','CoverageEligibilityRequest','CoverageEligibilityResponse','ExplanationOfBenefit','Task','Communication','ServiceRequest','DocumentReference'))
    async def health(self)->IntegrationHealth: return IntegrationHealth('healthy')
    async def get(self,resource_type:str,resource_id:str,request_id:str)->IntegrationResponse:
        if resource_type not in self.capabilities.resources: raise ValueError('unsupported_capability')
        return IntegrationResponse({'resourceType':resource_type,'id':resource_id},self.name,request_id,external_reference=resource_id)

@dataclass
class TestEligibilityProvider:
    name:str='test-eligibility'; version:str='test-v1'; capabilities:IntegrationCapabilities=IntegrationCapabilities(eligibility=True)
    async def health(self)->IntegrationHealth: return IntegrationHealth('healthy')
    async def check(self,member_id:str,request_id:str)->IntegrationResponse:
        if not member_id: raise ValueError('validation_error')
        return IntegrationResponse({'status':'eligible','member_id':member_id},self.name,request_id,external_reference=f'test-eligibility:{member_id}')

@dataclass
class TestEHRProvider:
    name:str='test-ehr'; version:str='test-v1'; capabilities:IntegrationCapabilities=IntegrationCapabilities(fhir=True,resources=('Patient','Coverage','Appointment','DocumentReference'))
    async def health(self)->IntegrationHealth: return IntegrationHealth('healthy')
    async def search_patient(self,query:str,request_id:str)->IntegrationResponse:
        return IntegrationResponse({'resourceType':'Bundle','type':'searchset','entry':[{'resource':{'resourceType':'Patient','id':'test-patient','name':[{'family':'Test','given':['Patient']}],'identifier':[{'value':query}]}}]},self.name,request_id,external_reference='test-patient')

@dataclass
class TestClaimsProvider:
    name:str='test-clearinghouse'; version:str='test-v1'; capabilities:IntegrationCapabilities=IntegrationCapabilities(claims=True,webhooks=True)
    async def health(self)->IntegrationHealth: return IntegrationHealth('healthy')
    async def submit(self,claim_id:str,request_id:str)->IntegrationResponse: return IntegrationResponse({'acknowledgement_status':'accepted','claim_id':claim_id},self.name,request_id,external_reference=f'TEST-CLAIM-{claim_id}')

@dataclass
class TestAuthorizationProvider:
    name:str='test-authorization'; version:str='test-v1'; capabilities:IntegrationCapabilities=IntegrationCapabilities(prior_authorization=True,webhooks=True)
    async def health(self)->IntegrationHealth: return IntegrationHealth('healthy')
    async def submit(self,authorization_id:str,request_id:str)->IntegrationResponse: return IntegrationResponse({'status':'pending','authorization_id':authorization_id},self.name,request_id,external_reference=f'TEST-AUTH-{authorization_id}')

@dataclass
class TestPaymentProvider:
    name:str='test-payment'; version:str='test-v1'; capabilities:IntegrationCapabilities=IntegrationCapabilities(payments=True)
    async def health(self)->IntegrationHealth: return IntegrationHealth('healthy')

@dataclass
class TestMessagingProvider:
    name:str='test-messaging'; version:str='test-v1'; capabilities:IntegrationCapabilities=IntegrationCapabilities(messaging=True)
    async def health(self)->IntegrationHealth: return IntegrationHealth('healthy')
