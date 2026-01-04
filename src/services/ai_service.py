"""
Bot Catatan Keuangan AI - AI Service (Full Groq Support)
Handles NLP parsing, categorization, and OCR using Groq.
Gemini remains as a secondary fallback.
"""
import google.generativeai as genai
from groq import Groq
from typing import Optional
import json
import re
import base64

from config import config
from utils.constants import Category, CATEGORY_KEYWORDS, CATEGORY_ICONS


class AIService:
    """Service for AI operations using Groq (Primary) and Gemini (Secondary/OCR)."""
    
    def __init__(self):
        # Initialize Gemini (Vision/Fallback)
        try:
            genai.configure(api_key=config.GEMINI_API_KEY)
            # Try multiple model names for compatibility
            self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
        except:
            try:
                self.gemini_model = genai.GenerativeModel('gemini-pro')
            except:
                self.gemini_model = None

        
        # Initialize Groq (Primary)
        self.groq_client = None
        if hasattr(config, 'GROQ_API_KEY') and config.GROQ_API_KEY:
            self.groq_client = Groq(api_key=config.GROQ_API_KEY)
        
    # ==================== HELPER ====================
    
    async def _safe_generate_content(self, prompt: str, use_vision: bool = False, image_data: bytes = None, response_type: str = "text") -> str:
        """Call Groq (Primary) with Vision or Text."""
        
        # 1. TRY GROQ FIRST (FAST & STABLE)
        if self.groq_client:
            try:
                model = "llama-3.3-70b-versatile"
                messages = []
                
                # Groq vision models are decommissioned - skip to Gemini for vision
                if use_vision and image_data:
                    raise Exception("Groq vision decommissioned, use Gemini")
                
                msg_content = prompt
                if response_type == "json":
                    msg_content += "\nRespond in VALID JSON format."
                messages = [{"role": "user", "content": msg_content}]

                chat_completion = self.groq_client.chat.completions.create(
                    messages=messages,
                    model=model,
                    response_format={"type": "json_object"} if response_type == "json" else None,
                    temperature=0.1
                )
                return chat_completion.choices[0].message.content
            except Exception as e:
                if not use_vision:
                    print(f"Groq API error: {e}")
                    print("Falling back to Gemini for text...")
                # For vision, fall through to Gemini

        # 2. FALLBACK TO GEMINI (For text fallback OR for vision)
        if self.gemini_model:
            try:
                if use_vision and image_data:
                    # Use Gemini Vision
                    import PIL.Image
                    import io
                    image = PIL.Image.open(io.BytesIO(image_data))
                    response = self.gemini_model.generate_content([prompt, image])
                else:
                    response = self.gemini_model.generate_content(prompt)
                return response.text
            except Exception as e:
                print(f"Gemini failed: {e}")
        
        raise Exception("All AI Services failed")


    # ==================== TRANSACTION PARSING ====================
    
    async def parse_transaction(self, text: str) -> dict:
        """Parse natural language transaction input."""
        prompt = f"""
Parse this financial transaction into JSON:
Input: "{text}"

JSON Structure:
{{
    "amount": number,
    "description": string,
    "category": "Makan" | "Transport" | "Belanja" | "Hiburan" | "Tagihan" | "Kesehatan" | "Pendidikan" | "Lainnya",
    "confidence": float
}}
"""
        try:
            result_text = await self._safe_generate_content(prompt, response_type="json")
            result_text = re.sub(r'```json\s*', '', result_text)
            result_text = re.sub(r'```\s*', '', result_text.strip())
            
            result = json.loads(result_text)
            
            # Add category icon
            category = result.get("category", "Lainnya")
            try:
                cat_enum = Category(category)
                result["category_icon"] = CATEGORY_ICONS.get(cat_enum, "📦")
            except:
                result["category"] = "Lainnya"
                result["category_icon"] = "📦"
            
            return result
        except Exception as e:
            print(f"AI parsing error: {e}")
            return self._fallback_parse(text)
    
    def _fallback_parse(self, text: str) -> dict:
        from utils.helpers import parse_amount
        amount = parse_amount(text)
        description = re.sub(r'rp\.?\s*[\d.,]+\s*(rb|ribu|k|jt|juta)?', '', text, flags=re.IGNORECASE)
        description = re.sub(r'[\d.,]+\s*(rb|ribu|k|jt|juta)?', '', description, flags=re.IGNORECASE)
        description = description.strip() or "Transaksi"
        category = self._categorize_by_keywords(text.lower())
        return {
            "amount": amount or 0,
            "description": description,
            "category": category.value,
            "category_icon": CATEGORY_ICONS.get(category, "📦"),
            "confidence": 0.5 if amount else 0.2,
        }
    
    def _categorize_by_keywords(self, text: str) -> Category:
        text_lower = text.lower()
        for category, keywords in CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return category
        return Category.LAINNYA

    # ==================== SMART CATEGORIZATION ====================
    
    async def suggest_category(self, description: str, amount: int) -> dict:
        prompt = f"Kategorikan transaksi: {description} Rp{amount}. Pilihan: Makan, Transport, Belanja, Hiburan, Tagihan, Kesehatan, Pendidikan, Lainnya."
        try:
            result_text = await self._safe_generate_content(prompt, response_type="json")
            return json.loads(result_text)
        except:
            return {"category": "Lainnya", "confidence": 0.3, "reason": "Error"}

    # ==================== OCR STRUK ====================
    
    async def process_receipt(self, image_data: bytes) -> dict:
        """Process receipt image using Groq Vision (Primary)."""
        prompt = """
Analyze this image carefully. Is this a shopping receipt or financial proof?
If NOT, return JSON: {"is_receipt": false}.
If YES, extract:
1. store_name: Name of store at the top.
2. total: GRAND TOTAL amount (net after discounts).
3. items: List of items with name, price, qty.
4. date: Date (YYYY-MM-DD).

Return ONLY JSON.
"""
        try:
            result_text = await self._safe_generate_content(
                prompt, 
                use_vision=True, 
                image_data=image_data, 
                response_type="json"
            )
            result_text = re.sub(r'```json\s*', '', result_text)
            result_text = re.sub(r'```\s*', '', result_text.strip())
            
            return json.loads(result_text)
        except Exception as e:
            print(f"OCR error: {e}")
            return {"error": str(e), "confidence": 0}
    
    # ==================== INSIGHT GENERATION ====================
    
    async def generate_insight(self, spending_data: dict, period: str = "bulanan") -> str:
        prompt = f"""
Berikan insight keuangan {period} untuk user. 
Bahasa: Indonesia Casual (gaul tapi sopan).
Gunakan emoji. Jangan kirim format JSON, kirim teks biasa saja.
Data: {json.dumps(spending_data)}
"""
        try:
            return await self._safe_generate_content(prompt, response_type="text")
        except Exception as e:
            return f"❌ Insight error: {e}"


# Singleton instance
ai = AIService()
