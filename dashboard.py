# /dashboard.py
from flask import Blueprint, render_template, jsonify, request

from tastytrade_client import client
from utils import format_currency, format_percentage, format_datetime
from logger import get_logger

logger = get_logger(__name__)

# Create Blueprint
dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/')
def index():
    """Render the main dashboard page."""
    logger.info("Loading dashboard")
    
    # Return the dashboard template
    return render_template('dashboard.html')

@dashboard.route('/api/data')
def get_data():
    """API endpoint to get the latest data for the dashboard."""
    logger.info("API request for dashboard data")
    
    # Check if the client is authenticated
    if not client.authenticated:
        logger.warning("Client not authenticated, returning demo data")
        return jsonify({
            "message": "Running in demo mode. Authentication failed or credentials not provided.",
            "account": {
                "cash_balance": format_currency(0),
                "total_equity": format_currency(0),
                "buying_power": format_currency(0),
                "raw_cash_balance": 0,
                "timestamp": None,
                "formatted_timestamp": "Demo Mode"
            },
            "mstu": {
                "symbol": "MSTU",
                "description": "Microstrategy Inc (Demo)",
                "last_price": format_currency(0),
                "bid_price": format_currency(0),
                "ask_price": format_currency(0),
                "change": format_currency(0),
                "percent_change": format_percentage(0),
                "raw_last_price": 0,
                "timestamp": None,
                "formatted_timestamp": "Demo Mode"
            },
            "api_calls": client.get_api_calls_history()
        })
    
    # Get account balance and MSTU price
    account_balance = client.get_account_balance()
    mstu_price = client.get_mstu_price()
    api_calls = client.get_api_calls_history()
    
    # Check if we got valid data
    if not account_balance:
        account_balance = {
            'cash_balance': 0,
            'total_equity': 0,
            'buying_power': 0,
            'timestamp': None
        }
    
    if not mstu_price:
        mstu_price = {
            'symbol': 'MSTU',
            'description': 'Microstrategy Inc',
            'last_price': 0,
            'bid_price': 0,
            'ask_price': 0,
            'change': 0,
            'percent_change': 0,
            'timestamp': None
        }
    
    # Format the data for display
    formatted_data = {
        'account': {
            'cash_balance': format_currency(account_balance['cash_balance']),
            'total_equity': format_currency(account_balance['total_equity']),
            'buying_power': format_currency(account_balance['buying_power']),
            'raw_cash_balance': account_balance['cash_balance'],
            'timestamp': account_balance['timestamp'],
            'formatted_timestamp': format_datetime(account_balance['timestamp']) if account_balance['timestamp'] else 'Unknown'
        },
        'mstu': {
            'symbol': mstu_price['symbol'],
            'description': mstu_price['description'],
            'last_price': format_currency(mstu_price['last_price']),
            'bid_price': format_currency(mstu_price['bid_price']),
            'ask_price': format_currency(mstu_price['ask_price']),
            'change': format_currency(mstu_price['change']),
            'percent_change': format_percentage(mstu_price['percent_change']),
            'raw_last_price': mstu_price['last_price'],
            'timestamp': mstu_price['timestamp'],
            'formatted_timestamp': format_datetime(mstu_price['timestamp']) if mstu_price['timestamp'] else 'Unknown'
        },
        'api_calls': api_calls
    }
    
    return jsonify(formatted_data)

@dashboard.route('/api/buy-mstu', methods=['POST'])
def buy_mstu():
    """API endpoint to buy MSTU stock."""
    logger.info("API request to buy MSTU")
    
    # Check if the client is authenticated
    if not client.authenticated:
        return jsonify({
            'success': False,
            'message': 'Cannot place orders in demo mode. Authentication required.'
        })
    
    try:
        # Get form data
        quantity = request.form.get('quantity', type=int)
        order_type = request.form.get('order_type', 'Market')
        price = request.form.get('price', type=float) if order_type == 'Limit' else None
        
        # Validate quantity
        if not quantity or quantity <= 0:
            logger.warning("Invalid quantity for MSTU purchase")
            return jsonify({
                'success': False,
                'message': 'Invalid quantity. Please enter a positive number.'
            })
        
        # Validate price for limit orders
        if order_type == 'Limit' and (not price or price <= 0):
            logger.warning("Invalid price for limit order")
            return jsonify({
                'success': False,
                'message': 'Invalid price for limit order. Please enter a positive number.'
            })
        
        # Place the order
        result = client.buy_mstu(quantity, order_type, price)
        
        # Return the result
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing buy MSTU request: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        })
