import random
from io import BytesIO
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify, send_file
from flask_login import login_required, current_user
from app.extensions import db, socketio
from app.models import User, Category, Quiz, Question, Option, Attempt, Answer
from app.utils.decorators import role_required
from app.utils.certificate import generate_pdf_certificate
from app.utils.mail import send_email

student_bp = Blueprint('student', __name__)

@student_bp.before_request
@login_required
@role_required('student')
def restrict_student_access():
    pass

@student_bp.route('/dashboard')
def dashboard():
    categories = Category.query.all()
    
    # Fetch filter parameters
    search_query = request.args.get('q', '').strip()
    category_id = request.args.get('category', type=int)
    
    query = Quiz.query.filter_by(is_published=True)
    if search_query:
        query = query.filter(Quiz.title.ilike(f'%{search_query}%'))
    if category_id:
        query = query.filter_by(category_id=category_id)
        
    quizzes = query.all()
    
    # Fetch student attempts
    attempts = Attempt.query.filter_by(user_id=current_user.id).order_by(Attempt.started_at.desc()).all()
    completed_quiz_ids = {att.quiz_id for att in attempts if att.status != 'in_progress'}
    
    # Selected category for UI state
    selected_category_id = category_id if category_id else None
    
    return render_template(
        'student/dashboard.html',
        categories=categories,
        quizzes=quizzes,
        attempts=attempts,
        completed_quiz_ids=completed_quiz_ids,
        search_query=search_query,
        selected_category_id=selected_category_id
    )

@student_bp.route('/quiz/<int:quiz_id>/intro')
def quiz_intro(quiz_id):
    quiz = Quiz.query.filter_by(id=quiz_id, is_published=True).first_or_404()
    
    # Check if student already has a completed attempt
    completed_attempt = Attempt.query.filter_by(
        user_id=current_user.id, 
        quiz_id=quiz.id
    ).filter(Attempt.status != 'in_progress').first()
    
    if completed_attempt:
        flash("You have already completed this examination.", "warning")
        return redirect(url_for('student.dashboard'))
    
    # Check if student already has a pending attempt in progress
    active_attempt = Attempt.query.filter_by(
        user_id=current_user.id, 
        quiz_id=quiz.id, 
        status='in_progress'
    ).first()
    
    return render_template('student/quiz_intro.html', quiz=quiz, active_attempt=active_attempt)

@student_bp.route('/quiz/<int:quiz_id>/attempt/start', methods=['POST'])
def start_attempt(quiz_id):
    quiz = Quiz.query.filter_by(id=quiz_id, is_published=True).first_or_404()
    
    # Check if already completed
    completed_attempt = Attempt.query.filter_by(
        user_id=current_user.id, 
        quiz_id=quiz.id
    ).filter(Attempt.status != 'in_progress').first()
    
    if completed_attempt:
        flash("You have already completed this examination.", "warning")
        return redirect(url_for('student.dashboard'))
        
    # Check if there's already an active attempt
    active_attempt = Attempt.query.filter_by(
        user_id=current_user.id, 
        quiz_id=quiz.id, 
        status='in_progress'
    ).first()
    
    if active_attempt:
        return redirect(url_for('student.attempt_quiz', attempt_id=active_attempt.id))
        
    # Create new attempt
    attempt = Attempt(
        user_id=current_user.id,
        quiz_id=quiz.id,
        status='in_progress'
    )
    
    db.session.add(attempt)
    db.session.commit()
    
    return redirect(url_for('student.attempt_quiz', attempt_id=attempt.id))

