import requests
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth
from app.extensions import db
from app.models.user import User
from app.auth.forms import LoginForm, RegisterForm

auth_bp = Blueprint('auth', __name__)

# OAuth object (will be initialized lazily on first request)
oauth = OAuth()
google = None

def get_google_oauth():
    """Lazily initialize the Google OAuth client with current app config."""
    global google
    if google is None:
        oauth.init_app(current_app._get_current_object())
        google = oauth.register(
            name='google',
            client_id=current_app.config.get('GOOGLE_CLIENT_ID'),
            client_secret=current_app.config.get('GOOGLE_CLIENT_SECRET'),
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'openid email profile'
            }
        )
    return google


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data.strip(),
            email=form.email.data.strip().lower(),
            role=form.role.data
        )
        user.set_password(form.password.data)
        try:
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created successfully! Please log in to continue.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating your account. Please try again.', 'danger')
            
    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')
            
            # Check for next query parameter for redirection safety
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
                
            if user.role in ['admin', 'teacher']:
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('student.dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
            
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


# ─────────────────────────────────────────────
#  Google OAuth Routes
# ─────────────────────────────────────────────

@auth_bp.route('/google')
def google_login():
    """Initiates Google OAuth by redirecting to Google's consent screen."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    # Check config is set
    if not current_app.config.get('GOOGLE_CLIENT_ID') or not current_app.config.get('GOOGLE_CLIENT_SECRET'):
        flash('Google login is not configured yet. Please set up GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your .env file.', 'warning')
        return redirect(url_for('auth.login'))
    
    g_client = get_google_oauth()
    redirect_uri = url_for('auth.google_callback', _external=True)
    return g_client.authorize_redirect(redirect_uri)


@auth_bp.route('/google/callback')
def google_callback():
    """Handles the return from Google after user grants permission."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    g_client = get_google_oauth()
    
    try:
        token = g_client.authorize_access_token()
    except Exception as e:
        flash('Google authentication failed or was cancelled. Please try again.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Get user info from Google
    user_info = token.get('userinfo')
    if not user_info:
        flash('Could not retrieve account info from Google. Please try again.', 'danger')
        return redirect(url_for('auth.login'))
    
    google_id = user_info.get('sub')           # Unique Google user ID
    email = user_info.get('email', '').lower()
    name = user_info.get('name', 'Google User')
    avatar_url = user_info.get('picture')

    if not email:
        flash('Google did not return an email address. Please check your Google account settings.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Find or create the user account
    user = User.query.filter_by(google_id=google_id).first()
    
    if not user:
        # Try matching by email (for users who previously registered manually)
        user = User.query.filter_by(email=email).first()
        if user:
            # Link this existing account to their Google profile
            user.google_id = google_id
            if avatar_url and not user.avatar_url:
                user.avatar_url = avatar_url
            db.session.commit()
        else:
            # Brand new user — create an account automatically
            user = User(
                name=name,
                email=email,
                google_id=google_id,
                avatar_url=avatar_url,
                role='student'  # Default role for all Google sign-ups
            )
            # No password set — this is a Google-only account
            try:
                db.session.add(user)
                db.session.commit()
                flash(f'Welcome to QuizVerse, {name}! Your account has been created via Google.', 'success')
            except Exception as e:
                db.session.rollback()
                flash('Failed to create account. Please try again.', 'danger')
                return redirect(url_for('auth.login'))

    # Log the user in
    login_user(user)
    if user.role in ['admin', 'teacher']:
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('student.dashboard'))
