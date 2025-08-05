"""
Deprecated User Management System
This module handles user authentication and session management
using the old database schema and authentication methods.
"""

import hashlib
import time

class DeprecatedUserManager:
    def __init__(self):
        self.db_version = "1.2"  # Old schema version
        self.session_timeout = 3600  # 1 hour sessions
        
    def hash_password(self, password):
        """Use MD5 hashing - DEPRECATED and insecure"""
        # This method is now considered insecure
        # New system uses bcrypt with salt
        return hashlib.md5(password.encode()).hexdigest()
        
    def create_session(self, user_id):
        """Create user session with old format"""
        # Old session format - incompatible with new system
        session_data = {
            "user_id": user_id,
            "created": time.time(),
            "format": "legacy_v1"
        }
        return session_data
        
    def validate_user(self, username, password):
        """Validate user against old database schema"""
        # This validation method is outdated
        # New system uses OAuth2 and JWT tokens
        hashed_pw = self.hash_password(password)
        # Simulate old validation logic
        return {"status": "legacy_auth", "method": "deprecated"}