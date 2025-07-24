import os
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# Import our modules with relative imports
from .strategy import Strategy, TradingMode
from .risk_guard import RiskGuard
from .ml_filter import MLFilter
from .schwab_client import SchwabClient

logger = logging.getLogger(__name__)

app = FastAPI(title="Robo-Pilot MAX API", version="1.0.0")

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
class BotState:
    def __init__(self):
        self.strategy = Strategy()
        self.risk_guard = RiskGuard()
        self.ml_filter = MLFilter()
        self.schwab = SchwabClient()
        self.is_paused = False
        self.account_balance = float(os.getenv("CAPITAL", "5000"))
        self.today_pnl = 0.0
        self.week_pnl = 0.0
        self.active_positions = []
        self.system_status = "green"
        self.last_update = datetime.now()
        self.trading_engine = None
        
bot_state = BotState()

# Response models
class StatsResponse(BaseModel):
    mode: str
    balance: float
    todayPnl: float
    weekPnl: float
    positions: List[Dict]
    systemStatus: str
    isPaused: bool
    riskUsed: float
    lastUpdate: str

class StatusResponse(BaseModel):
    success: bool
    message: str
    state: Optional[Dict] = None

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Robo-Pilot MAX API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mode": bot_state.strategy.mode.value,
        "is_paused": bot_state.is_paused
    }

@app.get("/api/debug")
async def debug_info():
    """Debug endpoint to see actual values"""
    return {
        "initial_capital": float(os.getenv("CAPITAL", "5000")),
        "account_balance": bot_state.account_balance,
        "today_pnl": bot_state.today_pnl,
        "week_pnl": bot_state.week_pnl,
        "calculated_balance": bot_state.account_balance + bot_state.today_pnl,
        "schwab_connected": bot_state.schwab.client is not None,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "enable_trading": os.getenv("ENABLE_TRADING", "false"),
        "positions_count": len(bot_state.active_positions),
        "trading_active": bot_state.trading_engine is not None and bot_state.trading_engine.is_running
    }

