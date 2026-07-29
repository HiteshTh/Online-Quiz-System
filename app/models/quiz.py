from datetime import datetime
from app.extensions import db

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Relationships
    quizzes = db.relationship('Quiz', back_populates='category', cascade='all, delete-orphan')

    def __init__(self, name=None, **kwargs):
        super(Category, self).__init__(**kwargs)
        if name is not None:
            self.name = name

    def __repr__(self):
        return f'<Category {self.name}>'


class Quiz(db.Model):
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False, default=30)
    shuffle_questions = db.Column(db.Boolean, nullable=False, default=False)
    negative_marking = db.Column(db.Boolean, nullable=False, default=False)
    negative_mark_value = db.Column(db.Float, nullable=False, default=0.25)
    pass_percentage = db.Column(db.Integer, nullable=False, default=50)
    is_published = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    category = db.relationship('Category', back_populates='quizzes')
    creator = db.relationship('User', back_populates='quizzes_created')
    questions = db.relationship('Question', back_populates='quiz', cascade='all, delete-orphan')
    attempts = db.relationship('Attempt', back_populates='quiz', cascade='all, delete-orphan')

    def __init__(self, title=None, description=None, category_id=None, created_by=None, duration_minutes=30, shuffle_questions=False, negative_marking=False, negative_mark_value=0.25, pass_percentage=50, is_published=False, **kwargs):
        super(Quiz, self).__init__(**kwargs)
        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        if category_id is not None:
            self.category_id = category_id
        if created_by is not None:
            self.created_by = created_by
        self.duration_minutes = duration_minutes
        self.shuffle_questions = shuffle_questions
        self.negative_marking = negative_marking
        self.negative_mark_value = negative_mark_value
        self.pass_percentage = pass_percentage
        self.is_published = is_published

    def __repr__(self):
        return f'<Quiz {self.title}>'
