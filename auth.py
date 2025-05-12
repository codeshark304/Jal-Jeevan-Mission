import hashlib
import os
from flask_login import UserMixin, LoginManager
from models import User, db

class UserLogin(UserMixin):
    def __init__(self, user):
        self.id = user.user_id
        self.username = user.username
        self.role = user.role
    
    @classmethod
    def get(cls, user_id):
        user = User.query.filter_by(user_id=user_id).first()
        if user:
            return cls(user)
        return None

# Initialize login manager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return UserLogin.get(int(user_id))

def hash_password(password):
    """Hash a password for storage"""
    salt = os.environ.get('PASSWORD_SALT', 'jjm_default_salt')
    salted = password + salt
    return hashlib.sha256(salted.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    """Verify a stored password against a provided password"""
    hashed_provided = hash_password(provided_password)
    return stored_password == hashed_provided

def create_user(username, password, role):
    """Create a new user"""
    # Check if user already exists
    if User.query.filter_by(username=username).first():
        return False, "Username already exists"
    
    # Create and save the user
    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role
    )
    
    try:
        db.session.add(user)
        db.session.commit()
        return True, "User created successfully"
    except Exception as e:
        db.session.rollback()
        return False, f"Error creating user: {str(e)}"

def authenticate_user(username, password):
    """Authenticate a user"""
    user = User.query.filter_by(username=username).first()
    if not user:
        return None
    
    if verify_password(user.password_hash, password):
        return UserLogin(user)
    
    return None

def is_admin(user):
    """Check if a user is an admin"""
    return user.role == 'admin'