import json
import re
import uuid
from datetime import datetime
from pydantic import BaseModel

# Example JobRecord model (simplified)
class JobRecord(BaseModel):
    job_id: str
    job_title: str
    company_name: str
    seniority_level: str
    description: str
    tech_stack: list
    responsibilities: list
    ctc: dict
    location: str
    mode: str
    working_days: list
    working_hours: str
    experience_required: dict
    duration_to_apply_days: int
    employment_type: str
    posted_date: str

# Sample raw response from LLM
raw_response = """
Here is a realistic job posting as a JSON object:

{
  "job_title": "Data Engineer",
  "company_name": "TechCorp",
  "seniority_level": "Mid",
  "description": "We are looking for an experienced Data Engineer to join our team in Hyderabad, India. As a Data Engineer, you will be responsible for designing, building and maintaining large-scale data processing systems.",
  "tech_stack": [
    "Python",
    "Hadoop",
    "Spark",
    "Pandas",
    "Docker"
  ],
  "responsibilities": [
    "Design and develop scalable data pipelines",
    "Build and maintain big data processing systems",
    "Collaborate with data scientists to integrate data into analytics workflows",
    "Troubleshoot and optimize data processing workflows"
  ],
  "ctc": {
    "amount": 1200000,
    "currency": "INR",
    "range_low": 1000000,
    "range_high": 1400000
  },
  "location": "Hyderabad, India",
  "mode": "hybrid",
  "working_days": [
    "Monday to Friday"
  ],
  "working_hours": "9:00 AM - 6:00 PM",
  "experience_required": {
    "min_years": 2,
    "max_years": 4
  },
  "duration_to_apply_days": 10,
  "employment_type": "Full-time",
  "posted_date": "2023-03-15T00:00:00"
}
"""

# --- Extract JSON block using regex ---
match = re.search(r"\{.*\}", raw_response, re.DOTALL)
if not match:
    raise ValueError("No JSON object found in raw response")

json_str = match.group(0)
data = json.loads(json_str)

# Add backend-controlled UUID
data["job_id"] = str(uuid.uuid4())

# Normalize posted_date to YYYY-MM-DD
if "posted_date" in data:
    try:
        dt = datetime.fromisoformat(data["posted_date"].replace("Z", "+00:00"))
        data["posted_date"] = dt.date().isoformat()
    except Exception:
        data["posted_date"] = datetime.today().isoformat()

# Validate with Pydantic model
job = JobRecord(**data)

# Print result
print(json.dumps(job.model_dump(), indent=2))
