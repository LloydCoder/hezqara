"""
Phone number utilities.
HIPAA compliance: raw phone numbers must never appear in logs.
"""
import re


def mask_phone_number(phone: str) -> str:
    """
    Mask a phone number for safe logging.
    +12125551234 → +1212555****
    """
    digits_only = re.sub(r"\D", "", phone)

    if len(digits_only) >= 10:
        visible = digits_only[:-4]
        masked = visible + "****"
        if phone.startswith("+"):
            return "+" + masked
        return masked

    # Too short to mask safely — replace all
    return "*" * len(phone)


def normalize_phone(phone: str) -> str:
    """
    Normalize to E.164 format.
    Assumes US number if no country code.
    """
    digits_only = re.sub(r"\D", "", phone)

    if len(digits_only) == 10:
        return f"+1{digits_only}"
    elif len(digits_only) == 11 and digits_only.startswith("1"):
        return f"+{digits_only}"
    elif phone.startswith("+"):
        return phone

    return phone
