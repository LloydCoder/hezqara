"""Clinic model — multi-tenant root."""
from sqlalchemy import Column, String, Boolean, ARRAY, TIMESTAMP, func
from app.models.base import Base

class Clinic(Base):
    __tablename__ = "clinics"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    clerk_org_id = Column(String, unique=True, nullable=False)
    ehr_type = Column(String, default="athenahealth")
    ehr_practice_id = Column(String)
    phone_number = Column(String)
    timezone = Column(String, default="America/New_York")
    country = Column(String, default="US")
    plan_tier = Column(String, default="starter")
    lemonsqueezy_sub_id = Column(String)
    active_agents = Column(ARRAY(String), default=["reception"])
    whatsapp_enabled = Column(Boolean, default=False)
    hipaa_baa_signed = Column(Boolean, default=False)
    hipaa_baa_date = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
