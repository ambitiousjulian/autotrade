import os
import asyncio
import logging
from datetime import datetime, time
import pytz
from typing import Dict

from .strategy import Strategy
from .schwab_client import SchwabClient
from .ml_filter import MLFilter
from .risk_guard import RiskGuard

logger = logging.getLogger(__name__)

class TradingEngine:
    """Main trading engine that coordinates all components"""
    
    def __init__(self):
        self.strategy = Strategy()
        self.schwab = SchwabClient()
        self.ml_filter = MLFilter()
        self.risk_guard = RiskGuard()
        self.is_running = False
        self.market_timezone = pytz.timezone('US/Eastern')
        
    async def start(self):
        """Start the trading engine"""
        self.is_running = True
        logger.info("Trading engine started")
        
        # Start streaming data
        self.schwab.start_stream(self._handle_stream_message)
        
        # Main trading loop
        while self.is_running:
            try:
                if self._is_market_open():
                    await self._trading_cycle()
                    
                # Sleep for 1 minute between cycles
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Trading cycle error: {e}")
                await asyncio.sleep(60)
                
    async def _trading_cycle(self):
        """Execute one trading cycle"""
        try:
            # Get market data
            market_data = await self._get_market_data()
            
            # Check if ML filter approves
            if not self.ml_filter.is_edge_today(market_data):
                logger.info("No edge detected by ML filter")
                return
                
            # Check risk limits
            account_balance = self.schwab.get_account_balance()
            position_size = self.strategy.calculate_position_size()
            
            risk_checks = self.risk_guard.check_limits(account_balance, position_size)
            if not risk_checks["all_ok"]:
                logger.warning(f"Risk limits breached: {risk_checks}")
                return
                
            # Place trade
            trade = self.strategy.place_trade(market_data)
            if trade and trade.order_id:
                logger.info(f"Trade placed successfully: {trade.order_id}")
                
                # Update risk tracking
                self.risk_guard.trades_today += 1
                
        except Exception as e:
            logger.error(f"Trading cycle error: {e}")
            
    async def _get_market_data(self) -> Dict:
        """Get current market data"""
        try:
            # Get SPY quote
            spy_quote = self.schwab.client.quote("SPY").json()
            
            # Get market internals
            vix_quote = self.schwab.client.quote("$VIX.X").json()
            
            # Calculate additional metrics
            spy_price = spy_quote.get("SPY", {}).get("quote", {}).get("lastPrice", 0)
            vix = vix_quote.get("$VIX.X", {}).get("quote", {}).get("lastPrice", 20)
            
            # Get IV rank (simplified)
            option_chain = self.schwab.get_option_chain("SPY", dte=30)
            iv_rank = self._calculate_iv_rank(option_chain)
            
            return {
                "price": spy_price,
                "vix": vix,
                "iv_rank": iv_rank,
                "spy_daily_range": self._calculate_daily_range(spy_quote),
                "trend": self._determine_trend(spy_quote),
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Failed to get market data: {e}")
            return {}
            
    def _calculate_iv_rank(self, chain: Dict) -> float:
        """Calculate IV rank from option chain"""
        # Simplified IV rank calculation
        # In production, you'd compare current IV to historical
        try:
            if chain and "volatility" in chain:
                return chain["volatility"] * 100
            return 50.0  # Default middle value
        except:
            return 50.0
            
    def _calculate_daily_range(self, quote: Dict) -> float:
        """Calculate daily range as percentage"""
        try:
            data = quote.get("SPY", {}).get("quote", {})
            high = data.get("highPrice", 0)
            low = data.get("lowPrice", 0)
            close = data.get("closePrice", 1)
            
            if close > 0:
                return ((high - low) / close) * 100
            return 0.0
        except:
            return 0.0
            
    def _determine_trend(self, quote: Dict) -> str:
        """Determine market trend"""
        try:
            data = quote.get("SPY", {}).get("quote", {})
            last = data.get("lastPrice", 0)
            close = data.get("closePrice", 0)
            
            if last > close * 1.005:
                return "bullish"
            elif last < close * 0.995:
                return "bearish"
            else:
                return "neutral"
        except:
            return "neutral"
            
    def _handle_stream_message(self, message):
        """Handle streaming messages"""
        try:
            # Parse message
            if isinstance(message, str):
                import json
                data = json.loads(message)
            else:
                data = message
                
            # Handle account activity
            if "data" in data and data.get("service") == "ACCT_ACTIVITY":
                for item in data["data"]:
                    msg_type = item.get("2")  # Message type field
                    
                    if msg_type == "OrderFillCompleted":
                        logger.info(f"Order filled: {item}")
                        # Update strategy win/loss tracking
                        if item.get("profit", 0) > 0:
                            self.strategy.update_performance({"profit": item["profit"]})
                            
        except Exception as e:
            logger.error(f"Stream message error: {e}")
            
    def _is_market_open(self) -> bool:
        """Check if market is open"""
        now = datetime.now(self.market_timezone)
        
        # Check if weekday (0-4 = Mon-Fri)
        if now.weekday() > 4:
            return False
            
        # Check time (9:30 AM - 4:00 PM ET)
        market_open = time(9, 30)
        market_close = time(16, 0)
        
        return market_open <= now.time() <= market_close
        
    def stop(self):
        """Stop the trading engine"""
        self.is_running = False
        if hasattr(self, 'schwab') and hasattr(self.schwab, 'streamer'):
            self.schwab.streamer.stop()
        logger.info("Trading engine stopped")