import requests
import random
import time  # <-- keep the time MODULE
from pymongo import MongoClient
from datetime import datetime, date  # <-- NO datetime.time import

# ----------------- API -----------------
URL = "http://127.0.0.1:8000/generate-job"

JOB_ROLES = [
    "Data Engineer", "Data Scientist", "ML Engineer",
    "Backend Developer", "Frontend Developer", "Full Stack Developer",
    "DevOps Engineer", "Cloud Engineer", "Site Reliability Engineer",
    "AI Researcher", "NLP Engineer", "Computer Vision Engineer",
    "Software Engineer", "Platform Engineer", "QA Engineer",
    "Automation Engineer", "Security Engineer", "Blockchain Developer",
    "Mobile App Developer", "Android Developer", "iOS Developer",
    "Product Manager", "Technical Program Manager",
    "Business Analyst", "Data Analyst",
    "Game Developer", "AR/VR Engineer",
    "Embedded Systems Engineer", "IoT Engineer"
]

LOCATIONS = [
    "Bangalore, India", "Hyderabad, India", "Chennai, India",
    "Pune, India", "Mumbai, India", "Delhi NCR, India",
    "Kolkata, India", "Ahmedabad, India", "Jaipur, India",
    "Indore, India", "Noida, India", "Gurgaon, India",
    "Remote - India", "Remote - Global",
    "San Francisco, USA", "New York, USA", "Austin, USA",
    "Toronto, Canada", "Vancouver, Canada",
    "London, UK", "Berlin, Germany", "Amsterdam, Netherlands",
    "Dublin, Ireland", "Paris, France"
]

EXPERIENCE = ["0-1", "1-3", "2-4", "3-5", "5-8", "8-12"]
MODES = ["online", "offline", "hybrid"]

# ----------------- MongoDB -----------------
MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)
db = client["job_generator"]
jobs_collection = db["jobs"]

# ----------------- Batch Job Generation -----------------
for i in range(1000):
    payload = {
        "job_role": random.choice(JOB_ROLES),
        "location": random.choice(LOCATIONS),
        "experience": random.choice(EXPERIENCE),
        "mode": random.choice(MODES),
        "temperature": round(random.uniform(0.3, 0.6), 2)
    }

    try:
        response = requests.post(URL, json=payload, timeout=180)
        response.raise_for_status()

        job = response.json()

        # Convert date → datetime for MongoDB safety
        for key in ["posted_date", "created_at"]:
            if key in job and isinstance(job[key], date) and not isinstance(job[key], datetime):
                job[key] = datetime.combine(job[key], datetime.min.time())

        jobs_collection.insert_one(job)

        print(
            f"{i + 1}/1000 inserted: "
            f"{job.get('job_title', 'Unknown')} at {job.get('company_name', 'Unknown')}"
        )

    except Exception as e:
        print(f"Failed at {i + 1}: {e}")

    time.sleep(0.3)  # throttle API requests
