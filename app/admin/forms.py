from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, BooleanField, FloatField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length

class QuizForm(FlaskForm):
    title = StringField('Quiz Title', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Description')
    category_name = StringField('Category', validators=[DataRequired(), Length(max=50)])
    duration_minutes = IntegerField('Duration (Minutes)', validators=[
        DataRequired(), 
        NumberRange(min=1, max=480, message="Duration must be between 1 and 480 minutes.")
    ], default=30)
    shuffle_questions = BooleanField('Shuffle Questions')
    negative_marking = BooleanField('Enable Negative Marking')
    negative_mark_value = FloatField('Negative Mark Value (e.g. 0.25)', validators=[
        NumberRange(min=0.0, max=10.0, message="Value must be non-negative.")
    ], default=0.25)
    pass_percentage = IntegerField('Passing Percentage', validators=[
        DataRequired(),
        NumberRange(min=0, max=100, message="Passing percentage must be between 0 and 100.")
    ], default=50)
    is_published = BooleanField('Publish Instantly')
    submit = SubmitField('Save Quiz')

class QuestionForm(FlaskForm):
    question_text = TextAreaField('Question Text', validators=[DataRequired()])
    question_type = SelectField('Question Type', choices=[
        ('mcq', 'Multiple Choice (MCQ)'),
        ('true_false', 'True / False'),
        ('fill_blank', 'Fill in the Blank')
    ], default='mcq')
    marks = IntegerField('Marks', validators=[
        DataRequired(),
        NumberRange(min=1, max=100, message="Marks must be at least 1.")
    ], default=1)
    difficulty = SelectField('Difficulty Level', choices=[
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ], default='medium')
    submit = SubmitField('Save Question')
