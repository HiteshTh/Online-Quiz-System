from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user

def role_required(*roles):
    """
    Decorator to restrict view access to specific user roles.
    Example: @role_required('admin', 'teacher')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            if current_user.role not in roles:
                flash("You do not have permission to access this page.", "danger")
                # Redirect user to their respective home dashboard based on role
                if current_user.role == 'admin':
                    return redirect(url_for('admin.dashboard'))
                elif current_user.role == 'teacher':
                    return redirect(url_for('admin.dashboard')) # Shared console for admin/teacher
                else:
                    return redirect(url_for('student.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
