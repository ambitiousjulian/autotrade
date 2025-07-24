#!/usr/bin/env python3
"""
Test Schwab API connection and basic functionality
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from schwab_client import SchwabClient
import logging

logging.basicConfig(level=logging.INFO)

def test_schwab_connection():
    """Test basic Schwab API functionality"""
    
    print("=== Testing Schwab API Connection ===\n")
    
    try:
        # Initialize client
        print("1. Initializing Schwab client...")
        schwab = SchwabClient()
        print("✓ Client initialized\n")
        
        # Test account access
        print("2. Getting account information...")
        balance = schwab.get_account_balance()
        print(f"✓ Account balance: ${balance:,.2f}\n")
        
        # Test positions
        print("3. Getting positions...")
        positions = schwab.get_positions()
        print(f"✓ Found {len(positions)} positions")
        for pos in positions[:5]:  # Show first 5
            print(f"   - {pos['symbol']}: ${pos['pnl']:,.2f} ({pos['pct']:.1f}%)")
        print()
        
        # Test quote
        print("4. Getting SPY quote...")
        quote = schwab.client.quote("SPY").json()
        spy_price = quote.get("SPY", {}).get("quote", {}).get("lastPrice", 0)
        print(f"✓ SPY price: ${spy_price:.2f}\n")
        
        # Test option chain
        print("5. Getting SPY option chain...")
        chain = schwab.get_option_chain("SPY", dte=0)
        if chain:
            print("✓ Option chain retrieved")
            call_count = len(chain.get("callExpDateMap", {}))
            put_count = len(chain.get("putExpDateMap", {}))
            print(f"   - Found {call_count} call expirations")
            print(f"   - Found {put_count} put expirations")
        print()
        
        # Test streaming
        print("6. Testing streaming connection...")
        def test_handler(msg):
            print(f"   Stream message received: {str(msg)[:100]}...")
            
        schwab.start_stream(test_handler)
        print("✓ Stream started (press Ctrl+C to stop)\n")
        
        print("=== All tests passed! ===")
        print("\nYour Schwab API connection is working correctly.")
        print("You can now run the trading bot with real data.")
        
        # Keep stream running for a few seconds
        import time
        time.sleep(5)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check your .env file has correct CLIENT_ID and CLIENT_SECRET")
        print("2. Make sure schwab_tokens.json exists (run auth first)")
        print("3. Ensure your app has both APIs enabled")
        print("4. Check that TOS is enabled on your account")
        
if __name__ == "__main__":
    test_schwab_connection()