"""
core/improver.py — Rule-based resume improvement suggestions + Gemini AI hook.
"""
import re
import os
import json
from dotenv import load_dotenv

load_dotenv()

WEAK_VERBS: dict[str, str] = {
    "made":    "engineered",
    "did":     "executed",
    "worked":  "collaborated",
    "helped":  "facilitated",
    "used":    "leveraged",
    "got":     "achieved",
    "fixed":   "resolved",
    "changed": "transformed",
    "showed":  "demonstrated",
    "ran":     "orchestrated",
    "wrote":   "authored",
}

PRIORITY = {"high": 0, "medium": 1, "low": 2}


def generate_suggestions(text: str, analysis: dict, job_matches: list) -> list[dict]:
    suggestions: list[dict] = []
    text_lower  = text.lower()
    sections    = analysis.get("sections", {})

    # ── 1. Missing critical sections ─────────────────────────────────────────
    if not sections.get("summary"):
        suggestions.append({
            "type": "missing_section", "priority": "high", "icon": "📝",
            "title": "Add a Professional Summary",
            "description": (
                "A compelling 2–3 sentence summary at the top dramatically "
                "improves recruiter engagement and ATS ranking."
            ),
        })

    if not sections.get("skills"):
        suggestions.append({
            "type": "missing_section", "priority": "high", "icon": "🛠️",
            "title": "Add a Dedicated Skills Section",
            "description": (
                "ATS systems scan for explicit skills sections. List your "
                "technical and soft skills with clear headings."
            ),
        })

    if not sections.get("projects"):
        suggestions.append({
            "type": "enhancement", "priority": "medium", "icon": "🚀",
            "title": "Showcase Personal / Academic Projects",
            "description": (
                "Projects demonstrate hands-on ability. Add 2–3 with bullet "
                "points describing your impact and technologies used."
            ),
        })

    if not sections.get("certifications"):
        suggestions.append({
            "type": "enhancement", "priority": "low", "icon": "🏆",
            "title": "Add Certifications",
            "description": (
                "Industry certifications (AWS, Google, Microsoft) validate "
                "expertise and are weighted heavily by ATS filters."
            ),
        })

    # ── 2. Weak action verbs ──────────────────────────────────────────────────
    found_weak = [v for v in WEAK_VERBS if re.search(rf"\b{v}\b", text_lower)]
    if found_weak:
        replacements = ", ".join(
            f"'{v}' → '{WEAK_VERBS[v]}'" for v in found_weak[:3]
        )
        suggestions.append({
            "type": "language", "priority": "medium", "icon": "💬",
            "title": "Strengthen Your Action Verbs",
            "description": f"Replace weak verbs — {replacements} — to convey greater impact.",
        })

    # ── 3. Quantified achievements ────────────────────────────────────────────
    if analysis.get("quantified_achievements", 0) < 4:
        suggestions.append({
            "type": "impact", "priority": "high", "icon": "📊",
            "title": "Quantify Your Achievements",
            "description": (
                "Numbers stand out. Add metrics like 'Improved load time by 35%' "
                "or 'Led a team of 8 engineers' to every bullet point."
            ),
        })

    # ── 4. Keyword gaps vs top matched role ───────────────────────────────────
    if job_matches:
        top_role = job_matches[0]
        found_flat = {
            s.lower()
            for skills_list in analysis.get("skills", {}).values()
            for s in skills_list
        }
        missing = [
            sk for sk in top_role.get("required_skills", [])
            if sk.lower() not in found_flat
        ]
        if missing:
            suggestions.append({
                "type": "keywords", "priority": "high", "icon": "🎯",
                "title": f"Add Keywords for {top_role['title']}",
                "description": (
                    f"Your top match is missing: {', '.join(missing[:5])}. "
                    "Add these (if applicable) to boost your match score."
                ),
            })

    # ── 5. Online presence ────────────────────────────────────────────────────
    if not re.search(r"linkedin", text_lower):
        suggestions.append({
            "type": "contact", "priority": "medium", "icon": "🔗",
            "title": "Add Your LinkedIn Profile",
            "description": "90 % of recruiters check LinkedIn. Include your profile URL in the header.",
        })

    if not re.search(r"github|portfolio|behance|dribbble", text_lower):
        suggestions.append({
            "type": "contact", "priority": "low", "icon": "💻",
            "title": "Link Your GitHub or Portfolio",
            "description": "A GitHub/portfolio link lets recruiters see real work, not just words.",
        })

    # ── 6. Gemini AI hook ─────────────────────────────────────────────────────
    ai_suggestions = _get_gemini_suggestions(text, analysis, job_matches)
    suggestions.extend(ai_suggestions)

    suggestions.sort(key=lambda x: PRIORITY.get(x.get("priority", "low"), 3))
    return suggestions


# ─────────────────────────────────────────────────────────────────────────────
#  GEMINI AI HOOK
#  To activate:
#    1. pip install google-generativeai  (already in requirements.txt)
#    2. Set GEMINI_API_KEY in your .env file
#    3. Uncomment the implementation block below
# ─────────────────────────────────────────────────────────────────────────────
def _get_gemini_suggestions(text: str, analysis: dict, job_matches: list) -> list[dict]:
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "your-gemini-api-key-here":
        return []

    # ── UNCOMMENT TO ACTIVATE ──────────────────────────────────────────────
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    top_role = job_matches[0]["title"] if job_matches else "Software Engineer"
    score    = analysis.get("score", 0)

    prompt = f"""
    You are an expert resume coach. The candidate is targeting a {top_role} role.
    Their resume score is {score}/100.

    Resume (first 2000 chars):
    {text[:2000]}

    Give 2 specific, actionable improvements as a JSON array:
    [{{\"title\":\"...\",\"description\":\"...\",\"priority\":\"high|medium|low\",\"icon\":\"emoji\",\"type\":\"ai\"}}]
    Return ONLY the JSON array — no markdown fences, no extra text.
    """
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        print(f"[Gemini hook] error: {e}")
        return []
    # ──────────────────────────────────────────────────────────────────────


def rewrite_resume_with_ai(raw_text: str, suggestions: list) -> str:
    """Uses Gemini AI to rewrite the entire resume incorporating suggestions."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "your-gemini-api-key-here":
        raise ValueError("Gemini API key is not configured. Cannot rewrite resume.")

    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash") # changed to flash to avoid 404 errors with some API keys

    prompt = f"""
    You are an elite, professional resume writer.
    
    Here is the candidate's current resume text:
    ---
    {raw_text}
    ---
    
    Here are the improvement suggestions they want to apply:
    {json.dumps(suggestions, indent=2)}
    
    Task:
    Rewrite the entire resume to be ATS-friendly, impactful, and incorporate ALL of the suggestions above.
    Do NOT include any conversational filler (like "Here is your rewritten resume").
    Return ONLY the raw resume text.
    Use clear, standard section headers like "SUMMARY", "EXPERIENCE", "EDUCATION", "SKILLS".
    Do not use markdown formatting like **bold** or ## headers, just use plain text with newlines so it can be cleanly exported to a .docx file.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"[Gemini Rewrite] error: {e}")
        raise ValueError(f"Failed to generate rewrite: {str(e)}")
