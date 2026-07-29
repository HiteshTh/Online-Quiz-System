import os
from app import create_app, db
from app.extensions import socketio
from app.models.user import User
from app.models.quiz import Category, Quiz
from app.models.question import Question, Option

app = create_app(os.environ.get('FLASK_ENV', 'development'))

# Ensure database tables and demo seed data are initialized
with app.app_context():
    db.create_all()
    
    # Check if we already have users, if not, seed default demo accounts
    if not User.query.first():
        print("Database is empty. Seeding demo accounts and mock quiz...")
        
        # 1. Demo Admin/Teacher
        admin = User(name="Examiner Admin", email="admin@quizverse.com", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)
        
        # 2. Demo Student
        student = User(name="John Doe", email="student@quizverse.com", role="student")
        student.set_password("student123")
        db.session.add(student)
        
        db.session.flush() # Flush to get user IDs
        
        # 3. Seed Category
        gk_cat = Category(name="General Knowledge")
        python_cat = Category(name="Python Programming")
        db.session.add(gk_cat)
        db.session.add(python_cat)
        db.session.flush()
        
        # 4. Seed a default Python Quiz
        quiz = Quiz(
            title="Python Fundamentals Challenge",
            description="A quick diagnostic assessment on Python variables, syntax, loops, and functions. Features negative marking and randomized presentation.",
            category_id=python_cat.id,
            created_by=admin.id,
            duration_minutes=5,
            shuffle_questions=True,
            negative_marking=True,
            negative_mark_value=0.25,
            pass_percentage=50,
            is_published=True
        )
        db.session.add(quiz)
        db.session.flush()
        
        # 5. Add Question 1 (MCQ)
        q1 = Question(
            quiz_id=quiz.id,
            question_text="Which of the following data types is immutable in Python?",
            question_type="mcq",
            marks=2,
            difficulty="easy"
        )
        db.session.add(q1)
        db.session.flush()
        
        o1 = Option(question_id=q1.id, option_text="List", is_correct=False)
        o2 = Option(question_id=q1.id, option_text="Dictionary", is_correct=False)
        o3 = Option(question_id=q1.id, option_text="Tuple", is_correct=True)
        o4 = Option(question_id=q1.id, option_text="Set", is_correct=False)
        db.session.add_all([o1, o2, o3, o4])
        
        # 6. Add Question 2 (True/False)
        q2 = Question(
            quiz_id=quiz.id,
            question_text="The 'elif' keyword in Python is short for 'else if'.",
            question_type="true_false",
            marks=1,
            difficulty="easy"
        )
        db.session.add(q2)
        db.session.flush()
        
        o_t = Option(question_id=q2.id, option_text="True", is_correct=True)
        o_f = Option(question_id=q2.id, option_text="False", is_correct=False)
        db.session.add_all([o_t, o_f])
        
        # 7. Add Question 3 (Fill-in-the-blank)
        q3 = Question(
            quiz_id=quiz.id,
            question_text="Which Python keyword is used to define a user-created function?",
            question_type="fill_blank",
            marks=2,
            difficulty="easy"
        )
        db.session.add(q3)
        db.session.flush()
        
        o_ans = Option(question_id=q3.id, option_text="def", is_correct=True)
        db.session.add(o_ans)
        
        db.session.commit()
        print("Database seeding completed successfully!")

if __name__ == '__main__':
    # Run the Flask-SocketIO server on localhost port 5000
    socketio.run(app, host='127.0.0.1', port=5000, debug=True, allow_unsafe_werkzeug=True)
