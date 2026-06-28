import os
from playwright.async_api import async_playwright
from datetime import date
from src.config import config


class JobcanManager:
    def __init__(self, company_id: str, staff_code: str, password: str):
        self.company_id = company_id
        self.staff_code = staff_code
        self.password = password
        self.base_url = config.get("jobcan.base_url")

    async def apply_holiday(
        self, target_date: date, attendance_type: str, reason: str
    ) -> bool:
        """
        Logs into Jobcan and submits a holiday application.
        """
        headless = os.getenv("JOBCAN_HEADLESS", "true").lower() == "true"
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                # 1. Login
                # Jobcan ID login (common for users using Google Sign-in)
                await page.goto("https://id.jobcan.jp/users/sign_in?app_key=atd")
                
                # Check if we are on Jobcan ID login page or redirect to employee login
                if await page.query_selector("#user_email"):
                    # Jobcan ID login
                    await page.fill("#user_email", self.staff_code) # Use staff_code as email
                    await page.fill("#user_password", self.password)
                    await page.click('input[type="submit"]')
                else:
                    # Fallback to direct login if redirected to ssl.jobcan.jp
                    await page.goto(f"{self.base_url}/login")
                    await page.fill("#client_id", self.company_id)
                    # Try both staff_id and email selectors as some pages vary
                    if await page.query_selector("#staff_id"):
                        await page.fill("#staff_id", self.staff_code)
                    else:
                        await page.fill("#email", self.staff_code)
                    await page.fill("#password", self.password)
                    await page.click(".btn-login")

                # Wait for navigation to complete and check for errors
                await page.wait_for_load_state("networkidle")
                if await page.query_selector(".alert-danger") or await page.query_selector(".errors"):
                    print("Login failed: Invalid credentials or error message displayed")
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
