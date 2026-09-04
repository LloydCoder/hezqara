"""
WhatsApp Intake Parser.
Nurse sends a WhatsApp message in natural language.
Carenova parses it and creates the patient record or books the appointment.
No computer required. Works on any phone on 2G.

Supported intents:
  - create_patient: "New patient: Amaka Obi, female, DOB 15 March 1990, phone 08031234567"
  - book_appointment: "Book Amaka Obi 08031234567 for Dr. Chukwu tomorrow 10am"
  - record_vitals: "Vitals PAT-001: BP 120/80, temp 37.2, pulse 72"
  - cancel_appointment: "Cancel appointment APT-001 for Amaka Obi"
  - patient_query: "Find patient Amaka Obi"

Supported languages:
  - en: English
  - ig: Igbo
  - yo: Yoruba
  - ha: Hausa
  - fr: French
  - sw: Swahili
"""
import re
import logging
from typing import Optional
from datetime import datetime, date, timedelta

logger = logging.getLogger(__name__)

# Month name mappings for date parsing
MONTH_NAMES = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
    # French
    "janvier": 1, "février": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12,
}

# Language detection keywords
LANGUAGE_MARKERS = {
    "ig": ["ọ bụ", "nke", "ezigbo", "ụmụ", "gịnị", "odịnaya"],
    "yo": ["ẹ", "ọ", "àgbàdo", "ìdílẹ", "àṣà"],
    "ha": ["shi", "tare", "kuma", "saboda", "wannan"],
    "fr": ["nouveau", "nouvelle", "patient", "née", "femme", "homme",
           "téléphone", "rendez-vous", "annuler", "janvier", "février"],
    "sw": ["mgonjwa", "mpya", "daktari", "tarehe", "miaka"],
}


