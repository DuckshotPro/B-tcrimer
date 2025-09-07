"""
Comprehensive authentication system tests for B-TCRimer.
Tests user management, session handling, and security features.
"""

import pytest
import tempfile
import os
import time
from datetime import datetime, timedelta
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.auth import AuthenticationManager
from utils.logging_config import setup_logging

# Setup logging for tests
setup_logging()

class TestAuthenticationManager:
    """Test suite for authentication system"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        db_fd, db_path = tempfile.mkstemp()
        yield db_path
        os.close(db_fd)
        os.unlink(db_path)
    
    @pytest.fixture
    def auth_manager(self, temp_db):
        """Create authentication manager with temporary database"""
        # Mock the get_db_connection to use our temp database
        import sqlite3
        original_get_db_connection = None
        
        def mock_get_db_connection():
            return sqlite3.connect(temp_db)
        
        # Monkey patch for testing
        import utils.auth
        if hasattr(utils.auth, 'get_db_connection'):
            original_get_db_connection = utils.auth.get_db_connection
            utils.auth.get_db_connection = mock_get_db_connection
        
        auth_manager = AuthenticationManager()
        
        yield auth_manager
        
        # Restore original function
        if original_get_db_connection:
            utils.auth.get_db_connection = original_get_db_connection
    
    def test_password_hashing(self, auth_manager):
        """Test password hashing and verification"""
        password = "test_password_123"
        
        # Test hashing
        password_hash, salt = auth_manager.hash_password(password)
        
        assert password_hash is not None
        assert salt is not None
        assert len(salt) == 64  # 32 bytes in hex
        assert len(password_hash) == 64  # 32 bytes in hex
        
        # Test verification
        assert auth_manager.verify_password(password, password_hash, salt)
        assert not auth_manager.verify_password("wrong_password", password_hash, salt)
    
    def test_create_user(self, auth_manager):
        """Test user creation"""
        username = "testuser"
        password = "secure_password_123"
        email = "test@example.com"
        role = "user"
        
        # Create user
        result = auth_manager.create_user(username, password, email, role)
        assert result is True
        
        # Verify user exists
        user = auth_manager.get_user(username)
        assert user is not None
        assert user['username'] == username
        assert user['email'] == email
        assert user['role'] == role
        assert user['is_active'] == 1
        
        # Test duplicate user creation fails
        result = auth_manager.create_user(username, password, email, role)
        assert result is False
    
    def test_user_authentication(self, auth_manager):
        """Test user authentication"""
        username = "authtest"
        password = "test_password_456"
        email = "auth@example.com"
        
        # Create user first
        auth_manager.create_user(username, password, email)
        
        # Test successful authentication
        success, message = auth_manager.authenticate_user(username, password)
        assert success is True
        assert "successful" in message.lower()
        
        # Test failed authentication
        success, message = auth_manager.authenticate_user(username, "wrong_password")
        assert success is False
        assert "invalid" in message.lower()
        
        # Test non-existent user
        success, message = auth_manager.authenticate_user("nonexistent", password)
        assert success is False
        assert "invalid" in message.lower()
    
    def test_account_lockout(self, auth_manager):
        """Test account lockout after failed attempts"""
        username = "lockouttest"
        password = "correct_password"
        email = "lockout@example.com"
        
        # Create user
        auth_manager.create_user(username, password, email)
        
        # Perform multiple failed login attempts
        for i in range(auth_manager.max_login_attempts):
            success, message = auth_manager.authenticate_user(username, "wrong_password")
            assert success is False
        
        # Account should be locked now
        success, message = auth_manager.authenticate_user(username, password)
        assert success is False
        assert "locked" in message.lower()
    
    def test_role_hierarchy(self, auth_manager):
        """Test role-based access control"""
        # Create users with different roles
        users = [
            ("user1", "password", "user1@example.com", "user"),
            ("premium1", "password", "premium1@example.com", "premium"),
            ("admin1", "password", "admin1@example.com", "admin"),
            ("super1", "password", "super1@example.com", "superadmin")
        ]
        
        for username, password, email, role in users:
            auth_manager.create_user(username, password, email, role)
        
        # Mock session state for role testing
        import streamlit as st
        
        # Test user role
        st.session_state = {}
        auth_manager.authenticate_user("user1", "password")
        assert auth_manager.has_role("user") is True
        assert auth_manager.has_role("premium") is False
        assert auth_manager.has_role("admin") is False
        
        # Test admin role
        st.session_state = {}
        auth_manager.authenticate_user("admin1", "password")
        assert auth_manager.has_role("user") is True
        assert auth_manager.has_role("premium") is True
        assert auth_manager.has_role("admin") is True
        assert auth_manager.has_role("superadmin") is False

class TestSecurityFeatures:
    """Test security-related features"""
    
    def test_sql_injection_protection(self):
        """Test protection against SQL injection attacks"""
        auth_manager = AuthenticationManager()
        
        # Attempt SQL injection in username
        malicious_username = "'; DROP TABLE users; --"
        password = "password"
        
        # Should not crash or succeed
        success, message = auth_manager.authenticate_user(malicious_username, password)
        assert success is False
        
        # Test in password field
        normal_username = "testuser"
        malicious_password = "' OR '1'='1"
        
        success, message = auth_manager.authenticate_user(normal_username, malicious_password)
        assert success is False
    
    def test_session_security(self):
        """Test session security features"""
        auth_manager = AuthenticationManager()
        
        # Create test user
        username = "sessiontest"
        password = "password"
        email = "session@example.com"
        auth_manager.create_user(username, password, email)
        
        # Mock Streamlit session state
        import streamlit as st
        st.session_state = {}
        
        # Authenticate user
        success, message = auth_manager.authenticate_user(username, password)
        assert success is True
        
        # Check session was created
        assert 'authenticated' in st.session_state
        assert 'user' in st.session_state
        assert 'session_token' in st.session_state
        
        # Validate session
        assert auth_manager.validate_session() is True
        
        # Test logout
        auth_manager.logout()
        assert 'authenticated' not in st.session_state
        assert auth_manager.validate_session() is False

def run_authentication_tests():
    """Run all authentication tests manually"""
    import traceback
    
    print("🧪 Running Authentication Tests...")
    
    test_results = {
        'passed': 0,
        'failed': 0,
        'errors': []
    }
    
    # Create test instance
    auth_manager = AuthenticationManager()
    
    try:
        # Test 1: Password Hashing
        print("  Testing password hashing...")
        password = "test_password_123"
        password_hash, salt = auth_manager.hash_password(password)
        
        assert password_hash and salt
        assert auth_manager.verify_password(password, password_hash, salt)
        assert not auth_manager.verify_password("wrong", password_hash, salt)
        
        test_results['passed'] += 1
        print("  ✅ Password hashing test passed")
        
    except Exception as e:
        test_results['failed'] += 1
        test_results['errors'].append(f"Password hashing: {str(e)}")
        print(f"  ❌ Password hashing test failed: {str(e)}")
    
    try:
        # Test 2: User Creation
        print("  Testing user creation...")
        result = auth_manager.create_user("testuser", "password", "test@example.com", "user")
        assert result is True
        
        user = auth_manager.get_user("testuser")
        assert user is not None
        assert user['username'] == "testuser"
        
        test_results['passed'] += 1
        print("  ✅ User creation test passed")
        
    except Exception as e:
        test_results['failed'] += 1
        test_results['errors'].append(f"User creation: {str(e)}")
        print(f"  ❌ User creation test failed: {str(e)}")
    
    try:
        # Test 3: Authentication
        print("  Testing authentication...")
        success, message = auth_manager.authenticate_user("testuser", "password")
        assert success is True
        
        success, message = auth_manager.authenticate_user("testuser", "wrong")
        assert success is False
        
        test_results['passed'] += 1
        print("  ✅ Authentication test passed")
        
    except Exception as e:
        test_results['failed'] += 1
        test_results['errors'].append(f"Authentication: {str(e)}")
        print(f"  ❌ Authentication test failed: {str(e)}")
    
    # Print results
    print(f"\n🧪 Authentication Test Results:")
    print(f"  ✅ Passed: {test_results['passed']}")
    print(f"  ❌ Failed: {test_results['failed']}")
    
    if test_results['errors']:
        print(f"  🚨 Errors:")
        for error in test_results['errors']:
            print(f"    - {error}")
    
    return test_results

if __name__ == "__main__":
    run_authentication_tests()