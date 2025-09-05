"""
Enterprise-grade authentication system for B-TCRimer.
Provides secure user management, session handling, and role-based access control.
"""

import streamlit as st
import hashlib
import hmac
import secrets
import time
import json
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from utils.logging_config import get_logger
from database.operations import get_db_connection

logger = get_logger(__name__)

class AuthenticationManager:
    """Professional authentication and session management system"""
    
    def __init__(self):
        self.session_timeout = 24 * 60 * 60  # 24 hours in seconds
        self.max_login_attempts = 5
        self.lockout_duration = 15 * 60  # 15 minutes
        
    def hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """Securely hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        # Use PBKDF2 for password hashing (more secure than simple SHA256)
        password_hash = hashlib.pbkdf2_hmac('sha256', 
                                           password.encode('utf-8'), 
                                           salt.encode('utf-8'), 
                                           100000)  # 100k iterations
        
        return password_hash.hex(), salt
    
    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """Verify password against hash"""
        password_hash, _ = self.hash_password(password, salt)
        return hmac.compare_digest(password_hash, hashed_password)
    
    def create_user(self, username: str, password: str, email: str, role: str = "user") -> bool:
        """Create new user account"""
        try:
            # Check if user already exists
            if self.get_user(username):
                logger.warning(f"User creation failed: {username} already exists")
                return False
            
            # Hash password
            password_hash, salt = self.hash_password(password)
            
            # Store user in database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    login_attempts INTEGER DEFAULT 0,
                    lockout_until TIMESTAMP
                )
            """)
            
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, salt, role)
                VALUES (?, ?, ?, ?, ?)
            """, (username, email, password_hash, salt, role))
            
            conn.commit()
            conn.close()
            
            logger.info(f"User created successfully: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating user {username}: {str(e)}")
            return False
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Retrieve user information"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, username, email, password_hash, salt, role, 
                       created_at, last_login, is_active, login_attempts, lockout_until
                FROM users WHERE username = ? AND is_active = 1
            """, (username,))
            
            user_data = cursor.fetchone()
            conn.close()
            
            if user_data:
                return {
                    'id': user_data[0],
                    'username': user_data[1],
                    'email': user_data[2],
                    'password_hash': user_data[3],
                    'salt': user_data[4],
                    'role': user_data[5],
                    'created_at': user_data[6],
                    'last_login': user_data[7],
                    'is_active': user_data[8],
                    'login_attempts': user_data[9],
                    'lockout_until': user_data[10]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving user {username}: {str(e)}")
            return None
    
    def authenticate_user(self, username: str, password: str) -> Tuple[bool, str]:
        """Authenticate user credentials"""
        try:
            user = self.get_user(username)
            
            if not user:
                logger.warning(f"Authentication failed: user {username} not found")
                return False, "Invalid username or password"
            
            # Check if account is locked
            if user['lockout_until']:
                lockout_time = datetime.fromisoformat(user['lockout_until'])
                if datetime.now() < lockout_time:
                    remaining = int((lockout_time - datetime.now()).total_seconds() / 60)
                    return False, f"Account locked. Try again in {remaining} minutes."
            
            # Verify password
            if self.verify_password(password, user['password_hash'], user['salt']):
                # Reset login attempts and update last login
                self._reset_login_attempts(username)
                self._update_last_login(username)
                
                # Create session
                self._create_session(user)
                
                logger.info(f"Successful authentication for user: {username}")
                return True, "Authentication successful"
            else:
                # Increment login attempts
                self._increment_login_attempts(username)
                logger.warning(f"Failed authentication attempt for user: {username}")
                return False, "Invalid username or password"
                
        except Exception as e:
            logger.error(f"Authentication error for {username}: {str(e)}")
            return False, "Authentication system error"
    
    def _increment_login_attempts(self, username: str):
        """Increment failed login attempts and lock account if necessary"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get current attempts
            cursor.execute("SELECT login_attempts FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            
            if result:
                attempts = result[0] + 1
                lockout_until = None
                
                if attempts >= self.max_login_attempts:
                    lockout_until = (datetime.now() + timedelta(seconds=self.lockout_duration)).isoformat()
                    logger.warning(f"Account locked for user {username} due to too many failed attempts")
                
                cursor.execute("""
                    UPDATE users 
                    SET login_attempts = ?, lockout_until = ?
                    WHERE username = ?
                """, (attempts, lockout_until, username))
                
                conn.commit()
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating login attempts for {username}: {str(e)}")
    
    def _reset_login_attempts(self, username: str):
        """Reset failed login attempts after successful login"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users 
                SET login_attempts = 0, lockout_until = NULL
                WHERE username = ?
            """, (username,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error resetting login attempts for {username}: {str(e)}")
    
    def _update_last_login(self, username: str):
        """Update user's last login timestamp"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP
                WHERE username = ?
            """, (username,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating last login for {username}: {str(e)}")
    
    def _create_session(self, user: Dict):
        """Create secure user session"""
        session_token = secrets.token_urlsafe(32)
        session_data = {
            'user_id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role'],
            'session_token': session_token,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(seconds=self.session_timeout)).isoformat()
        }
        
        # Store session in Streamlit session state
        st.session_state.authenticated = True
        st.session_state.user = session_data
        st.session_state.session_token = session_token
        
        logger.info(f"Session created for user: {user['username']}")
    
    def validate_session(self) -> bool:
        """Validate current user session"""
        try:
            if not st.session_state.get('authenticated', False):
                return False
            
            user_data = st.session_state.get('user')
            if not user_data:
                return False
            
            # Check session expiry
            expires_at = datetime.fromisoformat(user_data['expires_at'])
            if datetime.now() > expires_at:
                logger.info(f"Session expired for user: {user_data['username']}")
                self.logout()
                return False
            
            # Extend session if more than half the time has passed
            created_at = datetime.fromisoformat(user_data['created_at'])
            session_age = (datetime.now() - created_at).total_seconds()
            
            if session_age > self.session_timeout / 2:
                # Extend session
                user_data['expires_at'] = (datetime.now() + timedelta(seconds=self.session_timeout)).isoformat()
                st.session_state.user = user_data
                logger.debug(f"Session extended for user: {user_data['username']}")
            
            return True
            
        except Exception as e:
            logger.error(f"Session validation error: {str(e)}")
            return False
    
    def logout(self):
        """Logout user and clear session"""
        username = st.session_state.get('user', {}).get('username', 'unknown')
        
        # Clear session state
        for key in ['authenticated', 'user', 'session_token']:
            if key in st.session_state:
                del st.session_state[key]
        
        logger.info(f"User logged out: {username}")
    
    def get_current_user(self) -> Optional[Dict]:
        """Get current authenticated user"""
        if self.validate_session():
            return st.session_state.get('user')
        return None
    
    def has_role(self, required_role: str) -> bool:
        """Check if current user has required role"""
        user = self.get_current_user()
        if not user:
            return False
        
        role_hierarchy = {
            'user': 0,
            'premium': 1,
            'admin': 2,
            'superadmin': 3
        }
        
        user_level = role_hierarchy.get(user['role'], 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
    
    def require_auth(self, required_role: str = "user"):
        """Decorator/function to require authentication"""
        if not self.validate_session():
            return False
        
        if not self.has_role(required_role):
            st.error(f"Access denied. Required role: {required_role}")
            return False
        
        return True

def create_login_page():
    """Create professional login interface"""
    st.markdown("""
    <div style="max-width: 400px; margin: 2rem auto; padding: 2rem; 
                background: var(--bg-card); border-radius: 15px; 
                box-shadow: var(--shadow-strong);">
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="font-size: 2.5rem; margin-bottom: 1rem;">🔐</div>
            <h2 style="margin: 0; color: var(--text-primary);">Welcome to B-TCRimer</h2>
            <p style="margin: 0.5rem 0 0 0; color: var(--text-secondary);">
                Professional Cryptocurrency Analysis Platform
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        st.markdown("### 🔑 Sign In")
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        col1, col2 = st.columns(2)
        with col1:
            login_button = st.form_submit_button("Sign In", use_container_width=True)
        with col2:
            register_button = st.form_submit_button("Register", use_container_width=True)
        
        if login_button and username and password:
            auth_manager = AuthenticationManager()
            success, message = auth_manager.authenticate_user(username, password)
            
            if success:
                st.success("Login successful! Redirecting...")
                time.sleep(1)
                st.rerun()
            else:
                st.error(message)
        
        elif register_button:
            st.session_state.show_registration = True
            st.rerun()

def create_registration_page():
    """Create user registration interface"""
    st.markdown("### 📝 Create Account")
    
    with st.form("registration_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username*", placeholder="Choose a username")
            password = st.text_input("Password*", type="password", placeholder="Create a password")
            
        with col2:
            email = st.text_input("Email*", placeholder="your@email.com")
            confirm_password = st.text_input("Confirm Password*", type="password", placeholder="Confirm your password")
        
        role = st.selectbox("Account Type", ["user", "premium"], index=0)
        
        col1, col2 = st.columns(2)
        with col1:
            register_button = st.form_submit_button("Create Account", use_container_width=True)
        with col2:
            back_button = st.form_submit_button("Back to Login", use_container_width=True)
        
        if register_button:
            if not all([username, password, email, confirm_password]):
                st.error("Please fill in all required fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            elif len(password) < 8:
                st.error("Password must be at least 8 characters long")
            else:
                auth_manager = AuthenticationManager()
                if auth_manager.create_user(username, password, email, role):
                    st.success("Account created successfully! You can now sign in.")
                    st.session_state.show_registration = False
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Registration failed. Username or email may already exist.")
        
        elif back_button:
            st.session_state.show_registration = False
            st.rerun()

# Global auth manager instance
auth_manager = AuthenticationManager()

def require_authentication(required_role: str = "user"):
    """Check authentication and redirect to login if necessary"""
    if not auth_manager.validate_session():
        if st.session_state.get('show_registration', False):
            create_registration_page()
        else:
            create_login_page()
        st.stop()
    
    if not auth_manager.has_role(required_role):
        st.error(f"⚠️ Access Denied - Required role: {required_role}")
        st.stop()
    
    return True