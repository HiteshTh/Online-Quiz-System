from app.extensions import db

class Question(db.Model):
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False, default='mcq') # mcq, true_false, fill_blank
    marks = db.Column(db.Integer, nullable=False, default=1)
    difficulty = db.Column(db.String(20), nullable=False, default='medium') # easy, medium, hard
    
    # Relationships
    quiz = db.relationship('Quiz', back_populates='questions')
    options = db.relationship('Option', back_populates='question', cascade='all, delete-orphan')
    answers = db.relationship('Answer', back_populates='question', cascade='all, delete-orphan')

    def __init__(self, quiz_id=None, question_text=None, question_type='mcq', marks=1, difficulty='medium', **kwargs):
        super(Question, self).__init__(**kwargs)
        if quiz_id is not None:
            self.quiz_id = quiz_id
        if question_text is not None:
            self.question_text = question_text
        self.question_type = question_type
        self.marks = marks
        self.difficulty = difficulty

    def __repr__(self):
        return f'<Question {self.id} in Quiz {self.quiz_id}>'


class Option(db.Model):
    __tablename__ = 'options'
    
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    option_text = db.Column(db.String(255), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    
    # Relationships
    question = db.relationship('Question', back_populates='options')

    def __init__(self, question_id=None, option_text=None, is_correct=False, **kwargs):
        super(Option, self).__init__(**kwargs)
        if question_id is not None:
            self.question_id = question_id
        if option_text is not None:
            self.option_text = option_text
        self.is_correct = is_correct

    def __repr__(self):
        return f'<Option {self.id} for Question {self.question_id}>'
