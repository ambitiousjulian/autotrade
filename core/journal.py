import os
import logging
from datetime import datetime
from typing import Dict, Optional, List
import pandas as pd

logger = logging.getLogger(__name__)

class TradeJournal:
    """
    Lightweight trade journal for recording every trade, result, and annotation.
    """
    def __init__(self, path: str = "./journal.csv"):
        self.path = path
        if not os.path.exists(self.path):
            # Write headers if journal doesn't exist yet
            pd.DataFrame(columns=["timestamp", "symbol", "strategy", "qty", "entry_price",
                                  "exit_price", "pnl", "rationale", "notes"]).to_csv(self.path, index=False)

    def log_trade(self, symbol: str, strategy: str, qty: int, entry_price: float, exit_price: Optional[float], pnl: float,
                  rationale: Optional[str] = "", notes: Optional[str] = ""):
        """Add a new trade entry to the journal."""
        row = {
            "timestamp": datetime.now().isoformat(timespec='seconds'),
            "symbol": symbol,
            "strategy": strategy,
            "qty": qty,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl": pnl,
            "rationale": rationale,
            "notes": notes
        }
        df = pd.DataFrame([row])
        df.to_csv(self.path, mode="a", header=False, index=False)
        logger.info(f"Journaled trade: {row}")

    def get_trades(self) -> List[Dict]:
        """Return all trades as a list of dicts."""
        return pd.read_csv(self.path).to_dict(orient="records")

    def add_note(self, trade_idx: int, note: str):
        """Append a note to an existing trade entry by index (row)."""
        df = pd.read_csv(self.path)
        if 0 <= trade_idx < len(df):
            df.at[trade_idx, "notes"] = str(df.at[trade_idx, "notes"]) + " | " + note
            df.to_csv(self.path, index=False)
            logger.info(f"Added note to trade {trade_idx}")