@student_bp.route('/attempt/<int:attempt_id>')
def attempt_quiz(attempt_id):
    attempt = Attempt.query.get_or_404(attempt_id)
    
    if attempt.user_id != current_user.id:
        abort(403)
        
    if attempt.status != 'in_progress':
        return redirect(url_for('student.quiz_results', attempt_id=attempt.id))
        
    # Calculate time remaining
    elapsed_seconds = (datetime.utcnow() - attempt.started_at).total_seconds()
    total_seconds = attempt.quiz.duration_minutes * 60
    seconds_left = total_seconds - elapsed_seconds
    
    if seconds_left <= 0:
        # Auto submit immediately
        return redirect(url_for('student.submit_quiz', attempt_id=attempt.id, auto=True))
        
    # Load questions (shuffle if quiz configured to do so)
    questions = list(attempt.quiz.questions)
    if attempt.quiz.shuffle_questions:
        # We want to keep the same order for the session.
        # To avoid re-shuffling on page reload, we can seed the randomizer with the attempt ID!
        random.seed(attempt.id)
        random.shuffle(questions)
        
    return render_template(
        'student/attempt.html', 
        attempt=attempt, 
        questions=questions, 
        seconds_left=int(seconds_left)
    )

@student_bp.route('/attempt/<int:attempt_id>/flag', methods=['POST'])
def flag_attempt(attempt_id):
    attempt = Attempt.query.get_or_404(attempt_id)
    if attempt.user_id != current_user.id or attempt.status != 'in_progress':
        return jsonify({'error': 'Unauthorized'}), 403
        
    attempt.tab_switch_count += 1
    db.session.commit()
    return jsonify({
        'tab_switch_count': attempt.tab_switch_count,
        'action': 'none' if attempt.tab_switch_count < 3 else 'force_submit'
    })

@student_bp.route('/attempt/<int:attempt_id>/submit', methods=['POST'])
def submit_quiz(attempt_id):
    attempt = Attempt.query.get_or_404(attempt_id)
    if attempt.user_id != current_user.id or attempt.status != 'in_progress':
        return redirect(url_for('student.dashboard'))
        
    # Check server side timeout validation (grace: 12 seconds)
    elapsed_seconds = (datetime.utcnow() - attempt.started_at).total_seconds()
    total_seconds = attempt.quiz.duration_minutes * 60
    is_timeout = elapsed_seconds > (total_seconds + 12)
    
    # Check if force submitted via anti-cheat flag
    is_flag_submitted = request.form.get('flag_submit') == 'true' or attempt.tab_switch_count >= 3
    
    score = 0.0
    total_marks = 0
    
    for question in attempt.quiz.questions:
        total_marks += question.marks
        user_answer = request.form.get(f'question_{question.id}')
        
        selected_option_id = None
        text_answer = None
        is_correct = False
        
        # Check answer correctness
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
                text_answer = user_answer.strip()
                # Get the correct Option which holds the blank target phrase
                correct_opt = Option.query.filter_by(question_id=question.id, is_correct=True).first()
                if correct_opt and correct_opt.option_text.strip().lower() == text_answer.lower():
                    is_correct = True
                    
        # Apply marks / negative marking
        if is_correct:
            score += question.marks
        else:
            if attempt.quiz.negative_marking:
                score -= attempt.quiz.negative_mark_value
                
        # Record response
        ans = Answer(
            attempt_id=attempt.id,
            question_id=question.id,
            selected_option_id=selected_option_id,
            text_answer=text_answer,
            is_correct=is_correct
        )
        db.session.add(ans)
        
    # Cap negative scores at 0.0
    if score < 0.0:
        score = 0.0
        
    # Save attempt
    attempt.score = round(score, 2)
    attempt.total_marks = total_marks
    attempt.submitted_at = datetime.utcnow()
    
    if is_flag_submitted:
        attempt.status = 'auto_submitted_cheating'
        flash('Quiz auto-submitted due to tab-switch limit violations (Anti-Cheating Policy).', 'danger')
    elif is_timeout or request.args.get('auto'):
        attempt.status = 'auto_submitted'
        flash('Quiz auto-submitted because time expired.', 'warning')
    else:
        attempt.status = 'submitted'
        flash('Quiz submitted successfully!', 'success')
        
    db.session.commit()
    
    # Trigger Leaderboard update room
    socketio.emit('leaderboard_refresh', {'quiz_id': attempt.quiz_id}, to=f"leaderboard_{attempt.quiz_id}")
    
    return redirect(url_for('student.quiz_results', attempt_id=attempt.id))

