from flask import Flask, render_template, request, redirect, url_for
import os
from flask import Flask, render_template, request, redirect, session, flash, url_for


app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Sample skills and job listings for matching
SKILLS_DB = ['python', 'java', 'machine learning', 'sql', 'excel', 'html', 'css', 'javascript']
JOB_LISTINGS = [
    {"title": "Python Developer", "skills_required": ['python', 'sql'], "qualification": 'BCA', "experience_required": 1},
    {"title": "Frontend Developer", "skills_required": ['html', 'css', 'javascript'], "qualification": 'BCA', "experience_required": 0},
    {"title": "Data Analyst", "skills_required": ['excel', 'sql', 'python'], "qualification": 'BCA', "experience_required": 1}
]

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Default username and password
        username = request.form['username']
        password = request.form['password']

        # Check if the credentials are "admin" and "admin"
        if username == "admin" and password == "admin":
            session['user_id'] = 1  # Set user_id for the admin user
            session['username'] = "admin"
            session['is_admin'] = 1  # Set admin flag
            flash('Login successful!')
            return redirect(url_for('upload'))  # Redirect to the upload page
        else:
            flash('Invalid credentials. Try again.')

    return render_template('login.html')


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'resume' not in request.files:
            flash("No file part in the request.", "danger")
            return redirect(request.url)

        file = request.files['resume']
        if file.filename == '':
            flash("No file selected.", "danger")
            return redirect(request.url)

        if file and file.filename.lower().endswith(('.pdf', '.docx')):
            filename = secure_filename(file.filename)
            filepath = os.path.join(RESUME_FOLDER, filename)
            file.save(filepath)

            # Extract resume data
            skills = extract_skills(filepath)
            qualification = extract_qualification(filepath)
            experience = extract_experience(filepath)

            # Check for extraction success
            if not all([skills, qualification, experience]):
                flash("Resume extraction failed. Please try another file.", "danger")
                return redirect(request.url)

            # Store in session
            session['skills'] = skills
            session['qualification'] = qualification
            session['experience'] = experience

            # Match jobs
            matched_jobs = match_jobs(skills, qualification, experience)
            session['matched_jobs'] = matched_jobs

            flash("Resume uploaded and processed successfully.", "success")
            return redirect(url_for('result'))

        else:
            flash("Unsupported file format. Please upload a PDF or DOCX file.", "danger")
            return redirect(request.url)

    return render_template('upload.html')

@app.route('/result')
def result():
    skills = request.args.get('skills', '')
    qualification = request.args.get('qualification', '')
    experience = request.args.get('experience', 0)

    # Mocked job matching
    jobs = match_jobs(skills, qualification, experience)
    return render_template('result.html', skills=skills, qualification=qualification, experience=experience, jobs=jobs)

# Helper functions to extract details from the resume (mocked)
def extract_skills(filepath):
    return ['python', 'sql']  # This should be replaced with actual parsing logic

def extract_qualification(filepath):
    return 'BCA'  # This should be replaced with actual parsing logic

def extract_experience(filepath):
    return 1  # This should be replaced with actual parsing logic

# Function to match jobs (mocked)
def match_jobs(skills, qualification, experience):
    matched_jobs = []
    for job in JOB_LISTINGS:
        if set(job['skills_required']).issubset(skills) and job['qualification'].lower() == qualification.lower() and experience >= job['experience_required']:
            matched_jobs.append(job['title'])
    return matched_jobs

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Default username and password
        username = request.form['username']
        password = request.form['password']

        # Check if the credentials are "admin" and "admin"
        if username == "admin" and password == "admin":
            session['user_id'] = 1  # Set user_id for the admin user
            session['username'] = "admin"
            session['is_admin'] = 1  # Set admin flag
            flash('Login successful!')
            return redirect(url_for('upload'))  # Redirect to the upload page
        else:
            flash('Invalid credentials. Try again.')

    return render_template('login.html')
