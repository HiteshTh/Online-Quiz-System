import csv
import io
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from app.extensions import db
from app.models import User, Category, Quiz, Question, Option, Attempt, Answer
from app.utils.decorators import role_required
from app.admin.forms import QuizForm, QuestionForm

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
@login_required
@role_required('admin', 'teacher')
def restrict_admin_access():
    pass

@admin_bp.route('/dashboard')
def dashboard():
    # Analytics metrics
    total_students = User.query.filter_by(role='student').count()
    total_quizzes = Quiz.query.count()
    total_attempts = Attempt.query.filter(Attempt.status != 'in_progress').count()
    
    # Calculate pass rate
    passed_attempts = 0
    all_finished_attempts = Attempt.query.filter(Attempt.status != 'in_progress').all()
    for att in all_finished_attempts:
        if att.is_passed:
            passed_attempts += 1
    
    pass_rate = round((passed_attempts / total_attempts * 100), 1) if total_attempts > 0 else 0.0
    
    # Chart 1: Average score per Quiz
    quizzes = Quiz.query.all()
    quiz_labels = []
    quiz_avg_scores = []
    
    for q in quizzes:
        attempts_q = Attempt.query.filter_by(quiz_id=q.id).filter(Attempt.status != 'in_progress').all()
        if attempts_q:
            avg_score = sum(att.percentage for att in attempts_q) / len(attempts_q)
            quiz_labels.append(q.title)
            quiz_avg_scores.append(round(avg_score, 1))
            
    # Chart 2: Score distribution (ranges)
    score_ranges = {
        '0-20%': 0,
        '21-40%': 0,
        '41-60%': 0,
        '61-80%': 0,
        '81-100%': 0
    }
    for att in all_finished_attempts:
        pct = att.percentage
        if pct <= 20:
            score_ranges['0-20%'] += 1
        elif pct <= 40:
            score_ranges['21-40%'] += 1
        elif pct <= 60:
            score_ranges['41-60%'] += 1
        elif pct <= 80:
            score_ranges['61-80%'] += 1
        else:
            score_ranges['81-100%'] += 1
            
    # Hardest questions logic (highest percentage of incorrect answers)
    hardest_questions = []
    questions_list = Question.query.all()
    for quest in questions_list:
        total_answers = Answer.query.filter_by(question_id=quest.id).count()
        if total_answers > 0:
            incorrect_answers = Answer.query.filter_by(question_id=quest.id, is_correct=False).count()
            fail_pct = round((incorrect_answers / total_answers * 100), 1)
            if fail_pct > 30: # Only report questions with substantial failure rates
                hardest_questions.append({
                    'id': quest.id,
                    'text': quest.question_text,
                    'quiz_title': quest.quiz.title,
                    'fail_rate': fail_pct
                })
    # Sort hardest questions by failure rate descending
    hardest_questions = sorted(hardest_questions, key=lambda x: x['fail_rate'], reverse=True)[:5]

    return render_template(
        'admin/dashboard.html',
        total_students=total_students,
        total_quizzes=total_quizzes,
        total_attempts=total_attempts,
        pass_rate=pass_rate,
        quiz_labels=quiz_labels,
        quiz_avg_scores=quiz_avg_scores,
        distribution_labels=list(score_ranges.keys()),
        distribution_data=list(score_ranges.values()),
        hardest_questions=hardest_questions,
        quizzes=quizzes
    )

@admin_bp.route('/quiz/create', methods=['GET', 'POST'])
def create_quiz():
    form = QuizForm()
    if form.validate_on_submit():
        # Get or create Category
        cat_name = form.category_name.data.strip().title()
        category = Category.query.filter_by(name=cat_name).first()
        if not category:
            category = Category(name=cat_name)
            db.session.add(category)
            db.session.flush() # Generate category.id immediately
            
        quiz = Quiz(
            title=form.title.data.strip(),
            description=form.description.data,
            category_id=category.id,
            created_by=current_user.id,
            duration_minutes=form.duration_minutes.data,
            shuffle_questions=form.shuffle_questions.data,
            negative_marking=form.negative_marking.data,
            negative_mark_value=form.negative_mark_value.data,
            pass_percentage=form.pass_percentage.data,
            is_published=form.is_published.data
        )
        try:
            db.session.add(quiz)
            db.session.commit()
            flash(f"Quiz '{quiz.title}' created successfully!", "success")
            return redirect(url_for('admin.manage_questions', quiz_id=quiz.id))
        except Exception as e:
            db.session.rollback()
            flash("Error creating quiz. Try again.", "danger")
            
    return render_template('admin/quiz_form.html', form=form, title="Create Quiz")

