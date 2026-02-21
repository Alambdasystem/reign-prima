#!/usr/bin/env python
"""
REIGN Dashboard Launcher

Quick launcher for the REIGN desktop monitoring dashboard.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from reign.dashboard import ReignDashboard

if __name__ == "__main__":
    print("Starting REIGN Dashboard...")
    print("=" * 50)
    try:
        print("Creating dashboard instance...")
        dashboard = ReignDashboard()
        print("Dashboard created, calling run()...")
        dashboard.run()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
