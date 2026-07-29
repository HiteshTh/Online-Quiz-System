from datetime import datetime
from app.extensions import db

class Attempt(db.Model):
    __tablename__ = 'attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_at = db.Column(db.DateTime, nullable=True)
    score = db.Column(db.Float, default=0.0)
    total_marks = db.Column(db.Integer, default=0)
    status = db.Column(db.String(30), nullable=False, default='in_progress') # in_progress, submitted, auto_submitted
    tab_switch_count = db.Column(db.Integer, nullable=False, default=0)
    
    # Relationships
    user = db.relationship('User', back_populates='attempts')
    quiz = db.relationship('Quiz', back_populates='attempts')
    answers = db.relationship('Answer', back_populates='attempt', cascade='all, delete-orphan')

    def __init__(self, user_id=None, quiz_id=None, status='in_progress', **kwargs):
        super(Attempt, self).__init__(**kwargs)
        if user_id is not None:
            self.user_id = user_id
        if quiz_id is not None:
            self.quiz_id = quiz_id
        if status is not None:
            self.status = status

    @property
    def percentage(self):
        if self.total_marks == 0:
            return 0.0
        return round((self.score / self.total_marks) * 100, 2)

    @property
    def is_passed(self):
        return self.percentage >= self.quiz.pass_percentage

    def __repr__(self):
        return f'<Attempt {self.id} of Quiz {self.quiz_id} by User {self.user_id}>'


class Answer(db.Model):
    __tablename__ = 'answers'
    
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('attempts.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    selected_option_id = db.Column(db.Integer, db.ForeignKey('options.id'), nullable=True)
    text_answer = db.Column(db.String(255), nullable=True) # For Fill in the blank
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    
    # Relationships
    attempt = db.relationship('Attempt', back_populates='answers')
    question = db.relationship('Question', back_populates='answers')
    selected_option = db.relationship('Option')

    def __init__(self, attempt_id=None, question_id=None, selected_option_id=None, text_answer=None, is_correct=False, **kwargs):
        super(Answer, self).__init__(**kwargs)
        if attempt_id is not None:
            self.attempt_id = attempt_id
        if question_id is not None:
            self.question_id = question_id
        if selected_option_id is not None:
            self.selected_option_id = selected_option_id
        if text_answer is not None:
            self.text_answer = text_answer
        self.is_correct = is_correct

    def __repr__(self):
        return f'<Answer {self.id} to Question {self.question_id} in Attempt {self.attempt_id}>'

