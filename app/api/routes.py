from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user, login_user
from app.extensions import db
from app.models import User, Quiz, Question, Option, Attempt, Answer, Category

api_bp = Blueprint('api', __name__)

@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    """
    API User Login
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: student@domain.com
            password:
              type: string
              example: password123
    responses:
      200:
        description: Successful login, session established.
      401:
        description: Invalid credentials.
    """
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        login_user(user)
        return jsonify({
            'success': True,
            'message': 'Logged in successfully',
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role
            }
        }), 200
        
    return jsonify({'success': False, 'message': 'Invalid email or password'}), 401


@api_bp.route('/quizzes', methods=['GET'])
def get_published_quizzes():
    """
    List Published Quizzes
    ---
    responses:
      200:
        description: A list of published quizzes.
    """
    quizzes = Quiz.query.filter_by(is_published=True).all()
    results = []
    for q in quizzes:
        results.append({
            'id': q.id,
            'title': q.title,
            'description': q.description,
            'duration_minutes': q.duration_minutes,
            'category': q.category.name,
            'question_count': len(q.questions)
        })
    return jsonify(results), 200


@api_bp.route('/quizzes/<int:quiz_id>/questions', methods=['GET'])
@login_required
def get_quiz_questions(quiz_id):
    """
    Retrieve Quiz Questions (Correct Answers Masked)
    ---
    responses:
      200:
        description: Details of the quiz questions and option choices. Correct option flags are hidden.
    """
    quiz = Quiz.query.filter_by(id=quiz_id, is_published=True).first_or_404()
    questions_data = []
    
    for q in quiz.questions:
        options = []
        for opt in q.options:
            options.append({
                'id': opt.id,
                'option_text': opt.option_text
            })
            
        questions_data.append({
            'id': q.id,
            'question_text': q.question_text,
            'question_type': q.question_type,
            'marks': q.marks,
            'difficulty': q.difficulty,
            'options': options
        })
        
    return jsonify({
        'quiz_id': quiz.id,
        'title': quiz.title,
        'duration_minutes': quiz.duration_minutes,
        'questions': questions_data
    }), 200


@api_bp.route('/attempts', methods=['POST'])
@login_required
def start_api_attempt():
    """
    Register and Start a Quiz Attempt
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - quiz_id
          properties:
            quiz_id:
              type: integer
              example: 1
    responses:
      201:
        description: Attempt registered successfully.
    """
    data = request.get_json() or {}
    quiz_id = data.get('quiz_id')
    if not quiz_id:
        return jsonify({'error': 'quiz_id is required'}), 400
        
    quiz = Quiz.query.filter_by(id=quiz_id, is_published=True).first_or_404()
    
    # Check for active attempts
    active = Attempt.query.filter_by(user_id=current_user.id, quiz_id=quiz.id, status='in_progress').first()
    if active:
        return jsonify({
            'message': 'Attempt already in progress',
            'attempt_id': active.id
        }), 200
        
    attempt = Attempt(
        user_id=current_user.id,
        quiz_id=quiz.id,
        status='in_progress'
    )
    db.session.add(attempt)
    db.session.commit()
    
    return jsonify({
        'message': 'Attempt started',
        'attempt_id': attempt.id
    }), 201


@api_bp.route('/attempts/<int:attempt_id>/submit', methods=['POST'])
@login_required
def submit_api_attempt(attempt_id):
    """
    Submit Attempt Answers
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - answers
          properties:
            answers:
              type: object
              description: Mapping of question ID to answer input
              example: {"1": "3", "2": "True", "3": "print"}
    responses:
      200:
        description: Attempt scored and recorded. Returns final score.
    """
    attempt = Attempt.query.get_or_404(attempt_id)
    if attempt.user_id != current_user.id or attempt.status != 'in_progress':
        return jsonify({'error': 'Attempt cannot be modified'}), 400
        
    data = request.get_json() or {}
    answers_map = data.get('answers', {})
    
    score = 0.0
    total_marks = 0
    
    for question in attempt.quiz.questions:
        total_marks += question.marks
        user_answer = answers_map.get(str(question.id))
        
        selected_option_id = None
        text_answer = None
        is_correct = False
        
        if question.question_type in ['mcq', 'true_false']:
            if user_answer:
                try:
                    selected_option_id = int(user_answer)
                    opt = Option.query.get(selected_option_id)
                    if opt and opt.is_correct:
                        is_correct = True
                except ValueError:
                    pass
        elif question.question_type == 'fill_blank':
            if user_answer:
                text_answer = str(user_answer).strip()
                correct_opt = Option.query.filter_by(question_id=question.id, is_correct=True).first()
                if correct_opt and correct_opt.option_text.strip().lower() == text_answer.lower():
                    is_correct = True
                    
        if is_correct:
            score += question.marks
        else:
            if attempt.quiz.negative_marking:
                score -= attempt.quiz.negative_mark_value
                
        ans = Answer(
            attempt_id=attempt.id,
            question_id=question.id,
            selected_option_id=selected_option_id,
            text_answer=text_answer,
            is_correct=is_correct
        )
        db.session.add(ans)
        
    if score < 0.0:
        score = 0.0
        
    attempt.score = round(score, 2)
    attempt.total_marks = total_marks
    attempt.submitted_at = db.func.current_timestamp()
    attempt.status = 'submitted'
    
    db.session.commit()
    return jsonify({
        'message': 'Attempt submitted',
        'score': attempt.score,
        'total_marks': attempt.total_marks,
        'percentage': attempt.percentage,
        'passed': attempt.is_passed
    }), 200
