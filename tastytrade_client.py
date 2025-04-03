# /tastytrade_client.py
import time
import json
from datetime import datetime
import pytz

from tastytrade_sdk import Tastytrade
from tastytrade_sdk.exceptions import TastytradeSdkException

import config
from logger import get_logger

logger = get_logger(__name__)

class TastetradeClient:
    """Client for interacting with the Tastytrade API."""
    
    def __init__(self):
        self.tasty = None
        self.authenticated = False
        self.last_auth_time = None
        self.api_calls = []  # Track recent API calls
        self.MAX_API_CALLS_HISTORY = 50  # Maximum number of API calls to store in history
        
    def authenticate(self):
        """Authenticate with the Tastytrade API."""
        try:
            logger.info("Authenticating with Tastytrade API")
            self.tasty = Tastytrade(api_base_url=config.API_BASE_URL)
            self.tasty.login(config.TASTYTRADE_LOGIN, config.TASTYTRADE_PASSWORD)
            self.authenticated = True
            self.last_auth_time = datetime.now()
            self._track_api_call("Authentication", "SUCCESS")
            logger.info("Authentication successful")
            return True
        except Exception as e:
            self.authenticated = False
            self._track_api_call("Authentication", f"FAILED: {str(e)}")
            logger.error(f"Authentication failed: {str(e)}")
            return False
    
    def ensure_authenticated(self):
        """Ensure the client is authenticated, re-authenticate if necessary."""
        if not self.authenticated or not self.tasty:
            return self.authenticate()
        
        # Re-authenticate every 6 hours to be safe
        if self.last_auth_time and (datetime.now() - self.last_auth_time).total_seconds() > 21600:
            logger.info("Session may be expired, re-authenticating")
            return self.authenticate()
        
        return True
    
    def get_account_balance(self):
        """Get the account balance."""
        if not self.ensure_authenticated():
            return None
        
        try:
            logger.info(f"Fetching account balance for account {config.ACCOUNT_NUMBER}")
            response = self.tasty.api.get(f'/accounts/{config.ACCOUNT_NUMBER}/balances')
            
            if not response or 'data' not in response:
                self._track_api_call("Get Account Balance", "FAILED: No data in response")
                logger.error("Failed to get account balance: No data in response")
                return None
            
            # Extract the cash balance
            balances = response['data']
            cash_balance = balances.get('cash_balance', 0)
            total_equity = balances.get('equity', 0)
            buying_power = balances.get('buying_power', 0)
            
            result = {
                'cash_balance': cash_balance,
                'total_equity': total_equity,
                'buying_power': buying_power,
                'timestamp': datetime.now().isoformat()
            }
            
            self._track_api_call("Get Account Balance", "SUCCESS")
            logger.info(f"Account balance retrieved successfully: {json.dumps(result)}")
            return result
        except Exception as e:
            self._track_api_call("Get Account Balance", f"FAILED: {str(e)}")
            logger.error(f"Failed to get account balance: {str(e)}")
            return None
    
    def get_mstu_price(self):
        """Get the current MSTU price."""
        if not self.ensure_authenticated():
            return None
        
        try:
            logger.info("Fetching MSTU price")
            response = self.tasty.api.get(
                '/instruments/equities',
                params=[('symbol[]', 'MSTU')]
            )
            
            if not response or 'data' not in response or 'items' not in response['data']:
                self._track_api_call("Get MSTU Price", "FAILED: No data in response")
                logger.error("Failed to get MSTU price: No data in response")
                return None
            
            items = response['data']['items']
            if not items:
                self._track_api_call("Get MSTU Price", "FAILED: MSTU symbol not found")
                logger.error("Failed to get MSTU price: Symbol not found")
                return None
                
            # Get the first item (should be MSTU)
            mstu_data = items[0]
            
            # Check if we have quotes
            if 'quotes' not in mstu_data:
                # If no quotes, we need to get quotes separately
                try:
                    quotes_response = self.tasty.api.get(f"/quotes/equities/MSTU")
                    if quotes_response and 'data' in quotes_response:
                        quotes = quotes_response['data']
                    else:
                        self._track_api_call("Get MSTU Quote", "FAILED: No quote data")
                        logger.error("Failed to get MSTU quote data")
                        return None
                except Exception as e:
                    self._track_api_call("Get MSTU Quote", f"FAILED: {str(e)}")
                    logger.error(f"Error fetching MSTU quote: {str(e)}")
                    return None
            else:
                quotes = mstu_data['quotes']
            
            result = {
                'symbol': 'MSTU',
                'description': mstu_data.get('description', 'Microstrategy Inc'),
                'last_price': quotes.get('last', 0),
                'bid_price': quotes.get('bid', 0),
                'ask_price': quotes.get('ask', 0),
                'change': quotes.get('change', 0),
                'percent_change': quotes.get('change-percent', 0),
                'timestamp': datetime.now().isoformat()
            }
            
            self._track_api_call("Get MSTU Price", "SUCCESS")
            logger.info(f"MSTU price retrieved successfully: {json.dumps(result)}")
            return result
        except Exception as e:
            self._track_api_call("Get MSTU Price", f"FAILED: {str(e)}")
            logger.error(f"Failed to get MSTU price: {str(e)}")
            return None
    
    def buy_mstu(self, quantity, order_type='Limit', price=None, time_in_force='Day'):
        """
        Buy MSTU stock.
        
        Args:
            quantity: Number of shares to buy
            order_type: 'Market' or 'Limit'
            price: Limit price (required for Limit orders)
            time_in_force: 'Day', 'GTC', etc.
        
        Returns:
            dict: Information about the order status
        """
        if not self.ensure_authenticated():
            return {"success": False, "message": "Authentication failed"}
        
        if order_type == 'Limit' and price is None:
            message = "Limit orders require a price"
            self._track_api_call("Buy MSTU", f"FAILED: {message}")
            logger.error(message)
            return {"success": False, "message": message}
        
        try:
            # Prepare the order payload
            order_payload = {
                "account-id": config.ACCOUNT_NUMBER,
                "source": "API",
                "order-type": order_type,
                "time-in-force": time_in_force,
                "legs": [{
                    "instrument-type": "Equity",
                    "symbol": "MSTU",
                    "quantity": quantity,
                    "action": "Buy"
                }]
            }
            
            # Add price for limit orders
            if order_type == 'Limit' and price is not None:
                order_payload["price"] = price
                
            logger.info(f"Placing order to buy {quantity} shares of MSTU")
            logger.debug(f"Order payload: {json.dumps(order_payload)}")
            
            # Place the order
            response = self.tasty.api.post('/orders', data=order_payload)
            
            if not response or 'data' not in response:
                message = "No data in order response"
                self._track_api_call("Buy MSTU", f"FAILED: {message}")
                logger.error(f"Failed to place MSTU order: {message}")
                return {"success": False, "message": message}
            
            order_data = response['data']
            
            # Check if order was accepted
            if 'order' in order_data and order_data.get('status') == 'Received':
                order_id = order_data.get('order-id')
                message = f"Order successfully placed. Order ID: {order_id}"
                self._track_api_call("Buy MSTU", f"SUCCESS: {message}")
                logger.info(message)
                
                return {
                    "success": True,
                    "message": message,
                    "order_id": order_id,
                    "status": order_data.get('status'),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                error_code = order_data.get('error-code', 'Unknown error')
                error_message = order_data.get('error-message', 'No details provided')
                message = f"Order failed. Code: {error_code}, Message: {error_message}"
                self._track_api_call("Buy MSTU", f"FAILED: {message}")
                logger.error(message)
                
                return {
                    "success": False,
                    "message": message,
                    "error_code": error_code,
                    "error_message": error_message,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            message = f"Exception while placing MSTU order: {str(e)}"
            self._track_api_call("Buy MSTU", f"FAILED: {message}")
            logger.error(message)
            return {"success": False, "message": message}
    
    def get_api_calls_history(self):
        """Get the history of recent API calls."""
        return self.api_calls
    
    def _track_api_call(self, endpoint, status):
        """Track an API call in the history."""
        eastern = pytz.timezone('US/Eastern')
        timestamp = datetime.now(eastern).strftime("%Y-%m-%d %H:%M:%S %Z")
        
        self.api_calls.insert(0, {
            "endpoint": endpoint,
            "status": status,
            "timestamp": timestamp
        })
        
        # Trim the history if it gets too long
        if len(self.api_calls) > self.MAX_API_CALLS_HISTORY:
            self.api_calls = self.api_calls[:self.MAX_API_CALLS_HISTORY]

# Create a singleton instance
client = TastetradeClient()
