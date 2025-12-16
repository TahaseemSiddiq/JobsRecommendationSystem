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
    logger.info(f"Generating job for role: {req.job_role}, location: {req.location}, experience: {req.experience}")

    used_companies = jobs_collection.distinct(
        "company_name",
        {"job_title": req.job_role}
    )

    prompt = f"""
Return ONLY valid JSON.
You are generating a job posting.
Sector: Computer Science
STRICT RULES:
- Do NOT reuse company names listed below IF the job role is "{req.job_role}"
- If the job role is different, reuse is allowed
- You MUST generate a NEW, realistic company name if restricted
Restricted company names for role "{req.job_role}":
{used_companies}
Required fields:
- company_name (string)
- company_description (string)
- responsibilities (array of strings)
- tech_stack (array of strings)
Job role: {req.job_role}
Experience level: {req.experience}
Location: {req.location}
Work mode: {req.mode}
Do NOT include explanations.
ONLY return JSON.
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

        # 2️⃣ Normalize + fill missing fields
        final_data = normalize_job(
            llm_data=llm_data,
            job_role=req.job_role,
            location=req.location,
            mode=req.mode
        )

        # 3️⃣ Add backend ID
        final_data["job_id"] = str(uuid.uuid4())
        final_data["created_at"] = datetime.utcnow()
        final_data["sector"] = "Computer Science"

        # 4️⃣ Ensure datetime fields are valid
        for key, value in final_data.items():
            if isinstance(value, date) and not isinstance(value, datetime):
                final_data[key] = datetime.combine(value, datetime.min.time())

        # 5️⃣ Ensure unique company per role
        MAX_RETRIES = 3
        for _ in range(MAX_RETRIES):
            if final_data["company_name"] not in used_companies:
                break
        else:
            logger.error(f"Failed to generate unique company for role '{req.job_role}'")
            logger.debug(f"Raw response from LLM:\n{raw_output}")
            raise HTTPException(
                status_code=500,
                detail="Could not generate unique company name"
            )

        # 6️⃣ Insert into MongoDB
        jobs_collection.insert_one(final_data)

        # ✅ Success log
        logger.info(f"Job generated successfully: {final_data['job_title']} at {final_data['company_name']}")

        return JobRecord(**final_data)

    except Exception as e:
        # Error log: print raw_output for debugging
        logger.error(f"Job generation failed for role '{req.job_role}': {e}")
        if 'raw_output' in locals():
            logger.debug(f"Raw response from LLM:\n{raw_output}")
        raise HTTPException(
            status_code=422,
            detail={"error": str(e)}
        )
