"""
Secure API Key Manager for Resume Screening Application
Handles encrypted storage and retrieval of API keys with logging
"""

import os
import json
import hashlib
import logging
from datetime import datetime
from cryptography.fernet import Fernet
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class SecureAPIKeyManager:
    """Manages encrypted API key storage with logging."""
    
    def __init__(self, storage_file: str = "api_keys.enc", log_file: str = "api_key_usage.log"):
        self.storage_file = storage_file
        self.log_file = log_file
        self.master_key = "Eggp1an1F2shCvrry1!"
        self.encryption_key = self._generate_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        
        # Setup logging
        self._setup_logging()
        
        # Initialize storage file if it doesn't exist
        self._initialize_storage()
    
    def _generate_encryption_key(self) -> bytes:
        """Generate encryption key from master key."""
        return Fernet.generate_key()
    
    def _setup_logging(self):
        """Setup logging for API key usage."""
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def _initialize_storage(self):
        """Initialize encrypted storage file."""
        if not os.path.exists(self.storage_file):
            empty_data = {
                "keys": {},
                "usage_log": [],
                "created_at": datetime.now().isoformat()
            }
            self._save_encrypted_data(empty_data)
            logger.info("Initialized new API key storage")
    
    def _save_encrypted_data(self, data: Dict):
        """Save data to encrypted file."""
        try:
            json_data = json.dumps(data, indent=2)
            encrypted_data = self.fernet.encrypt(json_data.encode())
            
            with open(self.storage_file, 'wb') as f:
                f.write(encrypted_data)
            
        except Exception as e:
            logger.error(f"Failed to save encrypted data: {e}")
            raise
    
    def _load_encrypted_data(self) -> Dict:
        """Load data from encrypted file."""
        try:
            if not os.path.exists(self.storage_file):
                return {"keys": {}, "usage_log": []}
            
            with open(self.storage_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
            
        except Exception as e:
            logger.error(f"Failed to load encrypted data: {e}")
            return {"keys": {}, "usage_log": []}
    
    def _hash_key(self, api_key: str) -> str:
        """Create hash of API key for duplicate detection."""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def _log_usage(self, action: str, provider: str, key_hash: str, success: bool = True):
        """Log API key usage."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "provider": provider,
            "key_hash": key_hash[:16] + "...",  # Only log first 16 chars of hash
            "success": success
        }
        
        logger.info(f"API Key {action}: {provider} - {key_hash[:16]}... - {'Success' if success else 'Failed'}")
        
        # Also store in encrypted file
        data = self._load_encrypted_data()
        data["usage_log"].append(log_entry)
        
        # Keep only last 1000 log entries
        if len(data["usage_log"]) > 1000:
            data["usage_log"] = data["usage_log"][-1000:]
        
        self._save_encrypted_data(data)
        key_logger = logging.getLogger('api_key_manager')
        key_logger.setLevel(logging.INFO)
        
        # Create file handler
        handler = logging.FileHandler(self.log_file)
        handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        if not key_logger.handlers:
            key_logger.addHandler(handler)
        
        self.key_logger = key_logger
    
    def _load_keys(self) -> Dict:
        """Load and decrypt API keys from file."""
        if not os.path.exists(self.keys_file):
            return {}
        
        try:
            with open(self.keys_file, 'rb') as f:
                encrypted_data = f.read()
            
            if not encrypted_data:
                return {}
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode('utf-8'))
        
        except Exception as e:
            logger.error(f"Error loading API keys: {e}")
            return {}
    
    def _save_keys(self, keys_data: Dict):
        """Encrypt and save API keys to file."""
        try:
            json_data = json.dumps(keys_data, indent=2)
            encrypted_data = self.cipher.encrypt(json_data.encode('utf-8'))
            
            with open(self.keys_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Restrict file permissions
            os.chmod(self.keys_file, 0o600)
            
        except Exception as e:
            logger.error(f"Error saving API keys: {e}")
            raise
    
    def _hash_key(self, api_key: str) -> str:
        """Create a hash of the API key for identification."""
        return hashlib.sha256(api_key.encode()).hexdigest()[:16]
    
    def _mask_key(self, api_key: str) -> str:
        """Mask API key for display to users."""
        if len(api_key) <= 8:
            return "*" * len(api_key)
        return api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
    
    def store_api_key(self, provider: str, model: str, api_key: str, user_identifier: str = "unknown") -> Tuple[bool, str]:
        """
        Store API key if not duplicate.
        Returns (success, message)
        """
        try:
            if not api_key or api_key.strip() == "":
                return False, "Empty API key provided"
            
            # Check for special admin code
            if api_key == self.master_key:
                return False, "Cannot store master key as API key"
            
            key_hash = self._hash_key(api_key)
            data = self._load_encrypted_data()
            
            # Check for duplicates
            for stored_provider, stored_keys in data["keys"].items():
                for stored_model, stored_info in stored_keys.items():
                    if stored_info["key_hash"] == key_hash:
                        self._log_usage("duplicate_attempt", provider, key_hash, False)
                        return False, f"This API key is already stored for {stored_provider}/{stored_model}"
            
            # Store new key
            if provider not in data["keys"]:
                data["keys"][provider] = {}
            
            data["keys"][provider][model] = {
                "key_hash": key_hash,
                "encrypted_key": self.fernet.encrypt(api_key.encode()).decode(),
                "stored_at": datetime.now().isoformat(),
                "user_identifier": user_identifier,
                "usage_count": 0
            }
            
            self._save_encrypted_data(data)
            self._log_usage("stored", provider, key_hash, True)
            
            return True, "API key stored successfully"
            
        except Exception as e:
            logger.error(f"Failed to store API key: {e}")
            return False, f"Storage failed: {str(e)}"
    
    def get_api_key(self, provider: str, model: str) -> Optional[str]:
        """Retrieve API key for provider/model."""
        try:
            data = self._load_encrypted_data()
            
            if provider in data["keys"] and model in data["keys"][provider]:
                key_info = data["keys"][provider][model]
                encrypted_key = key_info["encrypted_key"].encode()
                api_key = self.fernet.decrypt(encrypted_key).decode()
                
                # Update usage count
                key_info["usage_count"] += 1
                key_info["last_used"] = datetime.now().isoformat()
                self._save_encrypted_data(data)
                
                self._log_usage("retrieved", provider, key_info["key_hash"], True)
                return api_key
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve API key: {e}")
            return None
    
    def list_stored_keys(self, admin_code: str) -> Optional[List[Dict]]:
        """List all stored keys (admin only)."""
        if admin_code != self.master_key:
            logger.warning("Unauthorized attempt to list API keys")
            return None
        
        try:
            data = self._load_encrypted_data()
            keys_list = []
            
            for provider, models in data["keys"].items():
                for model, key_info in models.items():
                    # Decrypt the key for admin view
                    encrypted_key = key_info["encrypted_key"].encode()
                    api_key = self.fernet.decrypt(encrypted_key).decode()
                    
                    keys_list.append({
                        "provider": provider,
                        "model": model,
                        "api_key": api_key,
                        "key_hash": key_info["key_hash"][:16] + "...",
                        "stored_at": key_info["stored_at"],
                        "user_identifier": key_info.get("user_identifier", "unknown"),
                        "usage_count": key_info.get("usage_count", 0),
                        "last_used": key_info.get("last_used", "Never")
                    })
            
            self._log_usage("admin_list", "admin", "admin_access", True)
            return keys_list
            
        except Exception as e:
            logger.error(f"Failed to list keys: {e}")
            return None
    
    def remove_api_key(self, provider: str, model: str, admin_code: str) -> Tuple[bool, str]:
        """Remove API key (admin only)."""
        if admin_code != self.master_key:
            return False, "Unauthorized"
        
        try:
            data = self._load_encrypted_data()
            
            if provider in data["keys"] and model in data["keys"][provider]:
                key_info = data["keys"][provider][model]
                del data["keys"][provider][model]
                
                # Clean up empty provider entries
                if not data["keys"][provider]:
                    del data["keys"][provider]
                
                self._save_encrypted_data(data)
                self._log_usage("removed", provider, key_info["key_hash"], True)
                
                return True, "API key removed successfully"
            
            return False, "API key not found"
            
        except Exception as e:
            logger.error(f"Failed to remove API key: {e}")
            return False, f"Removal failed: {str(e)}"
    
    def get_usage_stats(self, admin_code: str) -> Optional[Dict]:
        """Get usage statistics (admin only)."""
        if admin_code != self.master_key:
            return None
        
        try:
            data = self._load_encrypted_data()
            
            stats = {
                "total_keys": sum(len(models) for models in data["keys"].values()),
                "providers": list(data["keys"].keys()),
                "total_usage_events": len(data["usage_log"]),
                "recent_activity": data["usage_log"][-10:] if data["usage_log"] else []
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            return None

# Global instance
secure_key_manager = SecureAPIKeyManager()
