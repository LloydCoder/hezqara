"""
NDPA/GAID Compliance Tests — Replaces obsolete NDPR module.

The NDPR 2019 and its Implementation Framework ceased to apply once the
GAID (General Application and Implementation Directive) was issued by the
NDPC on 19 September 2025. The NDPA 2023 + GAID together are now the
complete governing framework for data protection in Nigeria.

Key facts this module must encode correctly:
  - NDPA enacted 12 June 2023, GAID effective 19 September 2025
  - Regulator: Nigeria Data Protection Commission (NDPC), not "NDPR body"
  - Breach notification: 72 hours to NDPC
  - Penalties: up to ₦10,000,000 or 2% of annual gross revenue (major importance)
              up to ₦2,000,000 or 2% of annual gross revenue (other)
  - Cross-border transfer requires documented legal basis: BCRs, NDPC-approved
    SCCs, or explicit data subject consent — Carenova uses Supabase Frankfurt,
    which is a cross-border transfer requiring this documentation
  - DPO required for "data controllers/processors of major importance"
    (processing >200 data subjects within 6 months)
"""
import pytest


class TestNDPACompliance:

    def test_ndpa_module_importable(self):
        from app.compliance.ndpa import NDPACompliance
        assert NDPACompliance is not None

    def test_old_ndpr_module_no_longer_used_as_primary(self):
        """ndpa.py must exist as the primary module — not ndpr.py."""
        import os
        assert os.path.exists("../../backend/app/compliance/ndpa.py")

    def test_act_name_is_correct(self):
        from app.compliance.ndpa import NDPACompliance
        info = NDPACompliance.get_act_info()
        assert info["act_name"] == "Nigeria Data Protection Act, 2023"
        assert "NDPR" not in info["act_name"]

    def test_regulator_is_ndpc(self):
        from app.compliance.ndpa import NDPACompliance
        info = NDPACompliance.get_act_info()
        assert info["regulator"] == "Nigeria Data Protection Commission (NDPC)"

    def test_gaid_effective_date_correct(self):
        from app.compliance.ndpa import NDPACompliance
        info = NDPACompliance.get_act_info()
        assert info["gaid_effective_date"] == "2025-09-19"

    def test_ndpa_enacted_date_correct(self):
        from app.compliance.ndpa import NDPACompliance
        info = NDPACompliance.get_act_info()
        assert info["ndpa_enacted_date"] == "2023-06-12"

    def test_breach_notification_window_is_72_hours(self):
        from app.compliance.ndpa import NDPACompliance
        info = NDPACompliance.get_act_info()
        assert info["breach_notification_hours"] == 72

    def test_penalty_amounts_correct(self):
        from app.compliance.ndpa import NDPACompliance
        penalties = NDPACompliance.get_penalty_structure()
        assert penalties["major_importance"]["max_fine_ngn"] == 10_000_000
        assert penalties["major_importance"]["max_fine_pct_revenue"] == 0.02
        assert penalties["other"]["max_fine_ngn"] == 2_000_000

    def test_data_subject_rights_present(self):
        from app.compliance.ndpa import NDPACompliance
        rights = NDPACompliance.get_data_subject_rights()
        assert "access" in rights
        assert "erasure" in rights
        assert "portability" in rights
        assert "object_to_automated_processing" in rights

    def test_dpo_required_threshold(self):
        """DPO required for processing >200 data subjects in 6 months."""
        from app.compliance.ndpa import NDPACompliance
        assert NDPACompliance.requires_dpo(data_subjects_count=250, months=6) is True
        assert NDPACompliance.requires_dpo(data_subjects_count=50, months=6) is False


class TestCrossBorderTransfer:

    def test_cross_border_module_importable(self):
        from app.compliance.ndpa import CrossBorderTransfer
        assert CrossBorderTransfer is not None

    def test_supabase_frankfurt_requires_documented_basis(self):
        """
        Carenova stores data in Supabase Frankfurt (Germany/EU).
        This is a cross-border transfer from Nigeria and must be documented.
        """
        from app.compliance.ndpa import CrossBorderTransfer
        result = CrossBorderTransfer.assess_transfer(
            destination_country="Germany",
            destination_region="EU",
        )
        assert result["is_cross_border"] is True
        assert result["requires_documentation"] is True
        assert "legal_basis_required" in result

    def test_adequate_jurisdiction_list_includes_eu(self):
        from app.compliance.ndpa import CrossBorderTransfer
        assert CrossBorderTransfer.is_adequate_jurisdiction("EU/Frankfurt") is True
        assert CrossBorderTransfer.is_adequate_jurisdiction("EU/Ireland") is True

    def test_generate_transfer_consent_record(self):
        """
        Generate the documented legal basis record required for the transfer.
        This must be captured during onboarding and stored per clinic.
        """
        from app.compliance.ndpa import CrossBorderTransfer
        record = CrossBorderTransfer.generate_consent_record(
            clinic_id="clinic_ng_001",
            clinic_name="Owerri Family Clinic",
            destination="Supabase Frankfurt (EU)",
            legal_basis="explicit_consent",
        )
        assert record["clinic_id"] == "clinic_ng_001"
        assert record["legal_basis"] == "explicit_consent"
        assert record["destination"] == "Supabase Frankfurt (EU)"
        assert "consented_at" in record

    def test_legal_basis_options_valid(self):
        from app.compliance.ndpa import CrossBorderTransfer
        valid = CrossBorderTransfer.VALID_LEGAL_BASES
        assert "binding_corporate_rules" in valid
        assert "ndpc_approved_scc" in valid
        assert "explicit_consent" in valid

    def test_invalid_legal_basis_rejected(self):
        from app.compliance.ndpa import CrossBorderTransfer
        with pytest.raises(ValueError):
            CrossBorderTransfer.generate_consent_record(
                clinic_id="clinic_ng_001",
                clinic_name="Test",
                destination="Somewhere",
                legal_basis="not_a_real_basis",
            )


class TestNDPABreachNotification:

    def test_breach_notification_template(self):
        from app.compliance.ndpa import NDPACompliance
        notice = NDPACompliance.generate_breach_notification(
            clinic_name="Owerri Family Clinic",
            incident_date="2026-07-01",
            discovery_date="2026-07-02",
            affected_patients=12,
            data_types=["names", "phone numbers", "visit records"],
            description="Unauthorized access to WhatsApp intake logs.",
        )
        assert "Owerri Family Clinic" in notice["ndpc_notification"]
        assert "NDPC" in notice["ndpc_notification"]
        assert notice["deadline_hours"] == 72
        assert notice["regulator_contact"] is not None
