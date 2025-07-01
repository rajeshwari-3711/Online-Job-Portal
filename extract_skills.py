# extract_skills.py

import spacy

def extract_skills(text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text.lower())
    skills = []
    skill_keywords = [
        "python", "java", "sql", "html", "css", "flask",
        "excel", "machine learning", "django", "javascript",
        "c++", "c#", "react", "node.js", "git", "github"
    ]
    for token in doc:
        if token.text in skill_keywords:
            skills.append(token.text)
    return list(set(skills))
