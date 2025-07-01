# Standard Library Imports
import os
import io
import re
import sqlite3
from uuid import uuid4
from functools import wraps

# Environment Variables
from dotenv import load_dotenv

# Flask & Related Modules
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, send_file
)
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# OpenAI API
import openai

# PDF/Doc Processing
from PyPDF2 import PdfReader
import docx  # Uncomment if using python-docx for DOCX parsing

# NLP
import spacy

# Custom Helper Modules (Make sure these .py files exist)
from extract_text import extract_text_from_pdf, extract_text_from_docx
from extract_skills import extract_skills
from extract_qualification import extract_qualification
from extract_experience import extract_experience
from job_matcher import match_jobs

UPLOAD_FOLDER = 'static/uploads/profile_pics'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Initialize Flask app ---
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')

nlp = spacy.load("en_core_web_sm")

# Define your custom skill keywords (extend as needed)
SKILL_KEYWORDS = [
    'python', 'java', 'flask', 'sql', 'html', 'css', 'javascript',
    'c++', 'c#', 'node.js', 'react', 'git', 'docker', 'linux',
    'excel', 'powerpoint', 'photoshop', 'wordpress', 'data analysis',
    'machine learning', 'ai', 'nlp', 'mysql', 'mongodb'
]
_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

def extract_resume_data(file):
    import io
    import re
    from PyPDF2 import PdfReader  # Or use pdfplumber/docx2txt depending on your file types

    # Read PDF content
    content = ''
    try:
        pdf = PdfReader(file)
        for page in pdf.pages:
            content += page.extract_text()
    except Exception as e:
        content = 'Error reading file: ' + str(e)

    # Example extraction logic (you can expand this)
    name_match = re.search(r"Name\s*:\s*(.+)", content)
    email_match = re.search(r"[\w\.-]+@[\w\.-]+", content)

    return {
        'name': name_match.group(1) if name_match else 'Not found',
        'email': email_match.group(0) if email_match else 'Not found',
        'content': content
    }


# Load environment variables from .env file
load_dotenv()



# --- Config ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///resume.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD')

)

# --- Initialize extensions ---
db = SQLAlchemy(app)
mail = Mail(app)
serializer = URLSafeTimedSerializer(app.secret_key)

# --- Constants and folders ---
UPLOAD_FOLDER = 'static/uploads/profile_pics'
RESUME_FOLDER = 'static/resumes'
GENERATED_RESUMES = 'static/generated_resumes'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESUME_FOLDER, exist_ok=True)
os.makedirs(GENERATED_RESUMES, exist_ok=True)

USER_DB = 'users.db'  # For sqlite3 user auth

# --- Database Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    dob = db.Column(db.String(50))  # Optional
    age = db.Column(db.Integer)
    profile_pic = db.Column(db.String(200), default='default.png')



class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(50))
    summary = db.Column(db.Text)
    skills = db.Column(db.Text)
    experience = db.Column(db.Text)
    education = db.Column(db.Text)
    projects = db.Column(db.Text)
    certifications = db.Column(db.Text)
    generated_resume = db.Column(db.Text)
    
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3


