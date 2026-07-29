from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=True)  # Nullable for Google OAuth users
    google_id = db.Column(db.String(100), unique=True, nullable=True)  # Google OAuth sub ID
    avatar_url = db.Column(db.String(300), nullable=True)  # Profile picture from Google
    role = db.Column(db.String(20), nullable=False, default='student') # admin, teacher, student
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attempts = db.relationship('Attempt', back_populates='user', cascade='all, delete-orphan')
    quizzes_created = db.relationship('Quiz', back_populates='creator')

    def __init__(self, name=None, email=None, role='student', google_id=None, avatar_url=None, password_hash=None, **kwargs):
        super(User, self).__init__(**kwargs)
        if name is not None:
            self.name = name
        if email is not None:
            self.email = email
        if role is not None:
            self.role = role
        if google_id is not None:
            self.google_id = google_id
        if avatar_url is not None:
            self.avatar_url = avatar_url
        if password_hash is not None:
            self.password_hash = password_hash

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        if not self.password_hash:
            return False  # Google-only accounts have no password
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_teacher(self):
        return self.role == 'teacher'

    @property
    def is_student(self):
        return self.role == 'student'

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