@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get current bot statistics for dashboard"""
    # Get real data from Schwab API
    try:
        # Update with real account data
        bot_state.account_balance = bot_state.schwab.get_account_balance()
        bot_state.today_pnl = bot_state.schwab.get_today_pnl()
        bot_state.active_positions = bot_state.schwab.get_positions()
    except Exception as e:
        logger.error(f"Failed to fetch real data: {e}")
        # Fall back to demo data if API fails
    
    # Calculate risk used percentage
    daily_limit = float(os.getenv("RISK_DAILY", "0.06"))
    risk_used = abs(bot_state.today_pnl / bot_state.account_balance) / daily_limit * 100 if bot_state.account_balance > 0 else 0
    
    # Determine system status based on risk
    if bot_state.is_paused:
        system_status = "red"
    elif risk_used > 80:
        system_status = "yellow"
    else:
        system_status = "green"
    
    # Only use mock data if no real positions exist (remove this section when fully connected)
    if not bot_state.active_positions and os.getenv("ENVIRONMENT") == "development":
        bot_state.active_positions = [
            {"symbol": "SPY Iron Condor", "pnl": 23, "pct": 18},
            {"symbol": "QQQ Credit Spread", "pnl": 12, "pct": 8}
        ]
    
    return StatsResponse(
        mode=bot_state.strategy.mode.value,
        balance=bot_state.account_balance + bot_state.today_pnl,
        todayPnl=bot_state.today_pnl,
        weekPnl=bot_state.week_pnl,
        positions=bot_state.active_positions,
        systemStatus=system_status,
        isPaused=bot_state.is_paused,
        riskUsed=round(risk_used, 1),
        lastUpdate=bot_state.last_update.isoformat()
    )

@app.post("/api/toggle_mode", response_model=StatusResponse)
async def toggle_mode(mode: str):
    """Switch between income and turbo modes"""
    try:
        if mode not in ["income", "turbo"]:
            raise ValueError("Mode must be 'income' or 'turbo'")
        
        bot_state.strategy.mode = TradingMode(mode)
        os.environ["MODE"] = mode
        
        logger.info(f"Switched to {mode} mode")
        
        return StatusResponse(
            success=True,
            message=f"Switched to {mode} mode",
            state={"mode": mode}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/pause", response_model=StatusResponse)
async def pause_trading():
    """Pause trading operations"""
    bot_state.is_paused = True
    logger.warning("Trading PAUSED by user")
    
    return StatusResponse(
        success=True,
        message="Trading paused",
        state={"is_paused": True}
    )

@app.post("/api/resume", response_model=StatusResponse)
async def resume_trading():
    """Resume trading operations"""
    bot_state.is_paused = False
    logger.info("Trading RESUMED by user")
    
    return StatusResponse(
        success=True,
        message="Trading resumed",
        state={"is_paused": False}
    )

@app.post("/api/exit_all", response_model=StatusResponse)
async def emergency_exit():
    """Emergency exit all positions"""
    try:
        # Pause trading first
        bot_state.is_paused = True
        
        # Call strategy emergency exit
        bot_state.strategy.emergency_exit_all()
        
        # Clear positions
        positions_closed = len(bot_state.active_positions)
        bot_state.active_positions = []
        
        logger.critical(f"EMERGENCY EXIT: Closed {positions_closed} positions")
        
        return StatusResponse(
            success=True,
            message=f"Emergency exit completed. Closed {positions_closed} positions",
            state={
                "is_paused": True,
                "positions_closed": positions_closed
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/update_risk")
async def update_risk_settings(daily_limit: float, per_trade_limit: float):
    """Update risk management settings"""
    try:
        os.environ["RISK_DAILY"] = str(daily_limit)
        os.environ["RISK_PER_TRADE"] = str(per_trade_limit)
        
        # Reinitialize risk guard with new settings
        bot_state.risk_guard = RiskGuard()
        
        return StatusResponse(
            success=True,
            message="Risk settings updated",
            state={
                "daily_limit": daily_limit,
                "per_trade_limit": per_trade_limit
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/start_trading", response_model=StatusResponse)
async def start_trading():
    """Manually start the trading engine"""
    try:
        if bot_state.trading_engine and bot_state.trading_engine.is_running:
            return StatusResponse(
                success=False,
                message="Trading engine is already running"
            )
        
        # Import and start trading engine
        from .trading_engine import TradingEngine
        bot_state.trading_engine = TradingEngine()
        asyncio.create_task(bot_state.trading_engine.start())
        
        return StatusResponse(
            success=True,
            message="Trading engine started",
            state={"trading_active": True}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stop_trading", response_model=StatusResponse)
async def stop_trading():
    """Stop the trading engine"""
    try:
        if bot_state.trading_engine:
            bot_state.trading_engine.stop()
            bot_state.trading_engine = None
        
        return StatusResponse(
            success=True,
            message="Trading engine stopped",
            state={"trading_active": False}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Background task to update real P&L data
async def update_real_pnl():
    """Update P&L from Schwab API"""
    while True:
        if not bot_state.is_paused:
            try:
                # Fetch real data from Schwab
                bot_state.account_balance = bot_state.schwab.get_account_balance()
                bot_state.today_pnl = bot_state.schwab.get_today_pnl()
                bot_state.active_positions = bot_state.schwab.get_positions()
                
                # TODO: Calculate week P&L from historical data
                # bot_state.week_pnl = bot_state.schwab.get_week_pnl()
                
            except Exception as e:
                logger.error(f"Failed to update P&L: {e}")
                
                # In development mode, simulate some P&L changes
                if os.getenv("ENVIRONMENT") == "development" and not bot_state.schwab.client:
                    import random
                    bot_state.today_pnl += random.uniform(-50, 100)
                    bot_state.week_pnl += random.uniform(-100, 200)
                
        bot_state.last_update = datetime.now()
        await asyncio.sleep(30)  # Update every 30 seconds

@app.on_event("startup")
async def startup_event():
    """Initialize bot on startup"""
    logger.info(f"Starting Robo-Pilot MAX API in {bot_state.strategy.mode.value} mode")
    
    # Start real P&L updates
    asyncio.create_task(update_real_pnl())
    
    # Start trading engine if enabled
    if os.getenv("ENABLE_TRADING", "false").lower() == "true":
        logger.warning("AUTOMATIC TRADING ENABLED - Starting trading engine")
        from .trading_engine import TradingEngine
        bot_state.trading_engine = TradingEngine()
        asyncio.create_task(bot_state.trading_engine.start())
    else:
        logger.info("Automatic trading is DISABLED (set ENABLE_TRADING=true to enable)")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Robo-Pilot MAX API")
    
    # Stop trading engine if running
    if bot_state.trading_engine:
        bot_state.trading_engine.stop()
    
    if bot_state.active_positions:
        logger.warning(f"Warning: {len(bot_state.active_positions)} positions still open")

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    uvicorn.run(app, host=host, port=port)