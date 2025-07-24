import os
import logging
from datetime import datetime
from functools import wraps
from typing import Dict, Callable

logger = logging.getLogger(__name__)

class RiskGuard:
    """Risk management system with mode-specific limits"""
    
    def __init__(self):
        self.daily_limit = float(os.getenv("RISK_DAILY", "0.06"))
        self.per_trade_limit = float(os.getenv("RISK_PER_TRADE", "0.01"))
        self.weekly_limit = float(os.getenv("RISK_WEEKLY", "0.05"))
        
        self.daily_loss = 0.0
        self.weekly_loss = 0.0
        self.trades_today = 0
        self.last_reset = datetime.now()
        
    def check_limits(self, account_balance: float, trade_risk: float) -> Dict[str, bool]:
        """Check if trade passes all risk limits"""
        checks = {
            "per_trade_ok": (trade_risk / account_balance) <= self.per_trade_limit,
            "daily_ok": (self.daily_loss + trade_risk) / account_balance <= self.daily_limit,
            "weekly_ok": (self.weekly_loss + trade_risk) / account_balance <= self.weekly_limit,
            "all_ok": True
        }
        
        checks["all_ok"] = all([checks["per_trade_ok"], checks["daily_ok"], checks["weekly_ok"]])
        
        if not checks["all_ok"]:
            logger.warning(f"Risk limits breached: {checks}")
            
        return checks
    
    def update_losses(self, pnl: float):
        """Update daily and weekly loss trackers"""
        if pnl < 0:
            self.daily_loss += abs(pnl)
            self.weekly_loss += abs(pnl)
            
    def reset_daily(self):
        """Reset daily counters"""
        self.daily_loss = 0.0
        self.trades_today = 0
        logger.info("Daily risk counters reset")
        
    def reset_weekly(self):
        """Reset weekly counters"""
        self.weekly_loss = 0.0
        logger.info("Weekly risk counters reset")

def risk_fence(func: Callable) -> Callable:
    """Decorator to check risk limits before placing trades"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Extract trade risk from arguments
        market_data = args[0] if args else kwargs.get("market_data", {})
        position_size = self.calculate_position_size()
        
        # Check risk limits (assuming self has access to capital and risk_guard)
        if hasattr(self, 'risk_guard') and hasattr(self, 'capital'):
            risk_checks = self.risk_guard.check_limits(self.capital, position_size)
            
            if not risk_checks["all_ok"]:
                logger.error(f"Trade blocked by risk fence: {risk_checks}")
                return None
            
        return func(self, *args, **kwargs)
    
    return wrapper