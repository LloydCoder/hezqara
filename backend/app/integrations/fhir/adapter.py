from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class FHIRMappingResult:
    resource_type: str
    resource: dict[str, Any]
    warnings: tuple[str, ...] = ()

class FHIRAdapter:
    """Explicit boundary for FHIR-shaped exchange; not a claim of conformance."""
    @staticmethod
    def patient(resource: dict[str, Any]) -> FHIRMappingResult:
        if resource.get('resourceType') != 'Patient': raise ValueError('expected FHIR Patient resource')
        return FHIRMappingResult('Patient',resource)
    @staticmethod
    def coverage(resource: dict[str, Any]) -> FHIRMappingResult:
        if resource.get('resourceType') != 'Coverage': raise ValueError('expected FHIR Coverage resource')
        return FHIRMappingResult('Coverage',resource)
    @staticmethod
    def claim(resource: dict[str, Any]) -> FHIRMappingResult:
        if resource.get('resourceType') != 'Claim': raise ValueError('expected FHIR Claim resource')
        return FHIRMappingResult('Claim',resource)
    @staticmethod
    def claim_response(resource: dict[str, Any]) -> FHIRMappingResult:
        if resource.get('resourceType') != 'ClaimResponse': raise ValueError('expected FHIR ClaimResponse resource')
        return FHIRMappingResult('ClaimResponse',resource)
