"""
Bot Catatan Keuangan AI - Configuration
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration from environment variables."""
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # Gemini AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Groq AI (Optional)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # Encryption
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")
    
    # Google Sheets (optional)
    GOOGLE_SHEETS_CREDENTIALS: str = os.getenv("GOOGLE_SHEETS_CREDENTIALS", "")
    
    # App Settings
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    BOT_NAME: str = os.getenv("BOT_NAME", "Bot Catatan Keuangan")
    
    # Security Settings
    PIN_MIN_LENGTH: int = int(os.getenv("PIN_MIN_LENGTH", "4"))
    PIN_MAX_LENGTH: int = int(os.getenv("PIN_MAX_LENGTH", "6"))
    AUTO_DELETE_HOURS: int = int(os.getenv("AUTO_DELETE_HOURS", "0"))
    SAFE_MODE_DEFAULT: bool = os.getenv("SAFE_MODE_DEFAULT", "false").lower() == "true"
    
    @classmethod
    def validate(cls) -> list[str]:
        """Validate required configuration. Returns list of missing configs."""
        missing = []
        
        if not cls.TELEGRAM_BOT_TOKEN:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not cls.GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")
        if not cls.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not cls.SUPABASE_ANON_KEY:
            missing.append("SUPABASE_ANON_KEY")
        if not cls.SUPABASE_SERVICE_KEY:
            missing.append("SUPABASE_SERVICE_KEY")
        if not cls.ENCRYPTION_KEY:
            missing.append("ENCRYPTION_KEY")
            
        return missing
    
    @classmethod
    def is_valid(cls) -> bool:
        """Check if all required configs are present."""
        return len(cls.validate()) == 0


# Singleton instance
config = Config()
