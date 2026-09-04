"""HIPAA Audit Log model — append-only."""
from sqlalchemy import Column, String, BigInteger, TIMESTAMP, JSON, func
from app.models.base import Base

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    event_type = Column(String, nullable=False)
    clinic_id = Column(String, nullable=False)
    call_id = Column(String)
    patient_id = Column(String)
    agent_type = Column(String)
    action = Column(String)
    meta_data = Column("metadata", JSON, default={})
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
