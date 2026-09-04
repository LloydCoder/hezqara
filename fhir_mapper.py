"""
FHIR R4 Mapper — converts between internal Carenova model and FHIR resources.
Canonical model lives here. All EHR implementations map through this.
"""


class FHIRMapper:

    def patient_to_fhir(self, patient: dict) -> dict:
        """Map internal patient dict to FHIR R4 Patient resource."""
        return {
            "resourceType": "Patient",
            "id": patient.get("patient_id", ""),
            "name": [{
                "use": "official",
                "family": patient.get("last_name", ""),
                "given": [patient.get("first_name", "")],
            }],
            "birthDate": patient.get("date_of_birth", ""),
            "telecom": [{"system": "phone", "value": patient.get("phone", "")}],
        }

    def fhir_patient_to_internal(self, fhir: dict) -> dict:
        """Map FHIR R4 Patient to internal dict."""
        name = fhir.get("name", [{}])[0]
        return {
            "patient_id": fhir.get("id", ""),
            "first_name": (name.get("given") or [""])[0],
            "last_name": name.get("family", ""),
            "date_of_birth": fhir.get("birthDate", ""),
            "phone": next(
                (t["value"] for t in fhir.get("telecom", []) if t.get("system") == "phone"),
                "",
            ),
        }

    def fhir_appointment_to_internal(self, fhir: dict) -> dict:
        """Map FHIR R4 Appointment to internal slot dict."""
        status_map = {
            "booked": "confirmed",
            "pending": "pending",
            "cancelled": "cancelled",
            "fulfilled": "completed",
        }
        provider_ref = ""
        for p in fhir.get("participant", []):
            ref = p.get("actor", {}).get("reference", "")
            if ref.startswith("Practitioner/"):
                provider_ref = ref.replace("Practitioner/", "")

        return {
            "appointment_id": fhir.get("id", ""),
            "status": status_map.get(fhir.get("status", ""), fhir.get("status", "")),
            "datetime": fhir.get("start", ""),
            "provider_id": provider_ref,
        }
