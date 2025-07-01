import re

def extract_experience(text):
    patterns = [
        r"(\d+\+?\s+years?)",                   # e.g. "3 years" or "3+ years"
        r"(\d+\s+yrs?)",                        # e.g. "3 yrs"
        r"experience\s+of\s+(\d+)\s+years?",   # e.g. "experience of 5 years"
        r"worked\s+for\s+(\d+)\s+years?",      # e.g. "worked for 2 years"
    ]

    experiences = []
    text_lower = text.lower()
    
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        experiences.extend(matches)

    if experiences:
        cleaned = []
        for exp in experiences:
            if isinstance(exp, tuple) or isinstance(exp, list):
                exp = exp[0]
            cleaned.append(exp.strip())
        unique_experiences = sorted(set(cleaned), key=lambda x: int(re.search(r'\d+', x).group()))
        return unique_experiences
    else:
        return ["No experience mentioned"]
