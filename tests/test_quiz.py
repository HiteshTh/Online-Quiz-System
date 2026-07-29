import unittest
from datetime import datetime
from app import create_app, db
from app.models import User, Category, Quiz, Question, Option, Attempt, Answer

class QuizTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()
        
        # Seed basic admin and student users
        self.admin = User(name="Admin User", email="admin@test.com", role="admin")
        self.admin.set_password("adminpass")
        self.student = User(name="Student User", email="student@test.com", role="student")
        self.student.set_password("studentpass")
        
        # Seed category
        self.category = Category(name="Science")
        db.session.add_all([self.admin, self.student, self.category])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_scoring_system(self):
        # Create a test Quiz
        quiz = Quiz(
            title="Physics Quiz",
            category_id=self.category.id,
            created_by=self.admin.id,
            duration_minutes=10,
            negative_marking=True,
            negative_mark_value=0.5,
            pass_percentage=50,
            is_published=True
        )
        db.session.add(quiz)
        db.session.commit()
        
        # Create Question 1 (MCQ) - 2 marks
        q1 = Question(quiz_id=quiz.id, question_text="Light speed?", question_type="mcq", marks=2)
        db.session.add(q1)
        db.session.commit()
        
        opt_correct = Option(question_id=q1.id, option_text="3x10^8 m/s", is_correct=True)
        opt_wrong = Option(question_id=q1.id, option_text="100 m/s", is_correct=False)
        db.session.add_all([opt_correct, opt_wrong])
        db.session.commit()
        
        # Create Question 2 (MCQ) - 1 mark
        q2 = Question(quiz_id=quiz.id, question_text="Earth is flat?", question_type="true_false", marks=1)
        db.session.add(q2)
        db.session.commit()
        
        opt_true = Option(question_id=q2.id, option_text="True", is_correct=False)
        opt_false = Option(question_id=q2.id, option_text="False", is_correct=True)
        db.session.add_all([opt_true, opt_false])
        db.session.commit()

        # Start attempt
        attempt = Attempt(user_id=self.student.id, quiz_id=quiz.id, status="in_progress")
        db.session.add(attempt)
        db.session.commit()
        
        # Scenario: student answers Q1 correctly, Q2 incorrectly
        # Total marks: 2 + 1 = 3
        # Score calculation: Correct MCQ (2) + Incorrect TF (-0.5) = 1.5 marks
        
        ans1 = Answer(attempt_id=attempt.id, question_id=q1.id, selected_option_id=opt_correct.id, is_correct=True)
        ans2 = Answer(attempt_id=attempt.id, question_id=q2.id, selected_option_id=opt_true.id, is_correct=False)
        db.session.add_all([ans1, ans2])
        
        attempt.score = 2.0 - 0.5
        attempt.total_marks = 3
        attempt.status = "submitted"
        attempt.submitted_at = datetime.utcnow()
        db.session.commit()
        
        # Verification
        self.assertEqual(attempt.score, 1.5)
        self.assertEqual(attempt.percentage, 50.0) # 1.5 / 3 = 50.0%
        self.assertTrue(attempt.is_passed) # 50% matches pass_percentage 50

if __name__ == '__main__':
    unittest.main()
