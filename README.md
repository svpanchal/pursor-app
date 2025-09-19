# Purser - Price Tracking Application

A minimal price tracking application built with FastAPI, SQLModel, and HTMX.

## Features

- **Watchlist Management**: Add product URLs to track prices
- **Price Targets**: Set target prices for items
- **Real-time Updates**: HTMX-powered dynamic updates
- **Scheduled Checks**: Hourly price checks and daily digests (placeholders)
- **Email Notifications**: Gmail SMTP integration (placeholder)

## Tech Stack

- **Backend**: FastAPI, SQLModel (SQLite)
- **Frontend**: Jinja2 templates, Tailwind CSS (CDN), HTMX
- **Scheduler**: APScheduler for background tasks
- **Email**: Gmail SMTP integration

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Configure Environment** (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your Gmail credentials if you want email functionality
   ```

3. **Run the Application**:
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Open in Browser**:
   Visit [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Usage

1. **Add Items**: Enter a product URL in the form and optionally set a target price
2. **View Watchlist**: See all tracked items with their current status
3. **Check Prices**: Click "Check Now" to trigger manual price checks
4. **Set Targets**: Add target prices to get notified when items reach your desired price

## API Endpoints

- `GET /` - Main watchlist page
- `POST /items` - Add new item (form: `url`, optional `target`)
- `POST /check/now` - Trigger manual price check

## Database Schema

- **Item**: Main product information (URL, domain, title, etc.)
- **Price**: Price history with timestamps
- **Target**: Price targets and rules
- **Flag**: Special flags (free shipping, offers, etc.)

## Development

The application uses:
- SQLite database (created automatically)
- Background scheduler for periodic tasks
- HTMX for dynamic updates without page refreshes
- Tailwind CSS for styling

## Next Steps

This is a minimal scaffold. Future enhancements could include:
- Actual price scraping logic
- Email notifications
- Price history charts
- Advanced filtering and search
- User authentication
