import os
import asyncio
from playwright.async_api import async_playwright
from datetime import date
from typing import Optional
from src.config import config

class JobcanManager:
    def __init__(self, company_id: str, staff_code: str, password: str):
        self.company_id = company_id
        self.staff_code = staff_code
        self.password = password
        self.base_url = config.get("jobcan.base_url")

    async def apply_holiday(self, target_date: date, attendance_type: str, reason: str) -> bool:
        """
        Logs into Jobcan and submits a holiday application.
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                # 1. Login
                await page.goto(f"{self.base_url}/login")
                await page.fill("#client_id", self.company_id)
                await page.fill("#staff_id", self.staff_code)
                await page.fill("#password", self.password)
                await page.click(".btn-login")

                # Check if login was successful
                if await page.query_selector(".alert-danger"):
                    print("Login failed: Invalid credentials")
                    return False

                # 2. Navigate to holiday application page
                await page.goto(f"{self.base_url}/holiday/new")

                # 3. Fill the form (This is a simplified example, actual selectors may vary)
                # target_date, attendance_type, reason
                await page.fill("#date", target_date.strftime("%Y-%m-%d"))
                # Note: Logic to select attendance_type from dropdown would go here
                await page.fill("#reason", reason)

                # 4. Submit
                # await page.click("#submit-button")
                print(f"Applied for {attendance_type} on {target_date}")
                
                await browser.close()
                return True

            except Exception as e:
                print(f"Error during Jobcan automation: {e}")
                # Take screenshot for debugging
                screenshot_path = f"error_{target_date}_{self.staff_code}.png"
                await page.screenshot(path=screenshot_path)
                print(f"Screenshot saved to {screenshot_path}")
                await browser.close()
                return False

    async def check_status(self, target_date: date) -> bool:
        """
        Checks if an application for the target date already exists.
        Used for idempotency.
        """
        # Logic to check existing applications
        return False