@admin_bp.route('/quiz/<int:quiz_id>/edit', methods=['GET', 'POST'])
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    form = QuizForm(obj=quiz)
    
    if request.method == 'GET':
        form.category_name.data = quiz.category.name

    if form.validate_on_submit():
        # Get or create Category
        cat_name = form.category_name.data.strip().title()
        category = Category.query.filter_by(name=cat_name).first()
        if not category:
            category = Category(name=cat_name)
            db.session.add(category)
            db.session.flush()
            
        quiz.title = form.title.data.strip()
        quiz.description = form.description.data
        quiz.category_id = category.id
        quiz.duration_minutes = form.duration_minutes.data
        quiz.shuffle_questions = form.shuffle_questions.data
        quiz.negative_marking = form.negative_marking.data
        quiz.negative_mark_value = form.negative_mark_value.data
        quiz.pass_percentage = form.pass_percentage.data
        quiz.is_published = form.is_published.data
        
        try:
            db.session.commit()
            flash(f"Quiz '{quiz.title}' updated successfully!", "success")
            return redirect(url_for('admin.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash("Error updating quiz.", "danger")
            
    return render_template('admin/quiz_form.html', form=form, title=f"Edit '{quiz.title}'")

@admin_bp.route('/quiz/<int:quiz_id>/delete', methods=['POST'])
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    try:
        db.session.delete(quiz)
        db.session.commit()
        flash("Quiz deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error deleting quiz.", "danger")
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/quiz/<int:quiz_id>/questions', methods=['GET', 'POST'])
def manage_questions(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    form = QuestionForm()
    
    if form.validate_on_submit():
        question = Question(
            quiz_id=quiz.id,
            question_text=form.question_text.data.strip(),
            question_type=form.question_type.data,
            marks=form.marks.data,
            difficulty=form.difficulty.data
        )
        
        db.session.add(question)
        db.session.flush() # Get question.id
        
        # Extract options depending on type
        if question.question_type == 'mcq':
            opt_texts = request.form.getlist('option_text[]')
            correct_idx = request.form.get('is_correct_mcq') # 0-indexed string index
            for idx, text in enumerate(opt_texts):
                if text.strip():
                    is_correct = (correct_idx == str(idx))
                    opt = Option(question_id=question.id, option_text=text.strip(), is_correct=is_correct)
                    db.session.add(opt)
        elif question.question_type == 'true_false':
            correct_val = request.form.get('true_false_val') == 'True'
            opt_true = Option(question_id=question.id, option_text='True', is_correct=correct_val)
            opt_false = Option(question_id=question.id, option_text='False', is_correct=not correct_val)
            db.session.add(opt_true)
            db.session.add(opt_false)
        elif question.question_type == 'fill_blank':
            blank_ans = request.form.get('fill_blank_ans', '').strip()
            # Register blank_ans as a correct option (fuzzy checked later)
            opt = Option(question_id=question.id, option_text=blank_ans, is_correct=True)
            db.session.add(opt)
            
        try:
            db.session.commit()
            flash("Question added successfully!", "success")
            return redirect(url_for('admin.manage_questions', quiz_id=quiz.id))
        except Exception as e:
            db.session.rollback()
            flash("Error saving question. Check details.", "danger")
            
    return render_template('admin/questions.html', quiz=quiz, form=form)

@admin_bp.route('/question/<int:question_id>/delete', methods=['POST'])
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    quiz_id = question.quiz_id
    try:
        db.session.delete(question)
        db.session.commit()
        flash("Question deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error deleting question.", "danger")
    return redirect(url_for('admin.manage_questions', quiz_id=quiz_id))

@admin_bp.route('/quiz/<int:quiz_id>/questions/import', methods=['POST'])
def import_questions(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    file = request.files.get('csv_file')
    if not file or not file.filename.endswith('.csv'):
        flash("Please upload a valid CSV file.", "danger")
        return redirect(url_for('admin.manage_questions', quiz_id=quiz.id))
        
    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.DictReader(stream)
        
        imported_count = 0
        for row in csv_reader:
            q_text = row.get('question_text')
            q_type = row.get('question_type', 'mcq').strip().lower()
            marks = int(row.get('marks', 1))
            difficulty = row.get('difficulty', 'medium').strip().lower()
            
            if not q_text:
                continue
                
            # Create question
            question = Question(
                quiz_id=quiz.id,
                question_text=q_text.strip(),
                question_type=q_type,
                marks=marks,
                difficulty=difficulty
            )
            db.session.add(question)
            db.session.flush()
            
            if q_type == 'mcq':
                options_str = row.get('options', '')
                correct_opt = row.get('correct_option', '').strip()
                opts = [o.strip() for o in options_str.split('|') if o.strip()]
                for opt_text in opts:
                    is_correct = (opt_text.lower() == correct_opt.lower())
                    opt = Option(question_id=question.id, option_text=opt_text, is_correct=is_correct)
                    db.session.add(opt)
            elif q_type == 'true_false':
                correct_val = row.get('correct_option', '').strip().lower() in ['true', '1', 'yes']
                opt_true = Option(question_id=question.id, option_text='True', is_correct=correct_val)
                opt_false = Option(question_id=question.id, option_text='False', is_correct=not correct_val)
                db.session.add(opt_true)
                db.session.add(opt_false)
            elif q_type == 'fill_blank':
                correct_ans = row.get('correct_option', '').strip()
                opt = Option(question_id=question.id, option_text=correct_ans, is_correct=True)
                db.session.add(opt)
                
            imported_count += 1
            
        db.session.commit()
        flash(f"Successfully imported {imported_count} questions from CSV!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error parsing CSV file. Please match template layout. Error: {str(e)}", "danger")
        
    return redirect(url_for('admin.manage_questions', quiz_id=quiz.id))
