import os
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import schwabdev

logger = logging.getLogger(__name__)

class SchwabClient:
    """Schwab API client for trading operations using schwabdev"""
    
    def __init__(self):
        self.app_key = os.getenv("CLIENT_ID")
        self.app_secret = os.getenv("CLIENT_SECRET")
        
        # Use absolute path in Docker
        if os.path.exists("/app/schwab_tokens.json"):
            tokens_file = "/app/schwab_tokens.json"
        else:
            tokens_file = "schwab_tokens.json"
        
        # Initialize schwabdev client
        try:
            self.client = schwabdev.Client(
                self.app_key,
                self.app_secret,
                callback_url="https://127.0.0.1",
                tokens_file=tokens_file,
                timeout=30
            )
            
            # Get all accounts
            self._init_accounts()
        except Exception as e:
            logger.error(f"Failed to initialize Schwab client: {e}")
            # Create a dummy client for development
            self.client = None
            self.accounts = {}
            self.primary_account_hash = None
            
    def _init_accounts(self):
        """Initialize all account information"""
        try:
            accounts = self.client.account_linked().json()
            self.accounts = {}
            
            if accounts:
                for account in accounts:
                    acc_hash = account['hashValue']
                    acc_number = account['accountNumber']
                    
                    # Get account details to determine type
                    details = self.client.account_details(acc_hash).json()
                    acc_type = details.get('securitiesAccount', {}).get('type', 'Unknown')
                    
                    self.accounts[acc_hash] = {
                        'number': acc_number,
                        'hash': acc_hash,
                        'type': acc_type,
                        'full_details': details
                    }
                    
                    logger.info(f"Found account: {acc_number} (Type: {acc_type})")
                
                # Set primary account (prefer Individual/Brokerage over IRA)
                self.primary_account_hash = self._select_primary_account()
                logger.info(f"Primary trading account: {self.accounts[self.primary_account_hash]['number']}")
            else:
                logger.error("No accounts found")
                self.primary_account_hash = None
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            self.accounts = {}
            self.primary_account_hash = None
            
    def _select_primary_account(self) -> Optional[str]:
        """Select primary account for trading (prefer Individual over IRA)"""
        # Check environment variable first
        preferred_account = os.getenv("TRADING_ACCOUNT_NUMBER")
        if preferred_account:
            for acc_hash, acc_info in self.accounts.items():
                if acc_info['number'].endswith(preferred_account):
                    return acc_hash
        
        # Otherwise, prefer Individual/Brokerage accounts
        for acc_hash, acc_info in self.accounts.items():
            if 'Individual' in acc_info['type'] or 'Brokerage' in acc_info['type']:
                return acc_hash
                
        # Fall back to first account
        return list(self.accounts.keys())[0] if self.accounts else None
        
    def _init_account(self):
        """Initialize account information"""
        try:
            accounts = self.client.account_linked().json()
            if accounts:
                self.account_hash = accounts[0]['hashValue']
                self.account_number = accounts[0]['accountNumber']
                logger.info(f"Connected to account: {self.account_number}")
            else:
                logger.error("No accounts found")
                self.account_hash = None
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            self.account_hash = None
            
    def get_account_balance(self, account_hash: Optional[str] = None) -> float:
        """Get current account balance"""
        if not self.client:
            return float(os.getenv("CAPITAL", "5000"))
            
        try:
            hash_to_use = account_hash or self.primary_account_hash
            response = self.client.account_details(hash_to_use)
            if response.ok:
                data = response.json()
                return data['securitiesAccount']['currentBalances']['liquidationValue']
            return 0.0
        except Exception as e:
            logger.error(f"Failed to get account balance: {e}")
            return float(os.getenv("CAPITAL", "5000"))
            
    def get_all_accounts_balance(self) -> Dict[str, float]:
        """Get balance for all accounts"""
        balances = {}
        for acc_hash, acc_info in self.accounts.items():
            balance = self.get_account_balance(acc_hash)
            balances[acc_info['number']] = balance
        return balances
            
    def get_positions(self, account_hash: Optional[str] = None) -> List[Dict]:
        """Get current open positions"""
        if not self.client:
            return []
            
        try:
            hash_to_use = account_hash or self.primary_account_hash
            response = self.client.account_details(hash_to_use, fields="positions")
            if response.ok:
                data = response.json()
                positions = data.get('securitiesAccount', {}).get('positions', [])
                return [
                    {
                        "symbol": pos['instrument']['symbol'],
                        "pnl": pos.get('currentDayProfitLoss', 0),
                        "pct": pos.get('currentDayProfitLossPercentage', 0)
                    }
                    for pos in positions
                ]
            return []
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []
            
    def get_today_pnl(self, account_hash: Optional[str] = None) -> float:
        """Get today's P&L"""
        if not self.client:
            return 0.0
            
        try:
            hash_to_use = account_hash or self.primary_account_hash
            response = self.client.account_details(hash_to_use, fields="positions")
            if response.ok:
                data = response.json()
                positions = data.get('securitiesAccount', {}).get('positions', [])
                return sum(pos.get('currentDayProfitLoss', 0) for pos in positions)
            return 0.0
        except Exception as e:
            logger.error(f"Failed to get today's P&L: {e}")
            return 0.0
            
    def place_iron_condor(self, symbol: str, strikes: Dict, quantity: int = 1) -> Optional[str]:
        """Place an iron condor order"""
        try:
            # Use primary account for trading
            if not self.primary_account_hash:
                logger.error("No primary account set for trading")
                return None
                
            # Format option symbols
            exp_date = strikes['expiration']  # YYMMDD format
            
            # Pad symbol to 6 chars
            symbol_padded = symbol.ljust(6)
            
            # Create option symbols
            short_call = f"{symbol_padded}{exp_date}C{strikes['short_call']:08.3f}".replace('.', '')
            long_call = f"{symbol_padded}{exp_date}C{strikes['long_call']:08.3f}".replace('.', '')
            short_put = f"{symbol_padded}{exp_date}P{strikes['short_put']:08.3f}".replace('.', '')
            long_put = f"{symbol_padded}{exp_date}P{strikes['long_put']:08.3f}".replace('.', '')
            
            order = {
                "orderStrategyType": "SINGLE",
                "orderType": "NET_CREDIT",
                "price": strikes.get('price', 0.50),
                "orderLegCollection": [
                    {
                        "instruction": "SELL_TO_OPEN",
                        "quantity": quantity,
                        "instrument": {
                            "assetType": "OPTION",
                            "symbol": short_call
                        }
                    },
                    {
                        "instruction": "BUY_TO_OPEN",
                        "quantity": quantity,
                        "instrument": {
                            "assetType": "OPTION",
                            "symbol": long_call
                        }
                    },
                    {
                        "instruction": "SELL_TO_OPEN",
                        "quantity": quantity,
                        "instrument": {
                            "assetType": "OPTION",
                            "symbol": short_put
                        }
                    },
                    {
                        "instruction": "BUY_TO_OPEN",
                        "quantity": quantity,
                        "instrument": {
                            "assetType": "OPTION",
                            "symbol": long_put
                        }
                    }
                ],
                "complexOrderStrategyType": "IRON_CONDOR",
                "duration": "DAY",
                "session": "NORMAL"
            }
            
            response = self.client.order_place(self.primary_account_hash, order)
            
            if response.ok:
                order_id = response.headers.get('location', '/').split('/')[-1]
                logger.info(f"Iron condor placed: Order ID {order_id}")
                return order_id
            else:
                logger.error(f"Failed to place order: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to place iron condor: {e}")
            return None
            
    def place_credit_spread(self, symbol: str, strikes: Dict, quantity: int = 1) -> Optional[str]:
        """Place a credit spread order"""
        try:
            exp_date = strikes['expiration']
            symbol_padded = symbol.ljust(6)
            
            spread_type = strikes.get('type', 'PUT')  # PUT or CALL spread
            
            if spread_type == 'PUT':
                short_strike = f"{symbol_padded}{exp_date}P{strikes['short_strike']:08.3f}".replace('.', '')
                long_strike = f"{symbol_padded}{exp_date}P{strikes['long_strike']:08.3f}".replace('.', '')
            else:
                short_strike = f"{symbol_padded}{exp_date}C{strikes['short_strike']:08.3f}".replace('.', '')
                long_strike = f"{symbol_padded}{exp_date}C{strikes['long_strike']:08.3f}".replace('.', '')
            
            order = {
                "orderStrategyType": "SINGLE",
                "orderType": "NET_CREDIT",
                "price": strikes.get('price', 0.25),
                "orderLegCollection": [
                    {
                        "instruction": "SELL_TO_OPEN",
                        "quantity": quantity,
                        "instrument": {
                            "assetType": "OPTION",
                            "symbol": short_strike
                        }
                    },
                    {
                        "instruction": "BUY_TO_OPEN",
                        "quantity": quantity,
                        "instrument": {
                            "assetType": "OPTION",
                            "symbol": long_strike
                        }
                    }
                ],
                "complexOrderStrategyType": "VERTICAL",
                "duration": "DAY",
                "session": "NORMAL"
            }
            
            response = self.client.order_place(self.account_hash, order)
            
            if response.ok:
                order_id = response.headers.get('location', '/').split('/')[-1]
                logger.info(f"Credit spread placed: Order ID {order_id}")
                return order_id
            else:
                logger.error(f"Failed to place order: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to place credit spread: {e}")
            return None
            
    def close_position(self, order_id: str) -> bool:
        """Close a position by order ID"""
        try:
            # First get order details
            response = self.client.order_details(self.account_hash, order_id)
            if not response.ok:
                return False
                
            order_data = response.json()
            
            # Create closing order (reverse the legs)
            closing_order = {
                "orderStrategyType": "SINGLE",
                "orderType": "NET_DEBIT",
                "price": 0.05,  # Try to close for minimal cost
                "orderLegCollection": [],
                "duration": "DAY",
                "session": "NORMAL"
            }
            
            # Reverse each leg
            for leg in order_data['orderLegCollection']:
                new_instruction = "BUY_TO_CLOSE" if leg['instruction'].startswith("SELL") else "SELL_TO_CLOSE"
                closing_order['orderLegCollection'].append({
                    "instruction": new_instruction,
                    "quantity": leg['quantity'],
                    "instrument": leg['instrument']
                })
            
            response = self.client.order_place(self.account_hash, closing_order)
            return response.ok
            
        except Exception as e:
            logger.error(f"Failed to close position: {e}")
            return False
            
    def get_option_chain(self, symbol: str, dte: int = 0) -> Dict:
        """Get option chain for analysis"""
        try:
            # Calculate expiration date
            exp_date = datetime.now() + timedelta(days=dte)
            
            response = self.client.option_chains(
                symbol,
                contractType="ALL",
                strikeCount=20,
                includeUnderlyingQuote=True,
                fromDate=exp_date.strftime("%Y-%m-%d"),
                toDate=exp_date.strftime("%Y-%m-%d")
            )
            
            if response.ok:
                return response.json()
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get option chain: {e}")
            return {}
            
    def start_stream(self, on_message=None):
        """Start streaming market data"""
        try:
            self.streamer = self.client.stream
            
            # Subscribe to account activity
            self.streamer.send(self.streamer.account_activity("Account Activity", "0,1,2,3"))
            
            # Start the stream
            self.streamer.start(on_message or self._default_handler)
            
        except Exception as e:
            logger.error(f"Failed to start stream: {e}")
            
    def _default_handler(self, message):
        """Default stream message handler"""
        logger.info(f"Stream message: {message}")