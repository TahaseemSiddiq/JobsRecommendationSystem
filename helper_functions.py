import json
import random
import re
from datetime import date

# -------------------------------------------------
# SAFE JSON EXTRACTION
# -------------------------------------------------
def extract_json_safe(text: str) -> dict:
    """
    Extracts JSON even if LLM adds garbage text.
    Returns empty dict if parsing fails.
    """
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return {}
        return json.loads(match.group(0))
    except Exception:
        return {}

# -------------------------------------------------
# NORMALIZATION (LLM-PROOF)
# -------------------------------------------------
def normalize_job(llm_data: dict, job_role: str, location: str, mode: str) -> dict:
    # ---- LLM FIELDS (safe defaults) ----
    company_name = llm_data.get("company_name", "Confidential Company")
    company_description = llm_data.get(
        "company_description",
        "A growing company focused on delivering quality technology solutions."
    )

    responsibilities = llm_data.get("responsibilities", [])
    if not isinstance(responsibilities, list):
        responsibilities = []

    tech_stack = llm_data.get("tech_stack", [])
    if not isinstance(tech_stack, list):
        tech_stack = []

    # ---- SENIORITY ----
    seniority = random.choice(["Junior", "Mid", "Senior"])

    # ---- EXPERIENCE ----
    min_exp = random.randint(0, 4)
    max_exp = min(min_exp + random.randint(1, 3), 7)

    # ---- CTC ----
    base = random.randint(4, 20) * 100000

    # ---- FINAL OBJECT ----
    return {
        "job_title": job_role,
        "company_name": company_name,
        "company_description": company_description,
        "description": f"{job_role} position at {company_name}",

        "seniority_level": seniority,
        "tech_stack": tech_stack or ["Python", "REST APIs"],
        "responsibilities": responsibilities or [
            "Develop scalable solutions",
            "Collaborate with cross-functional teams"
        ],

        "ctc": {
            "amount": base,
            "currency": "INR",
            "range_low": int(base * 0.9),
            "range_high": int(base * 1.1),
        },

        "location": location,
        "mode": mode if mode in ["online", "offline", "hybrid"] else "hybrid",

        "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "working_hours": "35-45 hours/week",

        "experience_required": {
            "min_years": min_exp,
            "max_years": max_exp
        },

        "duration_to_apply_days": random.randint(15, 45),
        "employment_type": "Full-time",
        "posted_date": date.today(),
        "company_size": random.choice(["1-50", "51-200", "201-1000", "1000+"])
    }
