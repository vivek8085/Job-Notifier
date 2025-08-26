from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel
from typing import List
import requests
from bs4 import BeautifulSoup
import asyncio
import threading
from urllib.parse import quote_plus
import datetime

# ---------- FastAPI ----------
app = FastAPI()

# --- Enable CORS so frontend can talk to backend ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in prod: ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- MongoDB ----------
username = quote_plus("s8994680")
password = quote_plus("Student@2238")
uri = f"mongodb+srv://{username}:{password}@cluster0.ojmuisw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)

db = client["job_monitor"]
sites_collection = db["sites"]
jobs_collection = db["jobs"]

# ---------- Models ----------
class Site(BaseModel):
    name: str
    url: str

class Job(BaseModel):
    title: str
    link: str
    site: str

# ---------- API Endpoints ----------
@app.get("/sites")
def get_sites():
    sites = list(sites_collection.find({}, {"_id": 0}))
    return {"sites": sites}

@app.post("/sites")
def add_site(site: Site):
    if sites_collection.find_one({"name": site.name}):
        return {"message": "Site already exists"}
    sites_collection.insert_one(site.dict())
    return {"message": "Site added successfully"}

@app.delete("/sites/{name}")
def delete_site(name: str):
    sites_collection.delete_one({"name": name})
    return {"message": "Site deleted successfully"}

@app.get("/jobs")
def get_jobs():
    jobs = list(jobs_collection.find({}, {"_id": 0}))
    return {"jobs": jobs}

@app.get("/check_now")
def check_now():
    results = run_scraper()
    return {"checked": results}

# ---------- Scraper ----------
def scrape_site(name, url):
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        links = soup.find_all("a")
        jobs = []
        for link in links[:10]:  # limit for demo
            title = link.get_text(strip=True)
            href = link.get("href")
            if title and href:
                jobs.append({
                    "title": title,
                    "link": href if href.startswith("http") else url + href,
                    "site": name
                })

        if jobs:
            jobs_collection.delete_many({"site": name})  # clear old
            jobs_collection.insert_many(jobs)
            print(f"[+] {len(jobs)} jobs updated from {name}")
            return f"{len(jobs)} jobs from {name}"
        return f"No jobs found on {name}"

    except Exception as e:
        print(f"[ERROR] {name} -> {e}")
        return f"Error scraping {name}: {e}"

def run_scraper():
    sites = list(sites_collection.find({}, {"_id": 0}))
    results = []
    for site in sites:
        results.append(scrape_site(site["name"], site["url"]))
    return results

# ---------- Scheduler ----------
async def scheduler():
    while True:
        run_scraper()
        await asyncio.sleep(3600)  # every 1 hr

def start_scheduler():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(scheduler())

threading.Thread(target=start_scheduler, daemon=True).start()
