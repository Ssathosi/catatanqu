"""
Bot Catatan Keuangan AI - Google Sheets Service
Handles backup and sync to Google Sheets.
"""
import json
from datetime import datetime, date
from typing import Optional, List
import gspread
from google.oauth2.service_account import Credentials

from config import config


class SheetsService:
    """Service for Google Sheets operations."""
    
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    def __init__(self):
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize Google Sheets client."""
        creds_json = config.GOOGLE_SHEETS_CREDENTIALS
        if not creds_json:
            return
        
        try:
            # Parse credentials JSON
            if creds_json.startswith('{'):
                creds_dict = json.loads(creds_json)
            else:
                # Assume it's a file path
                with open(creds_json, 'r') as f:
                    creds_dict = json.load(f)
            
            credentials = Credentials.from_service_account_info(
                creds_dict, 
                scopes=self.SCOPES
            )
            self.client = gspread.authorize(credentials)
        except Exception as e:
            print(f"Failed to initialize Sheets client: {e}")
            self.client = None
    
    def is_configured(self) -> bool:
        """Check if Sheets is configured."""
        return self.client is not None
    
    async def create_spreadsheet(self, title: str, share_email: Optional[str] = None) -> dict:
        """Create a new spreadsheet."""
        if not self.client:
            return {"error": "Google Sheets not configured"}
        
        try:
            spreadsheet = self.client.create(title)
            
            # Share with user if email provided
            if share_email:
                spreadsheet.share(share_email, perm_type='user', role='writer')
            
            # Create default worksheets
            # Transactions sheet
            ws_transactions = spreadsheet.sheet1
            ws_transactions.update_title("Transaksi")
            ws_transactions.append_row([
                "ID", "Tanggal", "Deskripsi", "Kategori", "Nominal", 
                "Toko", "Wallet", "Sumber"
            ])
            
            # Summary sheet
            ws_summary = spreadsheet.add_worksheet("Ringkasan", rows=100, cols=10)
            ws_summary.append_row([
                "Bulan", "Total Pengeluaran", "Jumlah Transaksi"
            ])
            
            # Wallets sheet
            ws_wallets = spreadsheet.add_worksheet("Wallet", rows=100, cols=10)
            ws_wallets.append_row([
                "ID", "Nama", "Tipe", "Saldo", "Icon"
            ])
            
            return {
                "id": spreadsheet.id,
                "url": spreadsheet.url,
                "title": title
            }
            
        except Exception as e:
            print(f"Error creating spreadsheet: {e}")
            return {"error": str(e)}
    
    async def get_spreadsheet(self, sheet_id: str):
        """Get spreadsheet by ID."""
        if not self.client:
            return None
        
        try:
            return self.client.open_by_key(sheet_id)
        except Exception as e:
            print(f"Error opening spreadsheet: {e}")
            return None
    
    async def backup_transactions(
        self, 
        sheet_id: str, 
        transactions: List[dict],
        decrypt_func
    ) -> dict:
        """Backup transactions to spreadsheet."""
        if not self.client:
            return {"error": "Google Sheets not configured", "count": 0}
        
        try:
            spreadsheet = self.client.open_by_key(sheet_id)
            worksheet = spreadsheet.worksheet("Transaksi")
            
            # Get existing transaction IDs to avoid duplicates
            existing_data = worksheet.get_all_values()
            existing_ids = set()
            if len(existing_data) > 1:
                for row in existing_data[1:]:  # Skip header
                    if row and row[0]:
                        try:
                            existing_ids.add(int(row[0]))
                        except:
                            pass
            
            # Prepare new rows
            new_rows = []
            for tx in transactions:
                if tx["id"] in existing_ids:
                    continue
                
                amount = decrypt_func(tx["amount_encrypted"])
                created_at = tx.get("created_at", "")
                if created_at:
                    try:
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        created_at = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        pass
                
                new_rows.append([
                    tx["id"],
                    created_at,
                    tx.get("description", ""),
                    tx.get("category", ""),
                    amount,
                    tx.get("store_name", ""),
                    tx.get("wallet_id", ""),
                    tx.get("source_type", "text")
                ])
            
            # Append new rows
            if new_rows:
                worksheet.append_rows(new_rows)
            
            return {
                "success": True,
                "count": len(new_rows),
                "total": len(transactions)
            }
            
        except Exception as e:
            print(f"Error backing up transactions: {e}")
            return {"error": str(e), "count": 0}
    
    async def backup_wallets(
        self,
        sheet_id: str,
        wallets: List[dict],
        decrypt_func
    ) -> dict:
        """Backup wallets to spreadsheet."""
        if not self.client:
            return {"error": "Google Sheets not configured", "count": 0}
        
        try:
            spreadsheet = self.client.open_by_key(sheet_id)
            worksheet = spreadsheet.worksheet("Wallet")
            
            # Clear existing data (except header)
            worksheet.clear()
            worksheet.append_row([
                "ID", "Nama", "Tipe", "Saldo", "Icon"
            ])
            
            # Add wallet rows
            rows = []
            for wallet in wallets:
                balance = decrypt_func(wallet["balance_encrypted"])
                rows.append([
                    wallet["id"],
                    wallet["name"],
                    wallet["type"],
                    balance,
                    wallet.get("icon", "💰")
                ])
            
            if rows:
                worksheet.append_rows(rows)
            
            return {
                "success": True,
                "count": len(rows)
            }
            
        except Exception as e:
            print(f"Error backing up wallets: {e}")
            return {"error": str(e), "count": 0}
    
    async def update_summary(
        self,
        sheet_id: str,
        summary_data: dict
    ) -> dict:
        """Update summary sheet."""
        if not self.client:
            return {"error": "Google Sheets not configured"}
        
        try:
            spreadsheet = self.client.open_by_key(sheet_id)
            worksheet = spreadsheet.worksheet("Ringkasan")
            
            # Clear and rebuild
            worksheet.clear()
            worksheet.append_row([
                "Bulan", "Total Pengeluaran", "Jumlah Transaksi"
            ])
            
            rows = []
            for month, data in summary_data.items():
                rows.append([
                    month,
                    data.get("total", 0),
                    data.get("count", 0)
                ])
            
            if rows:
                worksheet.append_rows(rows)
            
            return {"success": True}
            
        except Exception as e:
            print(f"Error updating summary: {e}")
            return {"error": str(e)}


# Singleton instance
sheets = SheetsService()
