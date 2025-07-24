import os
import logging
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd

logger = logging.getLogger(__name__)

class ReportGenerator:
    """
    Generates trading and risk reports for Robo-Pilot MAX.
    """
    def __init__(self, report_dir: str = "./reports"):
        self.report_dir = report_dir
        os.makedirs(self.report_dir, exist_ok=True)

    def save_daily_report(self, trades: List[Dict], pnl: float, date: Optional[datetime] = None) -> str:
        """Generate and save a daily trade report as CSV."""
        if date is None:
            date = datetime.now()
        report_file = os.path.join(self.report_dir, f"daily_{date.strftime('%Y-%m-%d')}.csv")
        df = pd.DataFrame(trades)
        df["pnl"] = pnl
        df["date"] = date.strftime('%Y-%m-%d')
        df.to_csv(report_file, index=False)
        logger.info(f"Saved daily report: {report_file}")
        return report_file

    def save_weekly_report(self, all_trades: List[Dict], total_pnl: float, week: Optional[str] = None) -> str:
        """Generate and save a weekly performance report as CSV."""
        if week is None:
            week = datetime.now().strftime("%Y-W%U")
        report_file = os.path.join(self.report_dir, f"weekly_{week}.csv")
        df = pd.DataFrame(all_trades)
        df["week"] = week
        df["total_pnl"] = total_pnl
        df.to_csv(report_file, index=False)
        logger.info(f"Saved weekly report: {report_file}")
        return report_file

    def summary_stats(self, trades: List[Dict]) -> Dict:
        """Return a quick dict of win rate, average pnl, and gross stats."""
        df = pd.DataFrame(trades)
        wins = df[df['pnl'] > 0].shape[0]
        losses = df[df['pnl'] <= 0].shape[0]
        total = max(wins + losses, 1)
        return {
            "win_rate": wins / total if total else 0,
            "avg_pnl": df['pnl'].mean() if not df.empty else 0,
            "total_trades": total,
            "gross_pnl": df['pnl'].sum() if not df.empty else 0,
        }
