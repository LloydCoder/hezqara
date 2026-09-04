"""Call log model."""
from sqlalchemy import Column, String, Integer, TIMESTAMP, ForeignKey, JSON, func
from app.models.base import Base

class Call(Base):
    __tablename__ = "calls"
    id = Column(String, primary_key=True)
    clinic_id = Column(String, ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.id"))
    retell_call_id = Column(String, unique=True)
    call_type = Column(String, default="inbound")
    from_number = Column(String)
    to_number = Column(String)
    duration_ms = Column(Integer)
    intent = Column(String)
    outcome = Column(String)
    agent_type = Column(String, default="reception")
    recording_r2_key = Column(String)
    transcript = Column(JSON)
    started_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    ended_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
