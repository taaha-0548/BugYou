#!/usr/bin/env python3
"""
BugYou Flask Server v2.0
"""

import sys
import os

# ==== Step 1: Import packages ====
try:
    from flask import Flask, render_template, redirect, url_for, request, jsonify, send_from_directory
    from flask_cors import CORS
    from flask_bcrypt import Bcrypt
    from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
    from flask_wtf import FlaskForm
    from wtforms import StringField, PasswordField, SubmitField
    from wtforms.validators import InputRequired, Length, ValidationError, Email
    from database_config import (
        get_challenges_by_language_difficulty,
        get_challenge_by_id,
        test_connection,
        DatabaseManager,
        CHALLENGE_TABLES
    )
except ImportError as e:
    print(f"❌ Missing package: {e}\nRun: pip install -r requirements.txt")
    sys.exit(1)

# ==== Step 2: Test DB Connection ====
print("🔌 Testing database connection...")
if not test_connection():
    print("❌ Database connection failed.")
    sys.exit(1)
print("✅ Database connected.")

# ==== Step 3: Initialize App ====
app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisisasecretkey'
CORS(app)
bcrypt = Bcrypt(app)
db = DatabaseManager()

# Static folders configuration
STATIC_FOLDERS = {
    'main': '../frontend/main_page',
    'login': '../frontend/login',
    'signup': '../frontend/signup',
    'admin': '../frontend/admin',
    'home': '../frontend/home',
    'about': '../frontend/about',
    'guide': '../frontend/guide',
    'assets': '../Assets'
}

# ==== Step 4: Login Manager ====
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    query = "SELECT user_id, username FROM users WHERE user_id = %s"
    result = db.execute_query(query, (user_id,), fetch_one=True)
    return User(result['user_id'], result['username']) if result else None

# ==== Step 5: Forms ====
class RegisterForm(FlaskForm):
    email = StringField(validators=[InputRequired(), Email()], render_kw={"placeholder": "Email"})
    fullname = StringField(validators=[InputRequired(), Length(min=2, max=50)], render_kw={"placeholder": "Full Name"})
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Register')

    def validate_username(self, username):
        query = "SELECT user_id FROM users WHERE username = %s"
        if db.execute_query(query, (username.data,), fetch_one=True):
            raise ValidationError('Username already exists.')

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired()], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired()], render_kw={"placeholder": "Password"})
    submit = SubmitField('Login')

# ==== Step 6: Routes ====
@app.route('/')
def serve_frontend():
    """Serve the main frontend page"""
    return send_from_directory(STATIC_FOLDERS['main'], 'index.html')

@app.route('/home')
def serve_home():
    """Serve the home page"""
    return send_from_directory(STATIC_FOLDERS['home'], 'home.html')

@app.route('/about')
def serve_about():
    """Serve the about page"""
    return send_from_directory(STATIC_FOLDERS['about'], 'about.html')

@app.route('/guide')
def serve_guide():
    """Serve the guide page"""
    return send_from_directory(STATIC_FOLDERS['guide'], 'guide.html')

@app.route('/admin')
def serve_admin():
    """Serve the admin page"""
    return send_from_directory(STATIC_FOLDERS['admin'], 'admin.html')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve files from Assets directory"""
    try:
        return send_from_directory('../Assets', filename)
    except Exception as e:
        print(f"Error serving asset {filename}: {str(e)}")
        return f"Asset {filename} not found", 404

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS, JS, etc.)"""
    # First try to serve from the current page's directory
    current_page = request.path.split('/')[1]  # Get the first part of the path
    if current_page in ['login', 'signup', 'admin', 'home', 'about', 'guide']:
        folder = STATIC_FOLDERS[current_page]
        if os.path.exists(os.path.join(folder, filename)):
            return send_from_directory(folder, filename)
    
    # Then try other static folders
    for folder_name, folder_path in STATIC_FOLDERS.items():
        if os.path.exists(os.path.join(folder_path, filename)):
            return send_from_directory(folder_path, filename)
    
    # If file not found in any directory, return 404
    return f"File {filename} not found", 404

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username and password:
            query = "SELECT user_id, username, password FROM users WHERE username = %s"
            result = db.execute_query(query, (username,), fetch_one=True)
            
            if result and bcrypt.check_password_hash(result['password'], password):
                login_user(User(result['user_id'], result['username']))
                return redirect('/')  # Redirect to main page
            else:
                # You could add flash messages here
                pass
    
    return send_from_directory(STATIC_FOLDERS['login'], 'login.html')

@app.route('/signup', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        fullname = request.form.get('fullname')
        username = request.form.get('username')
        password = request.form.get('password')
        
        if email and fullname and username and password:
            # Check if username already exists
            check_query = "SELECT user_id FROM users WHERE username = %s"
            existing_user = db.execute_query(check_query, (username,), fetch_one=True)
            
            if existing_user:
                # Username already exists
                pass
            else:
                # Hash password and create user
                hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
                insert_query = """
                    INSERT INTO users (username, password, emailaddress, fullname)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id, username
                """
                result = db.execute_query(insert_query, (
                    username, hashed_pw, email, fullname
                ), fetch_one=True)
                
                if result:
                    login_user(User(result['user_id'], result['username']))
                    return redirect('/')  # Redirect to main page
    
    return send_from_directory(STATIC_FOLDERS['signup'], 'signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/home')

# API Endpoints (keeping existing ones)
@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'database': 'connected' if test_connection() else 'disconnected'
    })

@app.route('/api/challenges')
def get_challenges():
    """Get all available challenges"""
    try:
        # This would need to be implemented based on your existing logic
        return jsonify({'success': True, 'challenges': []})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/challenges/<language>/<difficulty>')
def get_challenges_by_lang_diff(language, difficulty):
    """Get challenges for specific language and difficulty"""
    try:
        challenges = get_challenges_by_language_difficulty(language, difficulty)
        return jsonify({
            'success': True,
            'challenges': challenges,
            'count': len(challenges)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/challenge/<language>/<difficulty>/<int:challenge_id>')
def get_challenge_details(language, difficulty, challenge_id):
    """Get details for a specific challenge"""
    try:
        challenge = get_challenge_by_id(language, difficulty, challenge_id)
        if challenge:
            return jsonify({
                'success': True,
                'challenge': challenge
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Challenge not found'
            }), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cache/clear')
def clear_cache():
    """Clear all caches"""
    return jsonify({
        'success': True,
        'message': 'Cache cleared'
    })

# ==== Step 7: Run ====
if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 Starting BugYou Flask Server")
    print("📍 http://localhost:5000")
    print("🔗 Health Check: /api/health")
    print("🗄️  Database Connected")
    print("⚡ Code Execution via Piston API")
    print("="*50)
    try:
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\n👋 Server stopped.")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)