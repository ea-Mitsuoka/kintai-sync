import pytest
from unittest.mock import patch, MagicMock
from datetime import date
from src.jobcan import JobcanManager


@pytest.mark.asyncio
@patch("src.jobcan.async_playwright")
async def test_apply_holiday_success(mock_playwright):
    # Mock playwright async context manager and browser/page
    mock_pw_instance = mock_playwright.return_value.__aenter__.return_value
    mock_browser = await mock_pw_instance.chromium.launch()
    mock_context = await mock_browser.new_context()
    mock_page = await mock_context.new_page()

    # Simple success case: no .alert-danger found
    mock_page.query_selector.return_value = None

    manager = JobcanManager("C1", "S1", "pass")
    success = await manager.apply_holiday(date(2026, 6, 27), "morning_off", "Sick")

    assert success is True
    # Verify navigation
    mock_page.goto.assert_any_call("https://ssl.jobcan.jp/employee/login")


@pytest.mark.asyncio
@patch("src.jobcan.async_playwright")
async def test_apply_holiday_login_failure(mock_playwright):
    mock_pw_instance = mock_playwright.return_value.__aenter__.return_value
    mock_browser = await mock_pw_instance.chromium.launch()
    mock_context = await mock_browser.new_context()
    mock_page = await mock_context.new_page()

    # Simulate login failure
    mock_page.query_selector.return_value = MagicMock()  # alert-danger exists

    manager = JobcanManager("C1", "S1", "pass")
    success = await manager.apply_holiday(date(2026, 6, 27), "morning_off", "Sick")

    assert success is False
