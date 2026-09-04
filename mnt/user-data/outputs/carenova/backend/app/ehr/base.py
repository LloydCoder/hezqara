"""
BaseEHR — Abstract EHR interface.

All agents use this interface — never a specific EHR client directly.
Swapping from athenahealth to Epic needs zero agent code changes.
"""
from abc import ABC, abstractmethod
from typing import Optional


class BaseEHR(ABC):

    @abstractmethod
    async def get_patient(self, clinic_id: str, phone: str) -> Optional[dict]:
        pass

    @abstractmethod
    async def create_patient(self, clinic_id: str, data: dict) -> dict:
        pass

    @abstractmethod
    async def update_patient(self, clinic_id: str, patient_id: str, data: dict) -> dict:
        pass

    @abstractmethod
    async def get_available_slots(
        self, clinic_id: str, provider_id: str, date: str, reason: Optional[str] = None
    ) -> list:
        pass

    @abstractmethod
    async def book_appointment(
        self, clinic_id: str, patient_id: str, slot_id: str, reason: str
    ) -> dict:
        pass

    @abstractmethod
    async def cancel_appointment(
        self, clinic_id: str, patient_id: str, appointment_id: str
    ) -> dict:
        pass
