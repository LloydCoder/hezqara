from dataclasses import dataclass
from typing import Any

FHIR_R4 = 'R4'
SUPPORTED_RESOURCES = frozenset({'Patient','Organization','Practitioner','PractitionerRole','Encounter','Appointment','Coverage','Account','Claim','ClaimResponse','CoverageEligibilityRequest','CoverageEligibilityResponse','ExplanationOfBenefit','Task','Communication','ServiceRequest','DocumentReference','Bundle','OperationOutcome'})
REQUIRED_FIELDS = {'Patient': ('resourceType',), 'Coverage': ('resourceType','status','beneficiary'), 'Claim': ('resourceType','status','patient'), 'ClaimResponse': ('resourceType','status','patient'), 'Bundle': ('resourceType','type'), 'OperationOutcome': ('resourceType','issue')}

@dataclass(frozen=True)
class FHIRMappingResult:
    resource_type: str
    resource: dict[str, Any]
    warnings: tuple[str, ...] = ()

class FHIRValidationError(ValueError): pass

class FHIRAdapter:
    """Small, explicit FHIR R4 boundary. It is not a certification/conformance claim."""
    version = FHIR_R4

    @staticmethod
    def validate(resource: dict[str, Any], expected: str | None = None) -> FHIRMappingResult:
        if not isinstance(resource, dict): raise FHIRValidationError('FHIR resource must be an object')
        resource_type = resource.get('resourceType')
        if not isinstance(resource_type, str): raise FHIRValidationError('resourceType is required')
        if expected and resource_type != expected: raise FHIRValidationError(f'expected FHIR {expected} resource')
        if resource_type not in SUPPORTED_RESOURCES: raise FHIRValidationError(f'unsupported FHIR resource: {resource_type}')
        missing = [field for field in REQUIRED_FIELDS.get(resource_type, ()) if field not in resource]
        if missing: raise FHIRValidationError(f'missing required field(s): {", ".join(missing)}')
        if 'id' in resource and not isinstance(resource['id'], str): raise FHIRValidationError('FHIR id must be a string')
        if resource_type=='Bundle' and not isinstance(resource.get('entry',[]),list): raise FHIRValidationError('FHIR Bundle.entry must be an array')
        if resource_type=='OperationOutcome' and (not isinstance(resource.get('issue'),list) or not resource['issue']): raise FHIRValidationError('FHIR OperationOutcome.issue must be a non-empty array')
        if 'meta' in resource and not isinstance(resource['meta'],dict): raise FHIRValidationError('FHIR meta must be an object')
        if 'meta' in resource and 'profile' in resource['meta'] and not isinstance(resource['meta']['profile'],list): raise FHIRValidationError('FHIR meta.profile must be an array')
        return FHIRMappingResult(resource_type, resource)

    @staticmethod
    def patient(resource: dict[str, Any]) -> FHIRMappingResult: return FHIRAdapter.validate(resource, 'Patient')
    @staticmethod
    def organization(resource: dict[str, Any]) -> FHIRMappingResult: return FHIRAdapter.validate(resource, 'Organization')
    @staticmethod
    def practitioner(resource: dict[str, Any]) -> FHIRMappingResult: return FHIRAdapter.validate(resource, 'Practitioner')
    @staticmethod
    def practitioner_role(resource: dict[str, Any]) -> FHIRMappingResult: return FHIRAdapter.validate(resource, 'PractitionerRole')
    @staticmethod
    def appointment(resource: dict[str, Any]) -> FHIRMappingResult: return FHIRAdapter.validate(resource, 'Appointment')
    @staticmethod
    def coverage(resource: dict[str, Any]) -> FHIRMappingResult: return FHIRAdapter.validate(resource, 'Coverage')
    @staticmethod
    def account(resource: dict[str, Any]) -> FHIRMappingResult: return FHIRAdapter.validate(resource, 'Account')
    @staticmethod
    def claim(resource: dict[str, Any]) -> FHIRMappingResult: return FHIRAdapter.validate(resource, 'Claim')
    @staticmethod
    def claim_response(resource: dict[str, Any]) -> FHIRMappingResult: return FHIRAdapter.validate(resource, 'ClaimResponse')
    @staticmethod
    def eligibility_request(resource: dict[str, Any]) -> FHIRMappingResult: return FHIRAdapter.validate(resource, 'CoverageEligibilityRequest')
    @staticmethod
    def eligibility_response(resource: dict[str, Any]) -> FHIRMappingResult: return FHIRAdapter.validate(resource, 'CoverageEligibilityResponse')
    @staticmethod
    def explanation_of_benefit(resource: dict[str, Any]) -> FHIRMappingResult: return FHIRAdapter.validate(resource, 'ExplanationOfBenefit')
    @staticmethod
    def task(resource: dict[str, Any]) -> FHIRMappingResult: return FHIRAdapter.validate(resource, 'Task')
    @staticmethod
    def communication(resource: dict[str, Any]) -> FHIRMappingResult: return FHIRAdapter.validate(resource, 'Communication')
    @staticmethod
    def service_request(resource: dict[str, Any]) -> FHIRMappingResult: return FHIRAdapter.validate(resource, 'ServiceRequest')
    @staticmethod
    def bundle(resource: dict[str, Any]) -> FHIRMappingResult: return FHIRAdapter.validate(resource, 'Bundle')
    @staticmethod
    def operation_outcome(resource: dict[str, Any]) -> FHIRMappingResult: return FHIRAdapter.validate(resource, 'OperationOutcome')
    @staticmethod
    def document_reference(resource: dict[str, Any]) -> FHIRMappingResult: return FHIRAdapter.validate(resource, 'DocumentReference')

    @staticmethod
    def from_internal(resource_type: str, values: dict[str, Any]) -> dict[str, Any]:
        if resource_type not in SUPPORTED_RESOURCES: raise FHIRValidationError(f'unsupported FHIR resource: {resource_type}')
        result = {'resourceType': resource_type, **values}
        FHIRAdapter.validate(result, resource_type)
        return result
