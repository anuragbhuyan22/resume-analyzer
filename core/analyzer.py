"""
core/analyzer.py — NLP skill extraction, section detection, and resume scoring.
"""
import json
import re
import subprocess
from pathlib import Path

try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
        nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = None  # graceful fallback — no spaCy tokenisation

# ── Data ─────────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent.parent / "data"

with open(DATA_DIR / "skills.json", "r", encoding="utf-8") as f:
    SKILLS_DATA: dict = json.load(f)

SKILLS_BY_CATEGORY: dict[str, list[str]] = {
    cat: [s.lower() for s in skills]
    for cat, skills in SKILLS_DATA.items()
}

# ── Constants ─────────────────────────────────────────────────────────────────
ACTION_VERBS = {
    "developed", "designed", "built", "created", "implemented", "optimized",
    "managed", "led", "collaborated", "improved", "increased", "reduced",
    "delivered", "launched", "architected", "engineered", "automated",
    "deployed", "integrated", "analyzed", "researched", "mentored", "trained",
    "streamlined", "coordinated", "spearheaded", "oversaw", "established",
    "generated", "achieved", "maintained", "supported", "negotiated",
    "transformed", "executed", "facilitated", "directed", "supervised",
}

SECTION_KEYWORDS: dict[str, list[str]] = {
    "contact":        ["email", "phone", "linkedin", "github", "@", "mobile", "tel"],
    "summary":        ["summary", "objective", "about me", "profile", "overview"],
    "experience":     ["experience", "employment", "work history", "career", "intern"],
    "education":      ["education", "university", "college", "degree", "bachelor",
                       "master", "phd", "school", "gpa", "cgpa"],
    "skills":         ["skills", "technologies", "tools", "frameworks", "competencies",
                       "technical skills", "core skills"],
    "projects":       ["projects", "project", "portfolio", "side projects"],
    "certifications": ["certification", "certificate", "certified", "credential"],
    "achievements":   ["achievement", "award", "honor", "recognition", "accomplishment"],
}


# ── Public API ────────────────────────────────────────────────────────────────
def analyze_resume(text: str) -> dict:
    text_lower = text.lower()

    # spaCy lemmatization (optional — falls back to simple split)
    if nlp:
        doc = nlp(text[:50_000])
        lemmas = {t.lemma_.lower() for t in doc if not t.is_stop and not t.is_punct}
    else:
        lemmas = set(text_lower.split())

    found_skills   = _detect_skills(text_lower, lemmas)
    sections       = _detect_sections(text_lower)
    action_verbs   = _count_action_verbs(lemmas)
    quant_count    = _count_quantified(text)
    score_breakdown = _score(found_skills, sections, action_verbs, quant_count, text_lower)

    return {
        "skills":                 found_skills,
        "sections":               sections,
        "action_verb_count":      action_verbs,
        "quantified_achievements": quant_count,
        "score":                  score_breakdown["total"],
        "score_breakdown":        score_breakdown,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────
def _detect_skills(text_lower: str, lemmas: set) -> dict:
    found: dict[str, list[str]] = {}
    words = set(text_lower.split())
    for category, skills in SKILLS_BY_CATEGORY.items():
        matched = []
        for skill in skills:
            if " " in skill:             # multi-word (e.g. "machine learning")
                if skill in text_lower:
                    matched.append(_title(skill))
            else:                        # single word — use lemma match
                if skill in lemmas or skill in words:
                    matched.append(_title(skill))
        found[category] = sorted(set(matched))
    return found


def _detect_sections(text_lower: str) -> dict:
    return {
        sec: any(kw in text_lower for kw in kws)
        for sec, kws in SECTION_KEYWORDS.items()
    }


def _count_action_verbs(lemmas: set) -> int:
    return len(ACTION_VERBS & lemmas)


def _count_quantified(text: str) -> int:
    # Match numbers (standalone or with %, $, k, m, b, +)
    return len(re.findall(r"\b\d+[\+%$kmb]?\b", text, re.IGNORECASE))


def _score(found_skills, sections, action_verbs, quant_count, text_lower) -> dict:
    s: dict[str, int] = {}

    # Contact info — 10 pts
    has_email = bool(re.search(r"[\w.\-+]+@[\w.\-]+\.\w{2,}", text_lower))
    has_phone = bool(re.search(r"[\+\(]?[\d\s\-\(\)]{7,15}", text_lower))
    s["contact_info"] = (5 if has_email else 0) + (5 if has_phone else 0)

    # Skills diversity — 25 pts
    total_skills = sum(len(v) for v in found_skills.values())
    s["skills"] = min(25, int(total_skills * 1.25))

    # Work experience section — 20 pts
    s["experience"] = 20 if sections.get("experience") else 0

    # Education section — 15 pts
    s["education"] = 15 if sections.get("education") else 0

    # Action verbs — 15 pts
    s["action_verbs"] = min(15, action_verbs * 2)

    # Quantified achievements — 15 pts
    s["achievements"] = min(15, quant_count * 2)

    s["total"] = min(100, sum(v for k, v in s.items() if k != "total"))
    return s


def _title(skill: str) -> str:
    """Capitalise skill names nicely (Vue.js → Vue.Js → fixed manually)."""
    specials = {
        "node.js": "Node.js", "vue.js": "Vue.js", "next.js": "Next.js",
        "express.js": "Express.js", "scikit-learn": "scikit-learn",
        "asp.net": "ASP.NET", "devops": "DevOps", "mlops": "MLOps",
        "aws": "AWS", "gcp": "GCP", "sql": "SQL", "nosql": "NoSQL",
        "html": "HTML", "css": "CSS", "php": "PHP", "api": "API",
        "ci/cd": "CI/CD", "nlp": "NLP", "oop": "OOP", "rest": "REST",
    }
    return specials.get(skill.lower(), skill.title())
