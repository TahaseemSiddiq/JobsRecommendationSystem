from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class CTC(BaseModel):
    amount: float
    currency: str
    range_low: float
    range_high: float

class ExperienceRequired(BaseModel):
    min_years: int
    max_years: int

class JobRecord(BaseModel):
    job_id: str
    job_title: str
    sector: str
    company_name: str
    company_description: str
    seniority_level: str
    description: str

    tech_stack: List[str]
    responsibilities: List[str]

    ctc: CTC
    location: str
    mode: str
    working_days: List[str]
    working_hours: str

    experience_required: ExperienceRequired
    duration_to_apply_days: int
    employment_type: str
    posted_date: date
    company_size: str
