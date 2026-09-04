"""Patient model — PHI stored here, RLS enforced at DB level."""
from sqlalchemy import Column, String, Boolean, Date, TIMESTAMP, ForeignKey, func
from app.models.base import Base

class Patient(Base):
    __tablename__ = "patients"
    id = Column(String, primary_key=True)
    clinic_id = Column(String, ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False)
    ehr_patient_id = Column(String)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(Date)
    phone = Column(String)
    email = Column(String)
    address_street = Column(String)
    address_city = Column(String)
    address_state = Column(String)
    address_zip = Column(String)
    insurance_carrier = Column(String)
    insurance_member_id = Column(String)
    insurance_group = Column(String)
    uninsured = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
