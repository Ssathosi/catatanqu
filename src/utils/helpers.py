"""
Bot Catatan Keuangan AI - Utility Functions
"""
import re
from datetime import datetime
from typing import Optional


def parse_amount(text: str) -> Optional[int]:
    """
    Parse amount from various formats.
    
    Examples:
        "15000" -> 15000
        "15.000" -> 15000
        "15rb" -> 15000
        "15k" -> 15000
        "1.5jt" -> 1500000
        "1,5 juta" -> 1500000
    """
    if not text:
        return None
    
    # Clean and lowercase
    text = text.lower().strip()
    text = text.replace(",", ".")
    text = text.replace(" ", "")
    
    # Remove "rp" prefix if present
    text = re.sub(r'^rp\.?', '', text)
    
    # Handle "juta" / "jt" suffix
    juta_match = re.search(r'([\d.]+)\s*(juta|jt)', text)
    if juta_match:
        value = float(juta_match.group(1))
        return int(value * 1_000_000)
    
    # Handle "ribu" / "rb" / "k" suffix
    ribu_match = re.search(r'([\d.]+)\s*(ribu|rb|k)', text)
    if ribu_match:
        value = float(ribu_match.group(1))
        return int(value * 1_000)
    
    # Handle plain number with thousand separators
    # e.g., "15.000" or "15000"
    plain_match = re.search(r'([\d.]+)', text)
    if plain_match:
        value_str = plain_match.group(1)
        # If has dots, check if it's thousand separator or decimal
        if '.' in value_str:
            parts = value_str.split('.')
            # If last part is 3 digits, it's thousand separator
            if len(parts[-1]) == 3:
                value_str = value_str.replace('.', '')
        try:
            return int(float(value_str))
        except ValueError:
            return None
    
    return None


def format_currency(amount: int, with_prefix: bool = True) -> str:
    """
    Format amount as Indonesian Rupiah.
    
    Examples:
        15000 -> "Rp15.000"
        1500000 -> "Rp1.500.000"
    """
    formatted = f"{amount:,}".replace(",", ".")
    if with_prefix:
        return f"Rp{formatted}"
    return formatted


def format_date(dt: datetime, format_type: str = "short") -> str:
    """
    Format datetime for display.
    
    Args:
        dt: datetime object
        format_type: "short", "long", or "time"
    """
    if format_type == "short":
        return dt.strftime("%d/%m/%Y")
    elif format_type == "long":
        days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
        months = [
            "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
            "Juli", "Agustus", "September", "Oktober", "November", "Desember"
        ]
        day_name = days[dt.weekday()]
        return f"{day_name}, {dt.day} {months[dt.month]} {dt.year}"
    elif format_type == "time":
        return dt.strftime("%H:%M")
    elif format_type == "datetime":
        return dt.strftime("%d/%m/%Y %H:%M")
    return str(dt)


def clean_text(text: str) -> str:
    """Clean and normalize text input."""
    if not text:
        return ""
    # Remove extra whitespace
    text = " ".join(text.split())
    # Remove leading/trailing whitespace
    text = text.strip()
    return text


def extract_description(text: str, amount_str: str) -> str:
    """
    Extract description from transaction text after removing amount.
    
    Example:
        "Beli kopi 15rb" -> "Beli kopi"
        "15k ngopi" -> "ngopi"
    """
    if not text or not amount_str:
        return text
    
    # Remove the amount string from text
    description = text.replace(amount_str, "").strip()
    
    # Remove common prefixes
    prefixes = ["beli", "bayar", "untuk"]
    for prefix in prefixes:
        if description.lower().startswith(prefix + " "):
            description = description[len(prefix):].strip()
    
    return clean_text(description) or "Transaksi"


def validate_pin(pin: str, min_length: int = 4, max_length: int = 6) -> tuple[bool, str]:
    """
    Validate PIN format.
    
    Returns:
        (is_valid, error_message)
    """
    if not pin:
        return False, "PIN tidak boleh kosong"
    
    if not pin.isdigit():
        return False, "PIN harus berupa angka"
    
    if len(pin) < min_length:
        return False, f"PIN minimal {min_length} digit"
    
    if len(pin) > max_length:
        return False, f"PIN maksimal {max_length} digit"
    
    return True, ""
