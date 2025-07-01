### job_matcher.py
def match_jobs(skills, qualifications, experience):
    job_roles = {
        "Web Developer": ["html", "css", "javascript", "flask"],
        "Data Analyst": ["python", "excel", "sql"],
        "Machine Learning Engineer": ["python", "machine learning"]
    }
    matched_jobs = []
    for role, req_skills in job_roles.items():
        if any(skill in skills for skill in req_skills):
            matched_jobs.append(role)
    return matched_jobs
