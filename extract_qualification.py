def extract_qualification(text):
    qualifications = []
    keywords = ["bca", "mca", "b.tech", "bsc", "msc", "phd"]
    for line in text.lower().split("\n"):
        for keyword in keywords:
            if keyword in line:
                qualifications.append(keyword.upper())
    return list(set(qualifications))
