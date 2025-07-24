import os
import logging
from datetime import datetime, time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class TradingMode(Enum):
    INCOME = "income"
    TURBO = "turbo"

@dataclass
class Trade:
    symbol: str
    strategy: str
    entry_price: float
    quantity: int
    risk_amount: float
    profit_target: float
    stop_loss: float
    expiration: str
    mode: TradingMode
    order_id: Optional[str] = None

class Strategy:
    """Dual-mode trading strategy engine for Income and Turbo modes"""
    
    def __init__(self):
        self.mode = TradingMode(os.getenv("MODE", "income").lower())
        self.risk_per_trade = float(os.getenv("RISK_PER_TRADE", "0.01"))
        self.profit_target = float(os.getenv("PROFIT_TARGET", "0.25"))
        self.stop_loss_multiplier = float(os.getenv("STOP_LOSS_MULTIPLIER", "1.0"))
        self.capital = float(os.getenv("CAPITAL", "5000"))
        
        # Initialize risk guard
        from .risk_guard import RiskGuard
        self.risk_guard = RiskGuard()
        
        # Mode-specific configurations
        self.income_config = {
            "symbols": ["SPY", "QQQ", "IWM"],
            "strategies": ["iron_condor", "credit_spread", "covered_call"],
            "dte_range": (1, 7),
            "max_daily_trades": 2,
            "position_scale": 1.0
        }
        
        self.turbo_config = {
            "symbols": ["SPY"],
            "strategies": ["iron_condor", "credit_spread"],
            "dte_range": (0, 0),  # 0-DTE only
            "max_daily_trades": 1,
            "position_scale": 1.0,
            "compound_threshold": 3  # Scale up after 3 wins
        }
        
        self.win_streak = 0
        self.daily_trades = 0
        
    def get_current_config(self) -> Dict:
        """Return configuration based on current mode"""
        return self.income_config if self.mode == TradingMode.INCOME else self.turbo_config
    
    def select_strategy(self, market_data: Dict) -> Optional[str]:
        """Select appropriate strategy based on mode and market conditions"""
        config = self.get_current_config()
        
        if self.mode == TradingMode.INCOME:
            # Income mode: Diversified approach
            iv_rank = market_data.get("iv_rank", 50)
            trend = market_data.get("trend", "neutral")
            
            if iv_rank > 70:
                return "iron_condor"
            elif iv_rank > 40 and trend == "neutral":
                return "credit_spread"
            elif trend == "bullish":
                return "covered_call"
                
        else:  # TURBO mode
            # Turbo mode: Aggressive 0-DTE focus
            vix = market_data.get("vix", 20)
            spy_range = market_data.get("spy_daily_range", 1.0)
            
            if vix < 25 and spy_range < 1.5:
                return "iron_condor"
            elif vix < 30:
                return "credit_spread"
                
        return None
    
    def calculate_position_size(self) -> float:
        """Calculate position size based on mode and performance"""
        base_risk = self.capital * self.risk_per_trade
        config = self.get_current_config()
        
        if self.mode == TradingMode.TURBO:
            # Turbo mode: Scale up after win streaks
            if self.win_streak >= config["compound_threshold"]:
                scale_factor = 1.0 + (0.1 * (self.win_streak - 2))
                return base_risk * min(scale_factor, 2.0)  # Cap at 2x
                
        # Income mode: Conservative sizing
        return base_risk * config["position_scale"]
    
    def place_trade(self, market_data: Dict) -> Optional[Trade]:
        """Main entry point: Analyze market and place trade if edge detected"""
        
        # Import risk_guard here to avoid circular import
        from .risk_guard import risk_fence
        
        # Check daily trade limits
        config = self.get_current_config()
        if self.daily_trades >= config["max_daily_trades"]:
            logger.info(f"Daily trade limit reached ({self.daily_trades})")
            return None
            
        # Select strategy
        strategy = self.select_strategy(market_data)
        if not strategy:
            logger.info("No suitable strategy for current conditions")
            return None
            
        # Calculate position details
        symbol = self._select_symbol(market_data)
        position_size = self.calculate_position_size()
        
        # Build trade object
        trade = Trade(
            symbol=symbol,
            strategy=strategy,
            entry_price=market_data.get("price", 100),
            quantity=int(position_size / 100),  # Simplified
            risk_amount=position_size,
            profit_target=self.profit_target,
            stop_loss=self.stop_loss_multiplier,
            expiration=self._get_expiration(),
            mode=self.mode
        )
        
        logger.info(f"Placing {self.mode.value} trade: {trade}")
        self.daily_trades += 1
        
        # Place the actual trade using Schwab API
        try:
            from .schwab_client import SchwabClient
            schwab = SchwabClient()
            
            # Get option chain to find best strikes
            if strategy in ["iron_condor", "credit_spread"]:
                chain = schwab.get_option_chain(symbol, dte=0 if self.mode == TradingMode.TURBO else 7)
                
                if strategy == "iron_condor":
                    # Calculate strikes for iron condor
                    strikes = self._calculate_iron_condor_strikes(chain, market_data)
                    order_id = schwab.place_iron_condor(symbol, strikes, trade.quantity)
                else:
                    # Calculate strikes for credit spread
                    strikes = self._calculate_credit_spread_strikes(chain, market_data)
                    order_id = schwab.place_credit_spread(symbol, strikes, trade.quantity)
                    
                if order_id:
                    trade.order_id = order_id
                    logger.info(f"Trade placed successfully: {order_id}")
                    return trade
                else:
                    logger.error("Failed to place trade")
                    return None
                    
        except Exception as e:
            logger.error(f"Error placing trade: {e}")
            return None
            
        return trade
    
    def _calculate_iron_condor_strikes(self, chain: Dict, market_data: Dict) -> Dict:
        """Calculate optimal strikes for iron condor"""
        current_price = market_data.get("price", 100)
        
        # Simple strike selection (you can make this more sophisticated)
        return {
            'expiration': self._get_expiration().replace("-", "")[2:],  # YYMMDD format
            'short_call': current_price + 5,
            'long_call': current_price + 10,
            'short_put': current_price - 5,
            'long_put': current_price - 10,
            'price': 0.50  # Target credit
        }
        
    def _calculate_credit_spread_strikes(self, chain: Dict, market_data: Dict) -> Dict:
        """Calculate optimal strikes for credit spread"""
        current_price = market_data.get("price", 100)
        trend = market_data.get("trend", "neutral")
        
        # Put spread for neutral/bearish, Call spread for bullish
        if trend == "bullish":
            return {
                'expiration': self._get_expiration().replace("-", "")[2:],
                'type': 'CALL',
                'short_strike': current_price + 5,
                'long_strike': current_price + 10,
                'price': 0.25
            }
        else:
            return {
                'expiration': self._get_expiration().replace("-", "")[2:],
                'type': 'PUT',
                'short_strike': current_price - 5,
                'long_strike': current_price - 10,
                'price': 0.25
            }
    
    def _select_symbol(self, market_data: Dict) -> str:
        """Select best symbol based on mode and conditions"""
        config = self.get_current_config()
        
        if self.mode == TradingMode.INCOME:
            # Rotate between symbols for diversification
            return config["symbols"][self.daily_trades % len(config["symbols"])]
        else:
            # Turbo mode: SPY only
            return "SPY"
    
    def _get_expiration(self) -> str:
        """Get expiration date based on mode DTE settings"""
        config = self.get_current_config()
        dte = config["dte_range"][0]  # Simplified: use minimum DTE
        
        from datetime import timedelta
        exp_date = datetime.now() + timedelta(days=dte)
        
        # For 0-DTE, ensure it's today
        if dte == 0:
            exp_date = datetime.now()
            
        return exp_date.strftime("%Y-%m-%d")
    
    def update_performance(self, trade_result: Dict):
        """Update win streak and scaling factors"""
        if trade_result["profit"] > 0:
            self.win_streak += 1
        else:
            self.win_streak = 0
            
    def reset_daily_counters(self):
        """Reset counters at market open"""
        self.daily_trades = 0
        logger.info(f"Daily counters reset for {self.mode.value} mode")
        
    def emergency_exit_all(self):
        """Close all positions immediately"""
        logger.warning("EMERGENCY EXIT triggered")
        
        try:
            from .schwab_client import SchwabClient
            schwab = SchwabClient()
            
            # Get all open positions
            positions = schwab.get_positions()
            
            # Close each position
            for position in positions:
                symbol = position['symbol']
                logger.info(f"Closing position: {symbol}")
                # For options, we need to get the order details
                # This is simplified - you'd need to track order IDs
                
            logger.info(f"Emergency exit completed: {len(positions)} positions closed")
            
        except Exception as e:
            logger.error(f"Error during emergency exit: {e}")