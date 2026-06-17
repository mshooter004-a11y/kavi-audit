# audit_engine.py
"""
Audit engine for KaviAudit application.
"""

import hashlib
import json
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class AuditEngine:
    """Handles audit processing logic."""
    
    def __init__(self, authorized_accounts_file: str = "authorized_accounts.json"):
        self.authorized_accounts_file = authorized_accounts_file
        self.load_authorized_accounts()
        
        # Risk scoring weights
        self.risk_weights = {
            "duplicate": 30,
            "negative_amount": 20,
            "unauthorized_transfer": 50
        }
    
    def load_authorized_accounts(self):
        """Load authorized accounts from JSON file."""
        try:
            with open(self.authorized_accounts_file, 'r') as f:
                self.authorized_accounts = set(json.load(f))
        except FileNotFoundError:
            logger.warning(f"Authorized accounts file {self.authorized_accounts_file} not found.")
            self.authorized_accounts = set()
        except Exception as e:
            logger.error(f"Error loading authorized accounts: {e}")
            self.authorized_accounts = set()
    
    def calculate_hash(self, row_data: str) -> str:
        """Calculate SHA256 hash of row data."""
        return hashlib.sha256(row_data.encode()).hexdigest()
    
    def detect_duplicate(self, row_data: str, existing_hashes: set) -> bool:
        """Check if row data is a duplicate."""
        row_hash = self.calculate_hash(row_data)
        if row_hash in existing_hashes:
            return True
        existing_hashes.add(row_hash)
        return False
    
    def detect_negative_amount(self, row_data: str) -> bool:
        """Check if amount in row data is negative."""
        # This is a simple implementation - in a real application, 
        # you would parse the CSV columns properly
        try:
            parts = row_data.split(',')
            if len(parts) > 1:
                amount = float(parts[1].strip())  # Assuming amount is second column
                return amount < 0
        except (ValueError, IndexError):
            pass
        return False
    
    def detect_unauthorized_transfer(self, row_data: str) -> bool:
        """Check if account is unauthorized."""
        try:
            parts = row_data.split(',')
            if len(parts) >= 3:
                source_account = parts[2].strip()  # Assuming third column is source account
                return source_account not in self.authorized_accounts
        except IndexError:
            pass
        return False
    
    def analyze_row(self, row_data: str, existing_hashes: set) -> List[Dict[str, Any]]:
        """Analyze a single row for anomalies."""
        exceptions = []
        risk_score = 0
        
        # Check for duplicates
        if self.detect_duplicate(row_data, existing_hashes):
            exceptions.append({
                "type": "duplicate",
                "severity": 3,
                "description": "Duplicate transaction detected"
            })
            risk_score += self.risk_weights["duplicate"]
        
        # Check for negative amounts
        if self.detect_negative_amount(row_data):
            exceptions.append({
                "type": "negative_amount",
                "severity": 2,
                "description": "Negative transaction amount detected"
            })
            risk_score += self.risk_weights["negative_amount"]
        
        # Check for unauthorized transfers
        if self.detect_unauthorized_transfer(row_data):
            exceptions.append({
                "type": "unauthorized_transfer",
                "severity": 5,
                "description": "Transfer from unauthorized account"
            })
            risk_score += self.risk_weights["unauthorized_transfer"]
        
        return exceptions
    
    def run_audit(self, file_path: str) -> tuple:
        """Run audit on a CSV file."""
        exceptions = []
        existing_hashes = set()
        total_records = 0
        
        try:
            with open(file_path, 'r') as f:
                # Skip header if present
                header = f.readline()
                
                for line_num, line in enumerate(f, 2):  # Start at 2 since we read header
                    total_records += 1
                    row_data = line.strip()
                    row_exceptions = self.analyze_row(row_data, existing_hashes)
                    exceptions.extend(row_exceptions)
                    
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            
        return exceptions, total_records