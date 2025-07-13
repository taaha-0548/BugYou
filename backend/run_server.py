#!/usr/bin/env python3
"""
BugYou Flask Server v2.0
"""

import sys
import os

# ==== Step 1: Import packages ====
try:
    from flask import Flask, render_template, redirect, url_for, request
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
app = Flask(__name__, template_folder='../frontend', static_folder='../frontend')
app.config['SECRET_KEY'] = 'thisisasecretkey'
CORS(app)
bcrypt = Bcrypt(app)
db = DatabaseManager()

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
def home():
    return render_template('home/home.html')

@app.route('/about')
def about():
    return render_template('about/about.html')

@app.route('/guide')
def guide():
    return render_template('guide/guide.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        query = "SELECT user_id, username, password FROM users WHERE username = %s"
        result = db.execute_query(query, (form.username.data,), fetch_one=True)
        if result and bcrypt.check_password_hash(result['password'], form.password.data):
            login_user(User(result['user_id'], result['username']))
            return redirect(url_for('dashboard'))
    return render_template('login/login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        query = """
            INSERT INTO users (username, password, emailaddress, fullname)
            VALUES (%s, %s, %s, %s)
            RETURNING user_id, username
        """
        result = db.execute_query(query, (
            form.username.data, hashed_pw, form.email.data, form.fullname.data
        ), fetch_one=True)
        if result:
            login_user(User(result['user_id'], result['username']))
            return redirect(url_for('main_page/index.html'))
    return render_template('signup/signup.html', form=form)

@app.route('/main')
@login_required
def dashboard():
    return render_template('main_page/index.html', username=current_user.username)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/challenges/<language>/<difficulty>', methods=['GET'])
def api_get_challenges(language, difficulty):
    try:
        challenges = get_challenges_by_language_difficulty(language, difficulty)
        return {"challenges": challenges}, 200
    except Exception as e:
        return {"error": str(e)}, 400

@app.route('/api/challenge/<language>/<difficulty>/<int:challenge_id>', methods=['GET'])
def api_get_challenge(language, difficulty, challenge_id):
    try:
        challenge = get_challenge_by_id(language, difficulty, challenge_id)
        if challenge:
            return {"success": True, "challenge": challenge}, 200
        return {"success": False, "error": "Challenge not found"}, 404
    except Exception as e:
        return {"success": False, "error": str(e)}, 400

@app.route('/api/cache/clear')
def api_clear_cache():
    return {"status": "Cache cleared (noop)"}, 200

@app.route('/api/health')
def api_health():
    return {"status": "ok"}, 200

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
