import os
import uuid
import time
import requests
import random
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import date
from db import jobs_collection
from datetime import datetime
from JobRecord import JobRecord
from logger import setup_logger
from helper_functions import extract_json_safe, normalize_job

# -------------------------------------------------
# ENV & LOGGER
# -------------------------------------------------
load_dotenv()
logger = setup_logger("job-generator")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

if not OLLAMA_BASE_URL or not OLLAMA_MODEL:
    raise RuntimeError("Missing Ollama configuration")

app = FastAPI(title="LLM Job Generator API")

# -------------------------------------------------
# Ollama Call
# -------------------------------------------------
def call_ollama(payload, timeout=300):
    return requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json=payload,
        timeout=timeout
    )

# -------------------------------------------------
# REQUEST MODEL
# -------------------------------------------------
class JobPromptRequest(BaseModel):
    job_role: str
    location: str
    experience: str
    mode: str
    temperature: float = 0.4

# -------------------------------------------------
# ENDPOINT
# -------------------------------------------------
@app.post("/generate-job", response_model=JobRecord)
def generate_job(req: JobPromptRequest):
    logger.info("POST /generate-job")
    
    used_companies = jobs_collection.distinct(
    "company_name",
    {"job_title": req.job_role}
)

    prompt = f"""
Let’s play a very important and strict game.

You are a specialized data-generation AI whose ONLY job is to generate
a SINGLE job posting in VALID JSON format.

You have level 280 expertise in following rules and constraints.
If you violate ANY rule below, the output is considered FAILED and unusable,
causing system errors and data corruption. This is unacceptable.

========================
ABSOLUTE OUTPUT RULES
========================
- Output MUST be valid JSON
- Output MUST contain ONLY the JSON object
- NO comments
- NO explanations
- NO markdown
- NO trailing text
- NO duplicate records
- NO repeated company names when restricted

If you cannot comply PERFECTLY, you must internally retry until you can.

========================
TASK
========================
Generate ONE job posting.

Sector: Computer Science

========================
CRITICAL DEDUPLICATION RULE
========================
You are given a list of company names that have ALREADY been used.

IF AND ONLY IF the job role is EXACTLY:
"{req.job_role}"

THEN:
- You are STRICTLY FORBIDDEN from using ANY company name from the list below
- You MUST invent a BRAND-NEW, realistic company name
- The new company name MUST NOT be similar, derivative, or a variation
  of any listed company (no synonyms, abbreviations, or stylistic changes)

IF the job role is DIFFERENT:
- Reuse is allowed

Restricted company names (DO NOT USE for this role):
{used_companies}

========================
REQUIRED FIELDS (NO MORE, NO LESS)
========================
- company_name: string
- company_description: string
- responsibilities: array of strings
- tech_stack: array of strings

========================
JOB PARAMETERS
========================
Job role: {req.job_role}
Experience level: {req.experience}
Location: {req.location}
Work mode: {req.mode}

========================
SELF-CHECK BEFORE OUTPUT (MANDATORY)
========================
Before returning the JSON, you MUST internally verify:
1. The company_name is NOT in the restricted list (if restricted)
2. The company_name has NOT appeared previously in this session
3. All required fields exist and are correctly typed
4. responsibilities and tech_stack are arrays with multiple items
5. The JSON is syntactically valid

If ANY check fails → regenerate silently.

========================
FINAL INSTRUCTION
========================
Return ONLY the JSON object.
Anything else is a failure.
"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "temperature": req.temperature,
        "num_predict": 300,
        "stream": False
    }

    try:
        response = call_ollama(payload)
        raw_output = response.json().get("response", "")

        # 1️⃣ Extract JSON safely
        llm_data = extract_json_safe(raw_output)

        if not llm_data:
            logger.error("LLM returned invalid JSON")
            logger.debug(raw_output)
            raise ValueError("Invalid JSON from LLM")

        # 2️⃣ Normalize
        final_data = normalize_job(
            llm_data=llm_data,
            job_role=req.job_role,
            location=req.location,
            mode=req.mode
        )

        final_data["job_title"] = final_data.get("job_title") or req.job_role
        final_data["sector"] = "Computer Science"
        final_data["job_id"] = str(uuid.uuid4())
        final_data["created_at"] = datetime.utcnow()

        for key, value in final_data.items():
            if isinstance(value, date) and not isinstance(value, datetime):
                final_data[key] = datetime.combine(value, datetime.min.time())

        job = JobRecord(**final_data)
        jobs_collection.insert_one(final_data)

        # ✅ SUCCESS LOG (clean)
        logger.info(
            f"Inserted job | title={job.job_title} | company={job.company_name}"
        )

        return job

    except Exception as e:
        logger.exception("Job generation failed")
        raise HTTPException(
            status_code=422,
            detail={"error": str(e)}
        )
