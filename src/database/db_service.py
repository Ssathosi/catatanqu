"""
Bot Catatan Keuangan AI - Database Service (Supabase)
"""
from datetime import datetime, date
from typing import Optional
from supabase import create_client, Client

from config import config


class DatabaseService:
    """Service for interacting with Supabase database."""
    
    def __init__(self):
        self.client: Client = create_client(
            config.SUPABASE_URL,
            config.SUPABASE_SERVICE_KEY
        )

    # ==================== USER ====================

    async def get_user(self, telegram_id: int) -> Optional[dict]:
        response = self.client.table("users").select("*").eq("telegram_id", telegram_id).execute()
        return response.data[0] if response.data else None

    async def create_user(self, telegram_id: int, pin_hash: str, username: str = None, first_name: str = None) -> dict:
        data = {"telegram_id": telegram_id, "pin_hash": pin_hash, "username": username, "first_name": first_name, "safe_mode": False}
        response = self.client.table("users").insert(data).execute()
        return response.data[0]

    async def update_user(self, telegram_id: int, data: dict) -> dict:
        response = self.client.table("users").update(data).eq("telegram_id", telegram_id).execute()
        return response.data[0] if response.data else None

    # ==================== TRANSACTION ====================

    async def create_transaction(self, user_id: int, amount_encrypted: str, description: str, category: str, **kwargs) -> dict:
        data = {
            "user_id": user_id,
            "amount_encrypted": amount_encrypted,
            "description": description,
            "category": category,
            "source_type": kwargs.get("source_type", "text"),
            "wallet_id": kwargs.get("wallet_id")
        }
        response = self.client.table("transactions").insert(data).execute()
        return response.data[0]

    async def get_transaction(self, tx_id: int) -> Optional[dict]:
        response = self.client.table("transactions").select("*").eq("id", tx_id).execute()
        return response.data[0] if response.data else None

    async def get_user_transactions(self, user_id: int, start_date: date = None, end_date: date = None, limit: int = 100, category: str = None) -> list:
        from datetime import timedelta
        query = self.client.table("transactions").select("*").eq("user_id", user_id).order("created_at", desc=True)
        if start_date:
            # Adjust for timezone (UTC+7) - look 1 day back to catch all transactions
            adjusted_start = start_date - timedelta(days=1)
            query = query.gte("created_at", adjusted_start.isoformat())
        if end_date:
            # Extend end date to catch all transactions in timezone
            adjusted_end = end_date + timedelta(days=1)
            query = query.lte("created_at", adjusted_end.isoformat() + "T23:59:59")
        if category:
            query = query.eq("category", category)
        if limit:
            query = query.limit(limit)
        response = query.execute()
        return response.data

    async def delete_transaction(self, tx_id: int):
        self.client.table("transactions").delete().eq("id", tx_id).execute()

    async def update_transaction(self, tx_id: int, data: dict):
        response = self.client.table("transactions").update(data).eq("id", tx_id).execute()
        return response.data[0] if response.data else None

    async def update_transaction_category(self, tx_id: int, category: str):
        return await self.update_transaction(tx_id, {"category": category})

    # ==================== WALLET ====================

    async def create_wallet(self, user_id: int, name: str, wallet_type: str, balance_encrypted: str, icon: str = "💰", is_default: bool = False) -> dict:
        data = {
            "user_id": user_id,
            "name": name,
            "type": wallet_type,
            "balance_encrypted": balance_encrypted,
            "icon": icon,
            "is_default": is_default,
            "is_active": True
        }
        response = self.client.table("wallets").insert(data).execute()
        return response.data[0]

    async def get_user_wallets(self, user_id: int) -> list:
        response = self.client.table("wallets").select("*").eq("user_id", user_id).eq("is_active", True).execute()
        return response.data

    async def get_wallet(self, wallet_id: int) -> Optional[dict]:
        response = self.client.table("wallets").select("*").eq("id", wallet_id).execute()
        return response.data[0] if response.data else None

    async def update_wallet_balance(self, wallet_id: int, new_balance_encrypted: str, **kwargs):
        self.client.table("wallets").update({"balance_encrypted": new_balance_encrypted}).eq("id", wallet_id).execute()
        log_data = {
            "wallet_id": wallet_id,
            "amount_encrypted": kwargs.get("amount_encrypted"),
            "type": kwargs.get("log_type"),
            "transaction_id": kwargs.get("transaction_id"),
            "note": kwargs.get("note")
        }
        # Remove None values
        log_data = {k: v for k, v in log_data.items() if v is not None}
        try:
            self.client.table("wallet_logs").insert(log_data).execute()
        except:
            pass  # Ignore log errors

    async def delete_wallet(self, wallet_id: int):
        self.client.table("wallets").update({"is_active": False}).eq("id", wallet_id).execute()

    # ==================== SAVINGS TARGET ====================

    async def create_savings_target(self, user_id: int, name: str, target_amount: int, deadline_months: int) -> dict:
        data = {
            "user_id": user_id,
            "name": name,
            "target_amount": target_amount,
            "current_amount": 0,
            "deadline_months": deadline_months
        }
        response = self.client.table("savings_targets").insert(data).execute()
        return response.data[0]

    async def get_user_savings_targets(self, user_id: int) -> list:
        response = self.client.table("savings_targets").select("*").eq("user_id", user_id).execute()
        return response.data

    async def update_savings_target(self, target_id: int, data: dict):
        response = self.client.table("savings_targets").update(data).eq("id", target_id).execute()
        return response.data[0] if response.data else None


# Singleton instance
db = DatabaseService()
