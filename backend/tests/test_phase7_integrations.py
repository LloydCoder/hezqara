import asyncio
from app.integrations.testing.providers import TestAuthorizationProvider, TestClaimsProvider, TestEHRProvider, TestEligibilityProvider, TestFHIRProvider, TestMessagingProvider, TestPaymentProvider


def test_provider_contract_matrix_is_deterministic():
    providers=[TestFHIRProvider(),TestEHRProvider(),TestEligibilityProvider(),TestAuthorizationProvider(),TestClaimsProvider(),TestPaymentProvider(),TestMessagingProvider()]
    async def run():
        for provider in providers:
            health=await provider.health()
            assert health.state=='healthy'
        ehr=await providers[1].search_patient('member-1','request-1')
        eligibility=await providers[2].check('member-1','request-2')
        claim=await providers[4].submit('claim-1','request-3')
        auth=await providers[3].submit('auth-1','request-4')
        assert ehr.data['resourceType']=='Bundle'
        assert eligibility.data['status']=='eligible'
        assert claim.data['acknowledgement_status']=='accepted'
        assert auth.data['status']=='pending'
    asyncio.run(run())
