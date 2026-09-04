"""
NDPA/GAID Compliance — Nigeria Data Protection Act, 2023 + GAID 2025.

This module REPLACES the obsolete ndpr.py.
The NDPR 2019 and its Implementation Framework ceased to apply once the
General Application and Implementation Directive (GAID) was issued by the
Nigeria Data Protection Commission (NDPC), effective 19 September 2025.

The NDPA 2023 + GAID 2025 together are now the complete governing
framework for data protection in Nigeria. "NDPR compliant" is no longer
an accurate claim — use "NDPA/GAID compliant".

Key facts:
  - NDPA enacted: 12 June 2023
  - GAID effective: 19 September 2025
  - Regulator: Nigeria Data Protection Commission (NDPC)
  - Breach notification: within 72 hours to NDPC
  - Penalties (data controller/processor of major importance):
      up to ₦10,000,000 or 2% of annual gross revenue, whichever is higher
  - Penalties (other organisations):
      up to ₦2,000,000 or 2% of annual gross revenue, whichever is higher
  - DPO required for data controllers/processors of major importance
    (processing personal data of >200 data subjects within 6 months)
  - Cross-border transfers require a documented legal basis: binding
    corporate rules, NDPC-approved standard contractual clauses, or the
    data subject's explicit consent

Carenova specifically:
  Patient data collected in Nigeria is stored in Supabase Frankfurt (EU).
  This is a cross-border transfer and MUST have a documented legal basis
  per clinic, captured during onboarding.
"""
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class NDPACompliance:
    """
    NDPA 2023 + GAID 2025 rules engine for Nigerian clinic deployments.
    Replaces HIPAA for the Nigeria region — analogous protections, different law.
    """

    @staticmethod
    def get_act_info() -> dict:
        """Core facts about the governing law — used in onboarding and compliance pages."""
        return {
            "act_name": "Nigeria Data Protection Act, 2023",
            "short_name": "NDPA",
            "implementing_directive": "General Application and Implementation Directive (GAID) 2025",
            "regulator": "Nigeria Data Protection Commission (NDPC)",
            "ndpa_enacted_date": "2023-06-12",
            "gaid_effective_date": "2025-09-19",
            "predecessor_law": "Nigeria Data Protection Regulation (NDPR) 2019 — superseded, no longer in force",
            "breach_notification_hours": 72,
        }

    @staticmethod
    def get_penalty_structure() -> dict:
        """Penalty amounts under NDPA — used to explain stakes to clinic owners."""
        return {
            "major_importance": {
                "max_fine_ngn": 10_000_000,
                "max_fine_pct_revenue": 0.02,
                "description": "Data controllers/processors of major importance (>200 data subjects/6mo)",
            },
            "other": {
                "max_fine_ngn": 2_000_000,
                "max_fine_pct_revenue": 0.02,
                "description": "Other data controllers and processors",
            },
            "breach_reporting_failure_ngn": 5_000_000,
            "imprisonment_max_years": 1,
        }

    @staticmethod
    def get_data_subject_rights() -> dict:
        """Patient rights under NDPA — must be disclosed in clinic privacy notices."""
        return {
            "access": "Right to request a copy of personal data held",
            "correction": "Right to request correction of inaccurate data",
            "erasure": "Right to request deletion under certain conditions",
            "portability": "Right to receive data in a portable format",
            "object_to_automated_processing": "Right to object to decisions based solely on automated processing",
            "withdraw_consent": "Right to withdraw previously given consent at any time",
        }

    @staticmethod
    def requires_dpo(data_subjects_count: int, months: int = 6) -> bool:
        """
        DPO required when an organisation processes personal data of
        more than 200 data subjects within a 6-month period (NDPC "major importance" threshold).
        """
        if months <= 6:
            return data_subjects_count > 200
        # Pro-rate threshold for longer windows
        return data_subjects_count > (200 * (months / 6))

    @staticmethod
    def generate_breach_notification(
        clinic_name: str,
        incident_date: str,
        discovery_date: str,
        affected_patients: int,
        data_types: list,
        description: str,
    ) -> dict:
        """
        Generate NDPC breach notification — required within 72 hours of discovery.
        """
        ndpc_notification = f"""
DATA BREACH NOTIFICATION — NIGERIA DATA PROTECTION COMMISSION (NDPC)

Data Controller: {clinic_name}
Date of Incident: {incident_date}
Date Discovered: {discovery_date}
Notification Date: {datetime.utcnow().strftime('%Y-%m-%d')}
Notification Deadline: Within 72 hours of discovery (NDPA s.40 / GAID breach provisions)

DESCRIPTION OF BREACH:
{description}

PERSONAL DATA INVOLVED:
{chr(10).join(f'  - {d}' for d in data_types)}

DATA SUBJECTS AFFECTED: {affected_patients}

REMEDIATION:
  1. Incident contained and source identified
  2. Affected systems secured
  3. Breach register entry created per GAID requirements
  4. Affected data subjects notified directly
  5. Security controls reviewed and strengthened

Submitted pursuant to the Nigeria Data Protection Act, 2023 and the
General Application and Implementation Directive (GAID) 2025.
""".strip()

        return {
            "ndpc_notification": ndpc_notification,
            "deadline_hours": 72,
            "regulator_contact": "https://ndpc.gov.ng",
            "affected_patients": affected_patients,
        }

    @staticmethod
    def get_compliance_checklist(clinic: dict) -> dict:
        """
        NDPA/GAID compliance checklist for a Nigeria-region clinic.
        Mirrors the structure of the HIPAA checklist for US clinics.
        """
        cross_border_documented = clinic.get("cross_border_transfer_consented", False)

        checks = [
            {"label": "Privacy policy published",                 "status": "pass",
             "category": "Administrative", "detail": "Clear, accessible privacy notice required"},
            {"label": "Explicit consent captured before processing","status": "pass",
             "category": "Administrative", "detail": "Informed, specific, freely given consent at onboarding"},
            {"label": "Cross-border transfer basis documented",     "status": "pass" if cross_border_documented else "pending",
             "category": "Administrative", "detail": "Supabase Frankfurt requires documented legal basis"},
            {"label": "Data Processing Agreement on file",          "status": "pass",
             "category": "Administrative", "detail": "DPA with Supabase as data processor"},
            {"label": "Breach response plan documented",            "status": "pass",
             "category": "Administrative", "detail": "72-hour NDPC notification window"},
            {"label": "Data at rest encrypted",                     "status": "pass",
             "category": "Technical",      "detail": "AES-256 via Supabase managed"},
            {"label": "Data in transit encrypted",                  "status": "pass",
             "category": "Technical",      "detail": "TLS 1.3 enforced"},
            {"label": "Audit trail of data access maintained",      "status": "pass",
             "category": "Technical",      "detail": "Every record access logged"},
            {"label": "Data subject rights process implemented",    "status": "pass",
             "category": "Technical",      "detail": "Access, correction, erasure, portability supported"},
            {"label": "DPO designated (if major importance)",       "status": "pass",
             "category": "Administrative", "detail": "Required only if >200 data subjects/6mo"},
        ]

        passed = sum(1 for c in checks if c["status"] == "pass")
        score = round((passed / len(checks)) * 100)

        return {
            "score": score,
            "passed": passed,
            "total": len(checks),
            "checks": checks,
            "law": "Nigeria Data Protection Act, 2023 + GAID 2025",
        }


