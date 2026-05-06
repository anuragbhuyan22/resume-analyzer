"""
core/matcher.py — TF-IDF cosine-similarity job-role matching.
"""
import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_DIR = Path(__file__).parent.parent / "data"

with open(DATA_DIR / "job_roles.json", "r", encoding="utf-8") as f:
    JOB_ROLES: list[dict] = json.load(f)

# Pre-build corpus string for each role
_ROLE_CORPUS = [
    r["description"] + " " + " ".join(r.get("required_skills", []))
    for r in JOB_ROLES
]


def match_jobs(resume_text: str, top_n: int = 5) -> list[dict]:
    """Return top_n job roles most similar to the resume text."""
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=5000,
    )

    all_texts = _ROLE_CORPUS + [resume_text]
    tfidf_matrix = vectorizer.fit_transform(all_texts)

    resume_vec  = tfidf_matrix[-1]
    role_matrix = tfidf_matrix[:-1]
    sims        = cosine_similarity(resume_vec, role_matrix)[0]

    results = [
        {
            "title":           JOB_ROLES[i]["title"],
            "category":        JOB_ROLES[i].get("category", "General"),
            "match_percent":   round(float(sims[i]) * 100, 1),
            "required_skills": JOB_ROLES[i].get("required_skills", [])[:6],
        }
        for i in range(len(JOB_ROLES))
    ]

    results.sort(key=lambda x: x["match_percent"], reverse=True)
    return results[:top_n]
