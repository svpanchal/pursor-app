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
from .models import Item, Price, Target, Flag
from .emailer import send_email
from .scraping import fetch_listing

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

async def check_all_items():
    """Check all items for price updates."""
    logger.info("Checking all items for price updates...")
    
    session = get_session()
    try:
        # Get all active items
        statement = select(Item).where(Item.is_paused == False)
        items = session.exec(statement).all()
        
        for item in items:
            await check_single_item(item, session)
            
    except Exception as e:
        logger.error(f"Error in check_all_items: {e}")
    finally:
        session.close()

async def check_single_item(item: Item, session: Session):
    """Check a single item for price updates."""
    try:
        # Fetch listing data
        listing_data = await fetch_listing(item.url)
        
        # Update item with scraped data
        if listing_data.get("title"):
            item.title = listing_data["title"]
        if listing_data.get("image_url"):
            item.image_url = listing_data["image_url"]
        if listing_data.get("site_name"):
            item.site_name = listing_data["site_name"]
        if listing_data.get("currency"):
            item.currency = listing_data["currency"]
        
        item.updated_at = datetime.utcnow()
        session.add(item)
        
        # Save price if found
        price = listing_data.get("price")
        if price is not None:
            price_cents = int(price * 100)  # Convert to cents
            price_record = Price(
                item_id=item.id,
                price_cents=price_cents,
                currency=listing_data.get("currency", "USD"),
                fetched_at=datetime.utcnow(),
                source_confidence=1.0
            )
            session.add(price_record)
            
            logger.info(f"checked item={item.id} domain={item.domain} price={price} {listing_data.get('currency', 'USD')}")
        else:
            logger.info(f"checked item={item.id} domain={item.domain} price=None")
        
        # Save flags
        flags = listing_data.get("flags", {})
        if flags:
            # Get or create flag record
            flag_statement = select(Flag).where(Flag.item_id == item.id)
            flag_record = session.exec(flag_statement).first()
            
            if not flag_record:
                flag_record = Flag(item_id=item.id)
            
            if "free_shipping" in flags:
                flag_record.free_shipping = flags["free_shipping"]
            if "accepts_offers" in flags:
                flag_record.accepts_offers = flags["accepts_offers"]
            
            session.add(flag_record)
        
        session.commit()
        
    except Exception as e:
        logger.error(f"Error checking item {item.id}: {e}")
        session.rollback()

def send_daily_digest():
    """Send daily price digest email (placeholder)."""
    logger.info("Sending daily price digest...")
    # TODO: Implement daily digest logic

def build_watchlist_rows(session: Session) -> List[dict]:
    """Build enhanced rows for the watchlist table."""
    # Get all items
    statement = select(Item).order_by(Item.created_at.desc())
    items = session.exec(statement).all()
    
    # Build enhanced rows with price calculations
    rows = []
    for item in items:
        # Get ordered price history (oldest→newest)
        price_statement = select(Price).where(Price.item_id == item.id).order_by(Price.fetched_at.asc())
        prices = session.exec(price_statement).all()
        
        # Get target
        target_statement = select(Target).where(Target.item_id == item.id).limit(1)
        target = session.exec(target_statement).first()
        
        # Compute price metrics
        current_cents = prices[-1].price_cents if prices else None
        first_cents = prices[0].price_cents if prices else None
        
        # Calculate delta percentage
        delta_pct_str = "—"
        if current_cents and first_cents and first_cents > 0:
            delta_pct = ((current_cents - first_cents) / first_cents) * 100
            delta_pct_str = f"{delta_pct:+.1f}%"
        
        # Build sparkline data (last up to 10 values)
        sparkline_labels = []
        sparkline_values = []
        if prices:
            # Take last 10 prices
            recent_prices = prices[-10:]
            sparkline_labels = [str(i) for i in range(len(recent_prices))]
            sparkline_values = [float(price.price_cents) / 100.0 for price in recent_prices]  # Convert to USD
        
        sparkline = {
            "labels": sparkline_labels,
            "data": sparkline_values
        }
        
        # Build row data
        row = {
            "id": item.id,
            "url": item.url,
            "domain": item.domain,
            "title": item.title or item.url,
            "site_name": item.site_name or item.domain,
            "image_url": item.image_url,
            "current_cents": current_cents,
            "target_cents": target.target_cents if target else None,
            "delta_pct": delta_pct_str,
            "sparkline": sparkline
        }
        rows.append(row)
    
    return rows

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, session: Session = Depends(get_session)):
    """Render the main watchlist page."""
    rows = build_watchlist_rows(session)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "rows": rows
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
    
    # Build updated rows and return the full table for HTMX
    rows = build_watchlist_rows(session)
    
    return templates.TemplateResponse("partials/watchlist_table.html", {
        "request": request,
        "rows": rows
    })

@app.delete("/items/{item_id}", response_class=HTMLResponse)
async def remove_item(
    request: Request,
    item_id: int,
    session: Session = Depends(get_session)
):
    """Remove an item from the watchlist."""
    # Find the item
    statement = select(Item).where(Item.id == item_id)
    item = session.exec(statement).first()
    
    if item:
        # Delete related records first
        session.exec(select(Price).where(Price.item_id == item_id)).all()
        session.exec(select(Target).where(Target.item_id == item_id)).all()
        session.exec(select(Flag).where(Flag.item_id == item_id)).all()
        
        # Delete the item
        session.delete(item)
        session.commit()
        
        logger.info(f"Removed item {item_id}")
    
    # Build updated rows and return the full table for HTMX
    rows = build_watchlist_rows(session)
    
    return templates.TemplateResponse("partials/watchlist_table.html", {
        "request": request,
        "rows": rows
    })

@app.post("/check/now")
async def check_now():
    """Trigger immediate price check for all items."""
    logger.info("Manual price check triggered")
    
    try:
        # Run the check in the background
        await check_all_items()
        return {"message": "Price check completed", "status": "success"}
    except Exception as e:
        logger.error(f"Error in manual price check: {e}")
        return {"message": f"Price check failed: {str(e)}", "status": "error"}

