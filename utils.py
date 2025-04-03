# /utils.py
import json
from datetime import datetime
import pytz

from logger import get_logger

logger = get_logger(__name__)

def format_currency(value):
    """Format a value as US currency."""
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        logger.warning(f"Could not format currency value: {value}")
        return f"${0:,.2f}"

def format_percentage(value):
    """Format a value as a percentage."""
    try:
        return f"{float(value):.2f}%"
    except (ValueError, TypeError):
        logger.warning(f"Could not format percentage value: {value}")
        return f"0.00%"

def format_datetime(iso_datetime_str):
    """Format an ISO datetime string to a readable format."""
    try:
        dt = datetime.fromisoformat(iso_datetime_str)
        eastern = pytz.timezone('US/Eastern')
        dt = dt.astimezone(eastern)
        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")
    except (ValueError, TypeError):
        logger.warning(f"Could not format datetime: {iso_datetime_str}")
        return "Unknown time"

def safe_json_dumps(obj):
    """Safely convert an object to a JSON string."""
    try:
        return json.dumps(obj)
    except Exception as e:
        logger.error(f"Error converting to JSON: {str(e)}")
        return "{}"
