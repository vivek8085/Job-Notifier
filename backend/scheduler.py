# scheduler.py
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import os

from scraper import run_all_sites
from db import opportunities_collection, ensure_indexes
from notifier import send_email_alert

load_dotenv()
INTERVAL = int(os.getenv("CHECK_INTERVAL_SECONDS", "1800"))

async def check_once():
    print("[scheduler] running check at", datetime.utcnow().isoformat())
    try:
        items = await run_all_sites()
        for item in items:
            h = item["hash"]
            existing = await opportunities_collection.find_one({"hash": h})
            if existing:
                continue
            doc = {
                "title": item.get("title"),
                "link": item.get("link"),
                "organization": item.get("organization"),
                "posted_date": item.get("posted_date"),
                "summary": item.get("summary"),
                "hash": h,
                "discovered_at": item.get("discovered_at"),
                "notified": False,
                "applied": False,
            }
            try:
                await opportunities_collection.insert_one(doc)
            except Exception as e:
                print(f"[scheduler] insert failed: {e}")
                continue

            subject = f"New Opportunity: {doc['title']}"
            body = f"<p><strong>{doc['title']}</strong></p><p>Org: {doc.get('organization')}</p><p><a href='{doc['link']}'>Apply / View</a></p>"
            send_email_alert(subject, body)
            await opportunities_collection.update_one({"hash": h}, {"$set": {"notified": True}})
    except Exception as e:
        print("[scheduler] check_once error:", e)

def start_scheduler(loop=None):
    loop = loop or asyncio.get_event_loop()
    scheduler = AsyncIOScheduler(event_loop=loop)
    scheduler.add_job(lambda: asyncio.create_task(check_once()), 'interval', seconds=INTERVAL, next_run_time=datetime.utcnow())
    scheduler.start()
    print("[scheduler] started with interval", INTERVAL)

async def startup_tasks():
    await ensure_indexes()
    await check_once()
