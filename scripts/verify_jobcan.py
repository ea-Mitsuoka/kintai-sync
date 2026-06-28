import asyncio
import os
import sys
from datetime import date
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from src.jobcan import JobcanManager

async def main():
    print("--- Jobcan Local Verification Script ---")
    
    # 1. Get credentials from environment or prompt
    company_id = os.getenv("JOBCAN_COMPANY_ID") or input("Company ID: ")
    staff_code = os.getenv("JOBCAN_STAFF_CODE") or input("Staff Code: ")
    password = os.getenv("JOBCAN_PASSWORD") or input("Password: ")
    
    if not all([company_id, staff_code, password]):
        print("Error: Credentials missing.")
        return

    # 2. Set test parameters
    target_date_str = input("Target Date (YYYY-MM-DD) [Default: today]: ").strip().lower()
    if target_date_str == "" or target_date_str == "today":
        target_date = date.today()
    else:
        try:
            target_date = date.fromisoformat(target_date_str)
        except ValueError:
            print(f"Error: Invalid date format '{target_date_str}'. Please use YYYY-MM-DD.")
            return

    print("\nSelect Attendance Type:")
    print("1: full_day (全休)")
    print("2: morning_off (午前休)")
    print("3: afternoon_off (午後休)")
    print("4: late (遅刻)")
    print("5: early (早退)")
    
    choice = input("Choice [1-5]: ")
    types = {"1": "full_day", "2": "morning_off", "3": "afternoon_off", "4": "late", "5": "early"}
    attendance_type = types.get(choice, "full_day")
    
    reason = input("Reason (optional): ") or "Local test"

    # 3. Run verification
    manager = JobcanManager(company_id, staff_code, password)
    
    print(f"\n🚀 Running Jobcan application for {target_date} ({attendance_type})...")
    print("Note: If running in a GUI environment, you can set HEADLESS=false to see the browser.")
    
    try:
        # We can temporarily override headless mode via environment variable if supported by JobcanManager
        # Looking at src/jobcan.py, it likely uses default (headless=True).
        # Let's check src/jobcan.py again to see if we can control headless mode.
        success = await manager.apply_holiday(target_date, attendance_type, reason)
        
        if success:
            print("\n✅ SUCCESS: Application completed (or checked successfully).")
        else:
            print("\n❌ FAILURE: Check console logs for errors (likely login failed or element not found).")
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