DATABASE = 'users.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# --- SQLite user DB initialization (for login/registration) ---
def init_user_db():
    conn = sqlite3.connect(USER_DB)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            dob TEXT,
            age INTEGER,
            profile_pic TEXT DEFAULT 'default.png'
        )
    ''')
    conn.commit()
    conn.close()


init_user_db()

# --- Utility functions for DB ---
def get_user_db_connection():
    conn = sqlite3.connect(USER_DB)
    conn.row_factory = sqlite3.Row
    return conn

def get_resume_db_connection():
    conn = sqlite3.connect('resume.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- Get current logged-in user from DB ---
def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    conn = get_user_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user

# --- Inject user into all templates ---
@app.context_processor
def inject_user():
    user = get_current_user()
    return dict(user=user)

# --- Login required decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Job matching logic ---
JOB_LISTINGS = [
    {
        "title": "Python Developer",
        "skills_required": ['python', 'sql'],
        "qualification": 'BCA',
        "experience_required": 1,
        "search_url": "https://www.indeed.com/jobs?q=python+developer"
    },
    {
        "title": "Frontend Developer",
        "skills_required": ['html', 'css', 'javascript'],
        "qualification": 'BCA',
        "experience_required": 0,
        "search_url": "https://www.linkedin.com/jobs/frontend-developer-jobs"
    },
    {
        "title": "Data Analyst",
        "skills_required": ['excel', 'sql', 'python'],
        "qualification": 'BCA',
        "experience_required": 1,
        "search_url": "https://www.naukri.com/data-analyst-jobs"
    }
]

def match_jobs(skills, qualification, experience):
    matched = []
    for job in JOB_LISTINGS:
        if set(job['skills_required']).issubset(set(skills)) and \
           job['qualification'].lower() in [q.lower() for q in qualification] and \
           experience >= job['experience_required']:
            matched.append(job)

    return matched



# --- OpenAI API setup ---
openai.api_key = os.getenv("OPENAI_API_KEY")


# --- Routes ---

@app.route('/')
def index():
    return render_template('login.html')
from markupsafe import Markup

@app.template_filter('nl2br')
def nl2br_filter(s):
    if s is None:
        return ''
    return Markup(s.replace('\n', '<br>\n'))




from datetime import datetime

from werkzeug.utils import secure_filename
import os

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Collect form data
        name = request.form['name'].strip()
        dob_str = request.form['dob'].strip()
        college = request.form['college'].strip()
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        profile_pic_file = request.files.get('profile_pic')

        # Password check
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html')

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Calculate age
        try:
            from datetime import datetime
            dob = datetime.strptime(dob_str, "%Y-%m-%d")
            today = datetime.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        except ValueError:
            flash("Invalid date format for DOB.", "danger")
            return render_template('register.html')

        # Save profile picture if uploaded
        profile_pic_filename = 'default.png'
        if profile_pic_file and profile_pic_file.filename:
            filename = secure_filename(profile_pic_file.filename)
            profile_pic_path = os.path.join(UPLOAD_FOLDER, filename)
            profile_pic_file.save(profile_pic_path)
            profile_pic_filename = filename

        # Check if user already exists
        conn = get_user_db_connection()
        cursor = conn.cursor()
        existing_user = cursor.execute(
            'SELECT * FROM users WHERE username = ? OR email = ?',
            (username, email)
        ).fetchone()

        if existing_user:
            flash("Username or email already exists.", "danger")
            conn.close()
            return render_template('register.html')

        # Insert user into DB
        try:
            cursor.execute(
                '''
                INSERT INTO users (name, dob, age, college, username, email, password, profile_pic)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (name, dob_str, age, college, username, email, hashed_password, profile_pic_filename)
            )
            conn.commit()
            flash("Registration successful!", "success")
            return redirect(url_for('login'))
        except Exception as e:
            conn.rollback()
            flash(f"Registration failed due to a database error: {e}", "danger")
        finally:
            conn.close()

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        conn = get_user_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']  # Optional: session storage
            session['profile_pic'] = user['profile_pic']
            flash("Logged in successfully!", "success")
            return redirect(url_for('upload'))  # redirect to upload page after login
        else:
            flash("Invalid username or password.", "danger")
    return render_template('login.html')

@app.route('/result')
@login_required
def result():
    skills = session.get('skills')
    qualification = session.get('qualification')
    experience = session.get('experience')
    matched_jobs = session.get('matched_jobs')
    username = session.get('username')  # optional, user also injected globally

    if not skills or not qualification or experience is None or matched_jobs is None:
        flash("No resume data found. Please upload your resume.", "warning")
        return redirect(url_for('upload'))

    return render_template(
        'result.html',
        skills=skills,
        qualification=qualification,
        experience=experience,
        jobs=matched_jobs,
        username=username
    )

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/about')
def about():
    username = session.get('username')
    return render_template('about.html', username=username)

