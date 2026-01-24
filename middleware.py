# middleware.py
from flask import redirect, url_for, flash, request
from flask_login import current_user, logout_user

def init_middleware(app):
    """Initialize middleware for the Flask application."""
    
    @app.before_request
    def check_user_status():
        """
        Check if the user is active before processing a request.
        Also checks if user needs to change their password.
        """
        # Skip if user is not authenticated or if they're accessing the auth routes
        if not current_user.is_authenticated or request.blueprint == 'auth':
            return None
            
        # If user exists but is not active, log them out
        if not current_user.is_active:
            logout_user()
            flash('Sua conta foi desativada. Entre em contato com o suporte para mais informações.', 'danger')
            return redirect(url_for('auth.login'))
            
        # If user needs to change password, redirect to change password page
        # But only if not already on the change password page and not on static resources
        if hasattr(current_user, 'needs_password_change') and current_user.needs_password_change():
            # Check if not already on change password page to avoid redirect loop
            if request.endpoint != 'auth.change_password' and not request.path.startswith('/static/'):
                flash('Como este é seu primeiro acesso, você precisa alterar sua senha.', 'warning')
                return redirect(url_for('auth.change_password'))

        return None# middleware.py
from flask import redirect, url_for, flash, request
from flask_login import current_user, logout_user

def init_middleware(app):
    """Initialize middleware for the Flask application."""
    
    @app.before_request
    def check_user_status():
        """Check if the user is active before processing a request."""
        # Skip if user is not authenticated or if they're accessing the auth routes
        if not current_user.is_authenticated or request.blueprint == 'auth':
            return None
            
        # If user exists but is not active, log them out
        if not current_user.is_active:
            logout_user()
            flash('Sua conta foi desativada. Entre em contato com o suporte para mais informações.', 'danger')
            return redirect(url_for('auth.login'))

        return None