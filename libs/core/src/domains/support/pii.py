import re
from typing import Optional

def mask_phone(phone: str) -> str:
    """
    Masks a phone number. 
    Input: "0501234567" -> Output: "050****567"
    """
    if not phone or len(phone) < 7:
        return "****"
    return f"{phone[:3]}****{phone[-3:]}"

def mask_text(text: Optional[str]) -> str:
    """
    Masks general text/notes.
    """
    if not text:
        return ""
    return f"{text[:2]}..." if len(text) > 2 else "..."

def get_masked_value(value: str, field_type: str, role: str, has_break_glass: bool = False) -> str:
    """
    Returns masked or original value based on role and break-glass status.
    """
    # Admin and Manager always see full PII
    if role in ["admin", "manager"] or has_break_glass:
        return value
    
    if field_type == "phone":
        return mask_phone(value)
    elif field_type == "text":
        return mask_text(value)
    
    return "****"