@app.route('/contact')
def contact():
    username = session.get('username')
    return render_template('contact.html', username=username)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')

        # Check if user with that email exists
        conn = get_user_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user:
            # Generate token with expiration (1 hour)
            token = serializer.dumps(email, salt='password-reset-salt')

            reset_url = url_for('reset_password', token=token, _external=True)
            # Compose email
            msg = Message("Password Reset Request",
                          sender=app.config['MAIL_USERNAME'],
                          recipients=[email])
            msg.body = f"To reset your password, visit the following link:\n{reset_url}\nIf you did not request a password reset, please ignore this email."
            try:
                mail.send(msg)
                flash("Password reset email sent. Please check your inbox.", "info")
            except Exception as e:
                flash(f"Failed to send email: {e}", "danger")
        else:
            flash("Email not found.", "danger")

    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except Exception:
        flash("The password reset link is invalid or expired.", "danger")
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('reset_password.html', token=token)

        hashed_password = generate_password_hash(password)

        conn = get_user_db_connection()
        conn.execute("UPDATE users SET password = ? WHERE email = ?", (hashed_password, email))
        conn.commit()
        conn.close()

        flash("Password reset successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    username = session.get('username')

    if request.method == 'POST':
        print("==== POST received ====")

        if 'resume_file' not in request.files:
            print("No file part")
            flash("No file part in the request.", "danger")
            return redirect(request.url)

        file = request.files['resume_file']
        print("File part present:", file)

        if file.filename == '':
            print("Empty filename")
            flash("No file selected.", "danger")
            return redirect(request.url)

        if file and file.filename.lower().endswith(('.pdf', '.docx')):
            filename = secure_filename(file.filename)
            filepath = os.path.join(RESUME_FOLDER, filename)
            file.save(filepath)

            print("Saved file to:", filepath)

            if filename.lower().endswith('.pdf'):
                resume_text = extract_text_from_pdf(filepath)
            else:
                resume_text = extract_text_from_docx(filepath)

            print("Extracted text:", resume_text[:300])

            skills = extract_skills(resume_text)
            qualification = extract_qualification(resume_text)
            experience = extract_experience(resume_text)

            # Convert extracted experience to integer
            if isinstance(experience, list) and experience:
                match = re.search(r'\d+', experience[0])
                experience = int(match.group()) if match else 0
            elif isinstance(experience, str):
                match = re.search(r'\d+', experience)
                experience = int(match.group()) if match else 0
            else:
                experience = 0

            print("Skills:", skills)
            print("Qualification:", qualification)
            print("Experience:", experience)

            if not skills or not qualification:
                print("Validation failed.")
                flash("Resume extraction failed. Please try another file.", "danger")
                return redirect(request.url)

            matched_jobs = match_jobs(skills, qualification, experience)

            session['skills'] = skills
            session['qualification'] = qualification
            session['experience'] = experience
            session['matched_jobs'] = matched_jobs

            print("Redirecting to return page")
            return render_template(
                'return.html',
                skills=skills,
                qualification=qualification,
                experience=experience,
                jobs=matched_jobs,
                username=username
            )

        else:
            print("Invalid file type")
            flash("Unsupported file format. Please upload a PDF or DOCX file.", "danger")
            return redirect(request.url)

    # For GET request, just render the upload page
    return render_template('upload.html', username=username)



@app.route('/return')
@login_required
def return_page():
    skills = session.get('skills')
    qualification = session.get('qualification')
    experience = session.get('experience')
    matched_jobs = session.get('matched_jobs')
    username = session.get('username')

    if not all([skills, qualification, experience, matched_jobs]):
        flash("No resume data found. Please upload your resume.", "warning")
        return redirect(url_for('upload'))

    return render_template(
        'return.html',
        skills=skills,
        qualification=qualification,
        experience=experience,
        jobs=matched_jobs,
        username=username
    )

@app.route('/profile/<int:user_id>', methods=['GET', 'POST'])
@login_required
def profile(user_id):
    conn = get_user_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    if not user:
        conn.close()
        return "User not found", 404

    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        dob = request.form['dob']
        profile_pic_file = request.files.get('profile_pic')

        # Recalculate age
        try:
            dob_dt = datetime.strptime(dob, "%Y-%m-%d")
            today = datetime.today()
            age = today.year - dob_dt.year - ((today.month, today.day) < (dob_dt.month, dob_dt.day))
        except ValueError:
            flash("Invalid date format for DOB.", "danger")
            conn.close()
            return redirect(url_for('profile', user_id=user_id))

        # Use existing profile pic unless a new one is uploaded
        profile_pic_filename = user['profile_pic'] or 'default.png'
        if profile_pic_file and profile_pic_file.filename:
            filename = secure_filename(profile_pic_file.filename)
            profile_pic_path = os.path.join(UPLOAD_FOLDER, filename)
            profile_pic_file.save(profile_pic_path)
            profile_pic_filename = filename

        try:
            conn.execute(
                '''
                UPDATE users 
                SET username = ?, email = ?, dob = ?, age = ?, profile_pic = ?
                WHERE id = ?
                ''',
                (username, email, dob, age, profile_pic_filename, user_id)
            )
            conn.commit()
            flash("Profile updated successfully!", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Failed to update profile: {e}", "danger")
        finally:
            conn.close()

        return redirect(url_for('profile', user_id=user_id))

    conn.close()
    return render_template('profile.html', user=user)

@app.route('/resume_result')
@login_required
def resume_result():
    generated_resume = session.get('generated_resume')
    name = session.get('resume_owner_name')

    if not generated_resume:
        flash("No generated resume found. Please fill the form first.", "warning")
        return redirect(url_for('generate_resume_form'))

    return render_template('resume_result.html', generated_resume=generated_resume, name=name)

# --- Run app ---
if __name__ == '__main__':
    app.run(debug=True)