@student_bp.route('/attempt/<int:attempt_id>/results')
def quiz_results(attempt_id):
    attempt = Attempt.query.get_or_404(attempt_id)
    if attempt.user_id != current_user.id:
        abort(403)
        
    if attempt.status == 'in_progress':
        return redirect(url_for('student.attempt_quiz', attempt_id=attempt.id))
        
    return render_template('student/results.html', attempt=attempt)

@student_bp.route('/leaderboard/<int:quiz_id>')
def leaderboard(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    # Fetch top 10 finished attempts for this quiz
    attempts = Attempt.query.filter_by(quiz_id=quiz.id).filter(
        Attempt.status.in_(['submitted', 'auto_submitted'])
    ).all()
    
    # Group by user to show only their BEST attempt (so one student isn't occupying all spots)
    student_best = {}
    for att in attempts:
        uid = att.user_id
        if uid not in student_best or att.score > student_best[uid].score:
            student_best[uid] = att
            
    # Sort by score descending, then time taken ascending
    sorted_attempts = sorted(
        student_best.values(), 
        key=lambda x: (x.score, -(x.submitted_at - x.started_at).total_seconds()), 
        reverse=True
    )[:10]
    
    return render_template('student/leaderboard.html', quiz=quiz, leaderboards=sorted_attempts)

@student_bp.route('/attempt/<int:attempt_id>/certificate')
def download_certificate(attempt_id):
    attempt = Attempt.query.get_or_404(attempt_id)
    if attempt.user_id != current_user.id or not attempt.is_passed:
        abort(403)
        
    date_str = attempt.submitted_at.strftime('%Y-%m-%d') if attempt.submitted_at else datetime.utcnow().strftime('%Y-%m-%d')
    pdf_data = generate_pdf_certificate(
        student_name=attempt.user.name,
        quiz_title=attempt.quiz.title,
        score_percentage=attempt.percentage,
        completion_date_str=date_str
    )
    
    return send_file(
        BytesIO(pdf_data),
        download_name=f"certificate_{attempt.quiz.title.replace(' ', '_')}.pdf",
        as_attachment=True,
        mimetype="application/pdf"
    )

@student_bp.route('/attempt/<int:attempt_id>/email_certificate', methods=['POST'])
def email_certificate(attempt_id):
    attempt = Attempt.query.get_or_404(attempt_id)
    if attempt.user_id != current_user.id or not attempt.is_passed:
        abort(403)
        
    date_str = attempt.submitted_at.strftime('%Y-%m-%d') if attempt.submitted_at else datetime.utcnow().strftime('%Y-%m-%d')
    pdf_data = generate_pdf_certificate(
        student_name=attempt.user.name,
        quiz_title=attempt.quiz.title,
        score_percentage=attempt.percentage,
        completion_date_str=date_str
    )
    
    subject = f"Congratulations! Your Certificate for {attempt.quiz.title}"
    body = f"""
    <h3>Dear {attempt.user.name},</h3>
    <p>Congratulations on passing the online examination <strong>{attempt.quiz.title}</strong>!</p>
    <p>You scored <strong>{attempt.score} out of {attempt.total_marks} ({attempt.percentage}%)</strong>.</p>
    <p>Please find your official achievement certificate attached to this email.</p>
    <br>
    <p>Best regards,<br>QuizVerse Team</p>
    """
    
    success = send_email(
        subject=subject,
        recipients=[attempt.user.email],
        html_body=body,
        attachment_filename=f"certificate_{attempt.quiz.title.replace(' ', '_')}.pdf",
        attachment_data=pdf_data,
        attachment_mime="application/pdf"
    )
    
    if success:
        flash("Certificate successfully sent to your email address!", "success")
    else:
        flash("Your certificate was generated, but the email server is simulated. We logged the details locally.", "info")
        
    return redirect(url_for('student.quiz_results', attempt_id=attempt.id))
