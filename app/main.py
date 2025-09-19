"""Main FastAPI application."""
import os
import logging
from datetime import datetime
from urllib.parse import urlparse
from typing import List

from fastapi import FastAPI, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .db import engine, init_db, get_session
from .models import Item, Price, Target
from .emailer import send_email

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Purser", description="Price tracking application")

# Setup templates
templates = Jinja2Templates(directory="app/templates")

# Scheduler
scheduler = AsyncIOScheduler()

def domain_from_url(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.replace('www.', '')
    except:
        return "unknown"

@app.on_event("startup")
async def startup_event():
    """Initialize database and start scheduler."""
    logger.info("Starting up Purser...")
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Start scheduler
    scheduler.start()
    
    # Add hourly job to check all items
    scheduler.add_job(
        check_all_items,
        trigger=CronTrigger(minute=0),  # Every hour
        id="check_all_items",
        name="Check all items for price updates"
    )
    
    # Add daily digest job
    digest_time = os.getenv("DIGEST_TIME_ET", "09:00")
    scheduler.add_job(
        send_daily_digest,
        trigger=CronTrigger(hour=int(digest_time.split(':')[0]), 
                           minute=int(digest_time.split(':')[1])),
        id="send_daily_digest",
        name="Send daily price digest"
    )
    
    logger.info("Scheduler started with jobs configured")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown scheduler."""
    scheduler.shutdown()
    logger.info("Scheduler shutdown")

def check_all_items():
    """Check all items for price updates (placeholder)."""
    logger.info("Checking all items for price updates...")
    # TODO: Implement actual price scraping logic

def send_daily_digest():
    """Send daily price digest email (placeholder)."""
    logger.info("Sending daily price digest...")
    # TODO: Implement daily digest logic

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, session: Session = Depends(get_session)):
    """Render the main watchlist page."""
    # Get all items with their latest prices and targets
    statement = select(Item).order_by(Item.created_at.desc())
    items = session.exec(statement).all()
    
    # For each item, get the latest price and target
    for item in items:
        # Get latest price
        price_statement = select(Price).where(Price.item_id == item.id).order_by(Price.fetched_at.desc()).limit(1)
        item.prices = session.exec(price_statement).all()
        
        # Get target
        target_statement = select(Target).where(Target.item_id == item.id).limit(1)
        item.targets = session.exec(target_statement).all()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "items": items
    })

@app.post("/items", response_class=HTMLResponse)
async def add_item(
    request: Request,
    url: str = Form(...),
    target: int = Form(None),
    session: Session = Depends(get_session)
):
    """Add a new item to the watchlist."""
    # Extract domain from URL
    domain = domain_from_url(url)
    
    # Create new item
    item = Item(
        url=url,
        domain=domain,
        title=url,  # Use URL as title for now
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    session.add(item)
    session.commit()
    session.refresh(item)
    
    # Add target if provided
    if target:
        target_obj = Target(
            item_id=item.id,
            target_cents=target
        )
        session.add(target_obj)
        session.commit()
    
    # Get updated items list
    statement = select(Item).order_by(Item.created_at.desc())
    items = session.exec(statement).all()
    
    # For each item, get the latest price and target
    for item in items:
        # Get latest price
        price_statement = select(Price).where(Price.item_id == item.id).order_by(Price.fetched_at.desc()).limit(1)
        item.prices = session.exec(price_statement).all()
        
        # Get target
        target_statement = select(Target).where(Target.item_id == item.id).limit(1)
        item.targets = session.exec(target_statement).all()
    
    # Return just the table body for HTMX
    return templates.TemplateResponse("partials/table_body.html", {
        "request": request,
        "items": items
    })

@app.post("/check/now")
async def check_now():
    """Trigger immediate price check (placeholder)."""
    logger.info("Manual price check triggered")
    return {"message": "Price check triggered", "status": "success"}

