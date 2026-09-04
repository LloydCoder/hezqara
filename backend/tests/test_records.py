"""
Records Agent Tests — Sprint 11
TDD RED phase.

Handles all medical records requests:
  - Verify patient identity before releasing records
  - Retrieve records from EHR
  - Generate HIPAA-compliant release authorization
  - Upload documents to Cloudflare R2
  - Send records to requesting party (patient/provider/insurer)
  - Track release in audit log
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestRecordsAgentInitialisation:

    def test_records_agent_can_be_imported(self):
        from app.agents.records import RecordsAgent
        assert RecordsAgent is not None

    def test_records_agent_inherits_base_agent(self):
        from app.agents.records import RecordsAgent
        from app.agents.base_agent import BaseAgent
        assert issubclass(RecordsAgent, BaseAgent)

    def test_records_agent_requires_clinic_id(self):
        from app.agents.records import RecordsAgent
        with pytest.raises(TypeError):
            RecordsAgent()

    def test_records_agent_has_correct_type(self, clinic_id):
        from app.agents.records import RecordsAgent
        agent = RecordsAgent(clinic_id=clinic_id)
        assert agent.agent_type == "records"


class TestRecordsAgentIdentityVerification:

    @pytest.mark.asyncio
    async def test_verify_identity_with_dob_passes(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """Patient verified by matching DOB to EHR record."""
        from app.agents.records import RecordsAgent

        agent = RecordsAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        mock_ehr_client.get_patient.return_value = {
            "patient_id": "PAT_001",
            "first_name": "Maria",
            "last_name": "Santos",
            "date_of_birth": "1985-03-15",
        }

        result = await agent.verify_patient_identity(
            call_id="call_abc123",
            patient_id="PAT_001",
            provided_dob="1985-03-15",
            provided_last_name="Santos",
        )

        assert result["verified"] is True

    @pytest.mark.asyncio
    async def test_verify_identity_wrong_dob_fails(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """Wrong DOB fails identity verification."""
        from app.agents.records import RecordsAgent

        agent = RecordsAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        mock_ehr_client.get_patient.return_value = {
            "patient_id": "PAT_001",
            "date_of_birth": "1985-03-15",
            "last_name": "Santos",
        }

        result = await agent.verify_patient_identity(
            call_id="call_abc123",
            patient_id="PAT_001",
            provided_dob="1990-01-01",
            provided_last_name="Santos",
        )

        assert result["verified"] is False
        assert result["reason"] == "dob_mismatch"

    @pytest.mark.asyncio
    async def test_unverified_identity_blocks_record_release(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """
        Records are never released without verified identity.
        HIPAA requirement — non-negotiable.
        """
        from app.agents.records import RecordsAgent

        agent = RecordsAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        result = await agent.request_records_release(
            call_id="call_abc123",
            patient_id="PAT_001",
            identity_verified=False,
            record_type="visit_summary",
            recipient="patient",
        )

        assert result["success"] is False
        assert result["blocked_reason"] == "identity_not_verified"


class TestRecordsAgentDocumentHandling:

    @pytest.mark.asyncio
    async def test_retrieve_records_from_ehr(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """Fetches records from EHR by type."""
        from app.agents.records import RecordsAgent

        agent = RecordsAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        mock_ehr_client.get_patient_records = AsyncMock(return_value=[
            {"record_id": "R001", "type": "visit_summary", "date": "2026-06-01"},
            {"record_id": "R002", "type": "lab_results", "date": "2026-05-15"},
        ])

        records = await agent.retrieve_records(
            call_id="call_abc123",
            patient_id="PAT_001",
            record_type="all",
        )

        assert len(records) == 2
        assert records[0]["record_id"] == "R001"

    @pytest.mark.asyncio
    async def test_release_records_writes_audit_log(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """Every record release writes HIPAA audit log."""
        from app.agents.records import RecordsAgent

        agent = RecordsAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        mock_ehr_client.release_records = AsyncMock(return_value={
            "release_id": "REL001", "status": "sent"
        })

        with patch("app.agents.records.write_audit_log") as mock_audit:
            await agent.request_records_release(
                call_id="call_abc123",
                patient_id="PAT_001",
                identity_verified=True,
                record_type="visit_summary",
                recipient="patient",
            )
            mock_audit.assert_called_once()
            kwargs = mock_audit.call_args[1]
            assert kwargs["event_type"] == "records_released"
            assert kwargs["clinic_id"] == clinic_id

    @pytest.mark.asyncio
    async def test_release_records_stores_graphiti_episode(
        self, clinic_id, mock_llm_gateway, mock_graphiti, mock_ehr_client
    ):
        """Record release stored in Graphiti."""
        from app.agents.records import RecordsAgent

        agent = RecordsAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti
        agent.ehr = mock_ehr_client

        mock_ehr_client.release_records = AsyncMock(return_value={
            "release_id": "REL001", "status": "sent"
        })

        await agent.request_records_release(
            call_id="call_abc123",
            patient_id="PAT_001",
            identity_verified=True,
            record_type="visit_summary",
            recipient="patient",
        )

        mock_graphiti.add_episode.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_record_type_from_utterance(
        self, clinic_id, mock_llm_gateway, mock_graphiti
    ):
        """Classifies what type of records patient is requesting."""
        from app.agents.records import RecordsAgent

        agent = RecordsAgent(clinic_id=clinic_id)
        agent.llm = mock_llm_gateway
        agent.memory = mock_graphiti

        mock_llm_gateway.route.return_value = {
            "content": '{"record_type": "lab_results", "date_range": "last_6_months"}',
            "model_used": "ollama/deepseek-coder-v2",
            "tokens_used": 18,
            "cost_usd": 0.0,
        }

        result = await agent.classify_record_request(
            call_id="call_abc123",
            utterance="I need my blood test results from the last few months",
        )

        assert result["record_type"] == "lab_results"
