#!/usr/bin/env python3
"""
=============================================================================
Sri Sai Institute of Technology and Science (Autonomous)
Render 24/7 Keep-Alive Background Service
=============================================================================
Pings the Render web service every 10 minutes to prevent the free tier
instance from sleeping (hibernating). Eliminates the 10-30s cold start delay.
=============================================================================
"""

import time
import sys
from datetime import datetime
try:
    import urllib.request
except ImportError:
    pass

RENDER_URL = "https://ssits-edupulse.onrender.com/healthz"
PING_INTERVAL_SECONDS = 600  # 10 minutes (Render sleeps after 15 mins)

def ping():
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        req = urllib.request.Request(
            RENDER_URL, 
            headers={'User-Agent': 'SSITS-KeepAlive-Daemon/1.0'}
        )
        with urllib.request.urlopen(req, timeout=25) as response:
            status = response.getcode()
            print(f"[{now_str}] Ping successful -> HTTP {status} (Server is warm & active!)")
    except Exception as e:
        print(f"[{now_str}] Ping dispatched (Server waking up): {e}")

def main():
    print("=" * 65)
    print("  SSITS RENDER 24/7 KEEP-ALIVE DAEMON")
    print(f"  Target: {RENDER_URL}")
    print(f"  Interval: Every {PING_INTERVAL_SECONDS // 60} minutes")
    print("  Press Ctrl+C to terminate.")
    print("=" * 65)

    # Initial ping
    ping()

    while True:
        try:
            time.sleep(PING_INTERVAL_SECONDS)
            ping()
        except KeyboardInterrupt:
            print("\nKeep-alive service stopped by user.")
            sys.exit(0)

if __name__ == "__main__":
    main()
