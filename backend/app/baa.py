"""
HIPAA BAA Service — Business Associate Agreement management.
Generates, stores, and verifies BAA signatures.

In production:
  - BAA PDF generated with clinic details
  - Signed via HelloSign / DocuSign API
  - PDF stored in Cloudflare R2
  - Signing event recorded in Supabase audit_log

For now:
  - BAA text template ready
  - Signing flow API complete
  - PDF generation stubbed (add DocuSign in Phase 8)
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

BAA_TEMPLATE = """
BUSINESS ASSOCIATE AGREEMENT

This Business Associate Agreement ("BAA") is entered into between:

Covered Entity: {clinic_name}
Contact: {signatory_name}, {signatory_title}

Business Associate: Tinlance Limited
RC: 7962164
Contact: lloyd@tinlance.com

EFFECTIVE DATE: {signed_date}

1. DEFINITIONS
   "Protected Health Information" (PHI) has the meaning given under
   45 CFR §160.103, limited to PHI created, received, maintained, or
   transmitted by Business Associate on behalf of Covered Entity.

2. PERMITTED USES AND DISCLOSURES
   Business Associate may use and disclose PHI only to:
   (a) Provide AI-powered medical front office services including
       appointment scheduling, insurance verification, prior authorization,
       prescription refill management, patient recall, and related functions.
   (b) Fulfill any other purpose permitted under 45 CFR Part 164, Subpart E.

3. SAFEGUARDS
   Business Associate agrees to:
   (a) Implement and use appropriate administrative, physical, and technical
       safeguards to prevent unauthorized use or disclosure of PHI.
   (b) Encrypt all PHI in transit (TLS 1.3) and at rest (AES-256).
   (c) Maintain PHI audit logs per 45 CFR §164.312(b).
   (d) Use Supabase (Frankfurt, EU) with HIPAA BAA for data storage.
   (e) Use Retell AI with signed HIPAA BAA for voice processing.

4. BREACH NOTIFICATION
   Business Associate will notify Covered Entity of any breach of
   unsecured PHI without unreasonable delay and in no case later than
   60 calendar days of discovery, per 45 CFR §164.410.

5. TERM AND TERMINATION
   This BAA remains in effect while Business Associate provides services
   to Covered Entity. Either party may terminate upon 30 days written notice.

6. GOVERNING LAW
   This agreement is governed by applicable US federal law (HIPAA/HITECH)
   and the laws of the State of Delaware.

SIGNATURES:

Covered Entity: {clinic_name}
Signatory: {signatory_name}
Title: {signatory_title}
Date: {signed_date}
IP Address: {ip_address}
Reference: {baa_reference}

Business Associate: Tinlance Limited
Signatory: Chinaemerem Nwachukwu (Lloyd)
Title: Founder & CEO
Date: {signed_date}

This agreement is legally binding upon electronic execution.
""".strip()


class BAAService:

    @staticmethod
    def generate_baa(
        clinic_name: str,
        signatory_name: str,
        signatory_title: str,
        signed_date: str,
        ip_address: str = "recorded",
        clinic_id: str = "",
    ) -> dict:
        baa_ref = f"BAA-{clinic_id[:8].upper() if clinic_id else 'CARENOVA'}-2026"
        text = BAA_TEMPLATE.format(
            clinic_name=clinic_name,
            signatory_name=signatory_name,
            signatory_title=signatory_title,
            signed_date=signed_date,
            ip_address=ip_address,
            baa_reference=baa_ref,
        )
        return {
            "baa_reference": baa_ref,
            "text": text,
            "clinic_name": clinic_name,
            "signatory_name": signatory_name,
            "signed_date": signed_date,
            "baa_version": "2026-v1",
            "status": "signed",
        }

    @staticmethod
    def verify_baa(clinic: dict) -> dict:
        signed = clinic.get("hipaa_baa_signed", False)
        return {
            "signed": signed,
            "required_for_us": True,
            "required_for_nigeria": False,
            "reference": clinic.get("baa_reference"),
            "message": (
                "BAA signed — clinic cleared for US patient PHI processing."
                if signed else
                "BAA required before handling US patient PHI. Complete step 5 of onboarding."
            ),
        }
