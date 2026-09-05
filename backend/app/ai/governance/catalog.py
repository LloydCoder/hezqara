from app.ai.governance.contracts import RiskTier

RISK_BY_CAPABILITY={
 'reception':RiskTier.ADMINISTRATIVE,'scheduling':RiskTier.OPERATIONAL,'intake':RiskTier.ADMINISTRATIVE,
 'insurance':RiskTier.HIGH_IMPACT_ADMIN,'prior_authorization':RiskTier.HIGH_IMPACT_ADMIN,'refill':RiskTier.CLINICAL_HIGH_IMPACT,
 'records':RiskTier.OPERATIONAL,'referrals':RiskTier.HIGH_IMPACT_ADMIN,'recall':RiskTier.ADMINISTRATIVE,'email':RiskTier.ADMINISTRATIVE,
 'revenue_cycle':RiskTier.HIGH_IMPACT_ADMIN,'insurance_administrative':RiskTier.HIGH_IMPACT_ADMIN,'referral_records':RiskTier.HIGH_IMPACT_ADMIN,
}

def risk_for(capability_id:str)->RiskTier:return RISK_BY_CAPABILITY.get(capability_id,RiskTier.ADMINISTRATIVE)