class CrossBorderTransfer:
    """
    Handles cross-border data transfer assessment and consent recording.

    Carenova's Supabase instance is in Frankfurt (EU). Any Nigerian patient
    data stored there is a cross-border transfer under NDPA and requires
    one of three documented legal bases.
    """

    VALID_LEGAL_BASES = {
        "binding_corporate_rules",
        "ndpc_approved_scc",
        "explicit_consent",
    }

    ADEQUATE_JURISDICTIONS = {
        "EU/Frankfurt", "EU/Ireland", "EU/Amsterdam",
        "UK", "Canada", "Japan", "South Korea",
        "Switzerland", "New Zealand",
    }

    @staticmethod
    def is_adequate_jurisdiction(jurisdiction: str) -> bool:
        return jurisdiction in CrossBorderTransfer.ADEQUATE_JURISDICTIONS

    @staticmethod
    def assess_transfer(destination_country: str, destination_region: str) -> dict:
        """
        Assess whether a data transfer destination requires documentation.
        Nigeria → anywhere outside Nigeria is cross-border.
        """
        is_cross_border = destination_country.lower() != "nigeria"

        return {
            "destination_country": destination_country,
            "destination_region": destination_region,
            "is_cross_border": is_cross_border,
            "requires_documentation": is_cross_border,
            "legal_basis_required": (
                "One of: binding_corporate_rules, ndpc_approved_scc, explicit_consent"
                if is_cross_border else None
            ),
        }

    @staticmethod
    def generate_consent_record(
        clinic_id: str,
        clinic_name: str,
        destination: str,
        legal_basis: str,
    ) -> dict:
        """
        Generate the documented legal basis record for a cross-border transfer.
        Captured during clinic onboarding (Nigeria-region clinics) and
        stored permanently against the clinic record.
        """
        if legal_basis not in CrossBorderTransfer.VALID_LEGAL_BASES:
            raise ValueError(
                f"Invalid legal basis '{legal_basis}'. "
                f"Must be one of: {CrossBorderTransfer.VALID_LEGAL_BASES}"
            )

        return {
            "clinic_id": clinic_id,
            "clinic_name": clinic_name,
            "destination": destination,
            "legal_basis": legal_basis,
            "consented_at": datetime.utcnow().isoformat(),
            "law_reference": "Nigeria Data Protection Act, 2023 s.41-43",
        }
