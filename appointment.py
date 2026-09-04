"""Appointment model."""
from sqlalchemy import Column, String, Integer, TIMESTAMP, ForeignKey, func
from app.models.base import Base

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(String, primary_key=True)
    clinic_id = Column(String, ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    ehr_appointment_id = Column(String)
    provider_id = Column(String)
    provider_name = Column(String)
    appointment_datetime = Column(TIMESTAMP(timezone=True), nullable=False)
    duration_minutes = Column(Integer, default=20)
    reason = Column(String)
    status = Column(String, default="scheduled")
    booked_by_agent = Column(String, default="scheduling")
    call_id = Column(String)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
