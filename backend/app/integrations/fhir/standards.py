FHIR_R4_VERSION='4.0.1'
SMART_APP_LAUNCH_VERSION='2.2.0'
DAVINCI_IMPLEMENTATION_GUIDES={
 'HRex':'1.2.0',
 'CRD':'2.2.1',
 'DTR':'2.2.0',
 'PAS':'2.2.1',
 'PDex':'2.2.0',
}
FHIR_RESOURCE_PROFILES={
 'Patient':'http://hl7.org/fhir/StructureDefinition/Patient',
 'Coverage':'http://hl7.org/fhir/StructureDefinition/Coverage',
 'Claim':'http://hl7.org/fhir/StructureDefinition/Claim',
 'ClaimResponse':'http://hl7.org/fhir/StructureDefinition/ClaimResponse',
 'ServiceRequest':'http://hl7.org/fhir/StructureDefinition/ServiceRequest',
}
def interoperability_contracts()->dict:
    return {'fhir_r4':FHIR_R4_VERSION,'smart_app_launch':SMART_APP_LAUNCH_VERSION,'davinci':dict(DAVINCI_IMPLEMENTATION_GUIDES)}
