# app.py
from flask import Flask, render_template, url_for, redirect, request
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError, Email
from flask_bcrypt import Bcrypt
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
import time
from flask_wtf.csrf import CSRFProtect
from database_config import DatabaseManager, CHALLENGE_TABLES

app = Flask(
    __name__,
    template_folder='../frontend',
    static_folder='../frontend'
)

# Secret key for Flask-WTF
app.config['SECRET_KEY'] = 'thisisasecretkey'
print("SECRET_KEY IS:", app.config['SECRET_KEY'])

# Initialize extensions
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'



db = DatabaseManager()

class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    query = "SELECT user_id, username FROM users WHERE user_id = %s"
    result = db.execute_query(query, (user_id,), fetch_one=True)
    if result:
        return User(result['user_id'], result['username'])
    return None

class RegisterForm(FlaskForm):
    email = StringField(validators=[InputRequired(), Email()], render_kw={"placeholder": "Email address"})
    fullname = StringField(validators=[InputRequired(), Length(min=2, max=50)], render_kw={"placeholder": "Full Name"})
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Register')

    def validate_username(self, username):
        query = "SELECT user_id FROM users WHERE username = %s"
        existing_user = db.execute_query(query, (username.data,), fetch_one=True)
        if existing_user:
            raise ValidationError('That username already exists.')

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Login')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        query = "SELECT user_id, username, password FROM users WHERE username = %s"
        result = db.execute_query(query, (form.username.data,), fetch_one=True)
        if result and bcrypt.check_password_hash(result['password'], form.password.data):
            user_obj = User(result['user_id'], result['username'])
            login_user(user_obj)
            return  render_template('/main_page/index.html')
    return render_template('/login/login.html', form=form)

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
        values = (
            form.username.data,     
            hashed_pw,            
            form.email.data,          
            form.fullname.data       
        )
        result = db.execute_query(query, values, fetch_one=True)
        if result:
            login_user(User(result['user_id'], result['username']))
            return redirect(url_for('main_page'))
    return render_template('/signup/signup.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.username)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
