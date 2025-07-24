import os
import sys
import time
import logging
import subprocess
import requests
from datetime import datetime
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Watcher:
    """Health monitoring and auto-restart system"""
    
    def __init__(self):
        self.health_url = "http://localhost:8000/health"
        self.check_interval = 30  # seconds
        self.failure_threshold = 3
        self.consecutive_failures = 0
        self.is_backup = os.getenv("BACKUP_MODE", "false").lower() == "true"
        self.backup_delay = int(os.getenv("BACKUP_DELAY", "300"))
        
    def check_health(self) -> bool:
        """Check if the main service is healthy"""
        try:
            response = requests.get(self.health_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"Health check passed: {data}")
                return True
            else:
                logger.warning(f"Health check failed with status: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Health check error: {e}")
            return False
            
    def start_main_service(self):
        """Start the main FastAPI service"""
        logger.info("Starting main trading service...")
        
        # If we're in backup mode, wait before starting
        if self.is_backup:
            logger.info(f"Backup mode: waiting {self.backup_delay}s before starting...")
            time.sleep(self.backup_delay)
            
            # Check if primary is now healthy
            if self.check_health():
                logger.info("Primary service is healthy, backup standing by")
                return None
                
        # Start the FastAPI service
        cmd = [
            "uvicorn",
            "core.core_api:app",
            "--host", "0.0.0.0",
            "--port", "8000"
        ]
        
        # Add environment-specific flags
        if os.getenv("ENVIRONMENT") == "development":
            cmd.append("--reload")
        else:
            cmd.extend(["--workers", "1"])
        
        process = subprocess.Popen(cmd)
        logger.info(f"Service started with PID: {process.pid}")
        
        # Start the trading engine in a separate thread
        if os.getenv("ENABLE_TRADING", "true").lower() == "true":
            self._start_trading_engine()
            
        return process
        
    def _start_trading_engine(self):
        """Start the trading engine in a separate thread"""
        try:
            import threading
            import asyncio
            from .trading_engine import TradingEngine
            
            def run_trading_engine():
                engine = TradingEngine()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(engine.start())
                
            thread = threading.Thread(target=run_trading_engine, daemon=True)
            thread.start()
            logger.info("Trading engine started in background")
            
        except Exception as e:
            logger.error(f"Failed to start trading engine: {e}")
        
    def monitor_loop(self):
        """Main monitoring loop"""
        process = None
        
        try:
            # Initial startup
            process = self.start_main_service()
            
            if process is None and self.is_backup:
                # Backup mode - just monitor primary
                while True:
                    time.sleep(self.check_interval)
                    if not self.check_health():
                        logger.warning("Primary unhealthy, backup taking over")
                        process = self.start_main_service()
                        break
                        
            # Main monitoring loop
            while True:
                time.sleep(self.check_interval)
                
                # Check process health
                if process and process.poll() is not None:
                    logger.error(f"Process died with exit code: {process.returncode}")
                    process = self.start_main_service()
                    self.consecutive_failures = 0
                    continue
                    
                # Check HTTP health
                if not self.check_health():
                    self.consecutive_failures += 1
                    logger.warning(f"Health check failed ({self.consecutive_failures}/{self.failure_threshold})")
                    
                    if self.consecutive_failures >= self.failure_threshold:
                        logger.error("Health check threshold exceeded, restarting service...")
                        if process:
                            process.terminate()
                            process.wait(timeout=10)
                        process = self.start_main_service()
                        self.consecutive_failures = 0
                else:
                    if self.consecutive_failures > 0:
                        logger.info("Service recovered")
                    self.consecutive_failures = 0
                    
        except KeyboardInterrupt:
            logger.info("Shutdown requested")
        except Exception as e:
            logger.critical(f"Watcher error: {e}")
        finally:
            if process:
                logger.info("Terminating service...")
                process.terminate()
                process.wait(timeout=10)
                
    def run(self):
        """Entry point for the watcher"""
        logger.info(f"Starting Robo-Pilot MAX Watcher (Backup: {self.is_backup})")
        logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'production')}")
        logger.info(f"Mode: {os.getenv('MODE', 'income')}")
        
        self.monitor_loop()

if __name__ == "__main__":
    watcher = Watcher()
    watcher.run()