class WhatsAppIntakeParser:
    """
    Parses natural language WhatsApp messages from nurses.
    Returns structured intent + extracted data.
    """

    async def parse_nurse_message(self, message: str) -> dict:
        """
        Parse a nurse's WhatsApp message into structured data.
        Returns dict with intent + extracted fields.
        """
        msg = message.strip()
        language = self._detect_language(msg)
        intent = self._detect_intent(msg.lower())

        if intent == "create_patient":
            data = self._parse_new_patient(msg)
        elif intent == "book_appointment":
            data = self._parse_appointment_booking(msg)
        elif intent == "record_vitals":
            data = self._parse_vitals(msg)
        elif intent == "cancel_appointment":
            data = self._parse_cancellation(msg)
        else:
            data = {"raw": msg}

        return {
            "intent": intent,
            "language_detected": language,
            "raw_message": msg,
            **data,
        }

    def _detect_language(self, message: str) -> str:
        """Detect language from message content."""
        msg_lower = message.lower()
        for lang, markers in LANGUAGE_MARKERS.items():
            if any(m in msg_lower for m in markers):
                return lang
        return "en"

    def _detect_intent(self, msg: str) -> str:
        """Classify message intent."""
        new_patient_triggers = [
            "new patient", "new pat", "patient:", "nouveau patient",
            "nouvelle patiente", "mgonjwa mpya",
        ]
        booking_triggers = [
            "book", "schedule", "appointment for", "appt for",
            "rendez-vous", "book appt",
        ]
        vitals_triggers = [
            "vitals", "vital signs", "bp ", "blood pressure",
            "temperature", "temp ", "pulse", "weight",
        ]
        cancel_triggers = ["cancel", "annuler", "remove appointment"]

        if any(t in msg for t in new_patient_triggers):
            return "create_patient"
        if any(t in msg for t in booking_triggers):
            return "book_appointment"
        if any(t in msg for t in vitals_triggers):
            return "record_vitals"
        if any(t in msg for t in cancel_triggers):
            return "cancel_appointment"
        return "unknown"

    def _parse_new_patient(self, message: str) -> dict:
        """
        Extract patient details from new patient message.
        Handles: "New patient: Amaka Obi, female, DOB 15 March 1990, phone 08031234567"
        Also handles: "Patient: Chukwuemeka Nwosu, male, 45 years old, 07012345678"
        French: "Nouveau patient: Marie Dupont, femme, née le 10 mars 1985, téléphone 0701234567"
        """
        result: dict = {}

        # Extract name — text after "patient:" or "patient :" before first comma
        name_pattern = re.search(
            r"(?:new\s+)?patient[e]?\s*[:]\s*([^,\n]+)", message, re.IGNORECASE
        )
        if name_pattern:
            full_name = name_pattern.group(1).strip()
            parts = full_name.split()
            if len(parts) >= 2:
                result["first_name"] = parts[0]
                result["last_name"] = " ".join(parts[1:])
            elif len(parts) == 1:
                result["first_name"] = parts[0]
                result["last_name"] = ""

        # Extract gender
        msg_lower = message.lower()
        if any(w in msg_lower for w in ["female", "femme", "woman", "mwanamke", "f,"]):
            result["gender"] = "female"
        elif any(w in msg_lower for w in ["male", "homme", "man", "mwanaume", "m,"]):
            result["gender"] = "male"

        # Extract phone number — Nigerian and international formats
        phone_pattern = re.search(
            r"(?:phone\s*[:=]?\s*|téléphone\s*[:=]?\s*|tel\s*[:=]?\s*)?(\+?[0-9]{10,14})",
            message, re.IGNORECASE
        )
        if phone_pattern:
            result["phone"] = phone_pattern.group(1)

        # Extract date of birth
        dob = self._extract_date(message)
        if dob:
            result["date_of_birth"] = dob

        # Extract age if DOB not found
        if "date_of_birth" not in result:
            age_match = re.search(r"(\d{1,3})\s*years?\s*old", message, re.IGNORECASE)
            if age_match:
                age = int(age_match.group(1))
                birth_year = datetime.now().year - age
                result["approximate_age"] = age
                result["date_of_birth"] = f"{birth_year}-01-01"

        return result

    def _parse_appointment_booking(self, message: str) -> dict:
        """
        Extract appointment details.
        "Book Amaka Obi 08031234567 for Dr. Chukwu tomorrow 10am"
        """
        result: dict = {"intent": "book_appointment"}

        # Extract phone
        phone_match = re.search(r"\+?[0-9]{10,14}", message)
        if phone_match:
            result["phone"] = phone_match.group(0)

        # Extract provider name — "for Dr. X" or "with Dr. X"
        provider_match = re.search(
            r"(?:for|with)\s+(?:Dr\.?\s+|Doctor\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            message
        )
        if provider_match:
            result["provider_name"] = provider_match.group(1).strip()

        # Extract time
        time_match = re.search(
            r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", message, re.IGNORECASE
        )
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            period = time_match.group(3).lower()
            if period == "pm" and hour != 12:
                hour += 12
            elif period == "am" and hour == 12:
                hour = 0
            result["time"] = f"{hour:02d}:{minute:02d}"

        # Extract relative date
        msg_lower = message.lower()
        today = date.today()
        if "tomorrow" in msg_lower:
            result["date"] = (today + timedelta(days=1)).isoformat()
        elif "today" in msg_lower:
            result["date"] = today.isoformat()
        elif "monday" in msg_lower:
            result["day_of_week"] = "monday"
        else:
            extracted_date = self._extract_date(message)
            if extracted_date:
                result["date"] = extracted_date

        # Extract patient name — words before phone number
        name_match = re.search(
            r"(?:book|schedule)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)",
            message, re.IGNORECASE
        )
        if name_match:
            result["patient_name"] = name_match.group(1).strip()

        return result

    def _parse_vitals(self, message: str) -> dict:
        """
        Extract vitals from nurse message.
        "Vitals PAT-NG-001: BP 120/80, temp 37.2, pulse 72"
        """
        result: dict = {"intent": "record_vitals"}

        # Extract patient ID
        patient_id_match = re.search(r"PAT[-\s]?[A-Z0-9]+", message, re.IGNORECASE)
        if patient_id_match:
            result["patient_id"] = patient_id_match.group(0).replace(" ", "-").upper()

        # Blood pressure
        bp_match = re.search(r"(?:BP|blood pressure)\s*[:=]?\s*(\d{2,3}/\d{2,3})",
                              message, re.IGNORECASE)
        if bp_match:
            result["blood_pressure"] = bp_match.group(1)

        # Temperature
        temp_match = re.search(r"(?:temp|temperature)\s*[:=]?\s*(\d{2}\.?\d?)",
                                message, re.IGNORECASE)
        if temp_match:
            result["temperature"] = temp_match.group(1)

        # Pulse
        pulse_match = re.search(r"(?:pulse|hr|heart rate)\s*[:=]?\s*(\d{2,3})",
                                 message, re.IGNORECASE)
        if pulse_match:
            result["pulse"] = pulse_match.group(1)

        # Weight
        weight_match = re.search(r"(?:weight|wt)\s*[:=]?\s*(\d{2,3}\.?\d?)\s*kg",
                                  message, re.IGNORECASE)
        if weight_match:
            result["weight_kg"] = float(weight_match.group(1))

        # Height
        height_match = re.search(r"(?:height|ht)\s*[:=]?\s*(\d{3}\.?\d?)\s*cm",
                                  message, re.IGNORECASE)
        if height_match:
            result["height_cm"] = float(height_match.group(1))

        # SpO2
        spo2_match = re.search(r"(?:spo2|oxygen|o2)\s*[:=]?\s*(\d{2,3})%?",
                                message, re.IGNORECASE)
        if spo2_match:
            result["spo2_percent"] = int(spo2_match.group(1))

        return result

    def _parse_cancellation(self, message: str) -> dict:
        """Extract appointment ID from cancellation message."""
        result: dict = {"intent": "cancel_appointment"}
        apt_match = re.search(r"APT[-\s]?[A-Z0-9]+", message, re.IGNORECASE)
        if apt_match:
            result["appointment_id"] = apt_match.group(0).replace(" ", "-").upper()
        return result

    def _extract_date(self, message: str) -> Optional[str]:
        """
        Extract date in multiple formats:
          - "15 March 1990"
          - "March 15, 1990"
          - "15/03/1990"
          - "1990-03-15"
          - "10 mars 1985" (French)
        """
        # ISO format
        iso_match = re.search(r"(\d{4}-\d{2}-\d{2})", message)
        if iso_match:
            return iso_match.group(1)

        # DD/MM/YYYY or MM/DD/YYYY
        slash_match = re.search(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})", message)
        if slash_match:
            d, m, y = slash_match.groups()
            try:
                return f"{y}-{int(m):02d}-{int(d):02d}"
            except ValueError:
                pass

        # "15 March 1990" or "March 15, 1990" or "15 mars 1985"
        date_text_match = re.search(
            r"(\d{1,2})\s+([a-záàâéèêëîïôùûü]+)\s+(\d{4})|"
            r"([a-záàâéèêëîïôùûü]+)\s+(\d{1,2}),?\s+(\d{4})",
            message, re.IGNORECASE
        )
        if date_text_match:
            groups = date_text_match.groups()
            if groups[0]:  # DD Month YYYY
                day, month_str, year = groups[0], groups[1], groups[2]
            else:  # Month DD YYYY
                month_str, day, year = groups[3], groups[4], groups[5]

            month_num = MONTH_NAMES.get(month_str.lower())
            if month_num:
                try:
                    return f"{year}-{month_num:02d}-{int(day):02d}"
                except ValueError:
                    pass

        return None
