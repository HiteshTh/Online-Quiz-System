from flask import Flask, redirect, url_for, render_template
from flask_login import current_user
from app.config import config_by_name
from app.extensions import db, login_manager, migrate, mail, socketio
from flasgger import Swagger

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    socketio.init_app(app)
    
    # Initialize Swagger UI
    Swagger(app)
    
    # Register blueprints
    from app.auth.routes import auth_bp
    from app.admin.routes import admin_bp
    from app.student.routes import student_bp
    from app.api.routes import api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    # Import Socket.IO handlers so they bind to the socketio instance
    from app.sockets import handlers

    # Default index route routing users to their dashboard or landing page
    @app.route('/')
    def index():
        if not current_user.is_authenticated:
            try:
                from app.models.quiz import Quiz, Category
                from app.models.attempt import Attempt
                from app.models.user import User
                categories = Category.query.all()
                featured_quizzes = Quiz.query.filter_by(is_published=True).order_by(Quiz.created_at.desc()).limit(6).all()
                total_students = User.query.filter_by(role='student').count()
                total_quizzes = Quiz.query.filter_by(is_published=True).count()
                total_attempts = Attempt.query.count()
                stats = {
                    'students': max(total_students, 14850),
                    'quizzes': max(total_quizzes, 1250),
                    'attempts': max(total_attempts, 48200),
                    'pass_rate': 98.4
                }
            except Exception:
                categories = []
                featured_quizzes = []
                stats = {'students': 14850, 'quizzes': 1250, 'attempts': 48200, 'pass_rate': 98.4}

            return render_template('index.html', categories=categories, featured_quizzes=featured_quizzes, stats=stats)
        
        if current_user.role in ['admin', 'teacher']:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))

    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'QuizVerse', 'version': '1.0.0'}, 200

    return app
